from django.db import models


class UnifiedOrderRequest(models.Model):
    timestamp = models.BigIntegerField()
    channel = models.IntegerField(choices=((1, 'MTN'), (2, 'Airtel')))
    out_trade_no = models.CharField(max_length=36)
    amount = models.IntegerField()
    transaction_type = models.IntegerField(choices=((1, 'Collection'), (2, 'Disbursement')))
    trader_id = models.CharField(max_length=20)
    trader_full_name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)

    def __str__(self):
        return self.out_trade_no


class UnifiedOrderResponse(models.Model):
    status_code = models.IntegerField()
    succeeded = models.BooleanField()
    errors = models.TextField(null=True, blank=True)
    extras = models.TextField(null=True, blank=True)
    timestamp = models.BigIntegerField()
    
    out_trade_no = models.CharField(max_length=36)
    transaction_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=6,default=0.00)  # Base amount before fees
    actual_payment_amount = models.DecimalField(max_digits=12, decimal_places=6)
    actual_collect_amount = models.DecimalField(max_digits=12, decimal_places=6)
    payer_charge = models.DecimalField(max_digits=12, decimal_places=6)  # Aggregator's fee
    payee_charge = models.DecimalField(max_digits=12, decimal_places=6)  # Your platform fee
    channel_charge = models.DecimalField(max_digits=12, decimal_places=6)
    client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, related_name='orders')

    def __str__(self):
        return self.transaction_id
    
class OrderQueryRequest(models.Model):
    timestamp = models.BigIntegerField()
    out_trade_no = models.CharField(max_length=36)


class OrderQueryResponse(models.Model):
    status_code = models.IntegerField()
    succeeded = models.BooleanField()
    errors = models.TextField(null=True, blank=True)
    extras = models.TextField(null=True, blank=True)
    timestamp = models.BigIntegerField()

    pay_status = models.IntegerField(choices=((0, 'Processing'), (1, 'Success'), (2, 'Failed')))
    pay_time = models.DateTimeField(null=True, blank=True)
    out_trade_no = models.CharField(max_length=36)
    transaction_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=6)
    actual_payment_amount = models.DecimalField(max_digits=12, decimal_places=6)
    actual_collect_amount = models.DecimalField(max_digits=12, decimal_places=6)
    payer_charge = models.DecimalField(max_digits=12, decimal_places=6)
    payee_charge = models.DecimalField(max_digits=12, decimal_places=6)
    pay_message = models.CharField(max_length=255, null=True, blank=True)


class PaymentNotification(models.Model):
    pay_status = models.IntegerField(choices=((0, 'Processing'), (1, 'Success'), (2, 'Failed')))
    pay_time = models.DateTimeField(null=True, blank=True)
    out_trade_no = models.CharField(max_length=36)
    transaction_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=6)
    actual_payment_amount = models.DecimalField(max_digits=12, decimal_places=6)
    actual_collect_amount = models.DecimalField(max_digits=12, decimal_places=6)
    payer_charge = models.DecimalField(max_digits=12, decimal_places=6)
    payee_charge = models.DecimalField(max_digits=12, decimal_places=6)
    pay_message = models.CharField(max_length=255, null=True, blank=True)


class PrepaidBillRequest(models.Model):
    timestamp = models.BigIntegerField()
    channel = models.IntegerField(choices=((1, 'MTN'), (2, 'Airtel')))
    transaction_type = models.IntegerField(choices=((1, 'Collection'), (2, 'Disbursement')))
    trader_id = models.CharField(max_length=20)
    amount = models.IntegerField()


class PrepaidBillResponse(models.Model):
    status_code = models.IntegerField()
    succeeded = models.BooleanField()
    errors = models.TextField(null=True, blank=True)
    extras = models.TextField(null=True, blank=True)
    timestamp = models.BigIntegerField()

    trader_id = models.CharField(max_length=20)
    given_name = models.CharField(max_length=50)
    family_name = models.CharField(max_length=50)
    full_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=6)
    service_charge = models.DecimalField(max_digits=12, decimal_places=6)
    service_charge_rate = models.DecimalField(max_digits=5, decimal_places=2)


class BalanceRequest(models.Model):
    timestamp = models.BigIntegerField()


class BalanceResponse(models.Model):
    status_code = models.IntegerField()
    succeeded = models.BooleanField()
    errors = models.TextField(null=True, blank=True)
    extras = models.TextField(null=True, blank=True)
    timestamp = models.BigIntegerField()

    balance = models.DecimalField(max_digits=12, decimal_places=6)


class StatementRequest(models.Model):
    timestamp = models.BigIntegerField()
    start_time = models.CharField(max_length=8, null=True, blank=True)  # format: yyyyMMdd
    end_time = models.CharField(max_length=8, null=True, blank=True)  # format: yyyyMMdd

class StatementResponse(models.Model):
    status_code = models.IntegerField()
    succeeded = models.BooleanField()
    errors = models.TextField(null=True, blank=True)
    extras = models.TextField(null=True, blank=True)
    timestamp = models.BigIntegerField()

    statement_data = models.JSONField()  # Store the statement data as JSON