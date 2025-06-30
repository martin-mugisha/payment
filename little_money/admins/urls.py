from django.urls import path
from .views import (
    admin_dashboard,
    payouts_overview,
    kyc_status,
    chargebacks,
    risk_alerts,
    profile_admin,
    staff_user,
    staff_users,
    profile_view,
    platform_settings,
    export_csv,
    staff_user_delete,  # Import the staff_user_delete view
)

app_name = 'admins'

urlpatterns=[
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('payouts-overview/', payouts_overview, name='payouts_overview'),
    path('kyc-status/', kyc_status, name='kyc_status'),
    path('chargebacks/', chargebacks, name='chargebacks'),
    path('risk-alerts/', risk_alerts, name='risk_alerts'),
    path('profile-admin/', profile_admin, name='profile_admin'),
    path('staff-user/', staff_user, name='staff_user'),
    path('staff-users/', staff_users, name='staff_users'),
    path('profile/', profile_view, name='profile'),
    path('platform-settings/', platform_settings, name='platform_settings'),
    path('export-csv/', export_csv, name='export_csv'),
    path('delete-staff-user/<int:user_id>/', staff_user_delete, name='delete_staff_user'),  # New URL pattern
]