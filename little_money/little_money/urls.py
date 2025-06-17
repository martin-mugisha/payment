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
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)