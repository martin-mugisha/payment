from core.models import CustomUser
from django.db import models

class Client(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Clients"
        ordering = ['name']

class Finances(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='finances')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client.name} - Balance: {str(self.balance)}"
    
    class Meta:
        verbose_name_plural = "Client Finances"
        ordering = ['client__name']