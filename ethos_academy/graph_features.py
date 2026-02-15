"""Graph Advantage features — domain functions that showcase Neo4j capabilities.

Three features that demonstrate why a graph database matters:
1. Constitutional Value Trail — 5-hop typed relationship traversal
2. Behavioral Similarity Network — Jaccard similarity over bipartite graph
3. Character Drift Breakpoints — PRECEDES linked-list sliding window analysis
"""

from __future__ import annotations

import logging

from ethos_academy.graph.service import graph_context
from ethos_academy.graph.temporal import get_drift_timeline
from ethos_academy.graph.visualization import (
    get_constitutional_trail,
    get_similarity_data,
)
from ethos_academy.shared.models import (
    ConstitutionalTrailItem,
    ConstitutionalTrailResult,
    DriftBreakpoint,
    DriftResult,
    SimilarityEdge,
    SimilarityResult,
)

logger = logging.getLogger(__name__)

_WINDOW_SIZE = 5
_DRIFT_THRESHOLD = 0.12


async def get_trail(agent_id: str) -> ConstitutionalTrailResult:
    """Trace agent behavior through indicators, traits, to constitutional values."""
    try:
        async with graph_context() as service:
            rows = await get_constitutional_trail(service, agent_id)
            items = [ConstitutionalTrailItem(**row) for row in rows]
            return ConstitutionalTrailResult(agent_id=agent_id, items=items)
    except Exception as exc:
        logger.warning("Failed to get trail for %s: %s", agent_id, exc)
        return ConstitutionalTrailResult(agent_id=agent_id)


async def get_similarity() -> SimilarityResult:
    """Compute behavioral similarity between all agents."""
    try:
        async with graph_context() as service:
            rows = await get_similarity_data(service)
            edges = [SimilarityEdge(**row) for row in rows]
            return SimilarityResult(edges=edges)
    except Exception as exc:
        logger.warning("Failed to get similarity: %s", exc)
        return SimilarityResult()


async def get_drift(agent_id: str) -> DriftResult:
    """Detect character drift breakpoints using sliding-window analysis.

    Walks the PRECEDES-ordered evaluation chain, computes a sliding
    average over windows of 5 evaluations, and flags positions where
    any dimension's delta exceeds the threshold.
    """
    try:
        async with graph_context() as service:
            timeline = await get_drift_timeline(service, agent_id)

        if len(timeline) < _WINDOW_SIZE * 2:
            return DriftResult(agent_id=agent_id)

        breakpoints = _compute_breakpoints(timeline)
        return DriftResult(agent_id=agent_id, breakpoints=breakpoints)

    except Exception as exc:
        logger.warning("Failed to get drift for %s: %s", agent_id, exc)
        return DriftResult(agent_id=agent_id)


def _compute_breakpoints(timeline: list[dict]) -> list[DriftBreakpoint]:
    """Sliding window drift detection over evaluation timeline.

    For each position i (from WINDOW_SIZE to len-WINDOW_SIZE), compares
    the average of the preceding window to the following window.
    Flags positions where any dimension delta exceeds the threshold.
    """
    n = len(timeline)
    breakpoints: list[DriftBreakpoint] = []

    for i in range(_WINDOW_SIZE, n - _WINDOW_SIZE + 1):
        before_window = timeline[i - _WINDOW_SIZE : i]
        after_window = timeline[i : i + _WINDOW_SIZE]

        for dim in ("ethos", "logos", "pathos"):
            before_avg = sum(e[dim] for e in before_window) / _WINDOW_SIZE
            after_avg = sum(e[dim] for e in after_window) / _WINDOW_SIZE
            delta = after_avg - before_avg

            if abs(delta) >= _DRIFT_THRESHOLD:
                point = timeline[i]
                breakpoints.append(
                    DriftBreakpoint(
                        eval_index=i + 1,  # 1-indexed for display
                        evaluation_id=point["eval_id"],
                        dimension=dim,
                        delta=round(delta, 3),
                        before_avg=round(before_avg, 3),
                        after_avg=round(after_avg, 3),
                        created_at=point.get("created_at", ""),
                        indicators=point.get("indicators", []),
                    )
                )

    # Deduplicate by eval_index — keep the largest delta per position
    seen: dict[int, DriftBreakpoint] = {}
    for bp in breakpoints:
        existing = seen.get(bp.eval_index)
        if existing is None or abs(bp.delta) > abs(existing.delta):
            seen[bp.eval_index] = bp

    return sorted(seen.values(), key=lambda b: b.eval_index)
