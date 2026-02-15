"""Graph insight queries — read-only Cypher for MCP tools.

Showcase queries: topology stats, early warning indicators, sabotage status,
and global constitutional risk. Other insight tools reuse existing queries
from temporal.py, visualization.py, and read.py.
"""

from __future__ import annotations

import logging

from ethos_academy.graph.service import GraphService

logger = logging.getLogger(__name__)

# ── Network Topology ──────────────────────────────────────────────────────

_NODE_COUNTS_QUERY = """
MATCH (n)
WITH labels(n)[0] AS label, count(n) AS count
RETURN label, count
ORDER BY count DESC
"""

_REL_COUNTS_QUERY = """
MATCH ()-[r]->()
WITH type(r) AS rel_type, count(r) AS count
RETURN rel_type, count
ORDER BY count DESC
"""

_AGENT_EVAL_TOTALS_QUERY = """
MATCH (a:Agent)
OPTIONAL MATCH (a)-[:EVALUATED]->(e:Evaluation)
WITH count(DISTINCT a) AS agents, count(e) AS evaluations
RETURN agents, evaluations
"""


async def get_topology_stats(service: GraphService) -> dict:
    """Get graph node counts, relationship counts, and agent/eval totals."""
    if not service.connected:
        return {}
    try:
        node_records, _, _ = await service.execute_query(_NODE_COUNTS_QUERY)
        rel_records, _, _ = await service.execute_query(_REL_COUNTS_QUERY)
        agent_records, _, _ = await service.execute_query(_AGENT_EVAL_TOTALS_QUERY)

        node_counts = {r["label"]: r["count"] for r in node_records if r.get("label")}
        rel_counts = {
            r["rel_type"]: r["count"] for r in rel_records if r.get("rel_type")
        }
        totals = agent_records[0] if agent_records else {}

        return {
            "node_counts": node_counts,
            "relationship_counts": rel_counts,
            "total_nodes": sum(node_counts.values()),
            "total_relationships": sum(rel_counts.values()),
            "agent_count": totals.get("agents", 0),
            "evaluation_count": totals.get("evaluations", 0),
        }
    except Exception as exc:
        logger.warning("Failed to get topology stats: %s", exc)
        return {}


# ── Early Warning Indicators ──────────────────────────────────────────────
# Find indicators detected in an agent's first 3 evaluations,
# then check if that agent later showed misalignment.

_EARLY_WARNING_QUERY = """
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WITH a, e ORDER BY e.created_at ASC
WITH a, collect(e) AS evals
WHERE size(evals) >= 5
WITH a, evals[..3] AS early_evals,
     [x IN evals[size(evals)-3..] | x.alignment_status] AS late_statuses
UNWIND early_evals AS early
MATCH (early)-[:DETECTED]->(i:Indicator)
WITH DISTINCT i, a, late_statuses
WITH i,
     count(DISTINCT a) AS agent_count,
     sum(CASE
         WHEN any(s IN late_statuses WHERE s IN ['misaligned', 'drifting'])
         THEN 1 ELSE 0
     END) AS trouble_count
RETURN i.id AS indicator_id, i.name AS indicator_name, i.trait AS trait,
       agent_count, trouble_count,
       toFloat(trouble_count) / agent_count AS trouble_rate
ORDER BY trouble_rate DESC, trouble_count DESC
LIMIT 20
"""


async def get_early_warning_data(service: GraphService) -> list[dict]:
    """Find indicators that appear early and correlate with later trouble."""
    if not service.connected:
        return []
    try:
        records, _, _ = await service.execute_query(_EARLY_WARNING_QUERY)
        return [
            {
                "indicator_id": r.get("indicator_id", ""),
                "indicator_name": r.get("indicator_name", ""),
                "trait": r.get("trait", ""),
                "agent_count": r.get("agent_count", 0),
                "trouble_count": r.get("trouble_count", 0),
                "trouble_rate": round(float(r.get("trouble_rate", 0)), 4),
            }
            for r in records
        ]
    except Exception as exc:
        logger.warning("Failed to get early warning data: %s", exc)
        return []


# ── Sabotage Pathway Status ──────────────────────────────────────────────

_ALL_SABOTAGE_STATUS_QUERY = """
MATCH (a:Agent)-[r:EXHIBITS_PATTERN]->(p:Pattern)
RETURN a.agent_id AS agent_id, coalesce(a.agent_name, '') AS agent_name,
       p.pattern_id AS pattern_id, p.name AS pattern_name,
       p.description AS pattern_description,
       coalesce(p.severity, 'info') AS severity,
       r.confidence AS confidence,
       r.current_stage AS current_stage,
       toString(r.first_seen) AS first_seen,
       toString(r.last_seen) AS last_seen,
       r.occurrence_count AS occurrence_count
ORDER BY r.confidence DESC
"""

_AGENT_SABOTAGE_STATUS_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})-[r:EXHIBITS_PATTERN]->(p:Pattern)
OPTIONAL MATCH (p)-[:COMPOSED_OF]->(i:Indicator)
WITH a, r, p, collect(i.id) AS all_indicators
OPTIONAL MATCH (a)-[:EVALUATED]->(e:Evaluation)-[:DETECTED]->(di:Indicator)
WHERE di.id IN all_indicators
WITH a, r, p, all_indicators,
     collect(DISTINCT di.id) AS matched_indicators
RETURN a.agent_id AS agent_id,
       p.pattern_id AS pattern_id, p.name AS pattern_name,
       p.description AS pattern_description,
       coalesce(p.severity, 'info') AS severity,
       r.confidence AS confidence,
       r.current_stage AS current_stage,
       size(all_indicators) AS total_stages,
       matched_indicators,
       toString(r.first_seen) AS first_seen,
       toString(r.last_seen) AS last_seen,
       r.occurrence_count AS occurrence_count
ORDER BY r.confidence DESC
"""


async def get_all_sabotage_status(service: GraphService) -> list[dict]:
    """Get sabotage pathway status across all agents."""
    if not service.connected:
        return []
    try:
        records, _, _ = await service.execute_query(_ALL_SABOTAGE_STATUS_QUERY)
        return [
            {
                "agent_id": r.get("agent_id", ""),
                "agent_name": r.get("agent_name", ""),
                "pattern_id": r.get("pattern_id", ""),
                "pattern_name": r.get("pattern_name", ""),
                "pattern_description": r.get("pattern_description", ""),
                "severity": r.get("severity", "info"),
                "confidence": round(float(r.get("confidence", 0)), 4),
                "current_stage": r.get("current_stage", 0),
                "first_seen": r.get("first_seen", ""),
                "last_seen": r.get("last_seen", ""),
                "occurrence_count": r.get("occurrence_count", 0),
            }
            for r in records
        ]
    except Exception as exc:
        logger.warning("Failed to get all sabotage status: %s", exc)
        return []


async def get_agent_sabotage_status(service: GraphService, agent_id: str) -> list[dict]:
    """Get sabotage pathway status for a specific agent with stage detail."""
    if not service.connected:
        return []
    try:
        records, _, _ = await service.execute_query(
            _AGENT_SABOTAGE_STATUS_QUERY, {"agent_id": agent_id}
        )
        return [
            {
                "agent_id": r.get("agent_id", ""),
                "pattern_id": r.get("pattern_id", ""),
                "pattern_name": r.get("pattern_name", ""),
                "pattern_description": r.get("pattern_description", ""),
                "severity": r.get("severity", "info"),
                "confidence": round(float(r.get("confidence", 0)), 4),
                "current_stage": r.get("current_stage", 0),
                "total_stages": r.get("total_stages", 0),
                "matched_indicators": list(r.get("matched_indicators", [])),
                "first_seen": r.get("first_seen", ""),
                "last_seen": r.get("last_seen", ""),
                "occurrence_count": r.get("occurrence_count", 0),
            }
            for r in records
        ]
    except Exception as exc:
        logger.warning("Failed to get agent sabotage status: %s", exc)
        return []


# ── Evaluation Depth Distribution ─────────────────────────────────────────

_TIER_DISTRIBUTION_QUERY = """
MATCH (e:Evaluation)
RETURN e.routing_tier AS tier, count(e) AS count
ORDER BY count DESC
"""

_ALIGNMENT_STATUS_DISTRIBUTION_QUERY = """
MATCH (e:Evaluation)
RETURN e.alignment_status AS status, count(e) AS count
ORDER BY count DESC
"""


# ── Global Constitutional Risk ────────────────────────────────────────────
# 5-hop aggregation across all agents:
# Agent -> Evaluation -> Indicator -> Trait -> ConstitutionalValue

_GLOBAL_CONSTITUTIONAL_RISK_QUERY = """
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)-[d:DETECTED]->(i:Indicator)
      -[:BELONGS_TO]->(t:Trait)-[u:UPHOLDS]->(cv:ConstitutionalValue)
WITH cv, t, i, u.relationship AS impact,
     count(DISTINCT e) AS detection_count,
     count(DISTINCT a) AS agent_count,
     avg(d.confidence) AS avg_confidence
RETURN cv.name AS value_name, cv.priority AS priority,
       impact, t.name AS trait, t.polarity AS polarity,
       i.id AS indicator_id, i.name AS indicator_name,
       detection_count, agent_count, avg_confidence
ORDER BY cv.priority ASC, detection_count DESC
"""


async def get_depth_distribution(service: GraphService) -> dict:
    """Get evaluation routing tier and alignment status distributions."""
    if not service.connected:
        return {"tiers": [], "statuses": []}
    try:
        tier_records, _, _ = await service.execute_query(_TIER_DISTRIBUTION_QUERY)
        status_records, _, _ = await service.execute_query(
            _ALIGNMENT_STATUS_DISTRIBUTION_QUERY
        )
        return {
            "tiers": [
                {"tier": r.get("tier", "unknown"), "count": r.get("count", 0)}
                for r in tier_records
                if r.get("tier")
            ],
            "statuses": [
                {"status": r.get("status", "unknown"), "count": r.get("count", 0)}
                for r in status_records
                if r.get("status")
            ],
        }
    except Exception as exc:
        logger.warning("Failed to get depth distribution: %s", exc)
        return {"tiers": [], "statuses": []}


async def get_global_constitutional_risk(service: GraphService) -> list[dict]:
    """Get constitutional risk across all agents via 5-hop aggregation."""
    if not service.connected:
        return []
    try:
        records, _, _ = await service.execute_query(_GLOBAL_CONSTITUTIONAL_RISK_QUERY)
        return [
            {
                "value_name": r.get("value_name", ""),
                "priority": r.get("priority", 0),
                "impact": r.get("impact", ""),
                "trait": r.get("trait", ""),
                "polarity": r.get("polarity", ""),
                "indicator_id": r.get("indicator_id", ""),
                "indicator_name": r.get("indicator_name", ""),
                "detection_count": r.get("detection_count", 0),
                "agent_count": r.get("agent_count", 0),
                "avg_confidence": round(float(r.get("avg_confidence", 0)), 4),
            }
            for r in records
        ]
    except Exception as exc:
        logger.warning("Failed to get global constitutional risk: %s", exc)
        return []
