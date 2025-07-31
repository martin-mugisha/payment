from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db import transaction # Import transaction
from .models import PrepaidBillResponse, UnifiedOrderResponse, OrderQueryResponse
from .aggregator import PaymentResults, PrepaidBill, UnifiedOrder
from clients.models import Client
from finance.models import SystemEarnings
import time

def process_transaction(channel: int, t_type: int, client_id: int, base_amount: int, trader_id: str, message: str, name: str):
    try:
        client = get_object_or_404(Client, id=client_id)
        base_amount_decimal = Decimal(base_amount) # Convert to Decimal early

        # --- PrepaidBill Logic ---
        bill = PrepaidBill()
        bill_response = bill.get_bill(
            trader_id=trader_id,
            amount=int(base_amount_decimal * 100), # Use decimal version for multiplication
            channel=channel,
            transaction_type=t_type
        )

        if "error" in bill_response:
            return JsonResponse({"status": "error", "message": bill_response["error"]}, status=500)

        data = bill_response.get("Data")
        if not isinstance(data, dict):
            return JsonResponse({
                "status": "error",
                "message": "Invalid or missing 'Data' in bill response."
            }, status=500)

        prepaid_bill_resp_obj = PrepaidBillResponse(
            status_code=bill_response.get("StatusCode", 0),
            succeeded=bill_response.get("Succeeded"),
            errors=bill_response.get("Errors"),
            extras=bill_response.get("Extras"),
            timestamp=bill_response.get("Timestamp", int(time.time())),
            trader_id=data.get("TraderID", trader_id),
            full_name=data.get("FullName", name),
            amount=base_amount_decimal,
            service_charge=Decimal(str(data.get("ServiceCharge", '0.00'))),
            service_charge_rate=Decimal(str(data.get("ServiceChargeRate", '0.00'))),
        )
        prepaid_bill_resp_obj.save()

        if prepaid_bill_resp_obj.status_code != 200:
            error_message = prepaid_bill_resp_obj.errors or "Bill request failed with unknown error."
            return JsonResponse({"status": "error", "message": error_message}, status=400)

        # --- UnifiedOrder Logic ---
        unifiedorder = UnifiedOrder()
        unifiedorder_response, _ = unifiedorder.create_order( # status_code is returned but not used
            trader_id=trader_id,
            amount=int(base_amount_decimal * 100), # Use decimal version
            channel=channel,
            transaction_type=t_type,
            name=data.get("FullName"),
            message=message
        )

        unified_order_resp_obj = UnifiedOrderResponse(
            status_code=unifiedorder_response.get("StatusCode", 0),
            succeeded=unifiedorder_response.get("Succeeded", False),
            errors=unifiedorder_response.get("Errors"),
            extras=unifiedorder_response.get("Extras"),
            timestamp=unifiedorder_response.get("Timestamp", int(time.time())),
            status = "pending",
            out_trade_no=unifiedorder_response["Data"].get("OutTradeNo", "100000006"),
            transaction_id=unifiedorder_response["Data"].get("TransactionId", "100000006"),
            amount=Decimal(str(unifiedorder_response["Data"].get("Amount", base_amount_decimal))),
            actual_payment_amount=Decimal(str(unifiedorder_response["Data"].get("ActualPaymentAmount", base_amount_decimal))), # Consistent
            actual_collect_amount=Decimal(str(unifiedorder_response["Data"].get("ActualCollectAmount", base_amount_decimal))), # Consistent
            payer_charge=Decimal(str(unifiedorder_response["Data"].get("PayerCharge", '0.00'))),
            payee_charge=Decimal(str(unifiedorder_response["Data"].get("Payee_Charge", '0.00'))),
            channel_charge=Decimal(str(unifiedorder_response["Data"].get("ChannelCharge", '0.00'))),
            client=client
        )
        unified_order_resp_obj.save()

        transaction_succeeded = False # Flag to track overall success for system earnings

        if unified_order_resp_obj.status_code == 200:
            print("Unified order API call succeeded immediately.")
            transaction_succeeded = True
        else:
            print("Unified order API call failed initially. Attempting retry via query...")
            max_attempts = 3
            attempt = 0
            query_response = None
            while attempt < max_attempts:
                query_result = PaymentResults()
                query_response = query_result.get_result(unified_order_resp_obj.out_trade_no) # Use saved OutTradeNo
                if query_response and query_response.get("StatusCode") == 200 and query_response.get("Succeeded"):
                    transaction_succeeded = True
                    break
                attempt += 1
                time.sleep(1)

            order_query_resp_obj = OrderQueryResponse(
                status_code=query_response.get("StatusCode") if query_response else 0,
                succeeded=query_response.get("Succeeded", False) if query_response else False,
                errors=query_response.get("Errors") if query_response else "No query response",
                extras=query_response.get("Extras") if query_response else {},
                timestamp=query_response.get("Timestamp", int(time.time())) if query_response else int(time.time()),
                pay_status=query_response["Data"].get("PayStatus") if query_response and "Data" in query_response else None,
                pay_time=query_response["Data"].get("PayTime") if query_response and "Data" in query_response else None,
                out_trade_no=query_response["Data"].get("OutTradeNo", unified_order_resp_obj.out_trade_no) if query_response and "Data" in query_response else unified_order_resp_obj.out_trade_no,
                transaction_id=query_response["Data"].get("TransactionId", "100000006") if query_response and "Data" in query_response else "100000006",
                amount=Decimal(str(query_response["Data"].get("Amount", base_amount_decimal))) if query_response and "Data" in query_response else base_amount_decimal,
                actual_payment_amount=Decimal(str(query_response["Data"].get("ActualPaymentAmount", base_amount_decimal))) if query_response and "Data" in query_response else base_amount_decimal,
                actual_collect_amount=Decimal(str(query_response["Data"].get("ActualCollectAmount", base_amount_decimal))) if query_response and "Data" in query_response else base_amount_decimal,
                payer_charge=Decimal(str(query_response["Data"].get("PayerCharge", '0.00'))) if query_response and "Data" in query_response else Decimal('0.00'),
                payee_charge=Decimal(str(query_response["Data"].get("PayeeCharge", '0.00'))) if query_response and "Data" in query_response else Decimal('0.00'),
                pay_message=query_response["Data"].get("PayMessage", "") if query_response and "Data" in query_response else ""
            )
            order_query_resp_obj.save()

            if not transaction_succeeded: # If still not succeeded after retries
                return JsonResponse({"status": "error", "message": order_query_resp_obj.errors or "Transaction failed after multiple attempts."}, status=400)


        # --- System Earnings Update (Atomic) ---
        with transaction.atomic():
            system = SystemEarnings.load() # Reload inside atomic block to get freshest data
            system.total_transactions += 1 # Increment for every transaction attempt
            if transaction_succeeded:
                system.total_successful_transactions += 1
                # total_volume and total_earnings would be updated here if they are part of this function's scope.
                # As per your simplification, they are not, which is fine.
            system.save()

        return JsonResponse({"status": "success"})

    except Exception as e:
        print(f"An error occurred: {e}")
        # Consider logging the full traceback here for debugging in production
        # import traceback
        # traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=500)