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

from ethos_academy.context import request_id_var
from ethos_academy.evaluation.claude_client import call_claude_with_tools, _get_model
from ethos_academy.shared.errors import EvaluationError, ParseError
from ethos_academy.evaluation.instinct import scan
from ethos_academy.evaluation.intuition import intuit
from ethos_academy.evaluation.parser import parse_tool_response
from ethos_academy.evaluation.prompts import build_evaluation_prompt
from ethos_academy.evaluation.tools import EVALUATION_TOOLS
from ethos_academy.evaluation.scoring import (
    build_trait_scores,
    compute_alignment_status,
    compute_dimensions,
    compute_flags,
    compute_phronesis_level,
    compute_tier_scores,
)
from ethos_academy.graph.read import get_agent_profile, get_evaluation_history
from ethos_academy.graph.service import GraphService, graph_context
from ethos_academy.graph.write import store_evaluation
from ethos_academy.shared.models import (
    Claim,
    EvaluationResult,
    IntentClassification,
    PhronesisContext,
)

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 100_000


async def _build_phronesis_context(
    service: GraphService, source: str
) -> PhronesisContext | None:
    """Read agent history from graph to populate PhronesisContext.

    Passes source directly to read functions — source is already a hash
    when called from the API path (reflect), and returns empty for new
    raw agent IDs (no history yet, which is correct).

    Returns None if graph is unavailable or agent has no history.
    """
    try:
        profile = await get_agent_profile(service, source)
        if not profile:
            return None

        history = await get_evaluation_history(service, source, limit=10)

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
        logger.warning(
            "Failed to build phronesis context (%s): %s", type(exc).__name__, exc
        )
        return None


async def _try_store_evaluation(
    service: GraphService,
    agent_id: str,
    result: EvaluationResult,
    text: str,
    phronesis: str,
    agent_name: str = "",
    agent_specialty: str = "",
    message_timestamp: str = "",
    direction: str | None = None,
) -> None:
    """Attempt to store evaluation in graph. Non-fatal on failure."""
    try:
        message_hash = hashlib.sha256(text.encode()).hexdigest()
        await store_evaluation(
            service=service,
            agent_id=agent_id,
            result=result,
            message_hash=message_hash,
            message_content=text,
            phronesis=phronesis,
            agent_name=agent_name,
            agent_specialty=agent_specialty,
            message_timestamp=message_timestamp,
            direction=direction,
        )
    except Exception as exc:
        logger.warning(
            "Failed to store evaluation in graph (%s): %s", type(exc).__name__, exc
        )


async def evaluate(
    text: str,
    source: str | None = None,
    source_name: str = "",
    agent_specialty: str = "",
    message_timestamp: str = "",
    direction: str | None = None,
    conversation_context: list[dict] | None = None,
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
        message_timestamp: Optional ISO 8601 timestamp of the original message.
        direction: Optional evaluation direction (inbound/outbound/a2a_conversation).
        conversation_context: Optional list of prior messages in the thread for
            agent-to-agent conversation evaluation. Each dict should have
            "author" and "content" keys.

    Returns:
        EvaluationResult with scores and alignment flags.
    """
    if not text or not text.strip():
        raise EvaluationError("Text cannot be empty")
    if len(text) > MAX_TEXT_LENGTH:
        raise EvaluationError(
            f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters"
        )

    evaluation_id = str(uuid.uuid4())
    req_id = request_id_var.get()
    logger.info(
        "Evaluate started: eval_id=%s request_id=%s source=%s chars=%d",
        evaluation_id,
        req_id or "none",
        source or "anonymous",
        len(text),
    )

    # ── Faculty 1: INSTINCT ───────────────────────────────────────
    # Instant, no I/O. Constitutional priors, red lines.
    instinct_result = scan(text)
    tier = instinct_result.routing_tier
    has_hard_constraint = tier == "deep_with_context"

    # ── Faculty 2: INTUITION ──────────────────────────────────────
    # Fast, graph queries only. Pattern recognition from experience.
    intuition_result = await intuit(source, instinct_result)

    # Intuition can escalate the routing tier (never downgrade)
    if intuition_result.anomaly_flags and tier == "standard":
        tier = "focused"
    if intuition_result.confidence_adjustment > 0.2 and tier == "focused":
        tier = "deep"

    # ── Faculty 3: DELIBERATION ───────────────────────────────────
    # Slow, full Claude evaluation. Instinct + intuition inform the prompt.

    # Step 3a: Build prompts (intuition context enriches the prompt)
    system_prompt, user_prompt = build_evaluation_prompt(
        text,
        instinct_result,
        tier,
        intuition_result,
        direction=direction,
        conversation_context=conversation_context,
    )

    # Step 3b: Call Claude with three-tool pipeline (Think-then-Extract)
    tool_results, thinking_content = await call_claude_with_tools(
        system_prompt, user_prompt, tier, EVALUATION_TOOLS
    )

    # Step 3c: Parse tool call results
    parsed = parse_tool_response(tool_results)

    # Build IntentClassification from parsed intent_analysis
    intent_data = parsed.get("intent_analysis", {})
    intent_classification = None
    if intent_data:
        raw_claims = intent_data.get("claims", [])
        claims = [
            Claim(claim=c.get("claim", ""), type=c.get("type", "opinion"))
            for c in raw_claims
            if isinstance(c, dict)
        ]
        intent_classification = IntentClassification(
            rhetorical_mode=intent_data.get("rhetorical_mode", "informational"),
            primary_intent=intent_data.get("primary_intent", "inform"),
            action_requested=intent_data.get("action_requested", "none"),
            cost_to_reader=intent_data.get("cost_to_reader", "none"),
            stakes_reality=intent_data.get("stakes_reality", "real"),
            proportionality=intent_data.get("proportionality", "proportional"),
            persona_type=intent_data.get("persona_type", "real_identity"),
            relational_quality=intent_data.get("relational_quality", "present"),
            claims=claims,
        )
    scoring_reasoning = parsed.get("scoring_reasoning", "")

    # Step 3d: Deterministic scoring
    trait_scores_raw = parsed.get("trait_scores")
    if not trait_scores_raw:
        raise ParseError("No trait scores in evaluation response")
    traits = build_trait_scores(trait_scores_raw)
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
        phronesis=parsed.get("overall_trust", "developing"),
        alignment_status=alignment_status,
        traits=traits,
        detected_indicators=parsed.get("detected_indicators", []),
        tier_scores=tier_scores,
        flags=flags,
        routing_tier=tier,
        keyword_density=instinct_result.density,
        model_used=model_used,
        direction=direction,
        confidence=parsed.get("confidence", 1.0),
        intent_classification=intent_classification,
        scoring_reasoning=scoring_reasoning,
        thinking_content=thinking_content,
    )

    # ── Graph operations (optional) ───────────────────────────────
    phronesis_ctx = None
    if source:
        try:
            async with graph_context() as service:
                phronesis_ctx = await _build_phronesis_context(service, source)
                await _try_store_evaluation(
                    service,
                    source,
                    result,
                    text,
                    phronesis,
                    agent_name=source_name,
                    agent_specialty=agent_specialty,
                    message_timestamp=message_timestamp,
                    direction=direction,
                )
        except Exception as exc:
            logger.warning("Graph operations failed (%s): %s", type(exc).__name__, exc)

    if phronesis_ctx is not None:
        result.graph_context = phronesis_ctx

    return result
