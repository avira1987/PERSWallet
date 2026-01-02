from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import base64
import json
import config


def get_encryption_key() -> bytes:
    """
    Get or generate encryption key from config
    Fernet requires a URL-safe base64-encoded 32-byte key
    """
    key = config.ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode()
    
    if len(key) != 32:
        # If key is not 32 bytes, derive it using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'balancebot_salt',
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(key))
    else:
        # Encode to base64
        key = base64.urlsafe_b64encode(key)
    
    return key


def encrypt_state(state_data: dict) -> str:
    """
    Encrypt user state data
    """
    key = get_encryption_key()
    f = Fernet(key)
    
    state_json = json.dumps(state_data)
    encrypted = f.encrypt(state_json.encode())
    
    return encrypted.decode()


def decrypt_state(encrypted_state: str) -> dict:
    """
    Decrypt user state data
    """
    if not encrypted_state:
        return {}
    
    try:
        key = get_encryption_key()
        f = Fernet(key)
        
        decrypted = f.decrypt(encrypted_state.encode())
        state_data = json.loads(decrypted.decode())
        
        return state_data
    except Exception:
        return {}


# ARGON2ID Configuration
# Using recommended parameters for password hashing
# time_cost: number of iterations (higher = more secure but slower)
# memory_cost: memory usage in KB (higher = more secure but requires more RAM)
# parallelism: number of parallel threads
ARGON2_PH = PasswordHasher(
    time_cost=2,          # 2 iterations (good balance)
    memory_cost=65536,    # 64 MB memory
    parallelism=1,       # 1 thread
    hash_len=32,          # 32 bytes hash length
    salt_len=16           # 16 bytes salt length
)


def hash_password(password: str) -> str:
    """
    Hash a password using ARGON2ID algorithm
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    return ARGON2_PH.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """
    Verify a password against its hash using ARGON2ID
    
    Args:
        password_hash: Hashed password from database
        password: Plain text password to verify
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        ARGON2_PH.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def hash_account_number(account_number: str) -> str:
    """
    Hash an account number using ARGON2ID algorithm
    
    Args:
        account_number: Account number to hash
        
    Returns:
        Hashed account number string
    """
    return ARGON2_PH.hash(account_number)


def verify_account_number(account_number_hash: str, account_number: str) -> bool:
    """
    Verify an account number against its hash using ARGON2ID
    
    Args:
        account_number_hash: Hashed account number from database
        account_number: Plain text account number to verify
        
    Returns:
        True if account number matches, False otherwise
    """
    try:
        ARGON2_PH.verify(account_number_hash, account_number)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False

