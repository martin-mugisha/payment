from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from core.utils import is_admin, is_client, is_staff
from staff.models import Staff
from clients.models import Client
from admins.models import AdminProfile

@receiver(user_logged_in)
def create_related_model(sender, request, user, **kwargs):
    if is_admin(user):
        AdminProfile.objects.get_or_create(user=user, defaults={'name': user.username})
        user.role = 'admin'
        user.save(update_fields=['role'])
    elif is_staff(user):
        Staff.objects.get_or_create(user=user, defaults={'name': user.username})
        user.role = 'staff'
        user.save(update_fields=['role'])
    elif is_client(user):
        Client.objects.get_or_create(user=user, defaults={'name': user.username})
        user.role = 'client'
        user.save(update_fields=['role'])

