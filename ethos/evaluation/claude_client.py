"""Sync Anthropic SDK wrapper for Claude evaluation calls.

Loads API key lazily from EthosConfig.from_env() — not at import time.
Model selection based on routing tier with env var overrides.
"""

from __future__ import annotations

import os

import anthropic

from ethos.config.config import EthosConfig
from ethos.shared.errors import EvaluationError


# Default model IDs — overridable via environment variables (sign-001)
_DEFAULT_SONNET_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_OPUS_MODEL = "claude-opus-4-6"


def _get_model(tier: str) -> str:
    """Select the Claude model based on routing tier.

    Standard/focused → Sonnet (fast, cost-effective).
    Deep/deep_with_context → Opus (maximum reasoning).

    Override via ETHOS_SONNET_MODEL or ETHOS_OPUS_MODEL env vars.
    """
    if tier in ("deep", "deep_with_context"):
        return os.environ.get("ETHOS_OPUS_MODEL", _DEFAULT_OPUS_MODEL)
    return os.environ.get("ETHOS_SONNET_MODEL", _DEFAULT_SONNET_MODEL)


def call_claude(system_prompt: str, user_prompt: str, tier: str) -> str:
    """Call Claude with the given prompts and return the raw text response.

    Args:
        system_prompt: Instructions for Claude (goes in system parameter).
        user_prompt: The message to evaluate (goes in messages).
        tier: Routing tier — determines model selection.

    Returns:
        Raw text response from Claude.

    Raises:
        ConfigError: If ANTHROPIC_API_KEY is not set.
        EvaluationError: If the Anthropic API call fails.
    """
    config = EthosConfig.from_env()
    model = _get_model(tier)

    client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:
        raise EvaluationError(f"Claude API call failed: {exc}") from exc

    return response.content[0].text
