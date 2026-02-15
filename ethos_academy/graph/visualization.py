"""Graph visualization queries — pull subgraph data for NVL rendering.

Three query groups composed together:
1. Semantic layer: Dimensions, Traits, ConstitutionalValues, Patterns, Indicators
2. Episodic layer: Agents with recent evaluations and detected indicators
3. Indicator backbone: Only indicators with DETECTED relationships
"""

from __future__ import annotations

import logging

from ethos_academy.graph.service import GraphService

logger = logging.getLogger(__name__)

# ── Semantic Layer ──────────────────────────────────────────────────────────

_DIMENSIONS_AND_TRAITS_QUERY = """
MATCH (d:Dimension)<-[:BELONGS_TO]-(t:Trait)
RETURN d.name AS dim_name, d.greek AS dim_greek, d.description AS dim_desc,
       t.name AS trait_name, t.dimension AS trait_dim, t.polarity AS trait_polarity
"""

_CONSTITUTIONAL_VALUES_QUERY = """
MATCH (t:Trait)-[u:UPHOLDS]->(cv:ConstitutionalValue)
RETURN t.name AS trait_name,
       cv.name AS cv_name, cv.priority AS cv_priority,
       u.relationship AS upholds_rel
"""

_PATTERNS_AND_INDICATORS_QUERY = """
MATCH (p:Pattern)-[:COMPOSED_OF]->(i:Indicator)
RETURN p.pattern_id AS pattern_id, p.name AS pattern_name,
       p.description AS pattern_desc, p.severity AS pattern_severity,
       p.stage_count AS pattern_stage_count,
       i.id AS indicator_id, i.name AS indicator_name, i.trait AS indicator_trait
"""

# ── Episodic Layer ──────────────────────────────────────────────────────────

_AGENTS_AND_EVALUATIONS_QUERY = """
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WITH a, e ORDER BY e.created_at DESC
WITH a, collect(e)[0..3] AS recent_evals
UNWIND recent_evals AS e
OPTIONAL MATCH (e)-[d:DETECTED]->(i:Indicator)
RETURN a.agent_id AS agent_id,
       a.evaluation_count AS agent_eval_count,
       a.phronesis_score AS agent_phronesis,
       a.phronesis_trend AS agent_trend,
       a.agent_name AS agent_name,
       e.evaluation_id AS eval_id,
       e.ethos AS eval_ethos, e.logos AS eval_logos, e.pathos AS eval_pathos,
       e.alignment_status AS eval_alignment,
       e.phronesis AS eval_phronesis,
       e.model_used AS eval_model,
       e.created_at AS eval_created,
       i.id AS detected_indicator_id,
       d.confidence AS detected_confidence
"""

# ── PRECEDES (evaluation timeline) ────────────────────────────────────────

_PRECEDES_QUERY = """
MATCH (e1:Evaluation)-[:PRECEDES]->(e2:Evaluation)
RETURN e1.evaluation_id AS from_eval, e2.evaluation_id AS to_eval
"""

# ── Agent Dimension Graph ─────────────────────────────────────────────────
# Focused query: agents with average dimension scores for force-directed clustering

_AGENT_DIMENSION_QUERY = """
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WITH a, e ORDER BY e.created_at DESC
WITH a,
     count(e) AS eval_count,
     avg(e.ethos) AS avg_ethos,
     avg(e.logos) AS avg_logos,
     avg(e.pathos) AS avg_pathos,
     head(collect(e.model_used)) AS latest_model,
     head(collect(e.alignment_status)) AS latest_alignment
RETURN a.agent_id AS agent_id,
       a.agent_name AS agent_name,
       a.phronesis_score AS phronesis_score,
       eval_count,
       avg_ethos, avg_logos, avg_pathos,
       latest_model,
       latest_alignment
"""

# ── Indicator Frequency Graph ─────────────────────────────────────────────
# Full taxonomy (dimensions → traits → indicators) with detection counts

_INDICATOR_FREQUENCY_QUERY = """
MATCH (d:Dimension)<-[:BELONGS_TO]-(t:Trait)<-[:BELONGS_TO]-(i:Indicator)
OPTIONAL MATCH (e:Evaluation)-[det:DETECTED]->(i)
WITH d, t, i, count(det) AS det_count, count(DISTINCT e) AS eval_count
RETURN d.name AS dimension, d.greek AS dim_greek,
       t.name AS trait, t.polarity AS trait_polarity,
       i.id AS indicator_id, i.name AS indicator_name,
       det_count, eval_count
ORDER BY d.name, t.name, det_count DESC
"""

_AGENT_INDICATOR_QUERY = """
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)-[:DETECTED]->(i:Indicator)
WITH a, i, count(e) AS times_detected
RETURN a.agent_id AS agent_id, a.agent_name AS agent_name,
       a.phronesis_score AS phronesis_score,
       i.id AS indicator_id, times_detected
ORDER BY a.agent_id, times_detected DESC
"""

# ── Indicator Backbone ──────────────────────────────────────────────────────
# Only indicators that have at least one DETECTED relationship

_DETECTED_INDICATORS_BACKBONE_QUERY = """
MATCH (e:Evaluation)-[:DETECTED]->(i:Indicator)-[:BELONGS_TO]->(t:Trait)
WITH DISTINCT i, t
RETURN i.id AS indicator_id, i.name AS indicator_name,
       i.trait AS indicator_trait, t.name AS trait_name
"""


async def get_semantic_layer(service: GraphService) -> dict:
    """Pull dimensions, traits, constitutional values, and patterns.

    Returns dict with keys: dimensions, traits, trait_dimension_rels,
    constitutional_values, upholds_rels, patterns, pattern_indicator_rels.
    """
    result: dict = {
        "dimensions": {},
        "traits": {},
        "trait_dimension_rels": [],
        "constitutional_values": {},
        "upholds_rels": [],
        "patterns": {},
        "pattern_indicator_rels": [],
    }

    if not service.connected:
        return result

    try:
        # Dimensions + Traits
        records, _, _ = await service.execute_query(_DIMENSIONS_AND_TRAITS_QUERY)
        for rec in records:
            dim_name = rec.get("dim_name", "")
            if dim_name and dim_name not in result["dimensions"]:
                result["dimensions"][dim_name] = {
                    "name": dim_name,
                    "greek": rec.get("dim_greek", ""),
                    "description": rec.get("dim_desc", ""),
                }

            trait_name = rec.get("trait_name", "")
            if trait_name and trait_name not in result["traits"]:
                result["traits"][trait_name] = {
                    "name": trait_name,
                    "dimension": rec.get("trait_dim", ""),
                    "polarity": rec.get("trait_polarity", ""),
                }

            if dim_name and trait_name:
                result["trait_dimension_rels"].append(
                    {
                        "trait": trait_name,
                        "dimension": dim_name,
                    }
                )

        # Constitutional Values + UPHOLDS
        records, _, _ = await service.execute_query(_CONSTITUTIONAL_VALUES_QUERY)
        for rec in records:
            cv_name = rec.get("cv_name", "")
            if cv_name and cv_name not in result["constitutional_values"]:
                result["constitutional_values"][cv_name] = {
                    "name": cv_name,
                    "priority": rec.get("cv_priority", 0),
                }

            trait_name = rec.get("trait_name", "")
            if trait_name and cv_name:
                result["upholds_rels"].append(
                    {
                        "trait": trait_name,
                        "cv": cv_name,
                        "relationship": rec.get("upholds_rel", ""),
                    }
                )

        # Patterns + COMPOSED_OF → Indicators
        records, _, _ = await service.execute_query(_PATTERNS_AND_INDICATORS_QUERY)
        for rec in records:
            pattern_id = rec.get("pattern_id", "")
            if pattern_id and pattern_id not in result["patterns"]:
                result["patterns"][pattern_id] = {
                    "pattern_id": pattern_id,
                    "name": rec.get("pattern_name", ""),
                    "description": rec.get("pattern_desc", ""),
                    "severity": rec.get("pattern_severity", "info"),
                    "stage_count": rec.get("pattern_stage_count", 0),
                }

            indicator_id = rec.get("indicator_id", "")
            if pattern_id and indicator_id:
                result["pattern_indicator_rels"].append(
                    {
                        "pattern": pattern_id,
                        "indicator": indicator_id,
                    }
                )

    except Exception as exc:
        logger.warning("Failed to get semantic layer: %s", exc)

    return result


async def get_episodic_layer(service: GraphService) -> dict:
    """Pull agents, their recent evaluations, and detected indicators.

    Returns dict with keys: agents, evaluations, evaluated_rels, detected_rels.
    """
    result: dict = {
        "agents": {},
        "evaluations": {},
        "evaluated_rels": [],
        "detected_rels": [],
    }

    if not service.connected:
        return result

    try:
        records, _, _ = await service.execute_query(_AGENTS_AND_EVALUATIONS_QUERY)
        for rec in records:
            agent_id = rec.get("agent_id", "")
            if agent_id and agent_id not in result["agents"]:
                # Determine alignment from latest eval
                result["agents"][agent_id] = {
                    "agent_id": agent_id,
                    "agent_name": rec.get("agent_name"),
                    "evaluation_count": rec.get("agent_eval_count", 0),
                    "phronesis_score": rec.get("agent_phronesis"),
                    "phronesis_trend": rec.get("agent_trend", "insufficient_data"),
                }

            eval_id = rec.get("eval_id", "")
            if eval_id:
                if eval_id not in result["evaluations"]:
                    result["evaluations"][eval_id] = {
                        "evaluation_id": eval_id,
                        "ethos": rec.get("eval_ethos", 0.0),
                        "logos": rec.get("eval_logos", 0.0),
                        "pathos": rec.get("eval_pathos", 0.0),
                        "alignment_status": rec.get("eval_alignment", "unknown"),
                        "phronesis": rec.get("eval_phronesis", "undetermined"),
                        "model_used": rec.get("eval_model", ""),
                        "created_at": str(rec.get("eval_created", "")),
                    }

                # Agent → Evaluation rel (deduplicate)
                rel_key = (agent_id, eval_id)
                if rel_key not in {
                    (r["agent"], r["evaluation"]) for r in result["evaluated_rels"]
                }:
                    result["evaluated_rels"].append(
                        {
                            "agent": agent_id,
                            "evaluation": eval_id,
                        }
                    )

                # Evaluation → Indicator detected rel
                indicator_id = rec.get("detected_indicator_id")
                if indicator_id:
                    det_key = (eval_id, indicator_id)
                    if det_key not in {
                        (r["evaluation"], r["indicator"])
                        for r in result["detected_rels"]
                    }:
                        result["detected_rels"].append(
                            {
                                "evaluation": eval_id,
                                "indicator": indicator_id,
                                "confidence": rec.get("detected_confidence", 0.0),
                            }
                        )

        # Update agents with alignment_status from their most recent eval
        for rec in records:
            agent_id = rec.get("agent_id", "")
            if agent_id and agent_id in result["agents"]:
                alignment = rec.get("eval_alignment")
                if alignment and "alignment_status" not in result["agents"][agent_id]:
                    result["agents"][agent_id]["alignment_status"] = alignment

        # Set alignment_status default for agents that didn't get one
        for agent in result["agents"].values():
            if "alignment_status" not in agent:
                agent["alignment_status"] = "unknown"

    except Exception as exc:
        logger.warning("Failed to get episodic layer: %s", exc)

    return result


async def get_agent_indicator_data(service: GraphService) -> list[dict]:
    """Get agent-to-indicator detection pairs."""
    if not service.connected:
        return []
    try:
        records, _, _ = await service.execute_query(_AGENT_INDICATOR_QUERY)
        return [
            {
                "agent_id": rec["agent_id"],
                "agent_name": rec.get("agent_name"),
                "phronesis_score": rec.get("phronesis_score"),
                "indicator_id": rec["indicator_id"],
                "times_detected": rec.get("times_detected", 0),
            }
            for rec in records
            if rec.get("agent_id") and rec.get("indicator_id")
        ]
    except Exception as exc:
        logger.warning("Failed to get agent indicator data: %s", exc)
        return []


async def get_indicator_frequency_data(service: GraphService) -> list[dict]:
    """Get full taxonomy with detection counts for each indicator."""
    if not service.connected:
        return []
    try:
        records, _, _ = await service.execute_query(_INDICATOR_FREQUENCY_QUERY)
        return [
            {
                "dimension": rec["dimension"],
                "dim_greek": rec.get("dim_greek", ""),
                "trait": rec["trait"],
                "trait_polarity": rec.get("trait_polarity", "positive"),
                "indicator_id": rec["indicator_id"],
                "indicator_name": rec["indicator_name"],
                "det_count": rec.get("det_count", 0),
                "eval_count": rec.get("eval_count", 0),
            }
            for rec in records
            if rec.get("indicator_id")
        ]
    except Exception as exc:
        logger.warning("Failed to get indicator frequency data: %s", exc)
        return []


async def get_agent_dimension_data(service: GraphService) -> list[dict]:
    """Get agents with their average dimension scores for the force graph."""
    if not service.connected:
        return []
    try:
        records, _, _ = await service.execute_query(_AGENT_DIMENSION_QUERY)
        return [
            {
                "agent_id": rec["agent_id"],
                "agent_name": rec.get("agent_name"),
                "phronesis_score": rec.get("phronesis_score"),
                "eval_count": rec.get("eval_count", 0),
                "avg_ethos": rec.get("avg_ethos", 0.0),
                "avg_logos": rec.get("avg_logos", 0.0),
                "avg_pathos": rec.get("avg_pathos", 0.0),
                "latest_model": rec.get("latest_model", ""),
                "latest_alignment": rec.get("latest_alignment", "unknown"),
            }
            for rec in records
            if rec.get("agent_id")
        ]
    except Exception as exc:
        logger.warning("Failed to get agent dimension data: %s", exc)
        return []


async def get_precedes_rels(service: GraphService) -> list[dict]:
    """Pull PRECEDES relationships between evaluations."""
    if not service.connected:
        return []

    try:
        records, _, _ = await service.execute_query(_PRECEDES_QUERY)
        return [
            {"from_eval": rec["from_eval"], "to_eval": rec["to_eval"]}
            for rec in records
            if rec.get("from_eval") and rec.get("to_eval")
        ]
    except Exception as exc:
        logger.warning("Failed to get precedes rels: %s", exc)
        return []


# ── Constitutional Trail (5-hop path: Agent→Eval→Indicator→Trait→CV) ──────

_CONSTITUTIONAL_TRAIL_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
      -[d:DETECTED]->(i:Indicator)-[:BELONGS_TO]->(t:Trait)
      -[u:UPHOLDS]->(cv:ConstitutionalValue)
WITH cv, t, i, u.relationship AS impact,
     count(DISTINCT e) AS eval_count,
     avg(d.confidence) AS avg_confidence,
     collect(DISTINCT d.evidence)[..3] AS sample_evidence
RETURN cv.name AS cv_name, cv.priority AS cv_priority,
       impact, t.name AS trait_name, t.polarity AS trait_polarity,
       i.id AS indicator_id, i.name AS indicator_name,
       eval_count, avg_confidence, sample_evidence
ORDER BY cv.priority ASC, eval_count DESC
"""


async def get_constitutional_trail(service: GraphService, agent_id: str) -> list[dict]:
    """Trace Agent -> Evaluation -> Indicator -> Trait -> ConstitutionalValue."""
    if not service.connected:
        return []
    try:
        records, _, _ = await service.execute_query(
            _CONSTITUTIONAL_TRAIL_QUERY, {"agent_id": agent_id}
        )
        return [
            {
                "constitutional_value": rec.get("cv_name", ""),
                "cv_priority": rec.get("cv_priority", 0),
                "impact": rec.get("impact", ""),
                "trait": rec.get("trait_name", ""),
                "trait_polarity": rec.get("trait_polarity", ""),
                "indicator_id": rec.get("indicator_id", ""),
                "indicator_name": rec.get("indicator_name", ""),
                "eval_count": rec.get("eval_count", 0),
                "avg_confidence": rec.get("avg_confidence", 0.0),
                "sample_evidence": [e for e in (rec.get("sample_evidence") or []) if e],
            }
            for rec in records
        ]
    except Exception as exc:
        logger.warning("Failed to get constitutional trail: %s", exc)
        return []


# ── Behavioral Similarity (Jaccard over shared indicators) ────────────────

_SIMILARITY_QUERY = """
MATCH (a:Agent)-[:EVALUATED]->(:Evaluation)-[:DETECTED]->(i:Indicator)
WITH a, collect(DISTINCT i.id) AS indicators
WHERE size(indicators) > 0
WITH collect({agent_id: a.agent_id, agent_name: a.agent_name,
              phronesis: a.phronesis_score, indicators: indicators}) AS agents
UNWIND range(0, size(agents) - 2) AS idx1
UNWIND range(idx1 + 1, size(agents) - 1) AS idx2
WITH agents[idx1] AS a1, agents[idx2] AS a2
WITH a1, a2,
     [x IN a1.indicators WHERE x IN a2.indicators] AS shared
WITH a1, a2, shared,
     toFloat(size(shared)) /
       (size(a1.indicators) + size(a2.indicators) - size(shared)) AS jaccard
WHERE jaccard > 0.15
RETURN a1.agent_id AS agent1_id, a1.agent_name AS agent1_name,
       a1.phronesis AS agent1_phronesis,
       a2.agent_id AS agent2_id, a2.agent_name AS agent2_name,
       a2.phronesis AS agent2_phronesis,
       jaccard AS similarity, shared AS shared_indicators
ORDER BY jaccard DESC
"""


async def get_similarity_data(service: GraphService) -> list[dict]:
    """Compute Jaccard similarity between agents over shared indicators."""
    if not service.connected:
        return []
    try:
        records, _, _ = await service.execute_query(_SIMILARITY_QUERY)
        return [
            {
                "agent1_id": rec.get("agent1_id", ""),
                "agent1_name": rec.get("agent1_name", ""),
                "agent1_phronesis": rec.get("agent1_phronesis"),
                "agent2_id": rec.get("agent2_id", ""),
                "agent2_name": rec.get("agent2_name", ""),
                "agent2_phronesis": rec.get("agent2_phronesis"),
                "similarity": rec.get("similarity", 0.0),
                "shared_indicators": rec.get("shared_indicators", []),
            }
            for rec in records
        ]
    except Exception as exc:
        logger.warning("Failed to get similarity data: %s", exc)
        return []


async def get_indicator_backbone(service: GraphService) -> dict:
    """Pull only indicators that have at least one DETECTED relationship.

    Returns dict with keys: indicators, indicator_trait_rels.
    """
    result: dict = {
        "indicators": {},
        "indicator_trait_rels": [],
    }

    if not service.connected:
        return result

    try:
        records, _, _ = await service.execute_query(_DETECTED_INDICATORS_BACKBONE_QUERY)
        for rec in records:
            indicator_id = rec.get("indicator_id", "")
            if indicator_id and indicator_id not in result["indicators"]:
                result["indicators"][indicator_id] = {
                    "id": indicator_id,
                    "name": rec.get("indicator_name", ""),
                    "trait": rec.get("indicator_trait", ""),
                }

            trait_name = rec.get("trait_name", "")
            if indicator_id and trait_name:
                rel_key = (indicator_id, trait_name)
                if rel_key not in {
                    (r["indicator"], r["trait"]) for r in result["indicator_trait_rels"]
                }:
                    result["indicator_trait_rels"].append(
                        {
                            "indicator": indicator_id,
                            "trait": trait_name,
                        }
                    )

    except Exception as exc:
        logger.warning("Failed to get indicator backbone: %s", exc)

    return result
