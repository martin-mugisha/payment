import requests

MAILCOW_API_URL = 'https://your.mailcow.host/api/v1'
MAILCOW_API_KEY = 'your-mailcow-api-key'
MAILCOW_DOMAIN = 'yourdomain.com'  # Example: 'example.com'

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
        requests.post(
            f"{MAILCOW_API_URL}/edit/mailbox",
            headers=headers,
            json={
                "items": [email],
                "attr": {"password": password}
            }
        )
    else:
        # Create new mailbox
        requests.post(
            f"{MAILCOW_API_URL}/add/mailbox",
            headers=headers,
            json={
                "domain": MAILCOW_DOMAIN,
                "local_part": user.username,
                "name": f"{user.first_name} {user.last_name}",
                "password": password,
                "quota": 2048,  # in MB
                "active": 1
            }
        )
