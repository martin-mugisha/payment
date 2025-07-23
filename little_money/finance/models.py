from django.db import models

from staff.models import Staff

class SystemEarnings(models.Model):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_volume = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_transactions = models.PositiveIntegerField(default=0)
    total_successful_transactions = models.PositiveIntegerField(default=0)
    total_failed_transactions = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Total Earnings: {self.total_earnings}"
    
    def save(self, *args, **kwargs):
        self.pk = 1  # Always enforce single row
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]

    class Meta:
        verbose_name_plural = "System Earnings"
        ordering = ['-last_updated']
    @property
    def net_platform_earnings(self):
        staff_commission = StaffCommissionAggregate.load().total_commission
        return self.total_earnings - staff_commission

class PlatformSettings(models.Model):
    platform_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Platform Fee: {self.platform_fee_percent}%"

class PlatformFeeHistory(models.Model):
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Platform Fee {self.percentage}% at {self.created_at}"

    class Meta:
        ordering = ['-created_at']
    
class MonthlyEarnings(models.Model):
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    total_volume = models.DecimalField(max_digits=10, decimal_places=2)
    total_transactions = models.PositiveIntegerField()
    total_successful_transactions = models.PositiveIntegerField()
    total_failed_transactions = models.PositiveIntegerField()
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    snapshot_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('year', 'month')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"Earnings for {self.month}/{self.year}: {self.total_earnings}"

class Payout(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=15, decimal_places=2)  
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    requested_on = models.DateField()

    def __str__(self):
        return f"Payout to {self.staff.name} - {self.amount} ({self.status})"
    
class StaffCommissionAggregate(models.Model):
    total_commission = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Total Staff Commissions: {self.total_commission}"

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]

    class Meta:
        verbose_name_plural = "Staff Commission Totals"
