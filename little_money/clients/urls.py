from django.urls import path
from .views import (
                    overview_dashboard, 
                    transactions, 
                    payments, 
                    accounts, 
                    settings, 
                    help_support, 
                    force_password_change_view,
                    download_statement,
                    download_receipt
                    )

app_name = 'clients'

urlpatterns = [
    path('overview/', overview_dashboard, name='overview_dashboard'),
    path('transactions/', transactions, name='transactions'),
    path('payments/', payments, name='payments'),
    path('accounts/', accounts, name='accounts'),
    path('settings/', settings, name='settings'),
    path('help-support/', help_support, name='help_support'),
    path('force-password-change/', force_password_change_view, name='force_password_change'),
    path('download-statement/', download_statement, name='download-statements'),
    path('download-receipt/<str:transaction_id>/', download_receipt, name='download-receipt'),
]
