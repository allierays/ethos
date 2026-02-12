"""API key authentication dependency."""

import os

from fastapi import HTTPException, Request


def require_api_key(request: Request) -> None:
    """Validate Bearer token against ETHOS_API_KEY env var.

    If ETHOS_API_KEY is not set, auth is disabled (development mode).
    """
    api_key = os.environ.get("ETHOS_API_KEY", "")
    if not api_key:
        return
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {api_key}":
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
