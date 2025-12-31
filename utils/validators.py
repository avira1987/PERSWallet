import re
from typing import Tuple


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password: minimum 8 digits, only English numbers
    Returns: (is_valid, error_message)
    """
    if not password:
        return False, "رمز عبور نمی‌تواند خالی باشد."
    
    if len(password) < 8:
        return False, "رمز عبور باید حداقل ۸ رقم باشد."
    
    if not password.isdigit():
        return False, "رمز عبور باید فقط شامل اعداد انگلیسی باشد."
    
    # Check if all digits are English (0-9)
    if not re.match(r'^[0-9]+$', password):
        return False, "رمز عبور باید فقط شامل اعداد انگلیسی باشد."
    
    return True, ""


def validate_account_number(account_number: str) -> Tuple[bool, str]:
    """
    Validate 16-digit account number
    Returns: (is_valid, error_message)
    """
    if not account_number:
        return False, "شماره حساب نمی‌تواند خالی باشد."
    
    # Remove any spaces or dashes
    account_number = account_number.replace(' ', '').replace('-', '')
    
    if len(account_number) != 16:
        return False, "شماره حساب باید دقیقاً ۱۶ رقم باشد."
    
    if not account_number.isdigit():
        return False, "شماره حساب باید فقط شامل اعداد باشد."
    
    return True, ""


def validate_sheba(sheba: str) -> Tuple[bool, str]:
    """
    Validate Iranian IBAN (Sheba) format: IR + 24 digits
    Returns: (is_valid, error_message)
    """
    if not sheba:
        return False, "شماره شبا نمی‌تواند خالی باشد."
    
    # Remove spaces
    sheba = sheba.replace(' ', '').upper()
    
    if not sheba.startswith('IR'):
        return False, "شماره شبا باید با IR شروع شود."
    
    if len(sheba) != 26:  # IR + 24 digits
        return False, "شماره شبا باید ۲۶ کاراکتر باشد (IR + ۲۴ رقم)."
    
    if not re.match(r'^IR[0-9]{24}$', sheba):
        return False, "شماره شبا باید شامل IR و ۲۴ رقم باشد."
    
    return True, ""


def validate_card_number(card_number: str) -> Tuple[bool, str]:
    """
    Validate Iranian card number: 16 digits
    Returns: (is_valid, error_message)
    """
    if not card_number:
        return False, "شماره کارت نمی‌تواند خالی باشد."
    
    # Remove spaces and dashes
    card_number = card_number.replace(' ', '').replace('-', '')
    
    if len(card_number) != 16:
        return False, "شماره کارت باید ۱۶ رقم باشد."
    
    if not card_number.isdigit():
        return False, "شماره کارت باید فقط شامل اعداد باشد."
    
    return True, ""


def validate_bank_account_number(account_number: str) -> Tuple[bool, str]:
    """
    Validate Iranian bank account number (typically 10-13 digits)
    Returns: (is_valid, error_message)
    """
    if not account_number:
        return False, "شماره حساب بانکی نمی‌تواند خالی باشد."
    
    # Remove spaces
    account_number = account_number.replace(' ', '')
    
    if not account_number.isdigit():
        return False, "شماره حساب بانکی باید فقط شامل اعداد باشد."
    
    if len(account_number) < 10 or len(account_number) > 13:
        return False, "شماره حساب بانکی باید بین ۱۰ تا ۱۳ رقم باشد."
    
    return True, ""


def validate_amount(amount: str, min_value: float = 1.0) -> Tuple[bool, str, float]:
    """
    Validate amount: must be numeric, greater than min_value
    Returns: (is_valid, error_message, parsed_amount)
    """
    if not amount:
        return False, "مقدار نمی‌تواند خالی باشد.", 0.0
    
    try:
        amount_float = float(amount)
        if amount_float < min_value:
            return False, f"مقدار باید حداقل {min_value} باشد.", 0.0
        
        return True, "", amount_float
    except ValueError:
        return False, "مقدار باید یک عدد معتبر باشد.", 0.0

