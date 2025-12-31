from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
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

