from django.db import models
from django.conf import settings

class Withdrawal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    requested_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')  # e.g., Pending, Completed, Rejected

    def __str__(self):
        return f"Withdrawal {self.id} by {self.user.username} - {self.amount} ({self.status})"
