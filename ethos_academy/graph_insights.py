"""Graph Insight tools — read-only domain functions for MCP.

Seven tools that showcase Neo4j graph capabilities:
1. get_character_arc — temporal PRECEDES chain traversal
2. get_constitutional_risk_report — 5-hop multi-layer aggregation
3. find_similar_agents — bipartite Jaccard similarity
4. get_early_warning_indicators — temporal position + correlation
5. get_network_topology — graph metadata queries
6. get_sabotage_pathway_status — bi-directional traversal
7. compare_agents — parallel subgraph + set ops
"""

from __future__ import annotations

import logging

import asyncio

from ethos_academy.graph.alumni import get_alumni_averages
from ethos_academy.graph.insights import (
    get_agent_sabotage_status,
    get_all_sabotage_status,
    get_depth_distribution,
    get_early_warning_data,
    get_global_constitutional_risk,
    get_topology_stats,
)
from ethos_academy.graph.read import get_agent_profile
from ethos_academy.graph.service import graph_context
from ethos_academy.graph.temporal import get_drift_timeline
from ethos_academy.graph.visualization import (
    get_constitutional_trail,
    get_similarity_data,
)
from ethos_academy.shared.models import (
    AlumniResult,
    CohortInsightsResult,
    ConstitutionalRiskItem,
    DepthDistribution,
    DepthStatusCount,
    DepthTierCount,
    SabotagePathwaySummary,
)

logger = logging.getLogger(__name__)


def _top_items(items: list, n: int) -> list[dict]:
    """Count items and return top N with counts."""
    counts: dict[str, int] = {}
    for item in items:
        if item:
            counts[item] = counts.get(item, 0) + 1
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [{"name": name, "count": count} for name, count in sorted_items[:n]]


async def get_character_arc(agent_id: str) -> dict:
    """Trace the full story of how an agent's character formed over time.

    Walks the PRECEDES evaluation chain and builds a narrative arc:
    phases, turning points, and overall trajectory.
    """
    try:
        async with graph_context() as service:
            timeline = await get_drift_timeline(service, agent_id)

        if not timeline:
            return {
                "agent_id": agent_id,
                "arc": "no_data",
                "total_evaluations": 0,
                "phases": [],
                "turning_points": [],
            }

        n = len(timeline)

        # Split into phases (thirds)
        third = max(1, n // 3)
        phases = []

        for label, window in [
            ("early", timeline[:third]),
            ("middle", timeline[third : third * 2]),
            ("recent", timeline[third * 2 :]),
        ]:
            if not window:
                continue
            avg_e = sum(p["ethos"] for p in window) / len(window)
            avg_l = sum(p["logos"] for p in window) / len(window)
            avg_p = sum(p["pathos"] for p in window) / len(window)
            overall = (avg_e + avg_l + avg_p) / 3
            alignments = [p["alignment"] for p in window]
            misaligned_pct = sum(
                1 for a in alignments if a in ("misaligned", "drifting")
            ) / len(alignments)
            all_flags: list[str] = []
            all_indicators: list[str] = []
            for p in window:
                all_flags.extend(p.get("flags") or [])
                all_indicators.extend(p.get("indicators") or [])

            phases.append(
                {
                    "phase": label,
                    "evaluation_count": len(window),
                    "avg_ethos": round(avg_e, 4),
                    "avg_logos": round(avg_l, 4),
                    "avg_pathos": round(avg_p, 4),
                    "avg_overall": round(overall, 4),
                    "misaligned_rate": round(misaligned_pct, 4),
                    "top_flags": _top_items(all_flags, 3),
                    "top_indicators": _top_items(all_indicators, 5),
                    "first_eval": window[0].get("created_at", ""),
                    "last_eval": window[-1].get("created_at", ""),
                }
            )

        # Determine arc shape
        if len(phases) >= 2:
            early_score = phases[0]["avg_overall"]
            late_score = phases[-1]["avg_overall"]
            delta = late_score - early_score
            if delta > 0.08:
                arc = "growth"
            elif delta < -0.08:
                arc = "decline"
            else:
                arc = "steady"
        else:
            arc = "emerging"

        # Find turning points (biggest single-step changes)
        turning_points = []
        for i in range(1, n):
            prev = timeline[i - 1]
            curr = timeline[i]
            prev_overall = (prev["ethos"] + prev["logos"] + prev["pathos"]) / 3
            curr_overall = (curr["ethos"] + curr["logos"] + curr["pathos"]) / 3
            delta = curr_overall - prev_overall
            if abs(delta) >= 0.15:
                turning_points.append(
                    {
                        "eval_index": i + 1,
                        "evaluation_id": curr["eval_id"],
                        "delta": round(delta, 4),
                        "direction": "improvement" if delta > 0 else "regression",
                        "created_at": curr.get("created_at", ""),
                        "indicators": curr.get("indicators", []),
                    }
                )

        # Keep top 5 by magnitude
        turning_points.sort(key=lambda t: abs(t["delta"]), reverse=True)
        turning_points = turning_points[:5]

        return {
            "agent_id": agent_id,
            "total_evaluations": n,
            "arc": arc,
            "phases": phases,
            "turning_points": turning_points,
            "first_eval": timeline[0].get("created_at", ""),
            "last_eval": timeline[-1].get("created_at", ""),
        }
    except Exception as exc:
        logger.warning("Failed to get character arc for %s: %s", agent_id, exc)
        return {
            "agent_id": agent_id,
            "arc": "error",
            "total_evaluations": 0,
            "phases": [],
            "turning_points": [],
        }


async def get_constitutional_risk_report(agent_id: str = "") -> dict:
    """Report which constitutional values are most at risk.

    5-hop traversal: Agent -> Evaluation -> Indicator -> Trait -> ConstitutionalValue.
    If agent_id is provided, scoped to that agent. Otherwise, global across all agents.
    """
    try:
        async with graph_context() as service:
            if agent_id:
                raw = await get_constitutional_trail(service, agent_id)
            else:
                raw = await get_global_constitutional_risk(service)

        if not raw:
            return {
                "scope": agent_id or "global",
                "at_risk_values": [],
                "total_values_affected": 0,
            }

        # Group by constitutional value
        values: dict[str, dict] = {}
        for row in raw:
            cv_name = row.get("constitutional_value") or row.get("value_name", "")
            if not cv_name:
                continue

            if cv_name not in values:
                values[cv_name] = {
                    "value": cv_name,
                    "priority": row.get("cv_priority") or row.get("priority", 0),
                    "total_detections": 0,
                    "threat_indicators": [],
                    "protective_indicators": [],
                }

            entry = values[cv_name]
            det_count = row.get("eval_count") or row.get("detection_count", 0)
            entry["total_detections"] += det_count

            indicator_info = {
                "indicator": row.get("indicator_name", ""),
                "trait": row.get("trait", ""),
                "impact": row.get("impact", ""),
                "detections": det_count,
                "avg_confidence": round(float(row.get("avg_confidence", 0)), 4),
            }

            polarity = row.get("trait_polarity") or row.get("polarity", "")
            if polarity == "negative":
                entry["threat_indicators"].append(indicator_info)
            else:
                entry["protective_indicators"].append(indicator_info)

        # Sort by total detections (most at risk first)
        at_risk = sorted(
            values.values(), key=lambda v: v["total_detections"], reverse=True
        )

        return {
            "scope": agent_id or "global",
            "at_risk_values": at_risk,
            "total_values_affected": len(at_risk),
        }
    except Exception as exc:
        logger.warning("Failed to get constitutional risk: %s", exc)
        return {
            "scope": agent_id or "global",
            "at_risk_values": [],
            "total_values_affected": 0,
        }


async def find_similar_agents(agent_id: str) -> dict:
    """Find agents with similar behavioral patterns using Jaccard similarity.

    Computes similarity over shared indicators in the bipartite agent-indicator graph.
    """
    try:
        async with graph_context() as service:
            all_edges = await get_similarity_data(service)

        # Filter edges involving this agent
        matches = []
        for edge in all_edges:
            if edge["agent1_id"] == agent_id:
                matches.append(
                    {
                        "agent_id": edge["agent2_id"],
                        "agent_name": edge.get("agent2_name", ""),
                        "phronesis": edge.get("agent2_phronesis"),
                        "similarity": round(float(edge.get("similarity", 0)), 4),
                        "shared_indicators": edge.get("shared_indicators", []),
                    }
                )
            elif edge["agent2_id"] == agent_id:
                matches.append(
                    {
                        "agent_id": edge["agent1_id"],
                        "agent_name": edge.get("agent1_name", ""),
                        "phronesis": edge.get("agent1_phronesis"),
                        "similarity": round(float(edge.get("similarity", 0)), 4),
                        "shared_indicators": edge.get("shared_indicators", []),
                    }
                )

        matches.sort(key=lambda m: m["similarity"], reverse=True)

        return {
            "agent_id": agent_id,
            "similar_agents": matches,
            "total_matches": len(matches),
        }
    except Exception as exc:
        logger.warning("Failed to find similar agents for %s: %s", agent_id, exc)
        return {"agent_id": agent_id, "similar_agents": [], "total_matches": 0}


async def get_early_warning_indicators() -> dict:
    """Find indicators that appear early in agent timelines and predict trouble.

    Analyzes temporal position of indicator detection vs. later misalignment.
    """
    try:
        async with graph_context() as service:
            warnings = await get_early_warning_data(service)

        return {
            "indicators": warnings,
            "total_indicators": len(warnings),
            "high_risk": [w for w in warnings if w.get("trouble_rate", 0) >= 0.5],
        }
    except Exception as exc:
        logger.warning("Failed to get early warning indicators: %s", exc)
        return {"indicators": [], "total_indicators": 0, "high_risk": []}


async def get_network_topology() -> dict:
    """Get graph size and structure metadata."""
    try:
        async with graph_context() as service:
            stats = await get_topology_stats(service)

        if not stats:
            return {"connected": False}

        return {"connected": True, **stats}
    except Exception as exc:
        logger.warning("Failed to get network topology: %s", exc)
        return {"connected": False}


async def get_sabotage_pathway_status(agent_id: str = "") -> dict:
    """Check sabotage pathway status across agents or for a specific agent.

    Reads EXHIBITS_PATTERN relationships created by detect_patterns().
    """
    try:
        async with graph_context() as service:
            if agent_id:
                pathways = await get_agent_sabotage_status(service, agent_id)
            else:
                pathways = await get_all_sabotage_status(service)

        active = [p for p in pathways if p.get("confidence", 0) >= 0.5]
        emerging = [p for p in pathways if 0 < p.get("confidence", 0) < 0.5]

        return {
            "scope": agent_id or "global",
            "pathways": pathways,
            "active_count": len(active),
            "emerging_count": len(emerging),
            "total_detected": len(pathways),
        }
    except Exception as exc:
        logger.warning("Failed to get sabotage pathway status: %s", exc)
        return {
            "scope": agent_id or "global",
            "pathways": [],
            "active_count": 0,
            "emerging_count": 0,
            "total_detected": 0,
        }


async def compare_agents(agent_id_1: str, agent_id_2: str) -> dict:
    """Compare two agents side-by-side on dimensions, traits, and alignment.

    Pulls parallel subgraphs and computes set differences.
    """
    try:
        async with graph_context() as service:
            profile_1 = await get_agent_profile(service, agent_id_1)
            profile_2 = await get_agent_profile(service, agent_id_2)

        if not profile_1 and not profile_2:
            return {"error": "Neither agent found.", "agent_1": {}, "agent_2": {}}

        # Compute dimension deltas
        dims_1 = profile_1.get("dimension_averages", {})
        dims_2 = profile_2.get("dimension_averages", {})
        dimension_comparison = {}
        for dim in ("ethos", "logos", "pathos"):
            v1 = dims_1.get(dim, 0)
            v2 = dims_2.get(dim, 0)
            dimension_comparison[dim] = {
                "agent_1": round(v1, 4),
                "agent_2": round(v2, 4),
                "delta": round(v1 - v2, 4),
            }

        # Compute trait deltas
        traits_1 = profile_1.get("trait_averages", {})
        traits_2 = profile_2.get("trait_averages", {})
        all_traits = set(traits_1.keys()) | set(traits_2.keys())
        trait_comparison = {}
        for trait in sorted(all_traits):
            v1 = traits_1.get(trait, 0)
            v2 = traits_2.get(trait, 0)
            trait_comparison[trait] = {
                "agent_1": round(v1, 4),
                "agent_2": round(v2, 4),
                "delta": round(v1 - v2, 4),
            }

        # Alignment history comparison
        align_1 = profile_1.get("alignment_history", [])
        align_2 = profile_2.get("alignment_history", [])

        def alignment_rate(history: list) -> float:
            if not history:
                return 0.0
            return round(sum(1 for a in history if a == "aligned") / len(history), 4)

        # Find biggest differences
        biggest_diffs = sorted(
            trait_comparison.items(),
            key=lambda x: abs(x[1]["delta"]),
            reverse=True,
        )[:5]

        return {
            "agent_1": {
                "agent_id": profile_1.get("agent_id", agent_id_1),
                "agent_name": profile_1.get("agent_name", ""),
                "evaluation_count": profile_1.get("evaluation_count", 0),
                "alignment_rate": alignment_rate(align_1),
            },
            "agent_2": {
                "agent_id": profile_2.get("agent_id", agent_id_2),
                "agent_name": profile_2.get("agent_name", ""),
                "evaluation_count": profile_2.get("evaluation_count", 0),
                "alignment_rate": alignment_rate(align_2),
            },
            "dimension_comparison": dimension_comparison,
            "trait_comparison": trait_comparison,
            "biggest_differences": [
                {"trait": name, **vals} for name, vals in biggest_diffs
            ],
        }
    except Exception as exc:
        logger.warning("Failed to compare agents: %s", exc)
        return {"error": "Graph unavailable.", "agent_1": {}, "agent_2": {}}


async def get_cohort_insights() -> CohortInsightsResult:
    """Aggregate cohort insights for the academy dashboard.

    Runs graph queries in parallel: constitutional risk, depth distribution,
    sabotage pathways, alumni averages, and topology stats.
    """
    try:
        async with graph_context() as service:
            (
                constitutional_raw,
                depth_raw,
                sabotage_raw,
                alumni_raw,
                topology,
            ) = await asyncio.gather(
                get_global_constitutional_risk(service),
                get_depth_distribution(service),
                get_all_sabotage_status(service),
                get_alumni_averages(service),
                get_topology_stats(service),
            )

        constitutional = [
            ConstitutionalRiskItem(
                value_name=r.get("value_name", ""),
                priority=r.get("priority", 0),
                impact=r.get("impact", ""),
                trait=r.get("trait", ""),
                polarity=r.get("polarity", ""),
                indicator_name=r.get("indicator_name", ""),
                detection_count=r.get("detection_count", 0),
                agent_count=r.get("agent_count", 0),
                avg_confidence=round(float(r.get("avg_confidence", 0)), 4),
            )
            for r in constitutional_raw
        ]

        depth = DepthDistribution(
            tiers=[
                DepthTierCount(tier=t["tier"], count=t["count"])
                for t in depth_raw.get("tiers", [])
            ],
            statuses=[
                DepthStatusCount(status=s["status"], count=s["count"])
                for s in depth_raw.get("statuses", [])
            ],
        )

        # Aggregate sabotage by pattern (multiple agents may share a pattern)
        pattern_agg: dict[str, dict] = {}
        for row in sabotage_raw:
            pid = row.get("pattern_id", "")
            if not pid:
                continue
            if pid not in pattern_agg:
                pattern_agg[pid] = {
                    "pattern_id": pid,
                    "pattern_name": row.get("pattern_name", ""),
                    "severity": row.get("severity", "info"),
                    "agents": set(),
                    "confidences": [],
                }
            pattern_agg[pid]["agents"].add(row.get("agent_id", ""))
            pattern_agg[pid]["confidences"].append(float(row.get("confidence", 0)))

        sabotage = sorted(
            [
                SabotagePathwaySummary(
                    pattern_id=v["pattern_id"],
                    pattern_name=v["pattern_name"],
                    severity=v["severity"],
                    agent_count=len(v["agents"]),
                    avg_confidence=round(
                        sum(v["confidences"]) / len(v["confidences"]), 4
                    )
                    if v["confidences"]
                    else 0.0,
                )
                for v in pattern_agg.values()
            ],
            key=lambda s: s.agent_count,
            reverse=True,
        )

        alumni = AlumniResult(
            trait_averages=alumni_raw.get("trait_averages", {}),
            total_evaluations=alumni_raw.get("total_evaluations", 0),
        )

        return CohortInsightsResult(
            agent_count=topology.get("agent_count", 0),
            evaluation_count=topology.get("evaluation_count", 0),
            constitutional=constitutional,
            depth=depth,
            sabotage=sabotage,
            alumni=alumni,
        )
    except Exception as exc:
        logger.warning("Failed to get cohort insights: %s", exc)
        return CohortInsightsResult()
