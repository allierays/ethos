"""Shared test fixtures."""

import pytest

from api.rate_limit import _requests, _phone_requests


@pytest.fixture(autouse=True)
def _clear_rate_limits():
    """Reset in-memory rate limiter between tests to prevent bleed."""
    _requests.clear()
    _phone_requests.clear()
    yield
    _requests.clear()
    _phone_requests.clear()
