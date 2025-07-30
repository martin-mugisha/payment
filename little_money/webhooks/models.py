from django.db import models

class PaymentNotification(models.Model):
    PAY_STATUS_CHOICES = [
        (0, 'Processing'),
        (1, 'Payment Successful'),
        (2, 'Payment Failed'),
    ]

    pay_status = models.IntegerField(choices=PAY_STATUS_CHOICES)
    pay_time = models.DateTimeField(null=True, blank=True)
    out_trade_no = models.CharField(max_length=255, unique=True)  # merchant order no
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    actual_payment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    actual_collect_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payer_charge = models.DecimalField(max_digits=12, decimal_places=2)
    payee_charge = models.DecimalField(max_digits=12, decimal_places=2)
    pay_message = models.TextField(null=True, blank=True)
    sign = models.CharField(max_length=64)
    received_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.out_trade_no} - Status {self.pay_status}"
