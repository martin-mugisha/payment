# core/utils.py

def is_admin(user):
    return hasattr(user, 'role') and user.role == 'admin'

def is_staff(user):
    return hasattr(user, 'role') and user.role == 'staff'

def is_client(user):
    return hasattr(user, 'role') and user.role == 'client'

def format_phone_number(number: str) -> str:
    """
    Format the phone number to the specified MTN/Airtel format:
    075XXXXXXX, 070XXXXXXX, 074XXXXXXX, 076XXXXXXX, 078XXXXXXX, 077XXXXXXX, 079XXXXXXX
    Assumes input number is a string of digits possibly with country code.
    """
    if not number:
        return ''
    # Remove non-digit characters
    digits = ''.join(filter(str.isdigit, number))
    # Remove country code if present (e.g., 256)
    if digits.startswith('256'):
        digits = digits[3:]
    elif digits.startswith('0'):
        digits = digits[1:]
    # Now digits should be 9 digits
    if len(digits) == 9:
        # Format as 07Xxxxxxxx
        return '0' + digits
    else:
        # Return original if format unknown
        return number
