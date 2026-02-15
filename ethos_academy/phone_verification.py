"""Phone verification utilities. Pure functions, no I/O."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

VERIFICATION_TTL_MINUTES = 10
MAX_VERIFICATION_ATTEMPTS = 3


def generate_verification_code() -> str:
    """Generate a cryptographically random 6-digit verification code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_code(code: str) -> str:
    """SHA-256 hash a verification code for storage."""
    return hashlib.sha256(code.encode()).hexdigest()


def verification_expiry() -> str:
    """Return an ISO datetime string for when the verification code expires."""
    expires = datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_TTL_MINUTES)
    return expires.isoformat()


def is_expired(expiry_str: str) -> bool:
    """Check if a verification code has expired."""
    if not expiry_str:
        return True
    try:
        expiry = datetime.fromisoformat(expiry_str)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expiry
    except (ValueError, TypeError):
        return True
