"""Reflect on an agent's evaluation history to assess behavioral trends.

Two modes:
  1. reflect(agent_id, text="message") — evaluate text via evaluate() then return updated profile
  2. reflect(agent_id) — return profile only (no new evaluation)
"""

from __future__ import annotations

import logging

from ethos.evaluate import evaluate
from ethos.graph.read import get_agent_profile, get_evaluation_history
from ethos.graph.service import GraphService
from ethos.shared.models import ReflectionResult

logger = logging.getLogger(__name__)

_TRAIT_NAMES = [
    "virtue", "goodwill", "manipulation", "deception",
    "accuracy", "reasoning", "fabrication", "broken_logic",
    "recognition", "compassion", "dismissal", "exploitation",
]


def _compute_trend(evaluations: list[dict]) -> str:
    """Compute phronesis trend from evaluation history.

    Compares the average phronesis of the last 5 evaluations against
    the previous 5. Returns improving/declining/stable/insufficient_data.
    """
    if len(evaluations) < 10:
        return "insufficient_data"

    def _avg_phronesis(evals: list[dict]) -> float:
        scores = []
        for e in evals:
            ethos = float(e.get("ethos", 0))
            logos = float(e.get("logos", 0))
            pathos = float(e.get("pathos", 0))
            scores.append((ethos + logos + pathos) / 3.0)
        return sum(scores) / len(scores) if scores else 0.0

    # evaluations are ordered newest-first from get_evaluation_history
    recent = evaluations[:5]
    older = evaluations[5:10]

    recent_avg = _avg_phronesis(recent)
    older_avg = _avg_phronesis(older)
    diff = recent_avg - older_avg

    if diff > 0.1:
        return "improving"
    elif diff < -0.1:
        return "declining"
    else:
        return "stable"


def reflect(agent_id: str, text: str | None = None) -> ReflectionResult:
    """Analyze an agent's evaluation history for behavioral trends.

    When text is provided, evaluates it via evaluate(text, source=agent_id)
    to score and store, then returns the updated historical profile.
    When text is None, returns profile only.

    Args:
        agent_id: The identifier of the agent to reflect on.
        text: Optional message to evaluate before reflecting.

    Returns:
        ReflectionResult with dimension scores, trait averages, and trend.
    """
    # If text provided, evaluate it first (score + store)
    if text is not None:
        try:
            evaluate(text, source=agent_id)
        except Exception as exc:
            logger.warning("Evaluation failed during reflect: %s", exc)

    # Query graph for agent profile and history
    try:
        service = GraphService()
        service.connect()

        if not service.connected:
            return ReflectionResult(
                agent_id=agent_id,
                trend="insufficient_data",
            )

        profile = get_agent_profile(service, agent_id)
        history = get_evaluation_history(service, agent_id, limit=20)

        service.close()
    except Exception as exc:
        logger.warning("Graph unavailable for reflect: %s", exc)
        return ReflectionResult(
            agent_id=agent_id,
            trend="insufficient_data",
        )

    if not profile:
        return ReflectionResult(
            agent_id=agent_id,
            trend="insufficient_data",
        )

    # Extract dimension averages
    dim_avgs = profile.get("dimension_averages", {})
    ethos_avg = dim_avgs.get("ethos", 0.0)
    logos_avg = dim_avgs.get("logos", 0.0)
    pathos_avg = dim_avgs.get("pathos", 0.0)

    # Extract trait averages
    trait_averages = profile.get("trait_averages", {})

    # Evaluation count
    evaluation_count = profile.get("evaluation_count", 0)

    # Compute trend from history
    trend = _compute_trend(history)

    return ReflectionResult(
        agent_id=agent_id,
        ethos=round(ethos_avg, 4),
        logos=round(logos_avg, 4),
        pathos=round(pathos_avg, 4),
        trait_averages=trait_averages,
        evaluation_count=evaluation_count,
        trend=trend,
        # Backward-compat fields mapped from new fields
        compassion=round(trait_averages.get("compassion", 0.0), 4),
        honesty=round(trait_averages.get("accuracy", 0.0), 4),
        accuracy=round(trait_averages.get("accuracy", 0.0), 4),
    )
