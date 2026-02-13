"""Graph read operations — query evaluations and agent profiles.

All Cypher for reads lives here. Returns graceful defaults when Neo4j is down.
"""

from __future__ import annotations

import logging

from ethos.graph.service import GraphService
from ethos.shared.analysis import TRAIT_NAMES

logger = logging.getLogger(__name__)

_GET_ALL_AGENTS_QUERY = """
MATCH (a:Agent)
OPTIONAL MATCH (a)-[:EVALUATED]->(e:Evaluation)
WITH a, e
ORDER BY e.created_at ASC
WITH a, count(e) AS evals, last(collect(e.alignment_status)) AS latest
RETURN a.agent_id AS agent_id, coalesce(a.agent_name, '') AS agent_name, coalesce(a.agent_specialty, '') AS agent_specialty, evals, latest, coalesce(a.enrolled, false) AS enrolled
ORDER BY evals DESC
"""

_SEARCH_AGENTS_QUERY = """
MATCH (a:Agent)
WHERE toLower(a.agent_name) CONTAINS toLower($search)
OPTIONAL MATCH (a)-[:EVALUATED]->(e:Evaluation)
WITH a, e
ORDER BY e.created_at ASC
WITH a, count(e) AS evals, last(collect(e.alignment_status)) AS latest
RETURN a.agent_id AS agent_id, coalesce(a.agent_name, '') AS agent_name, coalesce(a.agent_specialty, '') AS agent_specialty, evals, latest, coalesce(a.enrolled, false) AS enrolled
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
       coalesce(a.agent_name, '') AS agent_name,
       coalesce(a.agent_specialty, '') AS agent_specialty,
       a.agent_model AS agent_model,
       a.created_at AS created_at,
       eval_count,
       avg_ethos, avg_logos, avg_pathos,
       avg_virtue, avg_goodwill, avg_manipulation, avg_deception,
       avg_accuracy, avg_reasoning, avg_fabrication, avg_broken_logic,
       avg_recognition, avg_compassion, avg_dismissal, avg_exploitation,
       alignment_history,
       coalesce(a.enrolled, false) AS enrolled,
       a.enrolled_at AS enrolled_at,
       coalesce(a.counselor_name, '') AS counselor_name,
       coalesce(a.entrance_exam_completed, false) AS entrance_exam_completed
"""


_AGENT_SIGNATURE_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WITH a, e ORDER BY e.created_at DESC
WITH a,
     count(e) AS eval_count,
     avg(e.ethos) AS avg_ethos,
     avg(e.logos) AS avg_logos,
     avg(e.pathos) AS avg_pathos,
     collect(e.alignment_status)[..10] AS recent_statuses,
     collect(e.flags)[..10] AS recent_flags,
     stdev(e.ethos) AS std_ethos,
     stdev(e.logos) AS std_logos,
     stdev(e.pathos) AS std_pathos,
     avg(e.trait_manipulation) AS avg_manipulation,
     avg(e.trait_deception) AS avg_deception,
     avg(e.trait_fabrication) AS avg_fabrication,
     avg(e.trait_exploitation) AS avg_exploitation,
     avg(e.trait_dismissal) AS avg_dismissal,
     avg(e.trait_broken_logic) AS avg_broken_logic
RETURN eval_count, avg_ethos, avg_logos, avg_pathos,
       recent_statuses, recent_flags,
       std_ethos, std_logos, std_pathos,
       avg_manipulation, avg_deception, avg_fabrication,
       avg_exploitation, avg_dismissal, avg_broken_logic,
       a.trait_variance AS stored_variance,
       a.balance_score AS stored_balance
"""

_RECENT_TREND_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WITH e ORDER BY e.created_at DESC LIMIT 5
WITH collect({
    ethos: e.ethos,
    logos: e.logos,
    pathos: e.pathos,
    alignment_status: e.alignment_status
}) AS recent
RETURN recent
"""


async def get_agent_signature(service: GraphService, agent_id: str) -> dict:
    """Get agent behavioral signature — aggregate stats + recent patterns.

    Returns dict with eval_count, avg dimensions, std devs, recent statuses/flags,
    and negative trait averages. Returns empty dict if unavailable.
    """
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _AGENT_SIGNATURE_QUERY, {"agent_id": agent_id}
        )
        if not records:
            return {}
        return dict(records[0])
    except Exception as exc:
        logger.warning("Failed to get agent signature: %s", exc)
        return {}


async def get_recent_trend(service: GraphService, agent_id: str) -> list[dict]:
    """Get last 5 evaluations for temporal trend analysis.

    Returns list of dicts with ethos, logos, pathos, alignment_status.
    Returns empty list if unavailable.
    """
    if not service.connected:
        return []

    try:
        records, _, _ = await service.execute_query(
            _RECENT_TREND_QUERY, {"agent_id": agent_id}
        )
        if not records:
            return []
        return records[0].get("recent", [])
    except Exception as exc:
        logger.warning("Failed to get recent trend: %s", exc)
        return []


async def get_evaluation_history(
    service: GraphService,
    agent_id: str,
    limit: int = 10,
) -> list[dict]:
    """Get recent evaluations for an agent. Returns empty list if unavailable."""
    if not service.connected:
        return []

    try:
        records, _, _ = await service.execute_query(
            _GET_HISTORY_QUERY, {"agent_id": agent_id, "limit": limit}
        )
        results = []
        for record in records:
            node = record["e"]
            results.append(dict(node))
        return results
    except Exception as exc:
        logger.warning("Failed to get evaluation history: %s", exc)
        return []


async def get_agent_profile(
    service: GraphService,
    agent_id: str,
) -> dict:
    """Get agent phronesis profile with averages. Returns empty dict if unavailable."""
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _GET_PROFILE_QUERY, {"agent_id": agent_id}
        )
        if not records:
            return {}

        record = records[0]
        trait_averages = {}
        for trait in TRAIT_NAMES:
            avg_val = record.get(f"avg_{trait}")
            if avg_val is not None:
                trait_averages[trait] = round(float(avg_val), 4)

        return {
            "agent_id": record.get("agent_id", ""),
            "agent_name": record.get("agent_name", ""),
            "agent_specialty": record.get("agent_specialty", ""),
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
            "enrolled": record.get("enrolled", False),
            "enrolled_at": str(record.get("enrolled_at") or ""),
            "counselor_name": record.get("counselor_name", ""),
            "entrance_exam_completed": record.get("entrance_exam_completed", False),
        }
    except Exception as exc:
        logger.warning("Failed to get agent profile: %s", exc)
        return {}


async def get_all_agents(service: GraphService, search: str = "") -> list[dict]:
    """Get all agents with evaluation counts. Returns empty list if unavailable.

    Args:
        service: Graph service connection.
        search: Optional name filter — matches agent_name case-insensitively.
    """
    if not service.connected:
        return []

    try:
        if search:
            records, _, _ = await service.execute_query(
                _SEARCH_AGENTS_QUERY, {"search": search}
            )
        else:
            records, _, _ = await service.execute_query(_GET_ALL_AGENTS_QUERY)
        results = []
        for record in records:
            results.append(
                {
                    "agent_id": record.get("agent_id", ""),
                    "agent_name": record.get("agent_name", ""),
                    "agent_specialty": record.get("agent_specialty", ""),
                    "evaluation_count": record.get("evals", 0),
                    "latest_alignment_status": record.get("latest") or "unknown",
                    "enrolled": record.get("enrolled", False),
                }
            )
        return results
    except Exception as exc:
        logger.warning("Failed to get all agents: %s", exc)
        return []
