# config/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta
from .models import UnifiedOrderResponse
from finance.models import SystemEarnings, PlatformSettings
from clients.models import Finances

@receiver(post_save, sender=UnifiedOrderResponse)
def update_system_earnings(sender, instance, created, **kwargs):
    if not created:
        return  # Only process new transactions to avoid double-counting

    earnings = SystemEarnings.load()  # Use the model's load method
    platform_settings = PlatformSettings.objects.first()  # Get platform fee settings

    # Calculate platform fee (if not provided by aggregator)
    platform_fee_percent = platform_settings.platform_fee_percent / 100 if platform_settings else 0.01
    expected_platform_fee = instance.amount * platform_fee_percent  # Your fee based on base amount

    # Update SystemEarnings
    earnings.total_transactions += 1
    if instance.succeeded:
        earnings.total_successful_transactions += 1
        # Total volume: base amount + your platform fee + aggregator's fee
        earnings.total_volume += instance.actual_collect_amount
        # Your earnings: platform fee (use payee_charge if it matches your calculation)
        earnings.total_earnings += instance.payee_charge
        earnings.total_platform_fees += instance.payee_charge
    else:
        earnings.total_failed_transactions += 1

    # Update clients with finances
    if instance.succeeded and instance.client:
        earnings.total_clients_with_finances += 1
        # Update client finances
        finances, _ = Finances.objects.get_or_create(client=instance.client)
        finances.balance += instance.amount  # Add base amount to client balance
        finances.save()

        # Update balance-related metrics
        if finances.balance > 0:
            earnings.total_clients_with_positive_balance += 1
        elif finances.balance < 0:
            earnings.total_clients_with_negative_balance += 1
        else:
            earnings.total_clients_with_zero_balance += 1

        # Update time-based metrics
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        if finances.last_updated.date() == today:
            earnings.total_clients_with_finances_updated_today += 1
        if finances.last_updated.date() >= week_start:
            earnings.total_clients_with_finances_updated_this_week += 1
        if finances.last_updated.date() >= month_start:
            earnings.total_clients_with_finances_updated_this_month += 1

    earnings.save()