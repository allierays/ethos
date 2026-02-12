"""Evaluate AI agent messages for honesty, accuracy, and intent.

Three faculties, one pipeline:
    1. INSTINCT  — instant keyword scan, constitutional priors (no I/O)
    2. INTUITION — graph-based pattern recognition (fast, graph queries only)
    3. DELIBERATION — full Claude evaluation across 12 traits (slow, LLM call)

Instinct and intuition inform deliberation. They don't score — they route.
Graph storage is optional — Neo4j down never crashes evaluate().
"""

from __future__ import annotations

import hashlib
import logging
import uuid

from ethos.evaluation.claude_client import call_claude, _get_model
from ethos.evaluation.instinct import scan
from ethos.evaluation.intuition import intuit
from ethos.evaluation.parser import parse_response
from ethos.evaluation.prompts import build_evaluation_prompt
from ethos.evaluation.scoring import (
    build_trait_scores,
    compute_alignment_status,
    compute_dimensions,
    compute_flags,
    compute_phronesis_level,
    compute_tier_scores,
)
from ethos.graph.read import get_agent_profile, get_evaluation_history
from ethos.graph.service import GraphService, graph_context
from ethos.graph.write import store_evaluation
from ethos.shared.models import EvaluationResult, PhronesisContext

logger = logging.getLogger(__name__)


def _build_phronesis_context(
    service: GraphService, source: str
) -> PhronesisContext | None:
    """Read agent history from graph to populate PhronesisContext.

    Passes source directly to read functions — source is already a hash
    when called from the API path (reflect), and returns empty for new
    raw agent IDs (no history yet, which is correct).

    Returns None if graph is unavailable or agent has no history.
    """
    try:
        profile = get_agent_profile(service, source)
        if not profile:
            return None

        history = get_evaluation_history(service, source, limit=10)

        # Count flagged evaluations in history
        flagged_patterns = []
        alumni_warnings = 0
        for eval_record in history:
            flags = eval_record.get("flags", [])
            if flags:
                alumni_warnings += 1
                for flag in flags:
                    if flag not in flagged_patterns:
                        flagged_patterns.append(flag)

        return PhronesisContext(
            prior_evaluations=profile.get("evaluation_count", 0),
            historical_phronesis=profile.get("dimension_averages", {}).get("ethos"),
            phronesis_trend=profile.get("alignment_history", ["insufficient_data"])[0]
            if profile.get("alignment_history")
            else "insufficient_data",
            flagged_patterns=flagged_patterns,
            alumni_warnings=alumni_warnings,
        )
    except Exception as exc:
        logger.warning("Failed to build phronesis context: %s", exc)
        return None


def _try_store_evaluation(
    service: GraphService,
    raw_agent_id: str,
    result: EvaluationResult,
    text: str,
    phronesis: str,
    agent_name: str = "",
    agent_specialty: str = "",
) -> None:
    """Attempt to store evaluation in graph. Non-fatal on failure."""
    try:
        message_hash = hashlib.sha256(text.encode()).hexdigest()
        store_evaluation(
            service=service,
            raw_agent_id=raw_agent_id,
            result=result,
            message_hash=message_hash,
            phronesis=phronesis,
            agent_name=agent_name,
            agent_specialty=agent_specialty,
        )
    except Exception as exc:
        logger.warning("Failed to store evaluation in graph: %s", exc)


def evaluate(
    text: str,
    source: str | None = None,
    source_name: str = "",
    agent_specialty: str = "",
) -> EvaluationResult:
    """Evaluate text for honesty, accuracy, and intent across ethos, logos, and pathos.

    Pipeline (three faculties):
        1. INSTINCT — scan(text) → instant keyword flags, routing tier
        2. INTUITION — intuit(source, instinct) → graph pattern recognition
        3. DELIBERATION:
           a. build_evaluation_prompt(text, instinct, intuition, tier)
           b. call_claude(system, user, tier) → raw JSON
           c. parse_response(raw) → trait scores, indicators
           d. Deterministic scoring → dimensions, tiers, alignment, phronesis, flags
        4. Graph operations (optional) — store evaluation, build phronesis context

    Args:
        text: The text to evaluate.
        source: Optional source agent identifier for graph tracking.
        source_name: Optional human-readable agent name for display.
        agent_specialty: Optional agent specialty for graph metadata.

    Returns:
        EvaluationResult with scores and alignment flags.
    """
    evaluation_id = str(uuid.uuid4())

    # ── Faculty 1: INSTINCT ───────────────────────────────────────
    # Instant, no I/O. Constitutional priors, red lines.
    instinct_result = scan(text)
    tier = instinct_result.routing_tier
    has_hard_constraint = tier == "deep_with_context"

    # ── Faculty 2: INTUITION ──────────────────────────────────────
    # Fast, graph queries only. Pattern recognition from experience.
    intuition_result = intuit(source, instinct_result)

    # Intuition can escalate the routing tier (never downgrade)
    if intuition_result.anomaly_flags and tier == "standard":
        tier = "focused"
    if intuition_result.confidence_adjustment > 0.2 and tier == "focused":
        tier = "deep"

    # ── Faculty 3: DELIBERATION ───────────────────────────────────
    # Slow, full Claude evaluation. Instinct + intuition inform the prompt.

    # Step 3a: Build prompts (intuition context enriches the prompt)
    system_prompt, user_prompt = build_evaluation_prompt(
        text, instinct_result, tier, intuition_result,
    )

    # Step 3b: Call Claude
    raw_response = call_claude(system_prompt, user_prompt, tier)

    # Step 3c: Parse response
    parsed = parse_response(raw_response)

    # Step 3d: Deterministic scoring
    traits = build_trait_scores(parsed["trait_scores"])
    dimensions = compute_dimensions(traits)
    tier_scores = compute_tier_scores(traits)
    alignment_status = compute_alignment_status(tier_scores, has_hard_constraint)
    phronesis = compute_phronesis_level(dimensions, alignment_status)
    flags = compute_flags(traits, {})  # No custom priorities yet

    # ── Build result ──────────────────────────────────────────────
    model_used = _get_model(tier)

    result = EvaluationResult(
        evaluation_id=evaluation_id,
        ethos=round(dimensions.get("ethos", 0.0), 4),
        logos=round(dimensions.get("logos", 0.0), 4),
        pathos=round(dimensions.get("pathos", 0.0), 4),
        phronesis=parsed["overall_trust"],
        alignment_status=alignment_status,
        traits=traits,
        detected_indicators=parsed["detected_indicators"],
        tier_scores=tier_scores,
        flags=flags,
        routing_tier=tier,
        keyword_density=instinct_result.density,
        model_used=model_used,
    )

    # ── Graph operations (optional) ───────────────────────────────
    phronesis_ctx = None
    if source:
        try:
            with graph_context() as service:
                phronesis_ctx = _build_phronesis_context(service, source)
                _try_store_evaluation(
                    service, source, result, text, phronesis,
                    agent_name=source_name,
                    agent_specialty=agent_specialty,
                )
        except Exception as exc:
            logger.warning("Graph operations failed: %s", exc)

    if phronesis_ctx is not None:
        result.graph_context = phronesis_ctx

    return result
