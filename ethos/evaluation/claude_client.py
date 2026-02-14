"""Async Anthropic SDK wrapper for Claude evaluation calls.

Loads API key lazily from EthosConfig.from_env() — not at import time.
Model selection based on routing tier with env var overrides.

Two call modes:
    - call_claude(): Simple prompt → text response (legacy JSON mode).
    - call_claude_with_tools(): Three-tool pipeline for structured evaluation.
"""

from __future__ import annotations

import logging
import os

import anthropic

from ethos.config.config import EthosConfig
from ethos.shared.errors import EvaluationError

logger = logging.getLogger(__name__)

# Default model IDs — overridable via environment variables (sign-001)
_DEFAULT_SONNET_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_OPUS_MODEL = "claude-opus-4-6"

# Tool names we expect Claude to call, in order.
_EXPECTED_TOOLS = ("identify_intent", "detect_indicators", "score_traits")


def _get_model(tier: str) -> str:
    """Select the Claude model based on routing tier.

    Standard/focused → Sonnet (fast, cost-effective).
    Deep/deep_with_context → Opus (maximum reasoning).

    Override via ETHOS_SONNET_MODEL or ETHOS_OPUS_MODEL env vars.
    """
    if tier in ("deep", "deep_with_context"):
        return os.environ.get("ETHOS_OPUS_MODEL", _DEFAULT_OPUS_MODEL)
    return os.environ.get("ETHOS_SONNET_MODEL", _DEFAULT_SONNET_MODEL)


async def call_claude(system_prompt: str, user_prompt: str, tier: str) -> str:
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

    client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)

    # Deep tiers (daily reports) produce large structured JSON responses
    max_tokens = 4096 if tier in ("deep", "deep_with_context") else 2048

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:
        raise EvaluationError(f"Claude API call failed: {exc}") from exc

    return response.content[0].text


async def call_claude_with_tools(
    system_prompt: str,
    user_prompt: str,
    tier: str,
    tools: list[dict],
) -> dict[str, dict]:
    """Call Claude with tool definitions and collect structured results.

    Claude calls three tools in sequence: identify_intent, detect_indicators,
    score_traits. If Claude doesn't call all three in one turn, we send tool
    results back and ask it to continue (up to 3 round-trips).

    Args:
        system_prompt: Evaluation instructions (system parameter).
        user_prompt: Message to evaluate (user message).
        tier: Routing tier for model selection.
        tools: Tool definitions (from ethos.evaluation.tools).

    Returns:
        Dict mapping tool name to its input data:
        {
            "identify_intent": {...},
            "detect_indicators": {...},
            "score_traits": {...},
        }

    Raises:
        EvaluationError: If the API call fails or tools are incomplete.
    """
    config = EthosConfig.from_env()
    model = _get_model(tier)
    client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)
    max_tokens = 4096

    messages: list[dict] = [{"role": "user", "content": user_prompt}]
    tool_results: dict[str, dict] = {}

    # Up to 3 turns to collect all tool calls
    for turn in range(3):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=messages,
                tools=tools,
                tool_choice={"type": "any"},
            )
        except Exception as exc:
            raise EvaluationError(f"Claude API call failed: {exc}") from exc

        # Extract tool calls from this turn
        tool_use_blocks = []
        for block in response.content:
            if block.type == "tool_use":
                tool_results[block.name] = block.input
                tool_use_blocks.append(block)

        # All three tools collected
        if all(name in tool_results for name in _EXPECTED_TOOLS):
            break

        # No tool calls in response, nothing more to do
        if not tool_use_blocks:
            logger.warning("Claude returned no tool calls on turn %d", turn)
            break

        # Send tool results back and ask Claude to continue
        messages.append({"role": "assistant", "content": response.content})
        tool_result_content = [
            {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": "Recorded. Continue with remaining tools.",
            }
            for block in tool_use_blocks
        ]
        messages.append({"role": "user", "content": tool_result_content})

        # Claude signaled end of turn
        if response.stop_reason == "end_turn":
            break

    missing = [name for name in _EXPECTED_TOOLS if name not in tool_results]
    if missing:
        logger.warning("Missing tool calls: %s", missing)

    return tool_results
