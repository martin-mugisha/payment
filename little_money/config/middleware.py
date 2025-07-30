from django.shortcuts import redirect
from django.urls import reverse
from core.utils import is_admin, is_client, is_staff
from staff.models import Staff
from clients.models import Client
from admins.models import AdminProfile

class FirstLoginPasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user = request.user

            # ✅ Ensure role-specific object exists BEFORE using them
            if is_staff(user):
                Staff.objects.get_or_create(user=user, defaults={'name': user.username})
            elif is_client(user):
                Client.objects.get_or_create(user=user, defaults={'name': user.username})
            elif is_admin(user):
                AdminProfile.objects.get_or_create(user=user, defaults={'name': user.username})

            # ✅ Define allowed paths (normalized)
            allowed_paths = [
                reverse('admins:force_password_change'),
                reverse('clients:force_password_change'),
                reverse('staff:force_password_change'),
                reverse('authenticate:logout'),
            ]

            normalized_path = request.path.rstrip("/")

            if normalized_path not in [p.rstrip("/") for p in allowed_paths]:
                if getattr(user, 'is_first_login', False):
                    print(f"Redirecting user {user.username} from {request.path} to password change page")

                    if is_admin(user):
                        return redirect('admins:force_password_change')
                    elif is_client(user):
                        return redirect('clients:force_password_change')
                    elif is_staff(user):
                        return redirect('staff:force_password_change')
                    else:
                        return redirect('authenticate:logout')

        return self.get_response(request)
