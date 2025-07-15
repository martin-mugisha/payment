import secrets
import string
import hashlib
import json
from typing import Dict, Any
from jsonschema import validate, ValidationError
from datetime import datetime
import pytz

# Global counter
sequence_counter = 0

def generate_signature(data_dict: Dict[str, Any], private_key: str) -> str:
    """
    Generates an MD5 signature string from sorted fields plus the private key.
    """
    keys = sorted(k for k in data_dict.keys() if k != 'Sign')
    raw_string = "&".join(f"{k}={data_dict[k]}" for k in keys)
    raw_string += f"&privateKey={private_key}"
    return hashlib.md5(raw_string.encode('utf-8')).hexdigest()


def verify_signature(data: Dict[str, Any], private_key: str) -> bool:
    """
    Reconstructs the string to sign, hashes it using MD5, and compares with the received Sign.
    """
    received_sign = data.get("Sign", "")
    if not received_sign:
        return False

    keys = sorted(k for k in data.keys() if k != 'Sign')
    raw_string = "&".join(f"{k}={data[k]}" for k in keys)
    raw_string += f"&privateKey={private_key}"

    generated_sign = hashlib.md5(raw_string.encode("utf-8")).hexdigest()
    return generated_sign == received_sign


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
    # East African Time timezone
    east_africa_tz = pytz.timezone('Africa/Nairobi')  # Nairobi is in EAT timezone
    # Get current time in UTC and convert to East African Time
    current_time_eat = datetime.now(tz=pytz.utc).astimezone(east_africa_tz)
    # Get the Unix timestamp (seconds since epoch)
    timestamp = int(current_time_eat.timestamp())
    return timestamp

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