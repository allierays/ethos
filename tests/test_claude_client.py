"""Tests for ethos/evaluation/claude_client.py — sync Anthropic SDK wrapper.

TDD: Tests written first, implementation follows.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ethos.shared.errors import ConfigError, EvaluationError


# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------

class TestModelSelection:
    """call_claude selects the correct model based on routing tier."""

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_standard_tier_uses_sonnet(self, mock_from_env, mock_anthropic):
        from ethos.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        call_claude("system", "user", "standard")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-sonnet-4-20250514"

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_focused_tier_uses_sonnet(self, mock_from_env, mock_anthropic):
        from ethos.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        call_claude("system", "user", "focused")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-sonnet-4-20250514"

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_deep_tier_uses_opus(self, mock_from_env, mock_anthropic):
        from ethos.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        call_claude("system", "user", "deep")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-opus-4-6"

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_deep_with_context_tier_uses_opus(self, mock_from_env, mock_anthropic):
        from ethos.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        call_claude("system", "user", "deep_with_context")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-opus-4-6"


# ---------------------------------------------------------------------------
# Prompt routing
# ---------------------------------------------------------------------------

class TestPromptRouting:
    """call_claude passes system_prompt and user_prompt correctly."""

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_system_prompt_in_system_param(self, mock_from_env, mock_anthropic):
        from ethos.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        call_claude("my system prompt", "my user prompt", "standard")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["system"] == "my system prompt"

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_user_prompt_in_messages(self, mock_from_env, mock_anthropic):
        from ethos.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        call_claude("sys", "my user prompt", "standard")

        call_args = mock_client.messages.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "my user prompt"

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_max_tokens_is_2048(self, mock_from_env, mock_anthropic):
        from ethos.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="response")]
        )

        call_claude("sys", "usr", "standard")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["max_tokens"] == 2048


# ---------------------------------------------------------------------------
# Return value
# ---------------------------------------------------------------------------

class TestReturnValue:
    """call_claude returns the raw text from Claude's response."""

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_returns_text_content(self, mock_from_env, mock_anthropic):
        from ethos.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text='{"trait_scores": {}}')]
        )

        result = call_claude("sys", "usr", "standard")

        assert result == '{"trait_scores": {}}'


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """call_claude raises descriptive errors on failure."""

    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_missing_api_key_raises_config_error(self, mock_from_env):
        from ethos.evaluation.claude_client import call_claude

        mock_from_env.side_effect = ConfigError("ANTHROPIC_API_KEY not set")

        with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
            call_claude("sys", "usr", "standard")

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    def test_api_error_raises_evaluation_error(self, mock_from_env, mock_anthropic):
        from ethos.evaluation.claude_client import call_claude

        cfg = MagicMock()
        cfg.anthropic_api_key = "test-key"
        mock_from_env.return_value = cfg

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API rate limited")

        with pytest.raises(EvaluationError, match="Claude API"):
            call_claude("sys", "usr", "standard")


# ---------------------------------------------------------------------------
# Model name from env override
# ---------------------------------------------------------------------------

class TestModelEnvOverride:
    """Model names should come from env vars, not be hardcoded (sign-001)."""

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    @patch.dict("os.environ", {"ETHOS_SONNET_MODEL": "claude-sonnet-4-5-20250929"})
    def test_sonnet_model_from_env(self, mock_from_env, mock_anthropic):
        from ethos.evaluation.claude_client import _get_model

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

    @patch("ethos.evaluation.claude_client.anthropic")
    @patch("ethos.evaluation.claude_client.EthosConfig.from_env")
    @patch.dict("os.environ", {"ETHOS_OPUS_MODEL": "claude-opus-4-20250514"})
    def test_opus_model_from_env(self, mock_from_env, mock_anthropic):
        from ethos.evaluation.claude_client import _get_model

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
