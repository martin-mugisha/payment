
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .help import process_transaction
from clients.models import Client # Still need Client to get client_id for process_transaction
from .Platform import PlatformEarnings # Still need PlatformEarnings for fee calculation during initiation

import logging
logger = logging.getLogger(__name__)

def initiate_payment_process(channel: int, t_type: int, client_id: int, base_amount: int, trader_id: str, message: str, name: str):
    """
    Initiates the payment process with the external aggregator.
    It does NOT update financial records (commissions, balances).
    Financial updates will be handled by the webhook notification.
    """
    try:
        logger.info(f"--- Starting initiate_payment_process for client_id: {client_id}, base_amount: {base_amount} ---")

        # Get client object (needed for client_id for process_transaction)
        client = get_object_or_404(Client, id=client_id)

        # Calculate platform fee and total amount for the initial order request
        base_amount_decimal = Decimal(base_amount)
        charge = PlatformEarnings()
        fee = Decimal(str(charge.calculate_platform_fee(base_amount)))
        total_amount = base_amount_decimal + fee

        logger.info(f"Calculated fee: {fee}, Total Amount for API call: {total_amount}")

        if total_amount <= 0:
            logger.warning(f"Total amount <= 0 for client {client_id}. Aborting initiation. Total: {total_amount}")
            return JsonResponse({"status": "error", "message": "Total amount must be greater than zero."}, status=400)

        # Call the Core Transaction Processor (API Interaction)
        logger.info("Calling process_transaction (external API interaction) for order initiation...")
        transaction_response = process_transaction(
            channel=channel,
            t_type=t_type,
            client_id=client_id,
            base_amount=base_amount, # Pass original int base_amount
            trader_id=trader_id,
            message=message,
            name=name
        )
        logger.info(f"Process transaction returned status: {transaction_response.status_code}")

        # Return the response from the initiation process.
        # Financial updates depend on the webhook.
        return transaction_response 

    except Client.DoesNotExist:
        logger.error(f"Client with ID {client_id} not found during payment initiation.")
        return JsonResponse({"status": "error", "message": "Client not found."}, status=404)
    except ValueError as ve:
        logger.error(f"ValueError in initiate_payment_process: {ve}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(ve)}, status=400)
    except Exception as e:
        logger.critical(f"An unexpected error occurred in initiate_payment_process: {e}", exc_info=True)
        return JsonResponse({"status": "error", "message": f"An unexpected error occurred during payment initiation: {str(e)}"}, status=500)