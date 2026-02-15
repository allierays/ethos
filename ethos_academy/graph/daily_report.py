"""Graph operations for DailyReport nodes — store and read report cards.

All Cypher for daily reports lives here. Uses MERGE on (agent_id, report_date)
for idempotent writes. Reports chain via FOLLOWS relationships.
"""

from __future__ import annotations

import json
import logging

from ethos_academy.graph.service import GraphService

logger = logging.getLogger(__name__)

_STORE_DAILY_REPORT_QUERY = """
MERGE (a:Agent {agent_id: $agent_id})
ON CREATE SET a.created_at = datetime(), a.evaluation_count = 0

MERGE (r:DailyReport {agent_id: $agent_id, report_date: $report_date})
ON CREATE SET
    r.report_id = $report_id,
    r.agent_name = $agent_name,
    r.generated_at = $generated_at,
    r.period_evaluation_count = $period_evaluation_count,
    r.total_evaluation_count = $total_evaluation_count,
    r.ethos = $ethos,
    r.logos = $logos,
    r.pathos = $pathos,
    r.trait_averages = $trait_averages,
    r.overall_score = $overall_score,
    r.grade = $grade,
    r.trend = $trend,
    r.risk_level = $risk_level,
    r.flagged_traits = $flagged_traits,
    r.flagged_dimensions = $flagged_dimensions,
    r.temporal_pattern = $temporal_pattern,
    r.character_drift = $character_drift,
    r.balance_trend = $balance_trend,
    r.anomaly_flags = $anomaly_flags,
    r.agent_balance = $agent_balance,
    r.summary = $summary,
    r.insights = $insights,
    r.homework = $homework,
    r.dimension_deltas = $dimension_deltas,
    r.risk_level_change = $risk_level_change
ON MATCH SET
    r.report_id = $report_id,
    r.generated_at = $generated_at,
    r.period_evaluation_count = $period_evaluation_count,
    r.total_evaluation_count = $total_evaluation_count,
    r.ethos = $ethos,
    r.logos = $logos,
    r.pathos = $pathos,
    r.trait_averages = $trait_averages,
    r.overall_score = $overall_score,
    r.grade = $grade,
    r.trend = $trend,
    r.risk_level = $risk_level,
    r.flagged_traits = $flagged_traits,
    r.flagged_dimensions = $flagged_dimensions,
    r.temporal_pattern = $temporal_pattern,
    r.character_drift = $character_drift,
    r.balance_trend = $balance_trend,
    r.anomaly_flags = $anomaly_flags,
    r.agent_balance = $agent_balance,
    r.summary = $summary,
    r.insights = $insights,
    r.homework = $homework,
    r.dimension_deltas = $dimension_deltas,
    r.risk_level_change = $risk_level_change

MERGE (a)-[:HAS_REPORT]->(r)

WITH r
OPTIONAL MATCH (prev:DailyReport {agent_id: $agent_id})
WHERE prev.report_date < $report_date
WITH r, prev ORDER BY prev.report_date DESC LIMIT 1
FOREACH (_ IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
    MERGE (r)-[:FOLLOWS]->(prev)
)
"""

_GET_LATEST_REPORT_QUERY = """
MATCH (r:DailyReport {agent_id: $agent_id})
RETURN r
ORDER BY r.report_date DESC
LIMIT 1
"""

_GET_REPORTS_QUERY = """
MATCH (r:DailyReport {agent_id: $agent_id})
RETURN r
ORDER BY r.report_date DESC
LIMIT $limit
"""

_GET_PERIOD_EVAL_COUNT_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WHERE e.created_at >= datetime($since)
RETURN count(e) AS eval_count
"""


def _report_to_dict(node: dict) -> dict:
    """Convert a DailyReport node to a plain dict, parsing JSON string fields."""
    d = dict(node)
    for key in ("trait_averages", "dimension_deltas", "insights", "homework"):
        val = d.get(key)
        if isinstance(val, str):
            try:
                d[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                d[key] = {} if key != "insights" else []
    return d


async def store_daily_report(
    service: GraphService,
    agent_id: str,
    report: dict,
) -> None:
    """Store a daily report in the graph. Idempotent via MERGE on (agent_id, report_date)."""
    if not service.connected:
        return

    params = {
        "agent_id": agent_id,
        "report_id": report.get("report_id", ""),
        "agent_name": report.get("agent_name", ""),
        "report_date": report.get("report_date", ""),
        "generated_at": report.get("generated_at", ""),
        "period_evaluation_count": report.get("period_evaluation_count", 0),
        "total_evaluation_count": report.get("total_evaluation_count", 0),
        "ethos": report.get("ethos", 0.0),
        "logos": report.get("logos", 0.0),
        "pathos": report.get("pathos", 0.0),
        "trait_averages": json.dumps(report.get("trait_averages", {})),
        "overall_score": report.get("overall_score", 0.0),
        "grade": report.get("grade", ""),
        "trend": report.get("trend", "insufficient_data"),
        "risk_level": report.get("risk_level", "low"),
        "flagged_traits": report.get("flagged_traits", []),
        "flagged_dimensions": report.get("flagged_dimensions", []),
        "temporal_pattern": report.get("temporal_pattern", "insufficient_data"),
        "character_drift": report.get("character_drift", 0.0),
        "balance_trend": report.get("balance_trend", "stable"),
        "anomaly_flags": report.get("anomaly_flags", []),
        "agent_balance": report.get("agent_balance", 0.0),
        "summary": report.get("summary", ""),
        "insights": json.dumps(report.get("insights", [])),
        "homework": json.dumps(report.get("homework", {})),
        "dimension_deltas": json.dumps(report.get("dimension_deltas", {})),
        "risk_level_change": report.get("risk_level_change", ""),
    }

    try:
        await service.execute_query(_STORE_DAILY_REPORT_QUERY, params)
    except Exception as exc:
        logger.warning("Failed to store daily report: %s", exc)


async def get_latest_daily_report(
    service: GraphService,
    agent_id: str,
) -> dict:
    """Get the most recent daily report for an agent. Returns empty dict if none exist."""
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _GET_LATEST_REPORT_QUERY, {"agent_id": agent_id}
        )
        if not records:
            return {}
        return _report_to_dict(records[0]["r"])
    except Exception as exc:
        logger.warning("Failed to get latest daily report: %s", exc)
        return {}


async def get_daily_reports(
    service: GraphService,
    agent_id: str,
    limit: int = 30,
) -> list[dict]:
    """Get daily report history for an agent. Returns empty list if unavailable."""
    if not service.connected:
        return []

    try:
        records, _, _ = await service.execute_query(
            _GET_REPORTS_QUERY, {"agent_id": agent_id, "limit": limit}
        )
        return [_report_to_dict(record["r"]) for record in records]
    except Exception as exc:
        logger.warning("Failed to get daily reports: %s", exc)
        return []


async def get_period_evaluation_count(
    service: GraphService,
    agent_id: str,
    since: str,
) -> int:
    """Count evaluations since a given ISO timestamp. Returns 0 if unavailable."""
    if not service.connected:
        return 0

    try:
        records, _, _ = await service.execute_query(
            _GET_PERIOD_EVAL_COUNT_QUERY, {"agent_id": agent_id, "since": since}
        )
        if records:
            return records[0].get("eval_count", 0)
        return 0
    except Exception as exc:
        logger.warning("Failed to get period evaluation count: %s", exc)
        return 0
