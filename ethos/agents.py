"""Agent domain functions — list, profile, history, alumni.

DDD layering: API calls these functions, these functions call graph/*.
API never touches graph directly.
"""

from __future__ import annotations

import logging

from ethos.graph.alumni import get_alumni_averages
from ethos.graph.read import get_agent_profile, get_all_agents, get_evaluation_history
from ethos.graph.service import graph_context
from ethos.shared.analysis import TRAIT_NAMES, compute_trend
from ethos.shared.models import (
    AgentProfile,
    AgentSummary,
    AlumniResult,
    EvaluationHistoryItem,
)

logger = logging.getLogger(__name__)


def list_agents(search: str = "") -> list[AgentSummary]:
    """List all agents with evaluation counts. Returns empty list if graph unavailable.

    Args:
        search: Optional name filter — matches agent_name case-insensitively.
    """
    try:
        with graph_context() as service:
            raw = get_all_agents(service, search=search)
            return [
                AgentSummary(
                    agent_id=a.get("agent_id", ""),
                    agent_name=a.get("agent_name", ""),
                    agent_specialty=a.get("agent_specialty", ""),
                    evaluation_count=a.get("evaluation_count", 0),
                    latest_alignment_status=a.get("latest_alignment_status", "unknown"),
                )
                for a in raw
            ]
    except Exception as exc:
        logger.warning("Failed to list agents: %s", exc)
        return []


def get_agent(agent_id: str) -> AgentProfile:
    """Get agent profile with averages. Returns default AgentProfile if unavailable."""
    try:
        with graph_context() as service:
            raw = get_agent_profile(service, agent_id)

            if not raw:
                return AgentProfile(agent_id=agent_id)

            # Compute trend dynamically from evaluation history
            history = get_evaluation_history(service, agent_id, limit=20)
            trend = compute_trend(history)

            return AgentProfile(
                agent_id=raw.get("agent_id", agent_id),
                agent_name=raw.get("agent_name", ""),
                agent_specialty=raw.get("agent_specialty", ""),
                agent_model=raw.get("agent_model", ""),
                created_at=str(raw.get("created_at", "")),
                evaluation_count=raw.get("evaluation_count", 0),
                dimension_averages=raw.get("dimension_averages", {}),
                trait_averages=raw.get("trait_averages", {}),
                phronesis_trend=trend,
                alignment_history=raw.get("alignment_history", []),
            )
    except Exception as exc:
        logger.warning("Failed to get agent: %s", exc)
        return AgentProfile(agent_id=agent_id)


def get_agent_history(
    agent_id: str, limit: int = 50
) -> list[EvaluationHistoryItem]:
    """Get evaluation history for an agent. Returns empty list if unavailable."""
    try:
        with graph_context() as service:
            raw = get_evaluation_history(service, agent_id, limit=limit)

            items = []
            for e in raw:
                trait_scores = {}
                for trait in TRAIT_NAMES:
                    val = e.get(f"trait_{trait}")
                    if val is not None:
                        trait_scores[trait] = round(float(val), 4)

                flags = e.get("flags", [])
                if isinstance(flags, str):
                    flags = [flags] if flags else []

                items.append(
                    EvaluationHistoryItem(
                        evaluation_id=e.get("evaluation_id", ""),
                        ethos=round(float(e.get("ethos", 0)), 4),
                        logos=round(float(e.get("logos", 0)), 4),
                        pathos=round(float(e.get("pathos", 0)), 4),
                        phronesis=e.get("phronesis", "unknown"),
                        alignment_status=e.get("alignment_status", "unknown"),
                        flags=flags,
                        created_at=str(e.get("created_at", "")),
                        trait_scores=trait_scores,
                    )
                )
            return items
    except Exception as exc:
        logger.warning("Failed to get agent history: %s", exc)
        return []


def get_alumni() -> AlumniResult:
    """Get alumni-wide trait averages. Returns default AlumniResult if unavailable."""
    try:
        with graph_context() as service:
            raw = get_alumni_averages(service)

            if not raw:
                return AlumniResult()

            return AlumniResult(
                trait_averages=raw.get("trait_averages", {}),
                total_evaluations=raw.get("total_evaluations", 0),
            )
    except Exception as exc:
        logger.warning("Failed to get alumni: %s", exc)
        return AlumniResult()
