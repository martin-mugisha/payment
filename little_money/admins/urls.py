from django.urls import path
from .views import (
    admin_dashboard,
    payouts_overview,
    approve_payout,
    chargebacks,
    risk_alerts,
    profile_admin,
    staff_user,
    staff_users,
    profile_view,
    platform_settings,
    staff_user_delete,  
    activity_logs,
    finance_dashboard,
)

app_name = 'admins'

urlpatterns=[
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('payouts/', payouts_overview, name='payouts_overview'),
    path('payouts/<int:payout_id>/approve/', approve_payout, name='approve_payout'),
    path('chargebacks/', chargebacks, name='chargebacks'),
    path('risk-alerts/', risk_alerts, name='risk_alerts'),
    path('profile-admin/', profile_admin, name='profile_admin'),
    path('staff-user/', staff_user, name='staff_user'),
    path('staff-users/', staff_users, name='staff_users'),
    path('activity-logs/', activity_logs, name='activity_logs'),
    path('profile/', profile_view, name='profile'),
    path('platform-settings/', platform_settings, name='platform_settings'),
    path('finance/', finance_dashboard, name='finance_dashboard'),
    path('delete-staff-user/<int:user_id>/', staff_user_delete, name='delete_staff_user'),  # New URL pattern
]
