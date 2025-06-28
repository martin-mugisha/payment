"""
URL configuration for little_money project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from webhooks.views import webhook_handler
from dashboard import views as dashboard_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from api.views import initiate_transaction, TransactionHistoryView
from django.conf import settings
from django.conf.urls.static import static


schema_view = get_schema_view(
   openapi.Info(
      title="Payment API",
      default_version='v1',
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', dashboard_views.index, name='index'),
    path('admin/', admin.site.urls),
    path('api/initiate/', initiate_transaction),
    path('api/history/', TransactionHistoryView.as_view()),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('webhooks/payment/', webhook_handler),
    path('dashboard/admin/', dashboard_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/platform-settings/', dashboard_views.platform_settings, name='platform_settings'),
    path('dashboard/export-csv/', dashboard_views.export_transactions_csv, name='export_transactions_csv'),
    path('dashboard/staff/', dashboard_views.staff_dashboard, name='staff_dashboard'),
    path('login/', dashboard_views.user_login, name='login'),
    path('logout/', dashboard_views.user_logout, name='logout'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('dashboard/staff-users/', dashboard_views.staff_users, name='staff_users'),
    path('dashboard/profile/', dashboard_views.profile_view, name='profile'),

    # Added missing views
    path('dashboard/admin/payouts-overview/', dashboard_views.payouts_overview, name='payouts_overview'),
    path('dashboard/admin/kyc-status/', dashboard_views.kyc_status, name='kyc_status'),
    path('dashboard/admin/chargebacks/', dashboard_views.chargebacks, name='chargebacks'),
    path('dashboard/admin/risk-alerts/', dashboard_views.risk_alerts, name='risk_alerts'),
    path('dashboard/admin/profile-admin/', dashboard_views.profile_admin, name='profile_admin'),
    path('dashboard/admin/staff-user/', dashboard_views.staff_user, name='staff_user'),

    path('dashboard/staff/merchant-list/', dashboard_views.merchant_list, name='merchant_list'),
    path('dashboard/staff/profile-staff/', dashboard_views.profile_staff, name='profile_staff'),
    path('dashboard/staff/earnings/', dashboard_views.earnings, name='earnings'),
    path('dashboard/staff/dispute-management/', dashboard_views.dispute_management, name='dispute_management'),
    path('dashboard/staff/refund-processing/', dashboard_views.refund_processing, name='refund_processing'),
    path('dashboard/staff/failed-transactions/', dashboard_views.failed_transactions, name='failed_transactions'),
    path('dashboard/staff/support-tickets/', dashboard_views.support_tickets, name='support_tickets'),
    path('dashboard/staff/suspicious-activity/', dashboard_views.suspicious_activity, name='suspicious_activity'),
    path('dashboard/staff/audit-logs/', dashboard_views.audit_logs, name='audit_logs'),
    path('dashboard/staff/base-staff/', dashboard_views.base_staff, name='base_staff'),
    path('dashboard/staff/staff/', dashboard_views.staff, name='staff'),
    path('dashboard/staff/payout-management/', dashboard_views.payout_management, name='payout_management'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)