from django.urls import path

from webhooks.views import payment_notification

app_name = 'webhooks'

urlpatterns = [
    path('payment-notification/', payment_notification, name='payment_notification'),
]