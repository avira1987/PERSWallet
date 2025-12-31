import random
import qrcode
from io import BytesIO
from PIL import Image


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


def generate_payment_link(bot_username: str, amount: float) -> str:
    """
    Generate payment link for Telegram bot
    Format: https://t.me/{bot_username}?start=pay_{amount}
    """
    return f"https://t.me/{bot_username}?start=pay_{amount}"

