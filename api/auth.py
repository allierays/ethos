"""API key authentication dependencies."""

import hmac
import logging
import os
from collections.abc import Generator

from fastapi import HTTPException, Request

from ethos_academy.context import agent_api_key_var

logger = logging.getLogger(__name__)

_auth_warning_logged = False


def require_api_key(request: Request) -> None:
    """Validate Bearer token against ETHOS_API_KEY env var.

    If ETHOS_API_KEY is not set or empty, auth is disabled (development mode).
    Per-agent tokens (ea_ prefix) skip server-level auth -- the domain layer
    handles those via agent_api_key_var.
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
    # Per-agent keys (ea_ prefix) bypass server auth; domain layer verifies them
    if auth.startswith("Bearer ea_"):
        return
    expected = f"Bearer {api_key}"
    if not hmac.compare_digest(auth.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def inject_agent_key(request: Request) -> Generator[None, None, None]:
    """Extract per-agent API key from Authorization header and set ContextVar.

    If the Bearer token starts with 'ea_', sets agent_api_key_var so the
    domain layer (enrollment/service.py) can verify it against the agent's
    stored hash. This dependency makes no auth decisions -- it only passes
    context through. The domain layer decides whether to enforce.

    Uses yield-based dependency to guarantee ContextVar reset after request.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ea_"):
        token = auth[7:].strip()
        reset_token = agent_api_key_var.set(token)
        try:
            yield
        finally:
            agent_api_key_var.reset(reset_token)
    else:
        yield
