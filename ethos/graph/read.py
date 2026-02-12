"""Graph read operations — query evaluations and agent profiles.

All Cypher for reads lives here. Returns graceful defaults when Neo4j is down.
"""

from __future__ import annotations

import logging

from ethos.graph.service import GraphService
from ethos.identity.hashing import hash_agent_id

logger = logging.getLogger(__name__)

_TRAIT_NAMES = [
    "virtue", "goodwill", "manipulation", "deception",
    "accuracy", "reasoning", "fabrication", "broken_logic",
    "recognition", "compassion", "dismissal", "exploitation",
]

_GET_ALL_AGENTS_QUERY = """
MATCH (a:Agent)
OPTIONAL MATCH (a)-[:EVALUATED]->(e:Evaluation)
WITH a, e
ORDER BY e.created_at ASC
WITH a, count(e) AS evals, last(collect(e.alignment_status)) AS latest
RETURN a.agent_id AS agent_id, evals, latest
ORDER BY evals DESC
"""

_GET_HISTORY_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
RETURN e
ORDER BY e.created_at DESC
LIMIT $limit
"""

_GET_PROFILE_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})
OPTIONAL MATCH (a)-[:EVALUATED]->(e:Evaluation)
WITH a,
     count(e) AS eval_count,
     avg(e.ethos) AS avg_ethos,
     avg(e.logos) AS avg_logos,
     avg(e.pathos) AS avg_pathos,
     avg(e.trait_virtue) AS avg_virtue,
     avg(e.trait_goodwill) AS avg_goodwill,
     avg(e.trait_manipulation) AS avg_manipulation,
     avg(e.trait_deception) AS avg_deception,
     avg(e.trait_accuracy) AS avg_accuracy,
     avg(e.trait_reasoning) AS avg_reasoning,
     avg(e.trait_fabrication) AS avg_fabrication,
     avg(e.trait_broken_logic) AS avg_broken_logic,
     avg(e.trait_recognition) AS avg_recognition,
     avg(e.trait_compassion) AS avg_compassion,
     avg(e.trait_dismissal) AS avg_dismissal,
     avg(e.trait_exploitation) AS avg_exploitation,
     collect(e.alignment_status) AS alignment_history
RETURN a.agent_id AS agent_id,
       a.agent_model AS agent_model,
       a.created_at AS created_at,
       eval_count,
       avg_ethos, avg_logos, avg_pathos,
       avg_virtue, avg_goodwill, avg_manipulation, avg_deception,
       avg_accuracy, avg_reasoning, avg_fabrication, avg_broken_logic,
       avg_recognition, avg_compassion, avg_dismissal, avg_exploitation,
       alignment_history
"""


def get_evaluation_history(
    service: GraphService,
    raw_agent_id: str,
    limit: int = 10,
) -> list[dict]:
    """Get recent evaluations for an agent. Returns empty list if unavailable."""
    if not service.connected:
        return []

    hashed_id = hash_agent_id(raw_agent_id)

    try:
        records, _, _ = service.execute_query(
            _GET_HISTORY_QUERY, {"agent_id": hashed_id, "limit": limit}
        )
        results = []
        for record in records:
            node = record["e"]
            results.append(dict(node))
        return results
    except Exception as exc:
        logger.warning("Failed to get evaluation history: %s", exc)
        return []


def get_agent_profile(
    service: GraphService,
    raw_agent_id: str,
) -> dict:
    """Get agent trust profile with averages. Returns empty dict if unavailable."""
    if not service.connected:
        return {}

    hashed_id = hash_agent_id(raw_agent_id)

    try:
        records, _, _ = service.execute_query(
            _GET_PROFILE_QUERY, {"agent_id": hashed_id}
        )
        if not records:
            return {}

        record = records[0]
        trait_averages = {}
        for trait in _TRAIT_NAMES:
            avg_val = record.get(f"avg_{trait}")
            if avg_val is not None:
                trait_averages[trait] = round(float(avg_val), 4)

        return {
            "agent_id": record.get("agent_id", ""),
            "agent_model": record.get("agent_model", ""),
            "created_at": str(record.get("created_at", "")),
            "evaluation_count": record.get("eval_count", 0),
            "dimension_averages": {
                "ethos": round(float(record.get("avg_ethos") or 0), 4),
                "logos": round(float(record.get("avg_logos") or 0), 4),
                "pathos": round(float(record.get("avg_pathos") or 0), 4),
            },
            "trait_averages": trait_averages,
            "alignment_history": record.get("alignment_history", []),
        }
    except Exception as exc:
        logger.warning("Failed to get agent profile: %s", exc)
        return {}


def get_all_agents(service: GraphService) -> list[dict]:
    """Get all agents with evaluation counts. Returns empty list if unavailable."""
    if not service.connected:
        return []

    try:
        records, _, _ = service.execute_query(_GET_ALL_AGENTS_QUERY)
        results = []
        for record in records:
            results.append({
                "agent_id": record.get("agent_id", ""),
                "evaluation_count": record.get("evals", 0),
                "latest_alignment_status": record.get("latest") or "unknown",
            })
        return results
    except Exception as exc:
        logger.warning("Failed to get all agents: %s", exc)
        return []
