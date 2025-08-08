from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from clients.models import Client as ClientModel, RecentTransaction
from core.models import CustomUser

class Staff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='staff')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Balance(models.Model):
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, null=True, blank=True)
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.staff.name} - Balance: {self.balance}"


class WithdrawHistory(models.Model):
    NETWORK_CHOICES = [
        ('MTN', 'MTN'),
        ('Airtel', 'Airtel'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'), 
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='withdrawals')
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=20)
    network = models.CharField(max_length=10, choices=NETWORK_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    requested_on = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.name} ({self.amount}) - {self.status}"

class ClientAssignment(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='assigned_clients')
    client = models.ForeignKey(ClientModel, on_delete=models.CASCADE, related_name='assigned_staff')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('staff', 'client')
    def __str__(self):
        return f"{self.staff.username} → {self.client.name}"


class Transaction(models.Model):
    recent_transaction = models.OneToOneField(
        'clients.RecentTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_transaction'
    )
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    reason = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return f"Transaction {self.name} - {self.status} - {self.amount}"

    # === Helper properties for display ===
    @property
    def client_name(self):
        return self.recent_transaction.client.name if self.recent_transaction else None

    @property
    def transaction_id(self):
        return self.recent_transaction.transaction_id if self.recent_transaction else None

    @property
    def date(self):
        return self.recent_transaction.date if self.recent_transaction else None

    @property
    def time(self):
        return self.recent_transaction.time if self.recent_transaction else None

    @property
    def recipient(self):
        return self.recent_transaction.recipient if self.recent_transaction else None

    @property
    def phone_number(self):
        return self.recent_transaction.phone if self.recent_transaction else None

    @property
    def transaction_type(self):
        return self.recent_transaction.transaction_type if self.recent_transaction else None

    @property
    def channel(self):
        return self.recent_transaction.payment_method if self.recent_transaction else None


class StaffCommissionHistory(models.Model):
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Staff Commission {self.percentage}% at {self.created_at}"

    class Meta:
        ordering = ['-created_at']
