from django.urls import path
from .views import overview_dashboard, transactions, payments, accounts, settings, help_support

app_name = 'client'

urlpatterns = [
    path('overview/', overview_dashboard, name='overview_dashboard'),
    path('transactions/', transactions, name='transactions'),
    path('payments/', payments, name='payments'),
    path('accounts/', accounts, name='accounts'),
    path('settings/', settings, name='settings'),
    path('help-support/', help_support, name='help_support'),
]
