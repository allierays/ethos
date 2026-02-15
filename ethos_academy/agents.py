"""Agent domain functions — list, profile, history, alumni.

DDD layering: API calls these functions, these functions call graph/*.
API never touches graph directly.
"""

from __future__ import annotations

import logging
import math

from ethos_academy.graph.alumni import get_alumni_averages
from ethos_academy.graph.read import (
    get_agent_highlights,
    get_agent_profile,
    get_all_agents,
    get_evaluation_history,
    search_evaluations,
)
from ethos_academy.graph.service import graph_context
from ethos_academy.shared.analysis import TRAIT_NAMES, compute_trend
from ethos_academy.shared.models import (
    AgentProfile,
    AgentSummary,
    AlumniResult,
    DetectedIndicatorSummary,
    EvaluationHistoryItem,
    HighlightIndicator,
    HighlightItem,
    HighlightsResult,
    IntentClassification,
    RecordItem,
    RecordsResult,
)

logger = logging.getLogger(__name__)


def _build_intent(e: dict) -> IntentClassification | None:
    """Build IntentClassification from flat intent_* properties on an Evaluation node.

    Returns None if no intent data was stored (pre-intent evaluations).
    """
    mode = e.get("intent_rhetorical_mode") or ""
    if not mode:
        return None
    return IntentClassification(
        rhetorical_mode=mode,
        primary_intent=e.get("intent_primary_intent") or "inform",
        action_requested="none",
        cost_to_reader=e.get("intent_cost_to_reader") or "none",
        stakes_reality=e.get("intent_stakes_reality") or "real",
        proportionality=e.get("intent_proportionality") or "proportional",
        persona_type=e.get("intent_persona_type") or "real_identity",
        relational_quality=e.get("intent_relational_quality") or "present",
    )


async def list_agents(search: str = "") -> list[AgentSummary]:
    """List all agents with evaluation counts. Returns empty list if graph unavailable.

    Args:
        search: Optional name filter — matches agent_name case-insensitively.
    """
    try:
        async with graph_context() as service:
            raw = await get_all_agents(service, search=search)
            summaries = [
                AgentSummary(
                    agent_id=a.get("agent_id", ""),
                    agent_name=a.get("agent_name") or a.get("agent_id", ""),
                    agent_specialty=a.get("agent_specialty", ""),
                    agent_model=a.get("agent_model", ""),
                    evaluation_count=a.get("evaluation_count", 0),
                    latest_alignment_status=a.get("latest_alignment_status", "unknown"),
                    enrolled=a.get("enrolled", False),
                    entrance_exam_completed=a.get("entrance_exam_completed", False),
                    dimension_averages={
                        k: round(float(v), 4)
                        for k, v in {
                            "ethos": a.get("avg_ethos"),
                            "logos": a.get("avg_logos"),
                            "pathos": a.get("avg_pathos"),
                        }.items()
                        if v is not None
                    },
                    trait_averages=a.get("trait_averages", {}),
                )
                for a in raw
            ]
            # Dedup by agent_id: keep the entry with highest evaluation_count
            seen: dict[str, AgentSummary] = {}
            for s in summaries:
                existing = seen.get(s.agent_id)
                if not existing or s.evaluation_count > existing.evaluation_count:
                    seen[s.agent_id] = s
            return list(seen.values())
    except Exception as exc:
        logger.warning("Failed to list agents: %s", exc)
        return []


async def get_agent(agent_id: str) -> AgentProfile:
    """Get agent profile with averages. Returns default AgentProfile if unavailable."""
    try:
        async with graph_context() as service:
            raw = await get_agent_profile(service, agent_id)

            if not raw:
                return AgentProfile(agent_id=agent_id)

            # Compute trend dynamically from evaluation history
            history = await get_evaluation_history(service, agent_id, limit=20)
            trend = compute_trend(history)

            return AgentProfile(
                agent_id=raw.get("agent_id") or agent_id,
                agent_name=raw.get("agent_name") or raw.get("agent_id") or agent_id,
                agent_specialty=raw.get("agent_specialty") or "",
                agent_model=raw.get("agent_model") or "",
                created_at=str(raw.get("created_at") or ""),
                evaluation_count=raw.get("evaluation_count") or 0,
                dimension_averages=raw.get("dimension_averages") or {},
                trait_averages=raw.get("trait_averages") or {},
                phronesis_trend=trend,
                alignment_history=raw.get("alignment_history") or [],
                enrolled=raw.get("enrolled", False),
                enrolled_at=str(raw.get("enrolled_at") or ""),
                guardian_name=raw.get("guardian_name", ""),
                entrance_exam_completed=raw.get("entrance_exam_completed", False),
            )
    except Exception as exc:
        logger.warning("Failed to get agent: %s", exc)
        return AgentProfile(agent_id=agent_id)


async def get_agent_history(
    agent_id: str, limit: int = 50
) -> list[EvaluationHistoryItem]:
    """Get evaluation history for an agent. Returns empty list if unavailable."""
    limit = min(limit, 1000)
    try:
        async with graph_context() as service:
            raw = await get_evaluation_history(service, agent_id, limit=limit)

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
                        message_content=e.get("message_content") or "",
                        intent_classification=_build_intent(e),
                        scoring_reasoning=e.get("scoring_reasoning") or "",
                    )
                )
            return items
    except Exception as exc:
        logger.warning("Failed to get agent history: %s", exc)
        return []


async def get_highlights(agent_id: str) -> HighlightsResult:
    """Get best and worst evaluations with message content for an agent."""
    try:
        async with graph_context() as service:
            raw = await get_agent_highlights(service, agent_id)

            def _to_item(e: dict) -> HighlightItem:
                flags = e.get("flags", [])
                if isinstance(flags, str):
                    flags = [flags] if flags else []
                raw_indicators = e.get("indicators", [])
                indicators = [
                    HighlightIndicator(
                        name=ind.get("name", ""),
                        trait=ind.get("trait", ""),
                        confidence=round(float(ind.get("confidence", 0)), 2),
                        evidence=ind.get("evidence", ""),
                    )
                    for ind in raw_indicators
                    if isinstance(ind, dict) and ind.get("name")
                ]
                # Sort by confidence descending, keep top 5
                indicators.sort(key=lambda x: x.confidence, reverse=True)
                indicators = indicators[:5]

                trait_scores = {}
                for trait in TRAIT_NAMES:
                    val = e.get(f"trait_{trait}")
                    if val is not None:
                        trait_scores[trait] = round(float(val), 4)

                return HighlightItem(
                    evaluation_id=e.get("evaluation_id", ""),
                    ethos=round(float(e.get("ethos", 0)), 4),
                    logos=round(float(e.get("logos", 0)), 4),
                    pathos=round(float(e.get("pathos", 0)), 4),
                    overall=round(float(e.get("overall", 0)), 4),
                    alignment_status=e.get("alignment_status", "unknown"),
                    flags=flags,
                    indicators=indicators,
                    message_content=e.get("message_content", ""),
                    created_at=str(e.get("created_at", "")),
                    intent_classification=_build_intent(e),
                    scoring_reasoning=e.get("scoring_reasoning") or "",
                    trait_scores=trait_scores,
                )

            return HighlightsResult(
                agent_id=agent_id,
                exemplary=[_to_item(e) for e in raw.get("exemplary", [])],
                concerning=[_to_item(e) for e in raw.get("concerning", [])],
            )
    except Exception as exc:
        logger.warning("Failed to get highlights: %s", exc)
        return HighlightsResult(agent_id=agent_id)


async def get_alumni() -> AlumniResult:
    """Get alumni-wide trait averages. Returns default AlumniResult if unavailable."""
    try:
        async with graph_context() as service:
            raw = await get_alumni_averages(service)

            if not raw:
                return AlumniResult()

            return AlumniResult(
                trait_averages=raw.get("trait_averages", {}),
                total_evaluations=raw.get("total_evaluations", 0),
            )
    except Exception as exc:
        logger.warning("Failed to get alumni: %s", exc)
        return AlumniResult()


async def search_records(
    search: str | None = None,
    agent_id: str | None = None,
    alignment_status: str | None = None,
    has_flags: bool | None = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    page: int = 0,
    page_size: int = 20,
) -> RecordsResult:
    """Search evaluation records with filters and pagination.

    Wraps search_evaluations() and builds RecordItem models from raw dicts.
    Returns empty RecordsResult on graph failure.
    """
    try:
        async with graph_context() as service:
            skip = page * page_size
            raw_items, total = await search_evaluations(
                service,
                search=search,
                agent_id=agent_id,
                alignment_status=alignment_status,
                has_flags=has_flags,
                sort_by=sort_by,
                sort_order=sort_order,
                skip=skip,
                limit=page_size,
            )

            items = []
            for e in raw_items:
                ethos_val = float(e.get("ethos", 0))
                logos_val = float(e.get("logos", 0))
                pathos_val = float(e.get("pathos", 0))
                overall = (ethos_val + logos_val + pathos_val) / 3.0

                flags = e.get("flags", [])
                if isinstance(flags, str):
                    flags = [flags] if flags else []

                trait_scores = {}
                for trait in TRAIT_NAMES:
                    val = e.get(f"trait_{trait}")
                    if val is not None:
                        trait_scores[trait] = round(float(val), 4)

                # Parse detected indicators from graph
                raw_indicators = e.get("indicators", [])
                detected_indicators = sorted(
                    [
                        DetectedIndicatorSummary(
                            id=ind.get("id", ""),
                            name=ind.get("name", ""),
                            trait=ind.get("trait", ""),
                            description=ind.get("description", ""),
                            confidence=round(float(ind.get("confidence", 0)), 4),
                            severity=round(float(ind.get("severity", 0)), 4),
                            evidence=ind.get("evidence", ""),
                        )
                        for ind in raw_indicators
                        if isinstance(ind, dict) and ind.get("name")
                    ],
                    key=lambda x: x.confidence,
                    reverse=True,
                )

                items.append(
                    RecordItem(
                        evaluation_id=e.get("evaluation_id", ""),
                        agent_id=e.get("agent_id", ""),
                        agent_name=e.get("agent_name", ""),
                        ethos=round(ethos_val, 4),
                        logos=round(logos_val, 4),
                        pathos=round(pathos_val, 4),
                        overall=round(overall, 4),
                        alignment_status=e.get("alignment_status", "unknown"),
                        flags=flags,
                        direction=e.get("direction"),
                        message_content=e.get("message_content", ""),
                        created_at=str(e.get("created_at", "")),
                        phronesis=e.get("phronesis", "unknown"),
                        scoring_reasoning=e.get("scoring_reasoning", ""),
                        intent_classification=_build_intent(e),
                        trait_scores=trait_scores,
                        model_used=e.get("model_used") or "",
                        agent_model=e.get("agent_model") or "",
                        routing_tier=e.get("routing_tier") or "standard",
                        keyword_density=float(e.get("keyword_density") or 0),
                        detected_indicators=detected_indicators,
                    )
                )

            total_pages = math.ceil(total / page_size) if page_size > 0 else 0

            return RecordsResult(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )
    except Exception as exc:
        logger.warning("Failed to search records: %s", exc)
        return RecordsResult(page=page, page_size=page_size)
