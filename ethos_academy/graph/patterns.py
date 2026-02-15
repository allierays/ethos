"""Graph pattern detection — Cypher queries for sabotage pathway detection.

Layer 3 pattern detector. NO LLM calls — pure graph queries on score sequences.
Detects 8 sabotage pathways (SP-01 through SP-08) by checking which indicators
from each pathway appear in an agent's recent evaluations.

All Cypher lives here. Domain function in ethos/patterns.py orchestrates.
"""

from __future__ import annotations

import logging

from ethos_academy.graph.service import GraphService

logger = logging.getLogger(__name__)


# ─── Cypher queries ───────────────────────────────────────────────────────────

_GET_AGENT_EVALUATION_COUNT = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
RETURN count(e) AS eval_count
"""

_GET_PATTERN_INDICATORS = """
MATCH (p:Pattern)-[:COMPOSED_OF]->(i:Indicator)
RETURN p.pattern_id AS pattern_id,
       p.name AS name,
       p.description AS description,
       collect(i.id) AS indicator_ids
"""

_GET_AGENT_DETECTED_INDICATORS = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)-[:DETECTED]->(i:Indicator)
WITH i.id AS indicator_id,
     count(e) AS occurrence_count,
     min(e.created_at) AS first_seen,
     max(e.created_at) AS last_seen
RETURN indicator_id, occurrence_count, first_seen, last_seen
"""

_MERGE_EXHIBITS_PATTERN = """
MATCH (a:Agent {agent_id: $agent_id})
MATCH (p:Pattern {pattern_id: $pattern_id})
MERGE (a)-[r:EXHIBITS_PATTERN]->(p)
ON CREATE SET r.first_seen = $first_seen,
              r.last_seen = $last_seen,
              r.occurrence_count = $occurrence_count,
              r.current_stage = $current_stage,
              r.confidence = $confidence
ON MATCH SET r.last_seen = $last_seen,
             r.occurrence_count = $occurrence_count,
             r.current_stage = $current_stage,
             r.confidence = $confidence
"""

_GET_EXISTING_PATTERNS = """
MATCH (a:Agent {agent_id: $agent_id})-[r:EXHIBITS_PATTERN]->(p:Pattern)
RETURN p.pattern_id AS pattern_id,
       p.name AS name,
       p.description AS description,
       r.first_seen AS first_seen,
       r.last_seen AS last_seen,
       r.occurrence_count AS occurrence_count,
       r.current_stage AS current_stage,
       r.confidence AS confidence
"""


# ─── Query functions ──────────────────────────────────────────────────────────


async def get_agent_evaluation_count(service: GraphService, agent_id: str) -> int:
    """Return number of evaluations for an agent. 0 if unavailable."""
    if not service.connected:
        return 0

    try:
        records, _, _ = await service.execute_query(
            _GET_AGENT_EVALUATION_COUNT, {"agent_id": agent_id}
        )
        if records:
            return records[0].get("eval_count", 0)
        return 0
    except Exception as exc:
        logger.warning("Failed to get evaluation count: %s", exc)
        return 0


async def get_pattern_indicator_map(service: GraphService) -> list[dict]:
    """Get all Pattern nodes with their COMPOSED_OF indicator IDs.

    Returns list of dicts:
        [{"pattern_id": "SP-01", "name": "...", "description": "...",
          "indicator_ids": ["DEC-SANDBAG", "FAB-TOOLRESULT"]}]
    """
    if not service.connected:
        return []

    try:
        records, _, _ = await service.execute_query(_GET_PATTERN_INDICATORS)
        return [
            {
                "pattern_id": r.get("pattern_id", ""),
                "name": r.get("name", ""),
                "description": r.get("description", ""),
                "indicator_ids": list(r.get("indicator_ids", [])),
            }
            for r in records
        ]
    except Exception as exc:
        logger.warning("Failed to get pattern indicators: %s", exc)
        return []


async def get_agent_detected_indicators(
    service: GraphService, agent_id: str
) -> dict[str, dict]:
    """Get all indicators detected for an agent across evaluations.

    Returns dict keyed by indicator_id:
        {"DEC-SANDBAG": {"occurrence_count": 3, "first_seen": "...", "last_seen": "..."}}
    """
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _GET_AGENT_DETECTED_INDICATORS, {"agent_id": agent_id}
        )
        result = {}
        for r in records:
            indicator_id = r.get("indicator_id", "")
            if indicator_id:
                result[indicator_id] = {
                    "occurrence_count": r.get("occurrence_count", 0),
                    "first_seen": str(r.get("first_seen", "")),
                    "last_seen": str(r.get("last_seen", "")),
                }
        return result
    except Exception as exc:
        logger.warning("Failed to get agent detected indicators: %s", exc)
        return {}


async def store_exhibits_pattern(
    service: GraphService,
    agent_id: str,
    pattern_id: str,
    first_seen: str,
    last_seen: str,
    occurrence_count: int,
    current_stage: int,
    confidence: float,
) -> None:
    """MERGE an EXHIBITS_PATTERN relationship between Agent and Pattern."""
    if not service.connected:
        return

    try:
        await service.execute_query(
            _MERGE_EXHIBITS_PATTERN,
            {
                "agent_id": agent_id,
                "pattern_id": pattern_id,
                "first_seen": first_seen,
                "last_seen": last_seen,
                "occurrence_count": occurrence_count,
                "current_stage": current_stage,
                "confidence": confidence,
            },
        )
    except Exception as exc:
        logger.warning("Failed to store EXHIBITS_PATTERN: %s", exc)


async def get_existing_patterns(service: GraphService, agent_id: str) -> list[dict]:
    """Get existing EXHIBITS_PATTERN relationships for an agent."""
    if not service.connected:
        return []

    try:
        records, _, _ = await service.execute_query(
            _GET_EXISTING_PATTERNS, {"agent_id": agent_id}
        )
        return [
            {
                "pattern_id": r.get("pattern_id", ""),
                "name": r.get("name", ""),
                "description": r.get("description", ""),
                "first_seen": str(r.get("first_seen", "")),
                "last_seen": str(r.get("last_seen", "")),
                "occurrence_count": r.get("occurrence_count", 0),
                "current_stage": r.get("current_stage", 0),
                "confidence": r.get("confidence", 0.0),
            }
            for r in records
        ]
    except Exception as exc:
        logger.warning("Failed to get existing patterns: %s", exc)
        return []
