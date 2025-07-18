from django.db import models

class SystemEarnings(models.Model):
    total_volume = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_transactions = models.PositiveIntegerField(default=0)
    total_successful_transactions = models.PositiveIntegerField(default=0)
    total_failed_transactions = models.PositiveIntegerField(default=0)
    total_platform_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_clients = models.PositiveIntegerField(default=0)
    total_clients_with_finances = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_clients_with_positive_balance = models.PositiveIntegerField(default=0)
    total_clients_with_negative_balance = models.PositiveIntegerField(default=0)
    total_clients_with_zero_balance = models.PositiveIntegerField(default=0)
    total_clients_with_finances_updated_today = models.PositiveIntegerField(default=0)
    total_clients_with_finances_updated_this_week = models.PositiveIntegerField(default=0)
    total_clients_with_finances_updated_this_month = models.PositiveIntegerField(default=0)
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
    