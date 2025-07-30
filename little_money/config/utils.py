from decimal import Decimal
import secrets
import string
import hashlib
import json
import time
from typing import Dict, Any
from venv import logger
from jsonschema import validate, ValidationError
from datetime import datetime
import pytz

# Global counter
sequence_counter = 0

def generate_signature(params, field_order, private_key) -> str:
    """
    Generates an MD5 signature string from strictly ordered stringified fields plus the private key.
    """
    to_sign = '&'.join(f"{k}={str(params[k])}" for k in field_order if k in params)
    to_sign += f"&privateKey={private_key}"
    return hashlib.md5(to_sign.encode('utf-8')).hexdigest()


def verify_signature(data: dict, private_key: str) -> bool:
    webhook_field_order = [
        'PayStatus',
        'PayTime',
        'OutTradeNo',
        'TransactionId',
        'Amount',
        'ActualPaymentAmount',
        'ActualCollectAmount',
        'PayerCharge',
        'PayeeCharge',
        'PayMessage'
    ]
    to_sign_parts = []
    for k in webhook_field_order:
        value = data.get(k)
        if value is None:
            value_str = ""
        elif isinstance(value, (int, float, Decimal)): 
            value_str = str(value)
        else:
            value_str = str(value)
        
        to_sign_parts.append(f"{k}={value_str}")

    to_sign = '&'.join(to_sign_parts)
    to_sign += f"&privateKey={private_key}" # Or &key=private_key or &secret=private_key based on their docs

    calculated_md5_hash = hashlib.md5(to_sign.encode('utf-8')).hexdigest()
    
    received_signature = data.get('Sign')
    
    logger.info(f"Received signature: {received_signature}")
    logger.info(f"String to sign (encoded): {to_sign.encode('utf-8')}")
    logger.info(f"Calculated signature: {calculated_md5_hash}")

    return calculated_md5_hash == received_signature


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