from django.urls import path
from .views import (
    staff_dashboard,
    merchant_list,
    profile_staff,
    earnings,
    dispute_management,
    refund_processing,
    failed_transactions,
    support_tickets,
    suspicious_activity,
    audit_logs,
    base_staff,
    staff,
    payout_management,
    export_csv
    )

app_name = 'staff'

urlpatterns = [    
    path('dashboard/', staff_dashboard, name='staff_dashboard'),
    path('merchant-list/', merchant_list, name='merchant_list'),
    path('profile-staff/', profile_staff, name='profile_staff'),
    path('earnings/', earnings, name='earnings'),
    path('dispute-management/', dispute_management, name='dispute_management'),
    path('refund-processing/', refund_processing, name='refund_processing'),
    path('failed-transactions/', failed_transactions, name='failed_transactions'),
    path('support-tickets/', support_tickets, name='support_tickets'),
    path('suspicious-activity/', suspicious_activity, name='suspicious_activity'),
    path('audit-logs/', audit_logs, name='audit_logs'),
    path('base-staff/', base_staff, name='base_staff'),
    path('staff/', staff, name='staff'),
    path('payout-management/', payout_management, name='payout_management'),
    path('export-csv/', export_csv, name='export_csv'),
    
]