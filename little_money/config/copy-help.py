from decimal import Decimal
import json
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from admins.models import AdminCommissionHistory, AdminProfile
from core.models import CustomUser
from .models import PrepaidBillResponse, UnifiedOrderResponse, OrderQueryResponse
from .Platform import PlatformEarnings
from .aggregator import PaymentResults, PrepaidBill, UnifiedOrder
from clients.models import Client, Finances
from staff.models import Balance, ClientAssignment, StaffCommissionHistory
from finance.models import SystemEarnings
import time

def process_transaction(channel: int, t_type: int, client_id: int, base_amount: int, trader_id: str, message: str, name: str):
    try:
        client = get_object_or_404(Client, id=client_id)
        assignment = ClientAssignment.objects.filter(client=client).first()
        staff = assignment.staff if assignment else None

        commission_record = StaffCommissionHistory.objects.order_by('-created_at').first()
        # Ensure commission_percent is always Decimal
        commission_percent = Decimal(str(commission_record.percentage)) if commission_record else Decimal("25.0")

        admin_commission_record = AdminCommissionHistory.objects.order_by('-created_at').first()
        # Ensure admin_commission_percent is always Decimal
        admin_commission_percent = Decimal(str(admin_commission_record.percentage)) if admin_commission_record else Decimal("10.0")

        system = SystemEarnings.load()
        charge = PlatformEarnings()

        # Convert base_amount to Decimal at the start for all calculations
        

        # Ensure fee is a Decimal
        # Assuming calculate_platform_fee might return a float, convert it to Decimal immediately
        fee = Decimal(str(charge.calculate_platform_fee(base_amount)))
        
        total_amount = base_amount_decimal + fee

        # All calculations involving fee, commission_percent, etc., should now be safe
        staff_commission = (fee * commission_percent / Decimal("100.0")) if staff else Decimal("0.0")
        admin_commission_total = (fee - staff_commission) * admin_commission_percent / Decimal("100.0")
        platform_profit = fee - staff_commission - admin_commission_total

        if total_amount <= 0:
            return JsonResponse({"status": "error", "message": "Total amount must be greater than zero."}, status=400)

        