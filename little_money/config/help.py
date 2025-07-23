from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from admins.models import AdminCommissionHistory, AdminProfile
from core.models import CustomUser
from .models import PrepaidBillResponse, UnifiedOrderResponse, OrderQueryResponse
from .Platform import PlatformEarnings
from .aggregator import PaymentResults, PrepaidBill, UnifiedOrder
from clients.models import Client, Finances
from staff.models import Balance, ClientAssignment, StaffCommissionHistory
from decimal import Decimal
from finance.models import StaffCommissionAggregate, SystemEarnings
import time

def process_transaction(channel:int , t_type:int, client_id:int , base_amount:int, trader_id:str, message:str ,name:str):
    try:
        # Fetch client
        client = get_object_or_404(Client, id=client_id)

        assignment = ClientAssignment.objects.filter(client=client).first()
        staff = assignment.staff if assignment else None

        commission_record = StaffCommissionHistory.objects.order_by('-created_at').first()
        commission_percent = commission_record.percentage if commission_record else 25.0

        system = SystemEarnings.load()
        # Platform fee calculation
        charge = PlatformEarnings()
        fee = charge.calculate_platform_fee(base_amount)
        total_amount = base_amount + fee

        # Staff commission
        staff = assignment.staff if assignment else None
        staff_commission = (fee * commission_percent / 100) if staff else 0


        # Admin commission
        admin_commission_record = AdminCommissionHistory.objects.order_by('-created_at').first()
        admin_commission_percent = admin_commission_record.percentage if admin_commission_record else 10.0
        admin_commission_total = (fee - staff_commission) * admin_commission_percent / 100


        # Remaining after all commissions
        platform_profit = fee - staff_commission - admin_commission_total

        if total_amount <= 0:
            return JsonResponse({"status": "error", "message": "Total amount must be greater than zero."}, status=400)

        # Create bill
        bill = PrepaidBill()
        #trader_id: str, amount: int, channel: int, transaction_type: int
        bill_response = bill.get_bill(
            trader_id=trader_id,
            amount=int(total_amount * 100),  # Convert to smallest currency unit
            channel=channel,
            transaction_type=t_type
        )
        if "error" in bill_response:
            return JsonResponse({"status": "error", "message": bill_response["error"]}, status=500)

        # Save bill response
        with transaction.atomic():
            response = PrepaidBillResponse(
                status_code=bill_response.get("status_code", 0),
                succeeded=bill_response.get("succeeded", False),
                errors=bill_response.get("errors"),
                extras=bill_response.get("extras"),
                timestamp=bill_response.get("timestamp", int(time.time())),
                trader_id=bill_response.get("trader_id", client.trader_id),
                out_trade_no=bill_response.get("out_trade_no", "100000006"),
                transaction_id=bill_response.get("transaction_id", "100000006"),
                full_name=bill_response.get("full_name", client.name),
                channel=bill_response.get("channel", 1),
                amount=base_amount,
                actual_payment_amount=bill_response.get("actual_payment_amount", total_amount),
                actual_collect_amount=bill_response.get("actual_collect_amount", total_amount),
                payer_charge=bill_response.get("payer_charge", Decimal('0.00')),
                payee_charge=bill_response.get("payee_charge", Decimal('0.00')),
                channel_charge=bill_response.get("channel_charge", Decimal('0.00')),
                service_charge=bill_response.get("service_charge", Decimal('0.00')),
                service_charge_rate=bill_response.get("service_charge_rate", Decimal('0.00')),
                client=client
            )
            response.save()
            if not response.succeeded:
                return JsonResponse({"status": "error", "message": response.errors}, status=400)

            # Create unified order
            unifiedorder = UnifiedOrder()
            #trader_id: str, amount: int, channel: int, transaction_type: int, name: str, message: str
            unifiedorder_response = unifiedorder.create_order(
                trader_id=trader_id,
                amount=int(total_amount * 100),
                channel=channel,
                transaction_type=t_type,
                name=name,
                message=message
            )

            # Save unified order response
            uni_res = UnifiedOrderResponse(
                status_code=unifiedorder_response.get("StatusCode", 0),
                succeeded=unifiedorder_response.get("Succeeded", False),
                errors=unifiedorder_response.get("Errors"),
                extras=unifiedorder_response.get("Extras"),
                timestamp=unifiedorder_response.get("Timestamp", int(time.time())),
                out_trade_no=unifiedorder_response["Data"].get("OutTradeNo", "100000006"),
                transaction_id=unifiedorder_response["Data"].get("TransactionId", "100000006"),
                amount=unifiedorder_response["Data"].get("Amount", base_amount),
                actual_payment_amount=unifiedorder_response["Data"].get("ActualPaymentAmount", total_amount),
                actual_collect_amount=unifiedorder_response["Data"].get("ActualCollectAmount", total_amount),
                payer_charge=unifiedorder_response["Data"].get("PayerCharge", Decimal('0.00')),
                payee_charge=unifiedorder_response["Data"].get("PayeeCharge", Decimal('0.00')),
                channel_charge=unifiedorder_response["Data"].get("ChannelCharge", Decimal('0.00')),
                client=client
            )
            uni_res.save()
            system.total_transactions += 1
            if unifiedorder_response.get("StatusCode") == 200:
                if staff:
                    staff_balance, _ = Balance.objects.get_or_create(staff=staff)
                    staff_balance.balance += staff_commission
                    staff_balance.save()

                    staff_comm_total = StaffCommissionAggregate.load()
                    staff_comm_total.total_commission += staff_commission
                    staff_comm_total.save()
                    
                client_finance, _ = Finances.objects.get_or_create(client=client)
                client_finance.balance += Decimal(base_amount)
                client_finance.save()

                # --- Distribute admin commission equally
                admins = CustomUser.objects.filter(role='admin')  # assuming superusers are your admins
                num_admins = admins.count()
                if num_admins > 0:
                    share = admin_commission_total / num_admins
                    for admin in admins:
                        admin.profile.balance += share  # assuming you have admin profile with balance
                        admin.profile.save()
                    # --- Update system earnings
                system.total_earnings += platform_profit
                system.total_volume += base_amount
                system.total_successful_transactions += 1
                system.save()

            # Check unified order response
            if unifiedorder_response.get("StatusCode") != 200 or not unifiedorder_response.get("Succeeded"):
                # Retry querying payment result
                system.total_transactions += 1
                max_attempts = 3
                attempt = 0
                query_response = None
                while attempt < max_attempts:
                    query_result = PaymentResults()
                    query_response = query_result.get_result(unifiedorder_response["Data"]["OutTradeNo"])
                    if query_response.get("StatusCode") == 200 and query_response.get("Succeeded"):
                        break
                    attempt += 1
                    time.sleep(1)  # Wait before retrying

                if query_response.get("StatusCode") != 200 or not query_response.get("Succeeded"):
                    return JsonResponse({"status": "error", "message": query_response.get("Errors", "Unknown error")}, status=500)

                # Save query response
                qu_res = OrderQueryResponse(
                    status_code=query_response.get("StatusCode"),
                    succeeded=query_response.get("Succeeded", False),
                    errors=query_response.get("Errors"),
                    extras=query_response.get("Extras"),
                    timestamp=query_response.get("Timestamp", int(time.time())),
                    pay_status=query_response["Data"].get("PayStatus"),
                    pay_time=query_response["Data"].get("PayTime"),
                    out_trade_no=query_response["Data"].get("OutTradeNo"),
                    transaction_id=query_response["Data"].get("TransactionId", "100000006"),
                    amount=query_response["Data"].get("Amount", base_amount),
                    actual_payment_amount=query_response["Data"].get("ActualPaymentAmount", total_amount),
                    actual_collect_amount=query_response["Data"].get("ActualCollectAmount", total_amount),
                    payer_charge=query_response["Data"].get("PayerCharge", Decimal('0.00')),
                    payee_charge=query_response["Data"].get("PayeeCharge", Decimal('0.00')),
                    pay_message=query_response["Data"].get("PayMessage", "")
                )
                qu_res.save()
                if not qu_res.succeeded:
                    return JsonResponse({"status": "error", "message": qu_res.errors}, status=400)

            return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)