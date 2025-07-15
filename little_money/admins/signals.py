# admins/signals.py

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils.timezone import now

@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    from .models import AuthLog
    AuthLog.objects.create(
        user=user,
        action='login',
        timestamp=now(),
        ip_address=get_client_ip(request)
    )

@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    from .models import AuthLog 
    AuthLog.objects.create(
        user=user,
        action='logout',
        timestamp=now(),
        ip_address=get_client_ip(request)
    )

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
