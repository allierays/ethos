"""Response parser — extract trait scores from Claude's evaluation output.

Pure parsing. No I/O, no LLM calls. Two modes:
- parse_response(): Legacy JSON mode (raw text → dict).
- parse_tool_response(): Tool-calling mode (tool call results → dict).

Both return the same dict structure for downstream compatibility.
"""

from __future__ import annotations

import json
import logging
import re

from ethos_academy.shared.models import DetectedIndicator
from ethos_academy.taxonomy.indicators import INDICATORS

logger = logging.getLogger(__name__)

# Valid indicator IDs from the taxonomy (module-level set for fast lookup).
VALID_IDS: set[str] = {ind["id"] for ind in INDICATORS}

# All 12 traits that must appear in the output.
_ALL_TRAITS = [
    "virtue",
    "goodwill",
    "manipulation",
    "deception",
    "accuracy",
    "reasoning",
    "fabrication",
    "broken_logic",
    "recognition",
    "compassion",
    "dismissal",
    "exploitation",
]

# Regex to extract JSON from markdown fences: ```json ... ``` or ``` ... ```
_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n\s*```", re.DOTALL)


def _clamp(value: float) -> float:
    """Clamp a score to 0.0–1.0."""
    return max(0.0, min(1.0, float(value)))


def _extract_json(raw: str) -> str:
    """Extract JSON string from raw text, stripping markdown fences if present."""
    match = _FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


def _default_result() -> dict:
    """Return a safe default result when parsing fails."""
    return {
        "trait_scores": {t: 0.5 for t in _ALL_TRAITS},
        "detected_indicators": [],
        "overall_trust": "unknown",
        "alignment_status": "unknown",
    }


def _parse_indicators(raw_indicators: list) -> list[DetectedIndicator]:
    """Parse indicator dicts into DetectedIndicator Pydantic objects.

    Filters out indicators with IDs not in VALID_IDS (logs a warning for each).
    """
    indicators = []
    for item in raw_indicators:
        if not isinstance(item, dict):
            continue
        ind_id = item.get("id", "")
        if ind_id not in VALID_IDS:
            logger.warning("Filtered invalid indicator ID: %s", ind_id)
            continue
        indicators.append(
            DetectedIndicator(
                id=ind_id,
                name=item.get("name", ""),
                trait=item.get("trait", ""),
                confidence=_clamp(item.get("confidence", 0.0)),
                severity=_clamp(item.get("severity", 0.0)),
                evidence=item.get("evidence", ""),
            )
        )
    return indicators


def parse_response(raw_text: str) -> dict:
    """Parse Claude's JSON response into a structured dict.

    Args:
        raw_text: Raw text from Claude (may include markdown fences).

    Returns:
        Dict with keys: trait_scores, detected_indicators, overall_trust, alignment_status.
        On parse failure, returns defaults (all scores 0.5, trust='unknown').
    """
    if not raw_text or not raw_text.strip():
        return _default_result()

    json_str = _extract_json(raw_text)

    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return _default_result()

    if not isinstance(data, dict):
        return _default_result()

    # Extract trait scores — fill missing, clamp out-of-range
    raw_scores = data.get("trait_scores", {})
    if not isinstance(raw_scores, dict):
        raw_scores = {}

    trait_scores = {}
    for trait in _ALL_TRAITS:
        value = raw_scores.get(trait, 0.0)
        try:
            trait_scores[trait] = _clamp(float(value))
        except (TypeError, ValueError):
            trait_scores[trait] = 0.0

    # Extract detected indicators
    raw_indicators = data.get("detected_indicators", [])
    if not isinstance(raw_indicators, list):
        raw_indicators = []
    detected_indicators = _parse_indicators(raw_indicators)

    # Extract trust and alignment
    overall_trust = data.get("overall_trust", "unknown")
    alignment_status = data.get("alignment_status", "unknown")

    return {
        "trait_scores": trait_scores,
        "detected_indicators": detected_indicators,
        "overall_trust": str(overall_trust),
        "alignment_status": str(alignment_status),
    }


def parse_tool_response(tool_results: dict[str, dict]) -> dict:
    """Parse tool call results into the standard evaluation dict.

    Accepts the dict returned by call_claude_with_tools:
        {"identify_intent": {...}, "detect_indicators": {...}, "score_traits": {...}}

    Returns the same structure as parse_response() for downstream compatibility,
    plus extra fields: confidence, intent_analysis, scoring_reasoning.
    """
    if not tool_results:
        result = _default_result()
        result["confidence"] = 0.0
        result["intent_analysis"] = {}
        result["scoring_reasoning"] = ""
        return result

    # ── identify_intent (stored for logging and audit) ──────────────
    intent_analysis = tool_results.get("identify_intent", {})

    # ── detect_indicators ───────────────────────────────────────────
    indicators_data = tool_results.get("detect_indicators", {})
    raw_indicators = indicators_data.get("indicators", [])
    if not isinstance(raw_indicators, list):
        raw_indicators = []
    detected_indicators = _parse_indicators(raw_indicators)

    # ── score_traits ────────────────────────────────────────────────
    scores_data = tool_results.get("score_traits", {})
    raw_scores = scores_data.get("trait_scores", {})
    if not isinstance(raw_scores, dict):
        raw_scores = {}

    trait_scores = {}
    for trait in _ALL_TRAITS:
        value = raw_scores.get(trait, 0.0)
        try:
            trait_scores[trait] = _clamp(float(value))
        except (TypeError, ValueError):
            trait_scores[trait] = 0.0

    overall_trust = scores_data.get("overall_trust", "unknown")
    confidence = scores_data.get("confidence", 0.5)
    try:
        confidence = _clamp(float(confidence))
    except (TypeError, ValueError):
        confidence = 0.5
    scoring_reasoning = scores_data.get("reasoning", "")

    return {
        "trait_scores": trait_scores,
        "detected_indicators": detected_indicators,
        "overall_trust": str(overall_trust),
        "alignment_status": "unknown",  # Computed deterministically downstream
        "confidence": confidence,
        "intent_analysis": intent_analysis,
        "scoring_reasoning": scoring_reasoning,
    }
