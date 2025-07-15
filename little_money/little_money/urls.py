from functools import cache
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView


schema_view = get_schema_view(
   openapi.Info(
      title="Payment API",
      default_version='v1',
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [ 
   path('', RedirectView.as_view(url='/auth/login/', permanent=False)),
    path('auth/', include('authenticate.urls', namespace='authenticate')),
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('staff/', include('staff.urls', namespace='staff')),
    path('finance/', include('finance.urls', namespace='finance')),
    path('admins/', include('admins.urls', namespace='super')),
    path('api/', include('api.urls', namespace='api')),
    path('client/', include('clients.urls', namespace='client')),
    path('webhooks/', include('webhooks.urls', namespace='webhooks')),
    path('redoc/', schema_view.with_ui('redoc', cache))
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)