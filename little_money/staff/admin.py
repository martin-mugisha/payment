from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered
from .models import Transaction

# Custom admin for Transaction
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'client_name',
        'transaction_id_display',
        'date_display',
        'time_display',
        'recipient_display',
        'phone_number_display',
        'amount',
        'transaction_type_display',
        'channel_display',
        'status',
    )

    def client_name(self, obj):
        return obj.recent_transaction.client.name if obj.recent_transaction else None

    def transaction_id_display(self, obj):
        return obj.recent_transaction.transaction_id if obj.recent_transaction else None

    def date_display(self, obj):
        return obj.recent_transaction.date if obj.recent_transaction else None

    def time_display(self, obj):
        return obj.recent_transaction.time if obj.recent_transaction else None

    def recipient_display(self, obj):
        return obj.recent_transaction.recipient if obj.recent_transaction else None

    def phone_number_display(self, obj):
        return obj.recent_transaction.phone if obj.recent_transaction else None

    def transaction_type_display(self, obj):
        return obj.recent_transaction.transaction_type if obj.recent_transaction else None

    def channel_display(self, obj):
        return obj.recent_transaction.payment_method if obj.recent_transaction else None


# Keep your auto-registration for all other models
app = apps.get_app_config('staff')
for model in app.get_models():
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass
