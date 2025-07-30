from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

PAYMENT_AGGREGATOR_API_KEY = os.getenv("AGGREGATOR_API_KEY")
if not PAYMENT_AGGREGATOR_API_KEY:
    raise ValueError("AGGREGATOR_API_KEY is required but not set.")

PAYMENT_MERCHANT_ID = os.getenv("MERCHANT_ID")
if not PAYMENT_MERCHANT_ID:
    raise ValueError("MERCHANT_ID is required but not set.")

PAYMENT_AGGREGATOR_BASE_URL = os.getenv("AGGREGATOR_BASE_URL")
if not PAYMENT_AGGREGATOR_BASE_URL:
    raise ValueError("AGGREGATOR_BASE_URL is required but not set.")

PAYMENT_AGGREGATOR_WEBHOOK_SECRET = os.getenv("AGGREGATOR_WEBHOOK_SECRET")
PAYMENT_AGGREGATOR_WEBHOOK_URL = os.getenv(
    "AGGREGATOR_WEBHOOK_URL",
    "https://mangupay.tech/webhooks/payment-notification/"
)
if not PAYMENT_AGGREGATOR_WEBHOOK_SECRET:
    raise ValueError("AGGREGATOR_WEBHOOK_SECRET is required but not set.")  