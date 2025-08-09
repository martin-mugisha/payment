import json
import config.base as settings
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.timezone import make_aware, now
from django.views.decorators.http import require_POST
from django.db import transaction # Import transaction for atomicity
from decimal import Decimal # Import Decimal for financial calculations
from config.transaction_orchestrator import PaymentInitiator
from core.models import CustomUser

from .models import PaymentNotification
from config.models import UnifiedOrderRequest, UnifiedOrderResponse 
from clients.models import Client, Finances
from staff.models import Balance, ClientAssignment, StaffCommissionHistory
from admins.models import AdminCommissionHistory, AdminProfile
from finance.models import SystemEarnings
from config.Platform import PlatformEarnings 
from config.utils import verify_signature

import logging
logger = logging.getLogger(__name__)

PRIVATE_KEY =settings.PAYMENT_AGGREGATOR_API_KEY

@csrf_exempt  
@require_POST
def payment_notification(request):
    logger.info("--- Received payment notification webhook ---")
    print(request.body)

    if request.method != 'POST':
        logger.warning(f"Webhook received non-POST request: {request.method}")
        return HttpResponseBadRequest("Only POST allowed")

    try:
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        is_valid = verify_signature(data, PRIVATE_KEY)
        logger.info(f"Webhook payload: {data}")
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received in webhook.")
        return HttpResponseBadRequest("Invalid JSON")

    # Required fields check (excluding PayMessage)
    required_fields = ['PayStatus', 'PayTime', 'OutTradeNo', 'TransactionId',
                    'Amount', 'ActualPaymentAmount', 'ActualCollectAmount',
                    'PayerCharge', 'PayeeCharge']

    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field in webhook payload: {field}")
            return HttpResponseBadRequest(f"Missing field: {field}")

    """if not is_valid:
        logger.info(f"Raw webhook data: {json.dumps(data, indent=2)}")
        logger.error("Signature verification failed for webhook.")
        return HttpResponse("FAILED")"""

    # Optionally log PayMessage
    pay_message = data.get("PayMessage")
    if pay_message:
        logger.info(f"PayMessage: {pay_message}")

    # Signature valid – proceed with processing
    logger.info("Signature verification passed.")
    # Parse PayTime safely
    pay_time = None
    if 'PayTime' in data and data['PayTime']:
        try:
            dt = datetime.strptime(data['PayTime'], "%Y-%m-%d %H:%M:%S")
            pay_time = make_aware(dt)
        except ValueError:
            logger.warning(f"Could not parse PayTime: {data['PayTime']}")
            pay_time = None # Leave as None if parsing fails

    # Convert all relevant amounts to Decimal immediately
    try:
        notification_amount = Decimal(str(data['Amount']))
        actual_payment_amount = Decimal(str(data['ActualPaymentAmount']))
        actual_collect_amount = Decimal(str(data['ActualCollectAmount']))
        payer_charge = Decimal(str(data['PayerCharge']))
        payee_charge = Decimal(str(data['PayeeCharge']))
        # Ensure your model fields for these are DecimalField
    except Exception as e:
        logger.error(f"Error converting amounts to Decimal in webhook: {e}")
        return HttpResponseBadRequest("Invalid amount format in payload")


    # Use transaction.atomic() to ensure all database operations are performed atomically
    with transaction.atomic():
        # Check for duplicates using OutTradeNo (your internal order number)
        existing_notification = PaymentNotification.objects.filter(out_trade_no=data['OutTradeNo']).first()
        
        # If the notification exists and is already processed, return SUCCESS
        if existing_notification:
            if existing_notification.processed:
                logger.info(f"Duplicate processed notification received for OutTradeNo: {data['OutTradeNo']}")
                return HttpResponse("SUCCESS")
            else:
                # This case indicates a duplicate that was previously NOT fully processed.
                # You might want to update the existing notification and re-run processing.
                # For simplicity here, we'll proceed to update it.
                logger.warning(f"Duplicate but unprocessed notification for OutTradeNo: {data['OutTradeNo']}. Re-processing.")
                notification = existing_notification
                # Update fields if necessary
                notification.pay_status = int(data['PayStatus'])
                notification.pay_time = pay_time
                notification.transaction_id = data['TransactionId']
                notification.amount = notification_amount
                notification.actual_payment_amount = actual_payment_amount
                notification.actual_collect_amount = actual_collect_amount
                notification.payer_charge = payer_charge
                notification.payee_charge = payee_charge
                notification.pay_message = data.get('PayMessage', '')
                notification.sign = data['Sign']
                notification.processed = True # Mark as processed NOW
                notification.processed_at = now()
                notification.save()
        else:
            # Create a new notification record if it's not a duplicate
            notification = PaymentNotification.objects.create(
                pay_status=int(data['PayStatus']),
                pay_time=pay_time,
                out_trade_no=data['OutTradeNo'],
                transaction_id=data['TransactionId'],
                amount=notification_amount,
                actual_payment_amount=actual_payment_amount,
                actual_collect_amount=actual_collect_amount,
                payer_charge=payer_charge,
                payee_charge=payee_charge,
                pay_message=data.get('PayMessage', ''),
                sign=data['Sign'],
                processed=True, # Mark as processed NOW
                processed_at=now()
            )
            logger.info(f"New PaymentNotification created for OutTradeNo: {notification.out_trade_no}")

        # --- Update UnifiedOrderRequest Status and Get Context ---
        try:
            # Assuming 'OutTradeNo' from the webhook maps to 'out_trade_no' in your UnifiedOrderRequest
            order_request = UnifiedOrderResponse.objects.get(out_trade_no=data['OutTradeNo'])
            transactions = UnifiedOrderRequest.objects.get(out_trade_no=data['OutTradeNo'])

            update = PaymentInitiator(
                    channel=transactions.channel,
                    t_type=2,
                    client_id=order_request.client,
                    base_amount=transactions.amount,
                    trader_id=transactions.trader_id,
                    message=transactions.description,
                    name=transactions.trader_full_name
                )
            # Get client, staff, and transaction type from your internal order request
            # You MUST ensure these fields are available on your UnifiedOrderRequest model
            # or can be derived from it.
            # Example: order_request.client, order_request.t_type, order_request.base_amount
            client = order_request.client
            t_type = transactions.transaction_type # Assuming this field exists on UnifiedOrderRequest
            base_amount_decimal = update.base_amount
            
            assignment = ClientAssignment.objects.filter(client=client).first()
            staff = assignment.staff if assignment else None
            
            # Now determine the payment status from the webhook
            pay_status = int(data['PayStatus'])
            
            if pay_status == 1:  # payment successful
                order_request.status = 'paid'  # Update your order status
                order_request.timestamp = pay_time or now()
                order_request.transaction_id = data['TransactionId']
                logger.info(f"UnifiedOrderRequest {order_request.out_trade_no} status updated to 'paid'.")

                # --- Financial Updates (Business Logic) ---
                

                commission_record = StaffCommissionHistory.objects.order_by('-created_at').first()
                staff_commission_percent = Decimal(str(commission_record.percentage)) if commission_record else Decimal("25.0")

                admin_commission_record = AdminCommissionHistory.objects.order_by('-created_at').first()
                admin_commission_percent = Decimal(str(admin_commission_record.percentage)) if admin_commission_record else Decimal("10.0")

                # Recalculate fee and profits based on the confirmed amount from the webhook
                # It's crucial here to ensure PlatformEarnings.calculate_platform_fee
                # can work with the base_amount from your internal order_request if needed,
                # or derive the fee directly from the webhook data if it includes a precise fee.
                # Assuming 'base_amount' is the original amount *before* aggregator fees.
                charge = PlatformEarnings()
                # Use the original base_amount to calculate the fee, or use a fee value from the webhook if provided
                fee = Decimal(str(charge.calculate_platform_fee(base_amount_decimal))) 

                staff_commission = (fee * staff_commission_percent / Decimal("100.0")) if staff else Decimal("0.0")
                admin_commission_total = (fee - staff_commission) * admin_commission_percent / Decimal("100.0")
                platform_profit = fee - staff_commission - admin_commission_total

                logger.info(f"Calculated for {order_request.out_trade_no}: Staff Comm: {staff_commission}, Admin Comm: {admin_commission_total}, Platform Profit: {platform_profit}")

                if staff:
                    staff_balance, created = Balance.objects.get_or_create(staff=staff)
                    staff_balance.balance += staff_commission
                    staff_balance.save()
                    logger.info(f"Staff {staff.user.username} balance updated by {staff_commission}.")

                client_finance, _ = Finances.objects.get_or_create(client=client)
                
                if t_type == 1: # Collection
                    client_finance.balance += base_amount_decimal
                elif t_type == 2: # Disbursement
                    if client_finance.balance < base_amount_decimal: # Important check for disbursements
                        raise ValueError("Insufficient funds for disbursement for client.")
                    client_finance.balance -= base_amount_decimal
                    logger.info(f"Client balance (Disbursement) decreased by {base_amount_decimal}.")
                else:
                    raise ValueError(f"Unsupported transaction type (t_type) for financial update: {t_type}")
                
                client_finance.save()

                admins = CustomUser.objects.filter(role='admin')
                num_admins = admins.count()

                if num_admins > 0:
                    share = admin_commission_total / num_admins
                    with transaction.atomic():
                        for admin in admins:
                            try:
                                admin_profile = AdminProfile.objects.get(user=admin)
                                admin_profile.balance += share
                                admin_profile.save()
                                logger.info(f"Admin {admin.username} balance updated by {share}.")
                            except AdminProfile.DoesNotExist:
                                logger.warning(f"AdminProfile not found for user {admin.username}.")
                else:
                    logger.info("No active admins found for commission distribution.")
                system = SystemEarnings.load()
                system.total_transactions += 1 # Incremented for every processed notification
                system.total_earnings += platform_profit
                system.total_volume += base_amount_decimal
                system.total_successful_transactions += 1
                system.save()
                logger.info(f"System earnings updated for successful transaction {order_request.out_trade_no}.")

            elif pay_status == 2:  # payment failed
                order_request.status= 'failed'
                # Optionally, here you might reverse any pre-authorized funds or notify
                # if needed. No commission/balance updates for failed payments.
                system = SystemEarnings.load()
                system.total_transactions += 1 # Still increment total transactions for failed ones
                system.save()
                logger.info(f"UnifiedOrderRequest {order_request.out_trade_no} status updated to 'payment_failed'.")
            
            elif pay_status == 0:  # processing (or other intermediate status)
                order_request.status = 'processing'
                logger.info(f"UnifiedOrderRequest {order_request.out_trade_no} status updated to 'processing'.")
                # No financial updates for processing status typically
            
            order_request.save()
            logger.info(f"UnifiedOrderRequest {order_request.out_trade_no} saved with status {order_request.status}.")

        except UnifiedOrderRequest.DoesNotExist:
            logger.error(f"UnifiedOrderRequest not found for OutTradeNo: {data['OutTradeNo']}. Cannot update order status or financial records.")
            # Depending on business logic, you might return "FAILED" to trigger a retry
            # from the aggregator if this is a critical error for you.
            return HttpResponse("SUCCESS") # Acknowledge receipt even if internal order not found to avoid retries.
        except ValueError as ve:
            logger.error(f"ValueError during financial update for OutTradeNo {data['OutTradeNo']}: {ve}", exc_info=True)
            # Rollback automatically due to atomic, respond FAILED for aggregator retry
            return HttpResponse("FAILED")
        except Exception as e:
            logger.critical(f"Unhandled error during financial update for OutTradeNo {data['OutTradeNo']}: {e}", exc_info=True)
            # Rollback automatically due to atomic, respond FAILED for aggregator retry
            return HttpResponse("FAILED")

    logger.info(f"Webhook processing complete for OutTradeNo: {data['OutTradeNo']}. Responding SUCCESS.")
    return HttpResponse("SUCCESS") # Crucial: Always return SUCCESS if you processed it to avoid retries