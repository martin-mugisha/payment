from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta
from config.models import UnifiedOrderResponse
from finance.models import SystemEarnings, PlatformSettings
from clients.models import Finances

@receiver(post_save, sender=UnifiedOrderResponse)
def update_system_earnings(sender, instance, created, **kwargs):
    if not created:
        return

    earnings = SystemEarnings.load()
    platform_settings = PlatformSettings.objects.first()

    platform_fee_percent = platform_settings.platform_fee_percent / 100 if platform_settings else 0.01
    expected_platform_fee = instance.amount * platform_fee_percent

    earnings.total_transactions += 1
    if instance.succeeded:
        earnings.total_successful_transactions += 1
        earnings.total_volume += instance.actual_collect_amount
        earnings.total_earnings += instance.payee_charge
        earnings.total_platform_fees += instance.payee_charge
    else:
        earnings.total_failed_transactions += 1

    if instance.succeeded and instance.client:
        earnings.total_clients_with_finances += 1
        finances, _ = Finances.objects.get_or_create(client=instance.client)
        finances.balance += instance.amount
        finances.save()

        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        if finances.last_updated.date() == today:
            earnings.total_clients_with_finances_updated_today += 1
        if finances.last_updated.date() >= week_start:
            earnings.total_clients_with_finances_updated_this_week += 1
        if finances.last_updated.date() >= month_start:
            earnings.total_clients_with_finances_updated_this_month += 1

        if finances.balance > 0:
            earnings.total_clients_with_positive_balance += 1
        elif finances.balance < 0:
            earnings.total_clients_with_negative_balance += 1
        else:
            earnings.total_clients_with_zero_balance += 1

    earnings.save()
