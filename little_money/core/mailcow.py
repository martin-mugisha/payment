import requests
from config import base as settings
MAILCOW_API_URL = 'https://mail.mangupay.tech/api/v1'  # replace with actual URL
MAILCOW_DOMAIN = 'mangupay.tech'  # replace with your actual domain

# Store credentials securely in Django settings
MAILCOW_ADMIN_EMAIL = settings.MAILCOW_ADMIN_EMAIL
MAILCOW_ADMIN_PASSWORD = settings.MAILCOW_ADMIN_PASSWORD
MAILCOW_API_KEY = settings.MAILCOW_API_KEY

def sync_mailcow_mailbox(user, password):
    if user.role not in ['staff', 'admin']:
        return  # Only sync for staff and admin

    email = f"{user.username}@{MAILCOW_DOMAIN}"

    headers = {
        'X-API-Key': MAILCOW_API_KEY,
        'Content-Type': 'application/json',
    }

    # Check if mailbox exists
    check_response = requests.post(
        f"{MAILCOW_API_URL}/get/mailbox",
        headers=headers,
        json=[email]
    )

    mailbox_exists = check_response.ok and check_response.json()

    if mailbox_exists:
        # Update existing mailbox password
        update_response = requests.post(
            f"{MAILCOW_API_URL}/edit/mailbox",
            headers=headers,
            json={
                "items": [email],
                "attr": {
                    "password": password,
                    "password2": password,
                    "force_pw_update": "1"
                }
            }
        )
        update_response.raise_for_status()
    else:
        # Create new mailbox
        create_response = requests.post(
            f"{MAILCOW_API_URL}/add/mailbox",
            headers=headers,
            json={
                "domain": MAILCOW_DOMAIN,
                "local_part": user.username,
                "name": f"{user.first_name} {user.last_name}",
                "password": password,
                "password2": password,
                "quota": "2048",  # in MB
                "active": "1",
                "force_pw_update": "1",
                "tls_enforce_in": "1",
                "tls_enforce_out": "1"
            }
        )
        create_response.raise_for_status()
