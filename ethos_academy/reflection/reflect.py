"""Reflect on an agent's evaluation history to assess behavioral trends.

Two modes:
  1. reflect(agent_id, text="message") — evaluate text via evaluate() then return updated profile
  2. reflect(agent_id) — return profile only (no new evaluation)
"""

from __future__ import annotations

import logging

from ethos_academy.evaluate import evaluate
from ethos_academy.graph.read import get_agent_profile, get_evaluation_history
from ethos_academy.graph.service import graph_context
from ethos_academy.shared.analysis import compute_trend
from ethos_academy.shared.models import ReflectionResult

logger = logging.getLogger(__name__)


async def reflect(agent_id: str, text: str | None = None) -> ReflectionResult:
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
            await evaluate(text, source=agent_id)
        except Exception as exc:
            logger.warning("Evaluation failed during reflect: %s", exc)

    # Query graph for agent profile and history
    try:
        async with graph_context() as service:
            if not service.connected:
                return ReflectionResult(
                    agent_id=agent_id,
                    trend="insufficient_data",
                )

            profile = await get_agent_profile(service, agent_id)
            history = await get_evaluation_history(service, agent_id, limit=20)
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
    trend = compute_trend(history)

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
