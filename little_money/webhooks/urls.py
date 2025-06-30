from django.urls import path
from .views import webhook_handler

app_name = 'webhooks'

urlpatterns = [
    path('webhooks/payment/', webhook_handler),
    ]