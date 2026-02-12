"""In-memory per-IP rate limiter dependency."""

import os
import time

from fastapi import HTTPException, Request


_requests: dict[str, list[float]] = {}


def _get_limit() -> int:
    """Requests per minute, configurable via ETHOS_RATE_LIMIT."""
    return int(os.environ.get("ETHOS_RATE_LIMIT", "10"))


def rate_limit(request: Request) -> None:
    """Sliding-window rate limiter keyed by client IP."""
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60.0
    limit = _get_limit()

    # Get or create timestamp list, prune expired entries
    timestamps = _requests.get(ip, [])
    timestamps = [t for t in timestamps if now - t < window]

    if len(timestamps) >= limit:
        retry_after = int(timestamps[0] + window - now) + 1
        _requests[ip] = timestamps
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    timestamps.append(now)
    _requests[ip] = timestamps

    # Cleanup stale IPs to prevent memory growth
    stale = [k for k, v in _requests.items() if k != ip and all(now - t >= window for t in v)]
    for k in stale:
        del _requests[k]
