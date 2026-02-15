"""API key authentication dependency."""

import hmac
import logging
import os

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

_auth_warning_logged = False


def require_api_key(request: Request) -> None:
    """Validate Bearer token against ETHOS_API_KEY env var.

    If ETHOS_API_KEY is not set or empty, auth is disabled (development mode).
    Uses constant-time comparison to prevent timing attacks.
    """
    global _auth_warning_logged
    api_key = os.environ.get("ETHOS_API_KEY", "").strip()
    if not api_key:
        if not _auth_warning_logged:
            logger.warning(
                "ETHOS_API_KEY not set. API authentication is DISABLED. "
                "Set ETHOS_API_KEY to enable auth for production."
            )
            _auth_warning_logged = True
        return
    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {api_key}"
    if not hmac.compare_digest(auth.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
