from datetime import timezone
from core.models import CustomUser
from django.db import models
from django.core.validators import MinValueValidator

class Client(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "Clients"
        ordering = ['name']
    
    @property
    def balance(self):
        finance = self.finances.first()
        return finance.balance if finance else 0.00

class Finances(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='finances')
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client.name} - Balance: {self.balance}"
    
    class Meta:
        verbose_name_plural = "Client Finances"
        ordering = ['client__name']
    def __str__(self):
        return f"Finances for {self.client.user.username}"

class RecentTransaction(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='recent_transactions')
    date = models.DateField()
    time = models.TimeField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    recipient = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, default='Pending', choices=[
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Processing', 'Processing'), 
    ])
    transaction_id = models.PositiveIntegerField(unique=True, blank=True, null=True)
    payment_method = models.CharField(max_length=20, blank=True, null=True)
    transaction_type = models.CharField(max_length=20, default='Cash In', choices=[
        ('Cash In', 'Cash In'),
        ('Cash Out', 'Cash Out'),
        ])
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client.name} - {self.recipient} - {self.amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            last = RecentTransaction.objects.all().order_by('-transaction_id').first()
            self.transaction_id = 1 if not last else last.transaction_id + 1
        super().save(*args, **kwargs)

 
    class Meta:
        ordering = ['-date', '-created_at']

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
