"""Temporal graph queries — PRECEDES chain analysis for drift detection.

Walks the evaluation linked list to extract time-ordered dimension scores
and detected indicators at each point.
"""

from __future__ import annotations

import logging

from ethos_academy.graph.service import GraphService

logger = logging.getLogger(__name__)

_DRIFT_TIMELINE_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
OPTIONAL MATCH (e)-[:DETECTED]->(i:Indicator)
WITH e, collect(DISTINCT i.name) AS indicator_names
ORDER BY e.created_at ASC
RETURN e.evaluation_id AS eval_id,
       e.ethos AS ethos,
       e.logos AS logos,
       e.pathos AS pathos,
       e.alignment_status AS alignment,
       e.flags AS flags,
       toString(e.created_at) AS created_at,
       indicator_names
"""


async def get_drift_timeline(service: GraphService, agent_id: str) -> list[dict]:
    """Get time-ordered evaluation scores with detected indicators.

    Returns a list of dicts ordered by created_at ASC.
    The caller computes sliding-window breakpoints in Python.
    """
    if not service.connected:
        return []
    try:
        records, _, _ = await service.execute_query(
            _DRIFT_TIMELINE_QUERY, {"agent_id": agent_id}
        )
        return [
            {
                "eval_id": rec.get("eval_id", ""),
                "ethos": rec.get("ethos", 0.0),
                "logos": rec.get("logos", 0.0),
                "pathos": rec.get("pathos", 0.0),
                "alignment": rec.get("alignment", "unknown"),
                "flags": rec.get("flags", []),
                "created_at": rec.get("created_at", ""),
                "indicators": rec.get("indicator_names", []),
            }
            for rec in records
            if rec.get("eval_id")
        ]
    except Exception as exc:
        logger.warning("Failed to get drift timeline: %s", exc)
        return []
