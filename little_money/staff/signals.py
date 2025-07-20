# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RecentTransaction, Transaction, Staff

@receiver(post_save, sender=RecentTransaction)
def create_or_update_transaction(sender, instance, **kwargs):
    # Get staff via client if possible (adjust logic to fit your model structure)
    staff = instance.client.assigned_staff.first().staff if instance.client.assigned_staff.exists() else None

    # Create or update the linked transaction
    transaction, created = Transaction.objects.update_or_create(
        recent_transaction=instance,
        defaults={
            'staff': staff,
            'name': f"{instance.client.name}",
            'status': 'completed',  # Or another status
            'reason': f"Sent to {instance.recipient}",
            'amount': instance.amount,
        }
    )
