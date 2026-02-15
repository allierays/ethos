"""Phronesis dimension balance — the core of the Aristotelian thesis.

Phronesis (practical wisdom) requires all virtues working in balance.
This module tests that claim empirically: ethos, logos, and pathos are
equally necessary and interdependent. None is weighted higher. Balance
itself predicts character.

Three questions this module answers:
  1. Is this agent balanced across dimensions? (get_agent_balance)
  2. Do balanced agents outperform lopsided ones? (get_balance_vs_phronesis)
  3. Do dimensions correlate — can you sustain one without the others? (get_dimension_correlation)

Returns graceful defaults when Neo4j is down.
"""

from __future__ import annotations

import logging

from ethos_academy.graph.service import GraphService

logger = logging.getLogger(__name__)


_GET_AGENT_BALANCE_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WITH a,
     avg(e.ethos) AS avg_ethos,
     avg(e.logos) AS avg_logos,
     avg(e.pathos) AS avg_pathos,
     count(e) AS eval_count
WITH a, avg_ethos, avg_logos, avg_pathos, eval_count,
     (CASE
         WHEN avg_ethos >= avg_logos AND avg_ethos >= avg_pathos THEN avg_ethos
         WHEN avg_logos >= avg_ethos AND avg_logos >= avg_pathos THEN avg_logos
         ELSE avg_pathos
     END) -
     (CASE
         WHEN avg_ethos <= avg_logos AND avg_ethos <= avg_pathos THEN avg_ethos
         WHEN avg_logos <= avg_ethos AND avg_logos <= avg_pathos THEN avg_logos
         ELSE avg_pathos
     END) AS spread
RETURN a.agent_id AS agent_id,
       avg_ethos, avg_logos, avg_pathos,
       eval_count, spread,
       CASE
           WHEN spread < 0.15 THEN 'balanced'
           WHEN spread < 0.30 THEN 'moderate'
           ELSE 'lopsided'
       END AS balance_category
"""


_GET_BALANCE_VS_PHRONESIS_QUERY = """
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WITH a,
     avg(e.ethos) AS avg_ethos,
     avg(e.logos) AS avg_logos,
     avg(e.pathos) AS avg_pathos,
     avg(e.phronesis_score) AS avg_phronesis,
     count(e) AS eval_count,
     sum(CASE WHEN size(e.flags) > 0 THEN 1 ELSE 0 END) AS flagged_count
WITH a, avg_ethos, avg_logos, avg_pathos, avg_phronesis, eval_count, flagged_count,
     (CASE
         WHEN avg_ethos >= avg_logos AND avg_ethos >= avg_pathos THEN avg_ethos
         WHEN avg_logos >= avg_ethos AND avg_logos >= avg_pathos THEN avg_logos
         ELSE avg_pathos
     END) -
     (CASE
         WHEN avg_ethos <= avg_logos AND avg_ethos <= avg_pathos THEN avg_ethos
         WHEN avg_logos <= avg_ethos AND avg_logos <= avg_pathos THEN avg_logos
         ELSE avg_pathos
     END) AS spread
WITH CASE
         WHEN spread < 0.15 THEN 'balanced'
         WHEN spread < 0.30 THEN 'moderate'
         ELSE 'lopsided'
     END AS balance_category,
     avg_phronesis, eval_count, flagged_count
RETURN balance_category,
       count(*) AS agent_count,
       avg(avg_phronesis) AS avg_phronesis,
       sum(flagged_count) * 1.0 / sum(eval_count) AS flag_rate
ORDER BY avg_phronesis DESC
"""


_GET_DIMENSION_GAPS_QUERY = """
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WITH a,
     avg(e.ethos) AS avg_ethos,
     avg(e.logos) AS avg_logos,
     avg(e.pathos) AS avg_pathos,
     count(e) AS eval_count
WITH a, avg_ethos, avg_logos, avg_pathos, eval_count,
     (avg_ethos + avg_logos + avg_pathos) / 3.0 AS overall_avg
WHERE (overall_avg - avg_ethos > 0.2)
   OR (overall_avg - avg_logos > 0.2)
   OR (overall_avg - avg_pathos > 0.2)
RETURN a.agent_id AS agent_id,
       avg_ethos, avg_logos, avg_pathos, eval_count,
       CASE
           WHEN overall_avg - avg_ethos >= overall_avg - avg_logos
                AND overall_avg - avg_ethos >= overall_avg - avg_pathos
           THEN 'ethos'
           WHEN overall_avg - avg_logos >= overall_avg - avg_ethos
                AND overall_avg - avg_logos >= overall_avg - avg_pathos
           THEN 'logos'
           ELSE 'pathos'
       END AS weak_dimension,
       CASE
           WHEN overall_avg - avg_ethos >= overall_avg - avg_logos
                AND overall_avg - avg_ethos >= overall_avg - avg_pathos
           THEN round(overall_avg - avg_ethos, 4)
           WHEN overall_avg - avg_logos >= overall_avg - avg_ethos
                AND overall_avg - avg_logos >= overall_avg - avg_pathos
           THEN round(overall_avg - avg_logos, 4)
           ELSE round(overall_avg - avg_pathos, 4)
       END AS gap_size
ORDER BY gap_size DESC
"""


_GET_DIMENSION_CORRELATION_QUERY = """
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WITH a,
     avg(e.ethos) AS avg_ethos,
     avg(e.logos) AS avg_logos,
     avg(e.pathos) AS avg_pathos,
     count(e) AS eval_count
WHERE eval_count >= $min_evaluations
WITH collect(avg_ethos) AS ethos_vals,
     collect(avg_logos) AS logos_vals,
     collect(avg_pathos) AS pathos_vals,
     count(*) AS n
WITH ethos_vals, logos_vals, pathos_vals, n,
     REDUCE(s = 0.0, x IN ethos_vals | s + x) / n AS mean_e,
     REDUCE(s = 0.0, x IN logos_vals | s + x) / n AS mean_l,
     REDUCE(s = 0.0, x IN pathos_vals | s + x) / n AS mean_p
WITH ethos_vals, logos_vals, pathos_vals, n, mean_e, mean_l, mean_p,
     [i IN range(0, n - 1) |
       (ethos_vals[i] - mean_e) * (logos_vals[i] - mean_l)] AS el_products,
     [i IN range(0, n - 1) |
       (ethos_vals[i] - mean_e) * (pathos_vals[i] - mean_p)] AS ep_products,
     [i IN range(0, n - 1) |
       (logos_vals[i] - mean_l) * (pathos_vals[i] - mean_p)] AS lp_products,
     [i IN range(0, n - 1) |
       (ethos_vals[i] - mean_e) * (ethos_vals[i] - mean_e)] AS e_sq,
     [i IN range(0, n - 1) |
       (logos_vals[i] - mean_l) * (logos_vals[i] - mean_l)] AS l_sq,
     [i IN range(0, n - 1) |
       (pathos_vals[i] - mean_p) * (pathos_vals[i] - mean_p)] AS p_sq
WITH n,
     REDUCE(s = 0.0, x IN el_products | s + x) AS cov_el,
     REDUCE(s = 0.0, x IN ep_products | s + x) AS cov_ep,
     REDUCE(s = 0.0, x IN lp_products | s + x) AS cov_lp,
     sqrt(REDUCE(s = 0.0, x IN e_sq | s + x)) AS sd_e,
     sqrt(REDUCE(s = 0.0, x IN l_sq | s + x)) AS sd_l,
     sqrt(REDUCE(s = 0.0, x IN p_sq | s + x)) AS sd_p
RETURN n AS agent_count,
       CASE WHEN sd_e * sd_l > 0 THEN cov_el / (sd_e * sd_l) ELSE 0 END AS r_ethos_logos,
       CASE WHEN sd_e * sd_p > 0 THEN cov_ep / (sd_e * sd_p) ELSE 0 END AS r_ethos_pathos,
       CASE WHEN sd_l * sd_p > 0 THEN cov_lp / (sd_l * sd_p) ELSE 0 END AS r_logos_pathos
"""


_GET_ALUMNI_BALANCE_DISTRIBUTION_QUERY = """
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WITH a,
     avg(e.ethos) AS avg_ethos,
     avg(e.logos) AS avg_logos,
     avg(e.pathos) AS avg_pathos
WITH a,
     (CASE
         WHEN avg_ethos >= avg_logos AND avg_ethos >= avg_pathos THEN avg_ethos
         WHEN avg_logos >= avg_ethos AND avg_logos >= avg_pathos THEN avg_logos
         ELSE avg_pathos
     END) -
     (CASE
         WHEN avg_ethos <= avg_logos AND avg_ethos <= avg_pathos THEN avg_ethos
         WHEN avg_logos <= avg_ethos AND avg_logos <= avg_pathos THEN avg_logos
         ELSE avg_pathos
     END) AS spread
WITH CASE
         WHEN spread < 0.15 THEN 'balanced'
         WHEN spread < 0.30 THEN 'moderate'
         ELSE 'lopsided'
     END AS balance_category
RETURN balance_category, count(*) AS agent_count
ORDER BY balance_category
"""


async def get_agent_balance(service: GraphService, agent_id: str) -> dict:
    """Get dimension balance analysis for a single agent.

    Returns dict with avg_ethos, avg_logos, avg_pathos, spread, and
    balance_category ('balanced', 'moderate', 'lopsided').
    Returns empty dict if unavailable.
    """
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _GET_AGENT_BALANCE_QUERY, {"agent_id": agent_id}
        )
        if not records:
            return {}

        record = records[0]
        return {
            "agent_id": record.get("agent_id", ""),
            "avg_ethos": round(float(record.get("avg_ethos") or 0), 4),
            "avg_logos": round(float(record.get("avg_logos") or 0), 4),
            "avg_pathos": round(float(record.get("avg_pathos") or 0), 4),
            "spread": round(float(record.get("spread") or 0), 4),
            "balance_category": record.get("balance_category", ""),
            "evaluation_count": record.get("eval_count", 0),
        }
    except Exception as exc:
        logger.warning("Failed to get agent balance: %s", exc)
        return {}


async def get_balance_vs_phronesis(service: GraphService) -> list[dict]:
    """Get balance vs phronesis correlation across all agents.

    Groups agents by balance category and returns average phronesis outcomes
    per group. Returns empty list if unavailable.
    """
    if not service.connected:
        return []

    try:
        records, _, _ = await service.execute_query(_GET_BALANCE_VS_PHRONESIS_QUERY)
        results = []
        for record in records:
            results.append(
                {
                    "balance_category": record.get("balance_category", ""),
                    "agent_count": record.get("agent_count", 0),
                    "avg_phronesis": round(float(record.get("avg_phronesis") or 0), 4),
                    "flag_rate": round(float(record.get("flag_rate") or 0), 4),
                }
            )
        return results
    except Exception as exc:
        logger.warning("Failed to get balance vs phronesis: %s", exc)
        return []


async def get_dimension_gaps(service: GraphService) -> list[dict]:
    """Find agents with a significant dimension gap.

    Returns agents where one dimension is > 0.2 below the average of
    all three. Includes the weak dimension name and gap size.
    Returns empty list if unavailable.
    """
    if not service.connected:
        return []

    try:
        records, _, _ = await service.execute_query(_GET_DIMENSION_GAPS_QUERY)
        results = []
        for record in records:
            results.append(
                {
                    "agent_id": record.get("agent_id", ""),
                    "avg_ethos": round(float(record.get("avg_ethos") or 0), 4),
                    "avg_logos": round(float(record.get("avg_logos") or 0), 4),
                    "avg_pathos": round(float(record.get("avg_pathos") or 0), 4),
                    "weak_dimension": record.get("weak_dimension", ""),
                    "gap_size": round(float(record.get("gap_size") or 0), 4),
                    "evaluation_count": record.get("eval_count", 0),
                }
            )
        return results
    except Exception as exc:
        logger.warning("Failed to get dimension gaps: %s", exc)
        return []


async def get_dimension_correlation(
    service: GraphService, min_evaluations: int = 3
) -> dict:
    """Get Pearson correlation between all dimension pairs across agents.

    Tests the Aristotelian thesis: ethos, logos, and pathos are interdependent.
    High positive correlations mean dimensions move together — you can't
    sustain one without the others.

    Returns dict with r_ethos_logos, r_ethos_pathos, r_logos_pathos, and
    agent_count. Returns empty dict if unavailable.
    """
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _GET_DIMENSION_CORRELATION_QUERY,
            {"min_evaluations": min_evaluations},
        )
        if not records:
            return {}

        record = records[0]
        return {
            "agent_count": record.get("agent_count", 0),
            "r_ethos_logos": round(float(record.get("r_ethos_logos") or 0), 4),
            "r_ethos_pathos": round(float(record.get("r_ethos_pathos") or 0), 4),
            "r_logos_pathos": round(float(record.get("r_logos_pathos") or 0), 4),
        }
    except Exception as exc:
        logger.warning("Failed to get dimension correlation: %s", exc)
        return {}


async def get_alumni_balance_distribution(service: GraphService) -> dict:
    """Get network-wide balance distribution.

    Returns count of agents in each balance category:
    {'balanced': N, 'moderate': N, 'lopsided': N, 'total_agents': N}
    Returns empty dict if unavailable.
    """
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _GET_ALUMNI_BALANCE_DISTRIBUTION_QUERY
        )
        if not records:
            return {}

        distribution = {"balanced": 0, "moderate": 0, "lopsided": 0}
        total = 0
        for record in records:
            category = record.get("balance_category", "")
            count = record.get("agent_count", 0)
            if category in distribution:
                distribution[category] = count
                total += count

        distribution["total_agents"] = total
        return distribution
    except Exception as exc:
        logger.warning("Failed to get alumni balance distribution: %s", exc)
        return {}
