"""Tests for rate limiting."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api import rate_limit as rate_limit_module
from ethos.shared.models import EvaluationResult


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    """Reset rate limiter state and disable auth for isolated tests."""
    rate_limit_module._requests.clear()
    monkeypatch.delenv("ETHOS_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _mock_evaluate():
    """Mock evaluate so tests don't need Claude."""
    with patch("api.main.evaluate", return_value=EvaluationResult()):
        yield


class TestUnderLimit:
    """Requests under the limit pass through."""

    def test_single_request(self, client):
        resp = client.post("/evaluate", json={"text": "hello"})
        assert resp.status_code == 200

    def test_multiple_under_limit(self, client, monkeypatch):
        monkeypatch.setenv("ETHOS_RATE_LIMIT", "5")
        for _ in range(5):
            resp = client.post("/evaluate", json={"text": "hello"})
            assert resp.status_code == 200


class TestOverLimit:
    """Requests over the limit get 429."""

    def test_exceeds_limit(self, client, monkeypatch):
        monkeypatch.setenv("ETHOS_RATE_LIMIT", "3")
        for _ in range(3):
            resp = client.post("/evaluate", json={"text": "hello"})
            assert resp.status_code == 200

        resp = client.post("/evaluate", json={"text": "hello"})
        assert resp.status_code == 429
        assert "Rate limit exceeded" in resp.json()["detail"]
        assert "Retry-After" in resp.headers


class TestWindowExpiry:
    """After the window expires, requests are allowed again."""

    def test_window_reset(self, client, monkeypatch):
        monkeypatch.setenv("ETHOS_RATE_LIMIT", "2")

        # Fill the window
        for _ in range(2):
            client.post("/evaluate", json={"text": "hello"})

        # Blocked
        resp = client.post("/evaluate", json={"text": "hello"})
        assert resp.status_code == 429

        # Simulate window expiry by backdating timestamps
        for ip, timestamps in rate_limit_module._requests.items():
            rate_limit_module._requests[ip] = [t - 61 for t in timestamps]

        # Allowed again
        resp = client.post("/evaluate", json={"text": "hello"})
        assert resp.status_code == 200
