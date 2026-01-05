import random
import qrcode
import secrets
import string
from io import BytesIO
from PIL import Image
from typing import Tuple, Optional


def generate_account_number() -> str:
    """
    Generate a random 16-digit account number
    """
    # Generate 16 random digits
    account_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
    return account_number


def generate_qr_code(data: str) -> BytesIO:
    """
    Generate QR code image from data string
    Returns: BytesIO object containing PNG image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to BytesIO
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes


def format_account_number(account_number: str) -> str:
    """
    Format account number for display with markdown (copyable)
    """
    return f"`{account_number}`"


def generate_payment_token() -> str:
    """
    Generate a unique token for payment links
    Returns a 32-character alphanumeric token
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


def generate_payment_link(bot_username: str, amount: float, destination_account: str, 
                         db_manager=None, user_id: str = None, token: str = None) -> str:
    """
    Generate payment link for Telegram bot
    New format (one-time use): https://t.me/{bot_username}?start=pay_{token}
    Old format (backward compatibility): https://t.me/{bot_username}?start=pay_{destination_account}_{amount}
    
    If db_manager and user_id are provided, creates a one-time use link with token.
    Otherwise, creates the old format link (backward compatibility).
    
    Note: Decimal point in amount is replaced with 'p' to avoid URL parsing issues
    Example: 50.5 becomes 50p5
    """
    if db_manager and user_id and token:
        # New format: one-time use with token
        return f"https://t.me/{bot_username}?start=pay_{token}"
    else:
        # Old format: backward compatibility
        amount_str = str(amount).replace('.', 'p')
        return f"https://t.me/{bot_username}?start=pay_{destination_account}_{amount_str}"


def parse_payment_link(url: str) -> Tuple[bool, Optional[str], Optional[float], Optional[str]]:
    """
    Parse payment link URL and extract information
    New format: https://t.me/{bot_username}?start=pay_{token}
    Old format: https://t.me/{bot_username}?start=pay_{destination_account}_{amount}
    Returns: (is_payment_link, destination_account, amount, token)
    """
    try:
        # Check if URL contains payment link pattern
        if '?start=pay_' not in url and '&start=pay_' not in url:
            return (False, None, None, None)
        
        # Extract the start parameter
        if '?start=' in url:
            params = url.split('?start=')[1].split('&')[0]
        elif '&start=' in url:
            params = url.split('&start=')[1].split('&')[0]
        else:
            return (False, None, None, None)
        
        if not params.startswith('pay_'):
            return (False, None, None, None)
        
        # Remove 'pay_' prefix
        link_data = params[4:]  # Remove 'pay_' (4 characters)
        
        # Check if it's a token (32 characters alphanumeric) or old format
        if len(link_data) == 32 and link_data.isalnum():
            # New format: token-based (one-time use)
            return (True, None, None, link_data)
        else:
            # Old format: pay_{destination_account}_{amount} or pay_{amount}
            link_parts = link_data.split('_')
            
            if len(link_parts) == 2:
                destination_account = link_parts[0]
                # Convert 'p' back to '.' for decimal amounts
                amount_str = link_parts[1].replace('p', '.')
                amount = float(amount_str)
                return (True, destination_account, amount, None)
            elif len(link_parts) == 1:
                # Old format: pay_{amount} (backward compatibility)
                # Convert 'p' back to '.' for decimal amounts
                amount_str = link_parts[0].replace('p', '.')
                amount = float(amount_str)
                return (True, None, amount, None)
            else:
                return (False, None, None, None)
    except (ValueError, IndexError):
        return (False, None, None, None)
