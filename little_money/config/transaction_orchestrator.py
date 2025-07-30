from decimal import Decimal
from pyexpat.errors import messages
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db import transaction # Important for atomic updates

# Import the core transaction processing function
# Assuming your previous function is in a file named 'transaction_processor.py'
# within the same Django app or a module accessible via 'your_app_name.transaction_processor'
from .help import process_transaction 

# Import models and services needed for financial updates
from admins.models import AdminCommissionHistory, AdminProfile
from core.models import CustomUser
from clients.models import Client, Finances
from staff.models import Balance, ClientAssignment, StaffCommissionHistory
from finance.models import SystemEarnings
from .Platform import PlatformEarnings # Assuming PlatformEarnings is in the same app

def handle_full_transaction(channel: int, t_type: int, client_id: int, base_amount: int, trader_id: str, message: str, name: str):
    """
    Orchestrates the entire transaction process, including external API calls
    and subsequent financial updates (commissions, balances, system earnings).

    This function should be called from your Django views.
    """
    try:
        # --- 1. Initial Data Retrieval and Pre-calculations ---
        client = get_object_or_404(Client, id=client_id)
        assignment = ClientAssignment.objects.filter(client=client).first()
        staff = assignment.staff if assignment else None

        # Convert base_amount to Decimal early for all internal financial calculations
        base_amount_decimal = Decimal(base_amount)

        # Calculate platform fee
        charge = PlatformEarnings()
        # Ensure fee is a Decimal. Assuming calculate_platform_fee might return a float.
        fee = Decimal(str(charge.calculate_platform_fee(base_amount)))
        
        total_amount = base_amount_decimal + fee

        if total_amount <= 0:
            return JsonResponse({"status": "error", "message": "Total amount must be greater than zero."}, status=400)

        # --- 2. Call the Core Transaction Processor (API Interaction) ---
        # Pass the original base_amount (int) as process_transaction expects it for API calls
        # process_transaction will handle its own Decimal conversions for model saving.
        transaction_response = process_transaction(
            channel=channel,
            t_type=t_type,
            client_id=client_id,
            base_amount=total_amount, 
            trader_id=trader_id,
            message=message,
            name=name
        )

        # Check if the core transaction processing was successful
        if transaction_response.status_code != 200:
            # If the API interaction failed (or subsequent query failed in process_transaction),
            # return the error response directly.
            return transaction_response # process_transaction already returns JsonResponse

        # --- 3. Financial Updates (Business Logic) - ONLY if transaction_response was successful ---
        # All financial updates must be atomic to ensure data consistency.
        # If any step within this block fails, all changes are rolled back.
        with transaction.atomic():
            # Load SystemEarnings inside the atomic block for freshest data
            system = SystemEarnings.load()

            # Get commission percentages
            commission_record = StaffCommissionHistory.objects.order_by('-created_at').first()
            staff_commission_percent = Decimal(str(commission_record.percentage)) if commission_record else Decimal("25.0")

            admin_commission_record = AdminCommissionHistory.objects.order_by('-created_at').first()
            admin_commission_percent = Decimal(str(admin_commission_record.percentage)) if admin_commission_record else Decimal("10.0")

            # Calculate commissions and profit
            staff_commission = (fee * staff_commission_percent / Decimal("100.0")) if staff else Decimal("0.0")
            admin_commission_total = (fee - staff_commission) * admin_commission_percent / Decimal("100.0")
            platform_profit = fee - staff_commission - admin_commission_total

            # Update staff balance
            if staff:
                staff_balance, created = Balance.objects.get_or_create(staff=staff)
                staff_balance.balance += staff_commission
                staff_balance.save()
                print(f"Staff {staff.user.username} balance updated by {staff_commission}. New balance: {staff_balance.balance}")

            # Update admin balances
            admins = CustomUser.objects.filter(role='admin')
            num_admins = admins.count()
            if num_admins > 0:
                share = admin_commission_total / num_admins
                for admin in admins:
                    admin.profile.balance += share
                    admin.profile.save()
                    print(f"Admin {admin.username} balance updated by {share}. New balance: {admin.profile.balance}")
            else:
                print("No active admins found to distribute commission.")

            # Update system earnings
            system.total_transactions += 1
            system.total_earnings += platform_profit
            system.total_volume += base_amount_decimal
            system.total_successful_transactions += 1
            system.save()
            print(f"System earnings updated. Total transactions: {system.total_transactions}, Earnings: {system.total_earnings}")

        return JsonResponse({"status": "success", "message": "Transaction processed and finances updated successfully."})

    except Client.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Client not found."}, status=404)
    except Exception as e:
        # Log the full exception traceback for debugging in production
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}, status=500)
    





from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db import transaction

# Import the core transaction processing function
from .help import process_transaction 

# Import models and services needed for financial updates
from admins.models import AdminCommissionHistory, AdminProfile
from core.models import CustomUser
from clients.models import Client, Finances
from staff.models import Balance, ClientAssignment, StaffCommissionHistory
from finance.models import SystemEarnings
from .Platform import PlatformEarnings

def handle_full_transaction(channel: int, t_type: int, client_id: int, base_amount: int, trader_id: str, message: str, name: str):
    """
    Orchestrates the entire transaction process, including external API calls
    and subsequent financial updates (commissions, balances, system earnings).

    - If t_type is 1 (Collection), client balance increases.
    - If t_type is 2 (Disbursement), client balance decreases.

    This function should be called from your Django views.
    """
    try:
        # --- 1. Initial Data Retrieval and Pre-calculations ---
        client = get_object_or_404(Client, id=client_id)
        assignment = ClientAssignment.objects.filter(client=client).first()
        staff = assignment.staff if assignment else None

        # Convert base_amount to Decimal early for all internal financial calculations
        base_amount_decimal = Decimal(base_amount)

        # Calculate platform fee
        charge = PlatformEarnings()
        # Ensure fee is a Decimal. Assuming calculate_platform_fee might return a float.
        fee = Decimal(str(charge.calculate_platform_fee(base_amount)))
        
        total_amount = base_amount_decimal + fee

        if total_amount <= 0:
            # This check might need refinement based on disbursement logic.
            # For collections, it's fine. For disbursements, a zero or negative
            # base_amount might be valid if it's a refund or correction.
            # Adjust this validation if disbursements can have <= 0 amounts that need processing.
            return JsonResponse({"status": "error", "message": "Total amount must be greater than zero."}, status=400)

        # --- 2. Call the Core Transaction Processor (API Interaction) ---
        transaction_response = process_transaction(
            channel=channel,
            t_type=t_type,
            client_id=client_id,
            base_amount=total_amount,
            trader_id=trader_id,
            message=message,
            name=name
        )

        # Check if the core transaction processing was successful
        if transaction_response.status_code != 200:
            return transaction_response 

        # --- 3. Financial Updates (Business Logic) - ONLY if transaction_response was successful ---
        with transaction.atomic():
            system = SystemEarnings.load()

            # Get commission percentages
            commission_record = StaffCommissionHistory.objects.order_by('-created_at').first()
            staff_commission_percent = Decimal(str(commission_record.percentage)) if commission_record else Decimal("25.0")

            admin_commission_record = AdminCommissionHistory.objects.order_by('-created_at').first()
            admin_commission_percent = Decimal(str(admin_commission_record.percentage)) if admin_commission_record else Decimal("10.0")

            # Calculate commissions and profit
            staff_commission = (fee * staff_commission_percent / Decimal("100.0")) if staff else Decimal("0.0")
            admin_commission_total = (fee - staff_commission) * admin_commission_percent / Decimal("100.0")
            platform_profit = fee - staff_commission - admin_commission_total

            # Update staff balance
            if staff:
                staff_balance, created = Balance.objects.get_or_create(staff=staff)
                staff_balance.balance += staff_commission
                staff_balance.save()
                print(f"Staff {staff.user.username} balance updated by {staff_commission}. New balance: {staff_balance.balance}")

            # --- Update client balance based on t_type (Collection vs. Disbursement) ---
            client_finance, _ = Finances.objects.get_or_create(client=client)
            
            if t_type == 1: # Collection
                client_finance.balance += base_amount_decimal
                messages.success(f"Client {client.user.username} balance (Collection) increased by {base_amount_decimal}. New balance: {client_finance.balance}")
            elif t_type == 2: # Disbursement
                # Optional: Add a check here if client_finance.balance < base_amount_decimal
                # for disbursements to prevent negative balances if not allowed.
                # if client_finance.balance < base_amount_decimal:
                #    raise ValueError("Insufficient funds for disbursement.")
                client_finance.balance -= base_amount_decimal
                messages.success(f"Client {client.user.username} balance (Disbursement) decreased by {base_amount_decimal}. New balance: {client_finance.balance}")
            else:
                # Handle unexpected t_type values
                raise ValueError(f"Unsupported transaction type (t_type): {t_type}")

            client_finance.save()


            # Update admin balances
            admins = CustomUser.objects.filter(role='admin')
            num_admins = admins.count()
            if num_admins > 0:
                share = admin_commission_total / num_admins
                for admin in admins:
                    admin.profile.balance += share
                    admin.profile.save()
                    print(f"Admin {admin.username} balance updated by {share}. New balance: {admin.profile.balance}")
            else:
                print("No active admins found to distribute commission.")

            # Update system earnings
            system.total_transactions += 1
            system.total_earnings += platform_profit
            system.total_volume += base_amount_decimal # Still records the full base amount for volume
            system.total_successful_transactions += 1
            system.save()
            print(f"System earnings updated. Total transactions: {system.total_transactions}, Earnings: {system.total_earnings}")

        return JsonResponse({"status": "success", "message": "Transaction processed and finances updated successfully."})

    except Client.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Client not found."}, status=404)
    except ValueError as ve: # Catch specific ValueErrors (e.g., for unsupported t_type or insufficient funds)
        return JsonResponse({"status": "error", "message": str(ve)}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}, status=500)