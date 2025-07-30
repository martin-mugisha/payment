from django.urls import path
from .views import overview_dashboard, transactions, payments, accounts, settings, help_support, force_password_change_view

app_name = 'clients'

urlpatterns = [
    path('overview/', overview_dashboard, name='overview_dashboard'),
    path('transactions/', transactions, name='transactions'),
    path('payments/', payments, name='payments'),
    path('accounts/', accounts, name='accounts'),
    path('settings/', settings, name='settings'),
    path('help-support/', help_support, name='help_support'),
    path('force-password-change/', force_password_change_view, name='force_password_change'),
]
