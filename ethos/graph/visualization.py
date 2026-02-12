"""Graph visualization queries — pull subgraph data for NVL rendering.

Three query groups composed together:
1. Semantic layer: Dimensions, Traits, ConstitutionalValues, Patterns, Indicators
2. Episodic layer: Agents with recent evaluations and detected indicators
3. Indicator backbone: Only indicators with DETECTED relationships
"""

from __future__ import annotations

import logging

from ethos.graph.service import GraphService

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
       e.evaluation_id AS eval_id,
       e.ethos AS eval_ethos, e.logos AS eval_logos, e.pathos AS eval_pathos,
       e.alignment_status AS eval_alignment,
       e.phronesis AS eval_phronesis,
       e.created_at AS eval_created,
       i.id AS detected_indicator_id,
       d.confidence AS detected_confidence
"""

# ── Indicator Backbone ──────────────────────────────────────────────────────
# Only indicators that have at least one DETECTED relationship

_DETECTED_INDICATORS_BACKBONE_QUERY = """
MATCH (e:Evaluation)-[:DETECTED]->(i:Indicator)-[:BELONGS_TO]->(t:Trait)
WITH DISTINCT i, t
RETURN i.id AS indicator_id, i.name AS indicator_name,
       i.trait AS indicator_trait, t.name AS trait_name
"""


def get_semantic_layer(service: GraphService) -> dict:
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
        records, _, _ = service.execute_query(_DIMENSIONS_AND_TRAITS_QUERY)
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
                result["trait_dimension_rels"].append({
                    "trait": trait_name,
                    "dimension": dim_name,
                })

        # Constitutional Values + UPHOLDS
        records, _, _ = service.execute_query(_CONSTITUTIONAL_VALUES_QUERY)
        for rec in records:
            cv_name = rec.get("cv_name", "")
            if cv_name and cv_name not in result["constitutional_values"]:
                result["constitutional_values"][cv_name] = {
                    "name": cv_name,
                    "priority": rec.get("cv_priority", 0),
                }

            trait_name = rec.get("trait_name", "")
            if trait_name and cv_name:
                result["upholds_rels"].append({
                    "trait": trait_name,
                    "cv": cv_name,
                    "relationship": rec.get("upholds_rel", ""),
                })

        # Patterns + COMPOSED_OF → Indicators
        records, _, _ = service.execute_query(_PATTERNS_AND_INDICATORS_QUERY)
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
                result["pattern_indicator_rels"].append({
                    "pattern": pattern_id,
                    "indicator": indicator_id,
                })

    except Exception as exc:
        logger.warning("Failed to get semantic layer: %s", exc)

    return result


def get_episodic_layer(service: GraphService) -> dict:
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
        records, _, _ = service.execute_query(_AGENTS_AND_EVALUATIONS_QUERY)
        for rec in records:
            agent_id = rec.get("agent_id", "")
            if agent_id and agent_id not in result["agents"]:
                # Determine alignment from latest eval
                result["agents"][agent_id] = {
                    "agent_id": agent_id,
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
                        "created_at": str(rec.get("eval_created", "")),
                    }

                # Agent → Evaluation rel (deduplicate)
                rel_key = (agent_id, eval_id)
                if rel_key not in {
                    (r["agent"], r["evaluation"])
                    for r in result["evaluated_rels"]
                }:
                    result["evaluated_rels"].append({
                        "agent": agent_id,
                        "evaluation": eval_id,
                    })

                # Evaluation → Indicator detected rel
                indicator_id = rec.get("detected_indicator_id")
                if indicator_id:
                    det_key = (eval_id, indicator_id)
                    if det_key not in {
                        (r["evaluation"], r["indicator"])
                        for r in result["detected_rels"]
                    }:
                        result["detected_rels"].append({
                            "evaluation": eval_id,
                            "indicator": indicator_id,
                            "confidence": rec.get("detected_confidence", 0.0),
                        })

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


def get_indicator_backbone(service: GraphService) -> dict:
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
        records, _, _ = service.execute_query(_DETECTED_INDICATORS_BACKBONE_QUERY)
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
                    (r["indicator"], r["trait"])
                    for r in result["indicator_trait_rels"]
                }:
                    result["indicator_trait_rels"].append({
                        "indicator": indicator_id,
                        "trait": trait_name,
                    })

    except Exception as exc:
        logger.warning("Failed to get indicator backbone: %s", exc)

    return result
