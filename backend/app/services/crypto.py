import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet_key() -> bytes:
    """
    Derive a deterministic 32-byte urlsafe Fernet key.
    If CALENDAR_TOKEN_ENCRYPTION_KEY is set and valid, use it.
    Otherwise, derive stably from GOOGLE_CLIENT_SECRET or fallback seed.
    """
    configured = (settings.CALENDAR_TOKEN_ENCRYPTION_KEY or "").strip()
    if configured:
        try:
            # Test if valid 32-byte urlsafe base64 key
            Fernet(configured.encode())
            return configured.encode()
        except Exception:
            pass

    # Deterministic derivation from secret or app name
    seed = (settings.GOOGLE_CLIENT_SECRET or settings.APP_NAME or "mediwell-secret-salt").encode()
    digest = hashlib.sha256(seed).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_token(token: Optional[str]) -> Optional[str]:
    """Encrypt a secret token string using Fernet authenticated encryption."""
    if not token:
        return None
    key = _get_fernet_key()
    fernet = Fernet(key)
    return fernet.encrypt(token.encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: Optional[str]) -> Optional[str]:
    """Decrypt a ciphertext token back into plaintext."""
    if not encrypted_token:
        return None
    key = _get_fernet_key()
    fernet = Fernet(key)
    try:
        return fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except Exception:
        return None
