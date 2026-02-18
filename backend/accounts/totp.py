"""TOTP (Time-based One-Time Password) utilities for 2FA.
Compatible with Google Authenticator and Microsoft Authenticator.
"""
import pyotp
import qrcode
import io
import base64


def generate_totp_secret():
    """Generate a new TOTP secret key."""
    return pyotp.random_base32()


def get_totp_uri(secret, username, issuer='AccountSystem'):
    """Generate a TOTP URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def generate_qr_code_base64(uri):
    """Generate a QR code as a base64 encoded PNG image."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def verify_totp(secret, code):
    """Verify a TOTP code against the secret.
    Allows a window of 1 for clock drift tolerance.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
