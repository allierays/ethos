"""Tests for ethos/evaluation/claude_client.py -- async Anthropic SDK wrapper.

Covers model selection, prompt routing, error handling, BYOK key resolution,
and security hardening (AuthenticationError catch, regex redaction).
"""

from __future__ import annotations

from unittest.mock import MagicMock, AsyncMock, patch

import anthropic
import pytest

from ethos_academy.shared.errors import ConfigError, EvaluationError


# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------


class TestModelSelection:
    """call_claude selects the correct model based on routing tier."""

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_standard_tier_uses_sonnet(self, mock_from_env, mock_anthropic):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        await call_claude("system", "user", "standard")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-sonnet-4-20250514"

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_focused_tier_uses_sonnet(self, mock_from_env, mock_anthropic):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        await call_claude("system", "user", "focused")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-sonnet-4-20250514"

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_deep_tier_uses_opus(self, mock_from_env, mock_anthropic):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        await call_claude("system", "user", "deep")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-opus-4-6"

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_deep_with_context_tier_uses_opus(
        self, mock_from_env, mock_anthropic
    ):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        await call_claude("system", "user", "deep_with_context")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-opus-4-6"


# ---------------------------------------------------------------------------
# Prompt routing
# ---------------------------------------------------------------------------


class TestPromptRouting:
    """call_claude passes system_prompt and user_prompt correctly."""

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_system_prompt_in_system_param(self, mock_from_env, mock_anthropic):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        await call_claude("my system prompt", "my user prompt", "standard")

        call_args = mock_client.messages.create.call_args
        system = call_args.kwargs["system"]
        # System prompt is now a cacheable content block array
        assert isinstance(system, list)
        assert system[0]["text"] == "my system prompt"
        assert system[0]["cache_control"] == {"type": "ephemeral"}

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_user_prompt_in_messages(self, mock_from_env, mock_anthropic):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        await call_claude("sys", "my user prompt", "standard")

        call_args = mock_client.messages.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "my user prompt"

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_max_tokens_is_2048(self, mock_from_env, mock_anthropic):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        await call_claude("sys", "usr", "standard")

        call_args = mock_client.messages.create.call_args
        # Sonnet gets thinking config, which bumps max_tokens to 8192
        assert call_args.kwargs["max_tokens"] == 8192


# ---------------------------------------------------------------------------
# Return value
# ---------------------------------------------------------------------------


class TestReturnValue:
    """call_claude returns the raw text from Claude's response."""

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_returns_text_content(self, mock_from_env, mock_anthropic):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        text_block = MagicMock(type="text", text='{"trait_scores": {}}')
        mock_client.messages.create.return_value = MagicMock(content=[text_block])

        result = await call_claude("sys", "usr", "standard")

        assert result == '{"trait_scores": {}}'


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """call_claude raises descriptive errors on failure."""

    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_missing_api_key_raises_config_error(self, mock_from_env):
        from ethos_academy.evaluation.claude_client import call_claude

        mock_from_env.side_effect = ConfigError("ANTHROPIC_API_KEY not set")

        with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
            await call_claude("sys", "usr", "standard")

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_api_error_raises_evaluation_error(
        self, mock_from_env, mock_anthropic
    ):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API rate limited")

        with pytest.raises(EvaluationError, match="Claude API"):
            await call_claude("sys", "usr", "standard")


# ---------------------------------------------------------------------------
# Model name from env override
# ---------------------------------------------------------------------------


class TestModelEnvOverride:
    """Model names should come from env vars, not be hardcoded (sign-001)."""

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    @patch.dict("os.environ", {"ETHOS_SONNET_MODEL": "claude-sonnet-4-5-20250929"})
    def test_sonnet_model_from_env(self, mock_from_env, mock_anthropic):
        from ethos_academy.evaluation.claude_client import _get_model

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        # _get_model should respect the env var
        model = _get_model("standard")
        assert model == "claude-sonnet-4-5-20250929"

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    @patch.dict("os.environ", {"ETHOS_OPUS_MODEL": "claude-opus-4-20250514"})
    def test_opus_model_from_env(self, mock_from_env, mock_anthropic):
        from ethos_academy.evaluation.claude_client import _get_model

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        model = _get_model("deep")
        assert model == "claude-opus-4-20250514"


# ---------------------------------------------------------------------------
# BYOK (Bring Your Own Key) -- ContextVar key resolution
# ---------------------------------------------------------------------------


class TestBYOKKeyResolution:
    """_resolve_api_key() returns BYOK key when set, falls back to config."""

    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    def test_falls_back_to_config_when_contextvar_unset(self, mock_from_env):
        from ethos_academy.evaluation.claude_client import _resolve_api_key

        cfg = MagicMock()
        cfg.anthropic_api_key = "server-key-123"
        mock_from_env.return_value = cfg

        assert _resolve_api_key() == "server-key-123"

    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    def test_returns_byok_key_when_contextvar_set(self, mock_from_env):
        from ethos_academy.context import anthropic_api_key_var
        from ethos_academy.evaluation.claude_client import _resolve_api_key

        token = anthropic_api_key_var.set("byok-user-key")
        try:
            result = _resolve_api_key()
            assert result == "byok-user-key"
            mock_from_env.assert_not_called()
        finally:
            anthropic_api_key_var.reset(token)

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    async def test_byok_key_used_in_call_claude(self, mock_anthropic):
        """call_claude uses BYOK key from ContextVar, skipping EthosConfig."""
        from ethos_academy.context import anthropic_api_key_var
        from ethos_academy.evaluation.claude_client import call_claude

        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(type="text", text="ok")]
        )

        token = anthropic_api_key_var.set("byok-key-abc")
        try:
            await call_claude("sys", "usr", "standard")
            mock_anthropic.AsyncAnthropic.assert_called_once_with(
                api_key="byok-key-abc", max_retries=1
            )
        finally:
            anthropic_api_key_var.reset(token)


# ---------------------------------------------------------------------------
# ContextVar default
# ---------------------------------------------------------------------------


class TestContextVar:
    """anthropic_api_key_var ContextVar has correct default."""

    def test_default_is_none(self):
        from ethos_academy.context import anthropic_api_key_var

        assert anthropic_api_key_var.get() is None


# ---------------------------------------------------------------------------
# Security: AuthenticationError -> ConfigError with from None
# ---------------------------------------------------------------------------


class TestAuthenticationErrorHandling:
    """AuthenticationError raises ConfigError with generic message."""

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_call_claude_auth_error_raises_config_error(
        self, mock_from_env, mock_anthropic
    ):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "bad-key"
        mock_from_env.return_value = cfg

        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client.messages.create.side_effect = anthropic.AuthenticationError(
            message="invalid x-api-key",
            response=MagicMock(status_code=401),
            body={"error": {"message": "invalid x-api-key"}},
        )

        with pytest.raises(ConfigError, match="Invalid Anthropic API key") as exc_info:
            await call_claude("sys", "usr", "standard")

        # from None suppresses __cause__
        assert exc_info.value.__cause__ is None

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_call_claude_with_tools_auth_error_raises_config_error(
        self, mock_from_env, mock_anthropic
    ):
        from ethos_academy.evaluation.claude_client import call_claude_with_tools

        cfg = MagicMock()
        cfg.anthropic_api_key = "bad-key"
        mock_from_env.return_value = cfg

        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client.messages.create.side_effect = anthropic.AuthenticationError(
            message="invalid x-api-key",
            response=MagicMock(status_code=401),
            body={"error": {"message": "invalid x-api-key"}},
        )

        with pytest.raises(ConfigError, match="Invalid Anthropic API key") as exc_info:
            await call_claude_with_tools("sys", "usr", "standard", [])

        assert exc_info.value.__cause__ is None

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_auth_error_message_never_echoes_key(
        self, mock_from_env, mock_anthropic
    ):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "sk-ant-secret123"
        mock_from_env.return_value = cfg

        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client.messages.create.side_effect = anthropic.AuthenticationError(
            message="invalid x-api-key sk-ant-secret123",
            response=MagicMock(status_code=401),
            body={"error": {"message": "invalid x-api-key"}},
        )

        with pytest.raises(ConfigError) as exc_info:
            await call_claude("sys", "usr", "standard")

        # Generic message, not the original error with the key
        assert "sk-ant-" not in str(exc_info.value)
        assert str(exc_info.value) == "Invalid Anthropic API key"


# ---------------------------------------------------------------------------
# Security: regex redaction of sk-ant- in error messages
# ---------------------------------------------------------------------------


class TestKeyRedaction:
    """Error messages scrub sk-ant-* tokens before wrapping."""

    def test_redact_removes_key_from_message(self):
        from ethos_academy.evaluation.claude_client import _redact

        msg = "Connection failed with key sk-ant-abc123-xyz for user"
        result = _redact(msg)
        assert "sk-ant-" not in result
        assert "[REDACTED]" in result
        assert "Connection failed with key" in result

    def test_redact_handles_no_key(self):
        from ethos_academy.evaluation.claude_client import _redact

        msg = "Connection timeout after 30s"
        assert _redact(msg) == msg

    def test_redact_handles_multiple_keys(self):
        from ethos_academy.evaluation.claude_client import _redact

        msg = "tried sk-ant-key1 then sk-ant-key2"
        result = _redact(msg)
        assert result == "tried [REDACTED] then [REDACTED]"

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_evaluation_error_redacts_key_in_message(
        self, mock_from_env, mock_anthropic
    ):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client.messages.create.side_effect = RuntimeError(
            "request failed: sk-ant-mysecretkey was rejected"
        )

        with pytest.raises(EvaluationError) as exc_info:
            await call_claude("sys", "usr", "standard")

        error_msg = str(exc_info.value)
        assert "sk-ant-" not in error_msg
        assert "[REDACTED]" in error_msg

    @patch("ethos_academy.evaluation.claude_client.anthropic")
    @patch("ethos_academy.evaluation.claude_client.EthosConfig.from_env")
    async def test_from_none_suppresses_cause_on_general_error(
        self, mock_from_env, mock_anthropic
    ):
        from ethos_academy.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        mock_anthropic.AuthenticationError = anthropic.AuthenticationError
        mock_client.messages.create.side_effect = RuntimeError("some error")

        with pytest.raises(EvaluationError) as exc_info:
            await call_claude("sys", "usr", "standard")

        # from None suppresses exception chaining
        assert exc_info.value.__cause__ is None
