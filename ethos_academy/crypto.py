"""Fernet symmetric encryption for phone numbers at rest.

Uses AES-128-CBC + HMAC-SHA256 via the cryptography library.
Key from ETHOS_ENCRYPTION_KEY env var. No key = passthrough with warning (dev mode).
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_fernet = None
_initialized = False


def _get_fernet():
    """Lazy-init Fernet cipher from env var. Returns None if no key configured."""
    global _fernet, _initialized
    if _initialized:
        return _fernet

    _initialized = True
    key = os.environ.get("ETHOS_ENCRYPTION_KEY", "")
    if not key:
        logger.warning(
            "ETHOS_ENCRYPTION_KEY not set. Phone numbers stored unencrypted (dev mode)."
        )
        return None

    try:
        from cryptography.fernet import Fernet

        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
        return _fernet
    except Exception as exc:
        logger.warning(
            "Failed to initialize Fernet: %s. Falling back to passthrough.", exc
        )
        return None


def encrypt(plaintext: str) -> str:
    """Encrypt a string. Returns Fernet token or passthrough if no key configured."""
    if not plaintext:
        return ""
    f = _get_fernet()
    if f is None:
        return plaintext
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a Fernet token. Handles pre-encryption plaintext gracefully."""
    if not ciphertext:
        return ""
    f = _get_fernet()
    if f is None:
        return ciphertext
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        # Pre-encryption plaintext value (safe migration path)
        return ciphertext


def reset():
    """Reset the cached Fernet instance. For testing only."""
    global _fernet, _initialized
    _fernet = None
    _initialized = False
