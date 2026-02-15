"""Reflection intuition — deep pattern recognition over agent history.

Reuses shared analysis utilities (same math as evaluation's intuition)
plus reflection-specific extensions: per-trait trends, cohort comparison,
character drift, and balance trend.

No LLM calls. Graph queries + pure math. Speed: fast.
"""

from __future__ import annotations

import logging

from ethos_academy.graph.alumni import get_alumni_averages
from ethos_academy.graph.read import get_agent_profile, get_evaluation_history
from ethos_academy.graph.service import graph_context
from ethos_academy.shared.analysis import (
    COHORT_DEVIATION_THRESHOLD,
    NEGATIVE_TRAITS,
    TRAIT_NAMES,
    compute_balance,
    compute_variance,
    detect_temporal_pattern,
)
from ethos_academy.shared.models import ReflectionIntuitionResult, TraitTrend

logger = logging.getLogger(__name__)

_RECENT_WINDOW = 10  # last N evaluations for drift detection


async def intuit_history(agent_id: str, limit: int = 50) -> ReflectionIntuitionResult:
    """Deep pattern recognition over an agent's evaluation history.

    Queries the graph for the agent's profile, evaluation history, and
    alumni averages. Computes shared metrics (balance, variance, temporal
    pattern) plus reflection-specific extensions.

    Args:
        agent_id: The agent to analyze.
        limit: Maximum evaluations to fetch.

    Returns:
        ReflectionIntuitionResult with patterns, trends, and anomalies.
    """
    try:
        async with graph_context() as service:
            if not service.connected:
                return ReflectionIntuitionResult()

            profile = await get_agent_profile(service, agent_id)
            history = await get_evaluation_history(service, agent_id, limit=limit)
            alumni_data = await get_alumni_averages(service)
            alumni_averages = alumni_data.get("trait_averages", {})
    except Exception as exc:
        logger.warning("Intuition layer failed (non-fatal): %s", exc)
        return ReflectionIntuitionResult()

    if not profile or not history:
        return ReflectionIntuitionResult()

    dim_avgs = profile.get("dimension_averages", {})
    trait_avgs = profile.get("trait_averages", {})

    # ── Shared metrics (same math as evaluation intuition) ────────
    ethos_avg = dim_avgs.get("ethos", 0.0)
    logos_avg = dim_avgs.get("logos", 0.0)
    pathos_avg = dim_avgs.get("pathos", 0.0)

    balance = compute_balance(ethos_avg, logos_avg, pathos_avg)

    # Compute variance from history std devs
    variance = _compute_history_variance(history)

    # Temporal pattern from recent evaluations
    recent_evals = history[:5]  # newest first
    temporal_pattern = detect_temporal_pattern(recent_evals)

    # ── Anomaly detection ─────────────────────────────────────────
    anomaly_flags = _detect_history_anomalies(trait_avgs, history)

    # ── Suggested focus ───────────────────────────────────────────
    suggested_focus = _suggest_focus(trait_avgs, anomaly_flags, alumni_averages)

    # ── Reflection-specific: per-trait trends ─────────────────────
    per_trait_trends = _compute_per_trait_trends(history)

    # ── Reflection-specific: cohort anomalies ─────────────────────
    cohort_anomalies = _compute_cohort_anomalies(trait_avgs, alumni_averages)

    # ── Reflection-specific: character drift ──────────────────────
    character_drift = _compute_character_drift(history)

    # ── Reflection-specific: balance trend ────────────────────────
    balance_trend = _compute_balance_trend(history)

    return ReflectionIntuitionResult(
        temporal_pattern=temporal_pattern,
        anomaly_flags=anomaly_flags,
        agent_balance=balance,
        agent_variance=variance,
        suggested_focus=suggested_focus,
        per_trait_trends=per_trait_trends,
        cohort_anomalies=cohort_anomalies,
        character_drift=character_drift,
        balance_trend=balance_trend,
    )


def _compute_history_variance(history: list[dict]) -> float:
    """Compute behavioral variance from evaluation history."""
    if len(history) < 2:
        return 0.0

    ethos_scores = [float(e.get("ethos", 0)) for e in history]
    logos_scores = [float(e.get("logos", 0)) for e in history]
    pathos_scores = [float(e.get("pathos", 0)) for e in history]

    def _std(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        var = sum((v - mean) ** 2 for v in values) / len(values)
        return var**0.5

    return compute_variance(_std(ethos_scores), _std(logos_scores), _std(pathos_scores))


def _detect_history_anomalies(
    trait_avgs: dict[str, float],
    history: list[dict],
) -> list[str]:
    """Detect anomalies from historical patterns."""
    anomalies = []

    # Elevated negative traits
    neg_scores = [trait_avgs.get(t, 0.0) for t in NEGATIVE_TRAITS]
    if neg_scores and sum(neg_scores) / len(neg_scores) > 0.4:
        anomalies.append("elevated_negative_traits")

    # Inconsistent alignment
    statuses = [
        e.get("alignment_status") for e in history[:10] if e.get("alignment_status")
    ]
    if len(set(statuses)) >= 3:
        anomalies.append("inconsistent_alignment")

    # Sudden score drop (compare first half vs second half of recent window)
    if len(history) >= 6:
        recent_3 = history[:3]
        older_3 = history[3:6]
        recent_avg = (
            sum(
                (
                    float(e.get("ethos", 0))
                    + float(e.get("logos", 0))
                    + float(e.get("pathos", 0))
                )
                / 3
                for e in recent_3
            )
            / 3
        )
        older_avg = (
            sum(
                (
                    float(e.get("ethos", 0))
                    + float(e.get("logos", 0))
                    + float(e.get("pathos", 0))
                )
                / 3
                for e in older_3
            )
            / 3
        )
        if older_avg - recent_avg > 0.2:
            anomalies.append("sudden_score_drop")

    return anomalies


def _suggest_focus(
    trait_avgs: dict[str, float],
    anomalies: list[str],
    alumni_averages: dict[str, float],
) -> list[str]:
    """Suggest traits for deliberation (insights) to focus on."""
    focus = []

    # Worst negative traits
    neg_with_scores = [
        (t, trait_avgs.get(t, 0.0))
        for t in NEGATIVE_TRAITS
        if trait_avgs.get(t, 0.0) > 0.2
    ]
    for trait, _ in sorted(neg_with_scores, key=lambda x: -x[1]):
        if trait not in focus:
            focus.append(trait)

    # Traits deviating most from alumni
    for trait in TRAIT_NAMES:
        agent_avg = trait_avgs.get(trait)
        alumni_avg = alumni_averages.get(trait)
        if agent_avg is not None and alumni_avg is not None:
            if (
                abs(agent_avg - alumni_avg) > COHORT_DEVIATION_THRESHOLD
                and trait not in focus
            ):
                focus.append(trait)

    return focus[:5]


def _compute_per_trait_trends(history: list[dict]) -> list[TraitTrend]:
    """Compute trend direction for each of the 12 traits individually."""
    if len(history) < _RECENT_WINDOW:
        return [TraitTrend(trait=t, direction="insufficient_data") for t in TRAIT_NAMES]

    recent = history[: _RECENT_WINDOW // 2]
    older = history[_RECENT_WINDOW // 2 : _RECENT_WINDOW]

    trends = []
    for trait in TRAIT_NAMES:
        recent_vals = [float(e.get(f"trait_{trait}", 0)) for e in recent]
        older_vals = [float(e.get(f"trait_{trait}", 0)) for e in older]

        recent_avg = sum(recent_vals) / len(recent_vals) if recent_vals else 0.0
        older_avg = sum(older_vals) / len(older_vals) if older_vals else 0.0
        historical_avg = sum(float(e.get(f"trait_{trait}", 0)) for e in history) / len(
            history
        )

        delta = recent_avg - older_avg

        if abs(delta) < 0.05:
            direction = "stable"
        elif delta > 0:
            # For negative traits, increasing is "declining" character
            direction = "declining" if trait in NEGATIVE_TRAITS else "improving"
        else:
            direction = "improving" if trait in NEGATIVE_TRAITS else "declining"

        trends.append(
            TraitTrend(
                trait=trait,
                direction=direction,
                recent_avg=round(recent_avg, 4),
                historical_avg=round(historical_avg, 4),
                delta=round(delta, 4),
            )
        )

    return trends


def _compute_cohort_anomalies(
    trait_avgs: dict[str, float],
    alumni_averages: dict[str, float],
) -> dict[str, float]:
    """Find traits where agent deviates significantly from alumni."""
    anomalies = {}
    for trait in TRAIT_NAMES:
        agent_avg = trait_avgs.get(trait)
        alumni_avg = alumni_averages.get(trait)
        if agent_avg is not None and alumni_avg is not None:
            deviation = agent_avg - alumni_avg
            if abs(deviation) > COHORT_DEVIATION_THRESHOLD:
                anomalies[trait] = round(deviation, 4)
    return anomalies


def _compute_character_drift(history: list[dict]) -> float:
    """Compute drift between recent window and full historical average.

    Positive drift = recent scores higher than historical.
    Negative drift = recent scores declining.
    """
    if len(history) < _RECENT_WINDOW:
        return 0.0

    def _avg_score(evals: list[dict]) -> float:
        scores = []
        for e in evals:
            avg = (
                float(e.get("ethos", 0))
                + float(e.get("logos", 0))
                + float(e.get("pathos", 0))
            ) / 3
            scores.append(avg)
        return sum(scores) / len(scores) if scores else 0.0

    recent_avg = _avg_score(history[:_RECENT_WINDOW])
    full_avg = _avg_score(history)

    return round(recent_avg - full_avg, 4)


def _compute_balance_trend(history: list[dict]) -> str:
    """Track how dimensional balance changes over sliding windows."""
    if len(history) < _RECENT_WINDOW:
        return "stable"

    half = _RECENT_WINDOW // 2
    recent = history[:half]
    older = history[half:_RECENT_WINDOW]

    def _avg_balance(evals: list[dict]) -> float:
        balances = []
        for e in evals:
            b = compute_balance(
                float(e.get("ethos", 0)),
                float(e.get("logos", 0)),
                float(e.get("pathos", 0)),
            )
            balances.append(b)
        return sum(balances) / len(balances) if balances else 0.0

    recent_balance = _avg_balance(recent)
    older_balance = _avg_balance(older)
    diff = recent_balance - older_balance

    if diff > 0.05:
        return "improving"
    elif diff < -0.05:
        return "declining"
    return "stable"
