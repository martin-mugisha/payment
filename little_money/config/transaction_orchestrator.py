from decimal import Decimal
import json
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from clients.models import Client
from .Platform import PlatformEarnings
from .help import process_transaction
import logging

logger = logging.getLogger(__name__)

class PaymentInitiator:
    def __init__(self, channel: int, t_type: int, client_id: int, base_amount: int, trader_id: str, message: str, name: str):
        self.channel = channel
        self.t_type = t_type
        self.client_id = client_id
        self.base_amount = Decimal(base_amount)
        self.trader_id = trader_id
        self.message = message
        self.name = name
        self.fee = None
        self.total_amount = None
        self.client = None
        self._calculate_fee()

    def _calculate_fee(self):
        self.client = get_object_or_404(Client, id=self.client_id)
        charge = PlatformEarnings()
        self.fee = Decimal(str(charge.calculate_platform_fee(self.base_amount)))
        self.total_amount = self.base_amount + self.fee
        logger.info(f"Fee calculated: {self.fee}, Total amount: {self.total_amount}")

    def get_base_amount(self):
        return self.base_amount

    def get_fee(self):
        return self.fee

    def get_total_amount(self):
        return self.total_amount

    def initiate_transaction(self):
        logger.info(f"Initiating transaction for client_id: {self.client_id}, total_amount: {self.total_amount}")
        if self.total_amount <= 0:
            return JsonResponse({"status": "error", "message": "Total amount must be greater than zero."}, status=400)
        
        try:
            response = process_transaction(
                channel=self.channel,
                t_type=self.t_type,
                client_id=self.client_id,
                base_amount=self.total_amount,
                trader_id=self.trader_id,
                message=self.message,
                name=self.name
            )
            result_data = json.loads(response.content)
            if result_data.get('status') == 'success':
                return JsonResponse({"status": "success", "message": "Transaction initiated successfully."}, status=200)
            else:
                return JsonResponse({"status": "error", "message": result_data.get('message')}, status=400)
        except Exception as e:
            logger.exception("Unexpected error during transaction initiation")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
