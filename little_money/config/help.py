from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from admins.models import AdminCommissionHistory, AdminProfile
from core.models import CustomUser
from .models import PrepaidBillResponse, UnifiedOrderResponse, OrderQueryResponse
from .Platform import PlatformEarnings
from .aggregator import PaymentResults, PrepaidBill, UnifiedOrder
from clients.models import Client, Finances
from staff.models import Balance, ClientAssignment, StaffCommissionHistory
from finance.models import StaffCommissionAggregate, SystemEarnings
import time

def process_transaction(channel: int, t_type: int, client_id: int, base_amount: int, trader_id: str, message: str, name: str):
    try:
        client = get_object_or_404(Client, id=client_id)
        assignment = ClientAssignment.objects.filter(client=client).first()
        staff = assignment.staff if assignment else None

        commission_record = StaffCommissionHistory.objects.order_by('-created_at').first()
        commission_percent = Decimal(str(commission_record.percentage)) if commission_record else Decimal("25.0")

        admin_commission_record = AdminCommissionHistory.objects.order_by('-created_at').first()
        admin_commission_percent = Decimal(str(admin_commission_record.percentage)) if admin_commission_record else Decimal("10.0")

        system = SystemEarnings.load()
        charge = PlatformEarnings()

        fee = charge.calculate_platform_fee(base_amount)
        fee = Decimal(str(fee))  # ensure Decimal

        total_amount = Decimal(base_amount) + fee

        staff_commission = (fee * commission_percent / Decimal("100.0")) if staff else Decimal("0.0")
        admin_commission_total = (fee - staff_commission) * admin_commission_percent / Decimal("100.0")
        platform_profit = fee - staff_commission - admin_commission_total

        if total_amount <= 0:
            return JsonResponse({"status": "error", "message": "Total amount must be greater than zero."}, status=400)

        # 🔽 SKIP PrepaidBill section entirely

        with transaction.atomic():
            unifiedorder = UnifiedOrder()
            unifiedorder_response = unifiedorder.create_order(
                trader_id=trader_id,
                amount=int(total_amount * 100),
                channel=channel,
                transaction_type=t_type,
                name=name,
                message=message
            )

            data = unifiedorder_response.get("Data", {})
            uni_res = UnifiedOrderResponse(
                status_code=unifiedorder_response.get("StatusCode", 0),
                succeeded=unifiedorder_response.get("Succeeded", False),
                errors=unifiedorder_response.get("Errors"),
                extras=unifiedorder_response.get("Extras"),
                timestamp=unifiedorder_response.get("Timestamp", int(time.time())),
                out_trade_no=data.get("OutTradeNo", "100000006"),
                transaction_id=data.get("TransactionId", "100000006"),
                amount=data.get("Amount", base_amount),
                actual_payment_amount=data.get("ActualPaymentAmount", total_amount),
                actual_collect_amount=data.get("ActualCollectAmount", total_amount),
                payer_charge=data.get("PayerCharge", Decimal('0.00')),
                payee_charge=data.get("PayeeCharge", Decimal('0.00')),
                channel_charge=data.get("ChannelCharge", Decimal('0.00')),
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

                admins = CustomUser.objects.filter(role='admin')
                num_admins = admins.count()
                if num_admins > 0:
                    share = admin_commission_total / num_admins
                    for admin in admins:
                        admin.profile.balance += share
                        admin.profile.save()

                system.total_earnings += platform_profit
                system.total_volume += base_amount
                system.total_successful_transactions += 1
                system.save()

            if unifiedorder_response.get("StatusCode") != 200 or not unifiedorder_response.get("Succeeded"):
                max_attempts = 3
                attempt = 0
                query_response = None
                while attempt < max_attempts:
                    query_result = PaymentResults()
                    query_response = query_result.get_result(data.get("OutTradeNo"))
                    if query_response.get("StatusCode") == 200 and query_response.get("Succeeded"):
                        break
                    attempt += 1
                    time.sleep(1)

                if query_response.get("StatusCode") != 200 or not query_response.get("Succeeded"):
                    return JsonResponse({"status": "error", "message": query_response.get("Errors", "Unknown error")}, status=500)

                query_data = query_response.get("Data", {})
                qu_res = OrderQueryResponse(
                    status_code=query_response.get("StatusCode"),
                    succeeded=query_response.get("Succeeded", False),
                    errors=query_response.get("Errors"),
                    extras=query_response.get("Extras"),
                    timestamp=query_response.get("Timestamp", int(time.time())),
                    pay_status=query_data.get("PayStatus"),
                    pay_time=query_data.get("PayTime"),
                    out_trade_no=query_data.get("OutTradeNo"),
                    transaction_id=query_data.get("TransactionId", "100000006"),
                    amount=query_data.get("Amount", base_amount),
                    actual_payment_amount=query_data.get("ActualPaymentAmount", total_amount),
                    actual_collect_amount=query_data.get("ActualCollectAmount", total_amount),
                    payer_charge=query_data.get("PayerCharge", Decimal('0.00')),
                    payee_charge=query_data.get("PayeeCharge", Decimal('0.00')),
                    pay_message=query_data.get("PayMessage", "")
                )
                qu_res.save()

                if not qu_res.succeeded:
                    return JsonResponse({"status": "error", "message": qu_res.errors}, status=400)

            return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)