from django.db import models
from django.conf import settings

class PlatformSettings(models.Model):
    platform_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Platform Fee: {self.platform_fee_percent}%"

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True)

    base_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    platform_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)