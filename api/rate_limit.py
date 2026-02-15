"""In-memory per-IP rate limiter dependencies."""

import os
import time

from fastapi import HTTPException, Request


_requests: dict[str, list[float]] = {}
_phone_requests: dict[str, list[float]] = {}


def _get_limit() -> int:
    """Requests per minute, configurable via ETHOS_RATE_LIMIT."""
    try:
        limit = int(os.environ.get("ETHOS_RATE_LIMIT", "10"))
    except (ValueError, TypeError):
        return 10
    return max(limit, 1)


def _sliding_window(
    store: dict[str, list[float]],
    key: str,
    limit: int,
    window: float,
) -> None:
    """Shared sliding-window check. Raises 429 if over limit."""
    now = time.time()
    timestamps = [t for t in store.get(key, []) if now - t < window]

    if len(timestamps) >= limit:
        retry_after = int(timestamps[0] + window - now) + 1
        store[key] = timestamps
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    timestamps.append(now)
    store[key] = timestamps

    # Cleanup stale keys to prevent memory growth
    stale = [
        k for k, v in store.items() if k != key and all(now - t >= window for t in v)
    ]
    for k in stale:
        del store[k]


def rate_limit(request: Request) -> None:
    """General sliding-window rate limiter keyed by client IP."""
    ip = request.client.host if request.client else "unknown"
    _sliding_window(_requests, ip, _get_limit(), 60.0)


def phone_rate_limit(request: Request) -> None:
    """Strict rate limiter for SMS endpoints: 3 requests per minute per IP."""
    ip = request.client.host if request.client else "unknown"
    _sliding_window(_phone_requests, f"phone:{ip}", 3, 60.0)
