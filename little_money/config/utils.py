import re
import json
from decimal import Decimal
import secrets
import string
import hashlib
import logging
from decimal import Decimal
import time
from typing import Dict
from venv import logger
from jsonschema import validate, ValidationError
from datetime import datetime
import pytz


logger = logging.getLogger(__name__)
# Global counter
sequence_counter = 0

def generate_signature(params, field_order, private_key) -> str:
    """
    Generates an MD5 signature string from strictly ordered stringified fields plus the private key.
    """
    to_sign = '&'.join(f"{k}={str(params[k])}" for k in field_order if k in params)
    to_sign += f"&privateKey={private_key}"
    return hashlib.md5(to_sign.encode('utf-8')).hexdigest()

def extract_raw_pay_message(raw_body: str) -> str:
    # Extract the raw string of PayMessage using regex (with escape chars preserved)
    match = re.search(r'"PayMessage"\s*:\s*"((?:\\.|[^"\\])*)"', raw_body)
    if match:
        return match.group(1)
    return ""

def verify_signature(data: dict, private_key: str, raw_pay_message: str = None) -> bool:
    fields = [
        'PayStatus', 'PayTime', 'OutTradeNo', 'TransactionId',
        'Amount', 'ActualPaymentAmount', 'ActualCollectAmount',
        'PayerCharge', 'PayeeCharge', 'ChannelCharge'
    ]

    sign_parts = []
    for field in fields:
        sign_parts.append(f"{field}={data[field]}")

    # Insert raw PayMessage string exactly as received
    if raw_pay_message is not None:
        sign_parts.append(f'PayMessage={raw_pay_message}')
    else:
        sign_parts.append(f'PayMessage={data["PayMessage"]}')  # fallback

    sign_parts.append(f"privateKey={private_key}")

    to_sign = '&'.join(sign_parts)
    calculated_md5 = hashlib.md5(to_sign.encode('utf-8')).hexdigest()

    print("==== Signature Debug ====")
    print("String to sign:", to_sign)
    print("Calculated MD5:", calculated_md5)
    print("Received Sign :", data.get("Sign"))
    print("=========================")

    return calculated_md5 == data.get("Sign")

def validate_signature(request_data, private_key):
    """
    Validate the 'Sign' in request_data matches the generated signature.
    """
    sign = request_data.get('Sign')
    if not sign:
        return False

    expected_sign = generate_signature(request_data, private_key)
    return sign == expected_sign

def validate_json_schema(data, schema):
    """
    Validate `data` dict against the given JSON schema.
    Returns (True, None) if valid,
    else (False, error_message).
    """
    try:
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e)

def transform_request_payload(payload, merchant, aggregator_creds):
    """
    Replace merchant-specific fields with aggregator fields,
    e.g., MchID, Sign, APIKey, etc., before forwarding to main aggregator.
    """
    new_payload = payload.copy()

    # Replace merchant id with aggregator merchant id
    new_payload['MchID'] = aggregator_creds.api_key

    # Remove or replace signature
    if 'Sign' in new_payload:
        del new_payload['Sign']

    # After this, caller should generate new Sign with aggregator_creds.api_secret
    return new_payload

def generate_api_key(length=40):
    """
    Generate a secure random API key consisting of letters and digits.
    Default length is 40 characters.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_transaction_id(length=12):
    """
    Generate a random transaction ID consisting of uppercase letters and digits.
    Default length is 12 characters.
    """
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_timestamp():
    return int(time.time())

def generate_unique_id():
    global sequence_counter
    # Timezone: East African Time (EAT)
    eat = pytz.timezone('Africa/Nairobi')
    now_eat = datetime.now(eat)

    # Format date
    current_date = now_eat.strftime('%Y%m%d')
    timestamp_ms = int(now_eat.timestamp() * 1000)

    # Pad sequence
    auto_number = f"{timestamp_ms}{sequence_counter:05d}"
    sequence_counter = (sequence_counter + 1) % 100000  # Wrap at 99999

    # Final unique ID
    unique_id = f"UGMP-{current_date}-{auto_number}"
    return unique_id