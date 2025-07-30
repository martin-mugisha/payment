import json
import config.base as settings
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.timezone import make_aware
from django.utils.timezone import now
from config.models import UnifiedOrderRequest 
from config.utils import verify_signature

from .models import PaymentNotification


PRIVATE_KEY =settings.PAYMENT_AGGREGATOR_API_KEY
@csrf_exempt
def payment_notification(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    # Basic required fields check
    required_fields = ['PayStatus', 'OutTradeNo', 'TransactionId', 'Amount', 
                       'ActualPaymentAmount', 'ActualCollectAmount', 'PayerCharge', 'PayeeCharge', 'Sign']

    for field in required_fields:
        if field not in data:
            return HttpResponseBadRequest(f"Missing field: {field}")

    # Verify signature
    if not verify_signature(data, PRIVATE_KEY):
        return HttpResponse("FAILED")

    # Parse PayTime safely
    pay_time_str = data.get('PayTime')
    pay_time = None
    if pay_time_str:
        try:
            dt = datetime.strptime(pay_time_str, "%Y-%m-%d %H:%M:%S")
            pay_time = make_aware(dt)
        except ValueError:
            pay_time = None

    # Check for duplicates using OutTradeNo (merchant order number)
    existing = PaymentNotification.objects.filter(out_trade_no=data['OutTradeNo']).first()
    if existing:
        # If already processed, respond SUCCESS to avoid retries
        if existing.processed:
            return HttpResponse("SUCCESS")
        else:
            # maybe update or log duplicate notification?
            return HttpResponse("SUCCESS")

    # Save notification
    try:
        notification = PaymentNotification.objects.create(
            pay_status=int(data['PayStatus']),
            pay_time=pay_time,
            out_trade_no=data['OutTradeNo'],
            transaction_id=data['TransactionId'],
            amount=float(data['Amount']),
            actual_payment_amount=float(data['ActualPaymentAmount']),
            actual_collect_amount=float(data['ActualCollectAmount']),
            payer_charge=float(data['PayerCharge']),
            payee_charge=float(data['PayeeCharge']),
            pay_message=data.get('PayMessage', ''),
            sign=data['Sign'],
            processed=True,
            processed_at=datetime.now()
        )
        
        try:
            order = UnifiedOrderRequest .objects.get(order_number=data['OutTradeNo'])
            
            pay_status = int(data['PayStatus'])
            
            if pay_status == 1:  # payment successful
                order.status = 'paid'  # use your order status field names
                order.payment_confirmed_at = pay_time or now()
                order.transaction_id = data['TransactionId']  # if you track this in order
                
                # Optional: trigger email notification
                # order.send_payment_confirmation_email()
                
            elif pay_status == 2:  # payment failed
                order.status = 'payment_failed'
                # Optional: notify user/admin
            
            elif pay_status == 0:  # processing
                order.status = 'processing'
            
            order.save()

            # You can also update other things here:
            # - Log activity
            # - Notify finance system
            # - Update dashboards
            
        except UnifiedOrderRequest .DoesNotExist:
            # Handle if order not found (log, alert, or ignore)
            pass

    except Exception as e:
        # Log the error and respond FAILED to trigger retry
        return HttpResponse("FAILED")

    return HttpResponse("SUCCESS")
