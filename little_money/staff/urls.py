from django.urls import path

app_name = 'staff'

from .views import profile_view, summary_dashboard, balance, transactions, my_earning, clients

urlpatterns = [
    path('profile/', profile_view, name='profile_staff'),
    path('dashboard/', summary_dashboard, name='summary_dashboard'),
    path('balance/', balance, name='balance'),
    path('transactions/', transactions, name='transaction'),
    path('my-earning/', my_earning, name='my_earning'),
    path('clients/', clients, name='clients'),
]
