from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from clients.models import Client as ClientModel
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
        return f"{self.client.name} - Balance: {self.balance}"

class WithdrawHistory(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=50)
    network = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_withdrawn = models.DateTimeField()

    def __str__(self):
        return f"WithdrawHistory {self.name} {self.amount} on {self.date_withdrawn}"

class ClientAssignment(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='assigned_clients')
    client = models.ForeignKey(ClientModel, on_delete=models.CASCADE, related_name='assigned_staff')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff.username} → {self.client.name}"

class Earnings(models.Model):
    EARNING_TYPE_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('highest', 'Highest'),
        ('lowest', 'Lowest'),
    ]
    type = models.CharField(max_length=10, choices=EARNING_TYPE_CHOICES)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True)
    day_or_week = models.CharField(max_length=50, blank=True, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Earnings {self.type} - {self.staff or self.day_or_week}: {self.amount}"

class Transaction(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    reason = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"Transaction {self.name} - {self.status} - {self.amount}"

class StaffCommissionHistory(models.Model):
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Staff Commission {self.percentage}% at {self.created_at}"

    class Meta:
        ordering = ['-created_at']
