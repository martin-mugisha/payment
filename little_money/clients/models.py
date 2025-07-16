from core.models import CustomUser
from django.db import models

class Client(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "Clients"
        ordering = ['name']

class Finances(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='finances')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client.name} - Balance: {self.balance}"
    
    class Meta:
        verbose_name_plural = "Client Finances"
        ordering = ['client__name']

class RecentTransaction(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='recent_transactions')
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    recipient = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.client.name} - {self.recipient} - {self.amount}"
 
    class Meta:
        ordering = ['-date']

class UpcomingPayment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='upcoming_payments')
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.client.name} - {self.amount} on {self.date}"

    class Meta:
        ordering = ['date']

class LinkedAccount(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='linked_accounts')
    account_type = models.CharField(max_length=50)
    details = models.CharField(max_length=255)
    balance = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.client.name} - {self.account_type} - {self.details}"

class UserSetting(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='user_settings')
    profile_name = models.CharField(max_length=255)
    profile_email = models.EmailField()
    password_set = models.BooleanField(default=True)
    two_factor_enabled = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)

    def __str__(self):
        return f"Settings for {self.client.name}"

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question

class ContactInfo(models.Model):
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    chat_availability = models.CharField(max_length=100)

    def __str__(self):
        return f"Contact Info: {self.email}"

class KnowledgeBaseEntry(models.Model):
    title = models.CharField(max_length=255)
    link = models.URLField()

    def __str__(self):
        return self.title

class DailyPayment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='daily_payments')
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.client.name} - {self.date} - {self.amount}"

    class Meta:
        ordering = ['date']
