import re
import json
import secrets
import string
import hashlib
import logging
import time
from typing import Dict, Any
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
    """
    Extracts the raw string of PayMessage from the webhook body,
    preserving escape characters.
    """
    # This regex correctly captures the value of PayMessage,
    # including the escaped quotes within it.
    match = re.search(r'"PayMessage"\s*:\s*"((?:\\.|[^"\\])*)"', raw_body)
    if match:
        return match.group(1)
    return ""

def verify_signature(data: Dict[str, Any], private_key: str, raw_body: str) -> bool:
    """
    Verifies the webhook signature by constructing the signing string
    in a precise and robust manner, matching the working `generate_signature` logic.

    Args:
        data: The dictionary parsed from the JSON webhook payload.
        private_key: The secret key from your aggregator settings.
        raw_body: The original, raw string of the webhook body.
    
    Returns:
        True if the signature is valid, False otherwise.
    """
    # 1. Define the exact order of fields for signature calculation.
    field_order = [
        'PayStatus', 'PayTime', 'OutTradeNo', 'TransactionId',
        'Amount', 'ActualPaymentAmount', 'ActualCollectAmount',
        'PayerCharge', 'PayeeCharge', 'ChannelCharge'
    ]

    sign_parts = []
    raw_pay_message = extract_raw_pay_message(raw_body)

    # 2. Reconstruct the string for all fields, handling PayMessage separately.
    for field in field_order:
        # This is the crucial fix: use the value from the parsed dict and
        # convert it to a string. This is consistent with your working function.
        value = data.get(field)
        if value is not None:
            # Note: We use str() to ensure consistent formatting, just like your
            # working `generate_signature` function.
            sign_parts.append(f"{field}={str(value)}")

    # 3. Add the raw PayMessage string exactly as received, with escapes.
    if raw_pay_message:
        sign_parts.append(f'PayMessage={raw_pay_message}')
    else:
        # Fallback to the parsed value if raw extraction fails
        sign_parts.append(f'PayMessage={data.get("PayMessage", "")}')

    # 4. Append the private key.
    sign_parts.append(f"privateKey={private_key}")

    # 5. Join all parts with '&' and calculate the MD5 hash.
    to_sign = '&'.join(sign_parts)
    calculated_md5 = hashlib.md5(to_sign.encode('utf-8')).hexdigest()

    # 6. Print debug info
    print("==== Signature Debug ====")
    print("String to sign:", to_sign)
    print("Calculated MD5:", calculated_md5)
    print("Received Sign :", data.get("Sign"))
    print("=========================")

    # 7. Compare calculated hash with the received signature.
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