"""Reflection history — query agent profile without triggering evaluation.

Pure graph read. Returns ReflectionResult with dimension averages,
trait averages, and trend. Same shape as reflect() but no evaluate() call.
"""

from __future__ import annotations

import logging

from ethos_academy.graph.read import get_agent_profile, get_evaluation_history
from ethos_academy.graph.service import graph_context
from ethos_academy.shared.analysis import compute_trend
from ethos_academy.shared.models import ReflectionResult

logger = logging.getLogger(__name__)


async def reflect_history(agent_id: str, limit: int = 50) -> ReflectionResult:
    """Get an agent's historical profile without evaluating new text.

    Args:
        agent_id: The identifier of the agent.
        limit: Maximum evaluations to consider for trend computation.

    Returns:
        ReflectionResult with dimension scores, trait averages, and trend.
    """
    try:
        async with graph_context() as service:
            if not service.connected:
                return ReflectionResult(
                    agent_id=agent_id,
                    trend="insufficient_data",
                )

            profile = await get_agent_profile(service, agent_id)
            history = await get_evaluation_history(service, agent_id, limit=limit)
    except Exception as exc:
        logger.warning("Graph unavailable for reflect_history: %s", exc)
        return ReflectionResult(
            agent_id=agent_id,
            trend="insufficient_data",
        )

    if not profile:
        return ReflectionResult(
            agent_id=agent_id,
            trend="insufficient_data",
        )

    dim_avgs = profile.get("dimension_averages", {})
    trait_averages = profile.get("trait_averages", {})

    return ReflectionResult(
        agent_id=agent_id,
        ethos=round(dim_avgs.get("ethos", 0.0), 4),
        logos=round(dim_avgs.get("logos", 0.0), 4),
        pathos=round(dim_avgs.get("pathos", 0.0), 4),
        trait_averages=trait_averages,
        evaluation_count=profile.get("evaluation_count", 0),
        trend=compute_trend(history),
        compassion=round(trait_averages.get("compassion", 0.0), 4),
        honesty=round(trait_averages.get("accuracy", 0.0), 4),
        accuracy=round(trait_averages.get("accuracy", 0.0), 4),
    )
