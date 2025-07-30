from django.urls import path

app_name = 'staff'

from .views import profile_view, summary_dashboard, balance, transactions, clients, force_password_change_view

urlpatterns = [
    path('profile/', profile_view, name='profile_staff'),
    path('dashboard/', summary_dashboard, name='summary_dashboard'),
    path('balance/', balance, name='balance'),
    path('transactions/', transactions, name='transaction'),
    path('clients/', clients, name='clients'),
    path('force-password-change/', force_password_change_view, name='force_password_change'),
]
