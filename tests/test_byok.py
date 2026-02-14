"""BYOK (Bring Your Own Key) integration and security tests.

Tests the full flow: X-Anthropic-Key header -> BYOKMiddleware -> ContextVar ->
_resolve_api_key() -> Claude client, plus security guarantees (key redaction,
exception chain suppression, contextvar isolation).
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api import rate_limit as rate_limit_module
from ethos.context import anthropic_api_key_var
from ethos.evaluation.claude_client import _resolve_api_key
from ethos.shared.errors import ConfigError, EvaluationError
from ethos.shared.models import EvaluationResult


_EVAL_PAYLOAD = {"text": "hello world", "source": "test-agent"}
_BYOK_KEY = "sk-ant-test-byok-key-123"
_SERVER_KEY = "sk-ant-server-key-456"


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """Ensure ETHOS_API_KEY is unset (dev mode) so auth doesn't block tests."""
    monkeypatch.delenv("ETHOS_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _clean_rate_limit():
    """Reset rate limiter between tests."""
    rate_limit_module._requests.clear()


# ---------------------------------------------------------------------------
# Key format validation (middleware rejects bad keys before ContextVar)
# ---------------------------------------------------------------------------


class TestBYOKKeyValidation:
    """BYOKMiddleware rejects keys with wrong prefix or excessive length."""

    def test_rejects_key_without_sk_ant_prefix(self, client):
        resp = client.post(
            "/evaluate/incoming",
            json=_EVAL_PAYLOAD,
            headers={"X-Anthropic-Key": "bad-prefix-key"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"] == "InvalidHeader"

    def test_rejects_key_exceeding_max_length(self, client):
        long_key = "sk-ant-" + "x" * 300
        resp = client.post(
            "/evaluate/incoming",
            json=_EVAL_PAYLOAD,
            headers={"X-Anthropic-Key": long_key},
        )
        assert resp.status_code == 400
        assert resp.json()["error"] == "InvalidHeader"

    @patch("api.main.evaluate_incoming")
    def test_accepts_valid_key_format(self, mock_eval, client):
        async def fake(*args, **kwargs):
            return EvaluationResult()

        mock_eval.side_effect = fake
        resp = client.post(
            "/evaluate/incoming",
            json=_EVAL_PAYLOAD,
            headers={"X-Anthropic-Key": _BYOK_KEY},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Key resolution (unit)
# ---------------------------------------------------------------------------


class TestResolveApiKey:
    """_resolve_api_key() checks ContextVar first, then falls back to config."""

    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_byok_takes_priority(self, mock_from_env):
        """ContextVar key wins over env key."""
        cfg = MagicMock()
        cfg.anthropic_api_key = _SERVER_KEY
        mock_from_env.return_value = cfg

        token = anthropic_api_key_var.set(_BYOK_KEY)
        try:
            assert _resolve_api_key() == _BYOK_KEY
            mock_from_env.assert_not_called()
        finally:
            anthropic_api_key_var.reset(token)

    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_falls_back_to_env(self, mock_from_env):
        """Without ContextVar, server env key used."""
        cfg = MagicMock()
        cfg.anthropic_api_key = _SERVER_KEY
        mock_from_env.return_value = cfg

        # ContextVar default is None, so fallback kicks in
        assert _resolve_api_key() == _SERVER_KEY


# ---------------------------------------------------------------------------
# API flow (integration via TestClient)
# ---------------------------------------------------------------------------


class TestBYOKApiFlow:
    """X-Anthropic-Key header flows through middleware to Claude client."""

    @patch("api.main.evaluate_incoming")
    @patch("ethos.evaluation.claude_client.anthropic")
    def test_byok_header_flows_through_api(self, mock_anthropic, mock_eval, client):
        """X-Anthropic-Key header sets ContextVar, reaches Claude client."""
        captured_keys = []

        async def fake_evaluate(*args, **kwargs):
            captured_keys.append(anthropic_api_key_var.get())
            return EvaluationResult()

        mock_eval.side_effect = fake_evaluate

        resp = client.post(
            "/evaluate/incoming",
            json=_EVAL_PAYLOAD,
            headers={"X-Anthropic-Key": _BYOK_KEY},
        )
        assert resp.status_code == 200
        assert captured_keys == [_BYOK_KEY]

    @patch("api.main.evaluate_incoming")
    def test_request_without_byok_uses_server_key(self, mock_eval, client):
        """No header means server key used (ContextVar stays None)."""
        captured_keys = []

        async def fake_evaluate(*args, **kwargs):
            captured_keys.append(anthropic_api_key_var.get())
            return EvaluationResult()

        mock_eval.side_effect = fake_evaluate

        resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)
        assert resp.status_code == 200
        assert captured_keys == [None]


# ---------------------------------------------------------------------------
# Security: error response redaction
# ---------------------------------------------------------------------------


class TestErrorRedaction:
    """sk-ant- patterns stripped from ALL error responses."""

    def test_config_error_redacts_key(self, client):
        """ConfigError path redacts sk-ant- patterns from response body."""
        with patch(
            "api.main.evaluate_incoming",
            side_effect=ConfigError(f"Bad key: {_BYOK_KEY}"),
        ):
            resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)

        body = resp.json()
        assert _BYOK_KEY not in resp.text
        assert "sk-ant-" not in body["message"]
        assert "[REDACTED]" in body["message"]

    def test_evaluation_error_redacts_key(self, client):
        """EvaluationError path also redacts sk-ant- patterns."""
        with patch(
            "api.main.evaluate_incoming",
            side_effect=EvaluationError(
                f"Claude API call failed: {_BYOK_KEY} was rejected"
            ),
        ):
            resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)

        assert resp.status_code == 422
        body = resp.json()
        assert _BYOK_KEY not in resp.text
        assert "sk-ant-" not in body["message"]


# ---------------------------------------------------------------------------
# Security: auth error -> 401, no exception chain
# ---------------------------------------------------------------------------


class TestAuthErrorSecurity:
    """Invalid BYOK key returns 401 with generic message, no key in body."""

    def test_invalid_key_returns_401(self, client):
        """Bad key returns HTTP 401 with generic message, no key in body."""
        with patch(
            "api.main.evaluate_incoming",
            side_effect=ConfigError("Invalid Anthropic API key"),
        ):
            resp = client.post(
                "/evaluate/incoming",
                json=_EVAL_PAYLOAD,
                headers={"X-Anthropic-Key": _BYOK_KEY},
            )

        assert resp.status_code == 401
        body = resp.json()
        assert body["error"] == "ConfigError"
        assert "Invalid" in body["message"]
        assert _BYOK_KEY not in resp.text

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    async def test_auth_error_no_exception_chain(self, mock_from_env, mock_anthropic):
        """AuthenticationError re-raise has __cause__ == None."""
        from ethos.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = _BYOK_KEY
        mock_from_env.return_value = cfg

        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client.messages.create.side_effect = anthropic.AuthenticationError(
            message=f"invalid x-api-key {_BYOK_KEY}",
            response=MagicMock(status_code=401),
            body={"error": {"message": "invalid x-api-key"}},
        )

        with pytest.raises(ConfigError) as exc_info:
            await call_claude("sys", "usr", "standard")

        assert exc_info.value.__cause__ is None
        assert "sk-ant-" not in str(exc_info.value)


# ---------------------------------------------------------------------------
# Security: ContextVar isolation between concurrent requests
# ---------------------------------------------------------------------------


class TestContextVarIsolation:
    """Two concurrent requests with different BYOK keys don't leak."""

    @patch("api.main.evaluate_incoming")
    async def test_contextvar_isolation(self, mock_eval):
        """Concurrent requests with different BYOK keys stay isolated."""
        captured = {}

        async def fake_evaluate(*args, **kwargs):
            key = anthropic_api_key_var.get()
            # Use the source field to identify which request this is
            source = kwargs.get("source", args[1] if len(args) > 1 else "unknown")
            captured[source] = key
            # Small delay to ensure overlap
            await asyncio.sleep(0.01)
            return EvaluationResult()

        mock_eval.side_effect = fake_evaluate

        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            key_a = "sk-ant-key-alice-111"
            key_b = "sk-ant-key-bob-222"

            resp_a, resp_b = await asyncio.gather(
                ac.post(
                    "/evaluate/incoming",
                    json={"text": "hello", "source": "alice-agent"},
                    headers={"X-Anthropic-Key": key_a},
                ),
                ac.post(
                    "/evaluate/incoming",
                    json={"text": "hello", "source": "bob-agent"},
                    headers={"X-Anthropic-Key": key_b},
                ),
            )

        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        assert captured.get("alice-agent") == key_a
        assert captured.get("bob-agent") == key_b
