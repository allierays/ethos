"""Tests for rate limiting."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api import rate_limit as rate_limit_module
from ethos_academy.shared.models import EvaluationResult


_EVAL_PAYLOAD = {"text": "hello", "source": "test-agent"}


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    """Reset rate limiter state and disable auth for isolated tests."""
    rate_limit_module._requests.clear()
    monkeypatch.delenv("ETHOS_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _mock_domain():
    """Mock domain functions so tests don't need Claude."""
    with patch("api.main.evaluate_incoming", return_value=EvaluationResult()):
        yield


class TestUnderLimit:
    """Requests under the limit pass through."""

    def test_single_request(self, client):
        resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
        assert resp.status_code == 200

    def test_multiple_under_limit(self, client, monkeypatch):
        monkeypatch.setenv("ETHOS_RATE_LIMIT", "5")
        for _ in range(5):
            resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
            assert resp.status_code == 200


class TestOverLimit:
    """Requests over the limit get 429."""

    def test_exceeds_limit(self, client, monkeypatch):
        monkeypatch.setenv("ETHOS_RATE_LIMIT", "3")
        for _ in range(3):
            resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
            assert resp.status_code == 200

        resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
        assert resp.status_code == 429
        assert "Rate limit exceeded" in resp.json()["detail"]
        assert "Retry-After" in resp.headers

    def test_retry_after_is_positive_integer(self, client, monkeypatch):
        monkeypatch.setenv("ETHOS_RATE_LIMIT", "1")
        client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
        resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
        assert resp.status_code == 429
        retry_after = int(resp.headers["Retry-After"])
        assert 1 <= retry_after <= 61


class TestWindowExpiry:
    """After the window expires, requests are allowed again."""

    def test_window_reset(self, client, monkeypatch):
        monkeypatch.setenv("ETHOS_RATE_LIMIT", "2")

        # Fill the window
        for _ in range(2):
            client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)

        # Blocked
        resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
        assert resp.status_code == 429

        # Simulate window expiry by backdating timestamps
        for ip, timestamps in rate_limit_module._requests.items():
            rate_limit_module._requests[ip] = [t - 61 for t in timestamps]

        # Allowed again
        resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
        assert resp.status_code == 200


class TestInvalidConfig:
    """Bad ETHOS_RATE_LIMIT values fall back to defaults."""

    def test_non_numeric_limit(self, client, monkeypatch):
        monkeypatch.setenv("ETHOS_RATE_LIMIT", "abc")
        resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
        assert resp.status_code == 200  # Falls back to 10, not crash

    def test_zero_limit_floors_to_one(self, client, monkeypatch):
        monkeypatch.setenv("ETHOS_RATE_LIMIT", "0")
        resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
        assert resp.status_code == 200  # Floors to 1, allows first request

    def test_negative_limit_floors_to_one(self, client, monkeypatch):
        monkeypatch.setenv("ETHOS_RATE_LIMIT", "-5")
        resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
        assert resp.status_code == 200  # Floors to 1, allows first request
