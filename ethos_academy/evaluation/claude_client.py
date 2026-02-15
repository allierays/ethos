"""Async Anthropic SDK wrapper for Claude evaluation calls.

Loads API key lazily from EthosConfig.from_env() — not at import time.
Model selection based on routing tier with env var overrides.

Two call modes:
    - call_claude(): Simple prompt -> text response (reports, insights).
    - call_claude_with_tools(): Think-then-Extract pipeline for structured evaluation.

Extended thinking (Think-then-Extract pattern):
    Call 1 (Think): Extended thinking enabled, no tools. Claude reasons deeply.
    Call 2 (Extract): No thinking, tool_choice="any", Sonnet. Fills tool schemas.
    Fallback: Unknown model or empty analysis -> original single-call path.

Prompt caching: Static system prompts use cache_control for 90% input cost reduction.
"""

from __future__ import annotations

import logging
import os
import re

import anthropic

from ethos_academy.config.config import EthosConfig
from ethos_academy.context import anthropic_api_key_var
from ethos_academy.shared.errors import ConfigError, EvaluationError

logger = logging.getLogger(__name__)

# Default model IDs — overridable via environment variables (sign-001)
_DEFAULT_SONNET_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_OPUS_MODEL = "claude-opus-4-6"

# Tool names we expect Claude to call, in order.
_EXPECTED_TOOLS = ("identify_intent", "detect_indicators", "score_traits")

# Extraction system prompt for Call 2 (Think-then-Extract)
_EXTRACT_SYSTEM = (
    "You are extracting a prior analysis into structured evaluation tools. "
    "Call all three tools: identify_intent, detect_indicators, score_traits."
)

# Regex patterns to redact API keys in error messages
_KEY_PATTERN = re.compile(
    r"sk-ant-\S+"  # Anthropic keys
    r"|moltbook_sk_\S+"  # Moltbook keys
    r"|(?<=['\"\s=])[A-Za-z0-9+/]{40,}(?=['\"\s]|$)"  # Long base64 tokens (Azure, etc.)
)


def _resolve_api_key() -> str:
    """Return the Anthropic API key for the current request.

    Checks the BYOK ContextVar first (per-request override), then falls
    back to the server key from EthosConfig.from_env().
    """
    byok = anthropic_api_key_var.get()
    if byok is not None:
        return byok
    return EthosConfig.from_env().anthropic_api_key


def _redact(msg: str) -> str:
    """Scrub any sk-ant-* tokens from an error message."""
    return _KEY_PATTERN.sub("[REDACTED]", msg)


def _get_model(tier: str) -> str:
    """Select the Claude model based on routing tier.

    Standard/focused -> Sonnet (fast, cost-effective).
    Deep/deep_with_context -> Opus (maximum reasoning).

    Override via ETHOS_SONNET_MODEL or ETHOS_OPUS_MODEL env vars.
    """
    if tier in ("deep", "deep_with_context"):
        return os.environ.get("ETHOS_OPUS_MODEL", _DEFAULT_OPUS_MODEL)
    return os.environ.get("ETHOS_SONNET_MODEL", _DEFAULT_SONNET_MODEL)


def _get_thinking_config(model: str) -> dict | None:
    """Return extended thinking config for models that support it.

    Opus 4.6: adaptive thinking (model decides depth).
    Sonnet 4: enabled with 4096 token budget.
    Other models: None (no thinking support).
    """
    if "opus-4-6" in model:
        return {"type": "adaptive"}
    if "sonnet-4" in model:
        return {"type": "enabled", "budget_tokens": 4096}
    return None


def _cacheable_system(system_prompt: str) -> list[dict]:
    """Convert a system prompt string to a cacheable content block array.

    The indicator catalog and constitutional values are static across calls.
    Caching skips re-tokenizing the same rulebook on repeated evaluations.
    """
    return [
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }
    ]


async def _call_think_then_extract(
    client: anthropic.AsyncAnthropic,
    model: str,
    system_prompt: str,
    user_prompt: str,
    tier: str,
    tools: list[dict],
    thinking_config: dict,
) -> tuple[dict[str, dict], str] | None:
    """Two-call Think-then-Extract pipeline.

    Call 1 (Think): Extended thinking, no tools. Deep reasoning about the message.
    Call 2 (Extract): No thinking, tool_choice="any", Sonnet. Fills tool schemas.

    Returns (tool_results, thinking_content) or None if Call 1 produces no analysis.
    """
    # ── Call 1: Think ──────────────────────────────────────────────
    think_suffix = (
        "\n\nAnalyze this message thoroughly. Assess the intent, identify "
        "behavioral indicators across all 12 traits, and determine appropriate "
        "scores. Provide your complete analysis as text."
    )

    think_kwargs: dict = {
        "model": model,
        "max_tokens": 16384,
        "system": _cacheable_system(system_prompt),
        "messages": [{"role": "user", "content": user_prompt + think_suffix}],
        "thinking": thinking_config,
    }

    try:
        think_response = await client.messages.create(**think_kwargs)
    except anthropic.AuthenticationError:
        raise ConfigError("Invalid Anthropic API key") from None
    except Exception as exc:
        logger.warning(
            "Think call failed, falling back to single-call: %s", _redact(str(exc))
        )
        return None

    # Extract thinking blocks and text from response
    thinking_content = ""
    analysis_text = ""
    for block in think_response.content:
        if block.type == "thinking":
            thinking_content += block.thinking
        elif block.type == "text":
            analysis_text += block.text

    if not analysis_text.strip():
        logger.warning("Think call returned empty analysis, falling back")
        return None

    logger.debug(
        "Think call: %d thinking chars, %d analysis chars",
        len(thinking_content),
        len(analysis_text),
    )

    # ── Call 2: Extract ────────────────────────────────────────────
    sonnet_model = os.environ.get("ETHOS_SONNET_MODEL", _DEFAULT_SONNET_MODEL)

    extract_messages: list[dict] = [
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": analysis_text},
        {
            "role": "user",
            "content": "Extract your analysis into the three evaluation tools.",
        },
    ]
    tool_results: dict[str, dict] = {}

    # Same multi-turn retry loop as the single-call path
    for turn in range(3):
        try:
            extract_response = await client.messages.create(
                model=sonnet_model,
                max_tokens=4096,
                system=_cacheable_system(_EXTRACT_SYSTEM),
                messages=extract_messages,
                tools=tools,
                tool_choice={"type": "any"},
            )
        except anthropic.AuthenticationError:
            raise ConfigError("Invalid Anthropic API key") from None
        except Exception as exc:
            raise EvaluationError(f"Extract call failed: {_redact(str(exc))}") from None

        tool_use_blocks = []
        for block in extract_response.content:
            if block.type == "tool_use":
                tool_results[block.name] = block.input
                tool_use_blocks.append(block)

        if all(name in tool_results for name in _EXPECTED_TOOLS):
            break

        if not tool_use_blocks:
            logger.warning("Extract returned no tool calls on turn %d", turn)
            break

        extract_messages.append(
            {"role": "assistant", "content": extract_response.content}
        )
        extract_messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Recorded. Continue with remaining tools.",
                    }
                    for block in tool_use_blocks
                ],
            }
        )

        if extract_response.stop_reason == "end_turn":
            break

    missing = [name for name in _EXPECTED_TOOLS if name not in tool_results]
    if missing:
        logger.warning("Missing tool calls after extract: %s", missing)

    return tool_results, thinking_content


async def call_claude(system_prompt: str, user_prompt: str, tier: str) -> str:
    """Call Claude with the given prompts and return the raw text response.

    Uses prompt caching on the system prompt. When extended thinking is
    available for the selected model, enables it for deeper reasoning.

    Args:
        system_prompt: Instructions for Claude (goes in system parameter).
        user_prompt: The message to evaluate (goes in messages).
        tier: Routing tier -- determines model selection.

    Returns:
        Raw text response from Claude.

    Raises:
        ConfigError: If ANTHROPIC_API_KEY is not set.
        EvaluationError: If the Anthropic API call fails.
    """
    api_key = _resolve_api_key()
    model = _get_model(tier)
    client = anthropic.AsyncAnthropic(api_key=api_key, max_retries=1)

    # Deep tiers (daily reports) produce large structured JSON responses
    max_tokens = 4096 if tier in ("deep", "deep_with_context") else 2048

    call_kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "system": _cacheable_system(system_prompt),
        "messages": [{"role": "user", "content": user_prompt}],
    }

    # Enable extended thinking when the model supports it
    thinking_config = _get_thinking_config(model)
    if thinking_config:
        call_kwargs["thinking"] = thinking_config
        call_kwargs["max_tokens"] = max(max_tokens, 8192)

    try:
        response = await client.messages.create(**call_kwargs)
    except anthropic.AuthenticationError:
        raise ConfigError("Invalid Anthropic API key") from None
    except Exception as exc:
        raise EvaluationError(f"Claude API call failed: {_redact(str(exc))}") from None

    # Extract text blocks (skip thinking blocks)
    text_parts = []
    for block in response.content:
        if block.type == "thinking":
            logger.debug("Thinking: %s", block.thinking[:200])
        elif block.type == "text":
            text_parts.append(block.text)

    return "".join(text_parts)


async def call_claude_with_tools(
    system_prompt: str,
    user_prompt: str,
    tier: str,
    tools: list[dict],
) -> tuple[dict[str, dict], str]:
    """Call Claude with tool definitions and collect structured results.

    Uses Think-then-Extract when extended thinking is available:
        Call 1: Deep reasoning with thinking enabled, no tools.
        Call 2: Extract analysis into tool schemas with Sonnet.

    Falls back to single-call path for models without thinking support
    or when the think call fails.

    Args:
        system_prompt: Evaluation instructions (system parameter).
        user_prompt: Message to evaluate (user message).
        tier: Routing tier for model selection.
        tools: Tool definitions (from ethos_academy.evaluation.tools).

    Returns:
        Tuple of (tool_results, thinking_content):
        - tool_results: Dict mapping tool name to its input data.
        - thinking_content: Extended thinking trace (empty string if not available).

    Raises:
        EvaluationError: If the API call fails or tools are incomplete.
    """
    api_key = _resolve_api_key()
    model = _get_model(tier)
    client = anthropic.AsyncAnthropic(api_key=api_key, max_retries=1)

    # Think-then-Extract only for deep tiers where reasoning depth matters.
    # Standard/focused stay on the fast single-call path — Sonnet's 4096-token
    # thinking budget doesn't produce meaningfully different scores, just 2x latency.
    if tier in ("deep", "deep_with_context"):
        thinking_config = _get_thinking_config(model)
        if thinking_config:
            result = await _call_think_then_extract(
                client, model, system_prompt, user_prompt, tier, tools, thinking_config
            )
            if result is not None:
                return result

    # Fallback: single-call path (original behavior + prompt caching)
    max_tokens = 4096
    messages: list[dict] = [{"role": "user", "content": user_prompt}]
    tool_results: dict[str, dict] = {}

    for turn in range(3):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=_cacheable_system(system_prompt),
                messages=messages,
                tools=tools,
                tool_choice={"type": "any"},
            )
        except anthropic.AuthenticationError:
            raise ConfigError("Invalid Anthropic API key") from None
        except Exception as exc:
            raise EvaluationError(
                f"Claude API call failed: {_redact(str(exc))}"
            ) from None

        tool_use_blocks = []
        for block in response.content:
            if block.type == "tool_use":
                tool_results[block.name] = block.input
                tool_use_blocks.append(block)

        if all(name in tool_results for name in _EXPECTED_TOOLS):
            break

        if not tool_use_blocks:
            logger.warning("Claude returned no tool calls on turn %d", turn)
            break

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

        if response.stop_reason == "end_turn":
            break

    missing = [name for name in _EXPECTED_TOOLS if name not in tool_results]
    if missing:
        logger.warning("Missing tool calls: %s", missing)

    return tool_results, ""
