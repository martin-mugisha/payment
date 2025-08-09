from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    is_first_login = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to='avatars/', blank=True, null=True)

class TransactionIDCounter(models.Model):
    first_letter_index = models.PositiveSmallIntegerField(default=0)
    second_letter_index = models.PositiveSmallIntegerField(default=0)
    number = models.PositiveSmallIntegerField(default=0)

    class Meta:
        # Make sure there is only one row
        verbose_name = "Transaction ID Counter"
        verbose_name_plural = "Transaction ID Counters"