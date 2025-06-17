import requests
from django.conf import settings
from django.core.mail import send_mail

class PaymentAggregatorClient:
    def __init__(self):
        self.base_url = settings.PAYMENT_AGGREGATOR_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {settings.PAYMENT_AGGREGATOR_API_KEY}',
            'Content-Type': 'application/json'
        }

    def initiate_payment(self, payload):
        response = requests.post(f"{self.base_url}/pay", json=payload, headers=self.headers)
        return response.json()

    def get_transaction_status(self, transaction_id):
        response = requests.get(f"{self.base_url}/status/{transaction_id}", headers=self.headers)
        return response.json()

    def notify_user(self, email, status):
        subject = 'Transaction Update'
        message = f'Your transaction status is now: {status}'
        send_mail(subject, message, settings.EMAIL_HOST_USER, [email])