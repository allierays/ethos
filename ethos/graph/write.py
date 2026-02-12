"""Graph write operations — store evaluations, merge nodes.

All Cypher for mutations lives here. Uses MERGE for idempotent writes.
Message content is NEVER stored — only scores, hashes, and metadata.
"""

from __future__ import annotations

import logging
import math

from ethos.graph.service import GraphService
from ethos.identity.hashing import hash_agent_id
from ethos.shared.models import EvaluationResult

logger = logging.getLogger(__name__)

_STORE_EVALUATION_QUERY = """
MERGE (a:Agent {agent_id: $agent_id})
ON CREATE SET a.created_at = datetime(), a.evaluation_count = 0
SET a.evaluation_count = a.evaluation_count + 1,
    a.agent_model = CASE WHEN $agent_model <> '' THEN $agent_model ELSE a.agent_model END,
    a.agent_name = CASE WHEN $agent_name <> '' THEN $agent_name ELSE coalesce(a.agent_name, '') END,
    a.agent_specialty = CASE WHEN $agent_specialty <> '' THEN $agent_specialty ELSE coalesce(a.agent_specialty, '') END,
    a.phronesis_score = $phronesis_score,
    a.phronesis_trend = $phronesis_trend,
    a.trait_variance = $trait_variance,
    a.balance_score = $balance_score

CREATE (e:Evaluation {
    evaluation_id: $evaluation_id,
    ethos: $ethos,
    logos: $logos,
    pathos: $pathos,
    phronesis: $phronesis,
    alignment_status: $alignment_status,
    flags: $flags,
    message_hash: $message_hash,
    routing_tier: $routing_tier,
    keyword_density: $keyword_density,
    model_used: $model_used,
    phronesis_score: $phronesis_score,
    trait_virtue: $trait_virtue,
    trait_goodwill: $trait_goodwill,
    trait_manipulation: $trait_manipulation,
    trait_deception: $trait_deception,
    trait_accuracy: $trait_accuracy,
    trait_reasoning: $trait_reasoning,
    trait_fabrication: $trait_fabrication,
    trait_broken_logic: $trait_broken_logic,
    trait_recognition: $trait_recognition,
    trait_compassion: $trait_compassion,
    trait_dismissal: $trait_dismissal,
    trait_exploitation: $trait_exploitation,
    agent_model: $agent_model,
    created_at: datetime()
})
CREATE (a)-[:EVALUATED]->(e)

WITH a, e
OPTIONAL MATCH (a)-[:EVALUATED]->(prev:Evaluation)
WHERE prev.evaluation_id <> e.evaluation_id
WITH e, prev ORDER BY prev.created_at DESC LIMIT 1
FOREACH (_ IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
    CREATE (prev)-[:PRECEDES]->(e)
)

WITH e
UNWIND CASE WHEN size($indicators) > 0 THEN $indicators ELSE [null] END AS ind
WITH e, ind WHERE ind IS NOT NULL
MATCH (indicator:Indicator {id: ind.id})
CREATE (e)-[:DETECTED {
    confidence: ind.confidence,
    severity: ind.severity,
    evidence: ind.evidence
}]->(indicator)
"""


def _get_trait_score(result: EvaluationResult, trait_name: str) -> float:
    """Extract a trait score from the result, defaulting to 0.0."""
    if trait_name in result.traits:
        return result.traits[trait_name].score
    return 0.0


def store_evaluation(
    service: GraphService,
    raw_agent_id: str,
    result: EvaluationResult,
    message_hash: str = "",
    phronesis: str = "undetermined",
    agent_name: str = "",
    agent_specialty: str = "",
) -> None:
    """Store an evaluation in the graph. Merges Agent, creates Evaluation node.

    Agent ID is hashed before storage. Fails silently if Neo4j is down.
    Creates DETECTED relationships for any detected_indicators.
    Updates Agent aggregate fields (phronesis_score, phronesis_trend).
    """
    if not service.connected:
        return

    hashed_id = hash_agent_id(raw_agent_id)

    # Compute agent-level phronesis_score as running avg of 3 dimensions
    phronesis_score = round((result.ethos + result.logos + result.pathos) / 3.0, 4)

    # Compute balance_score: how balanced across dimensions (1.0 = perfectly balanced)
    scores = [result.ethos, result.logos, result.pathos]
    mean = sum(scores) / 3.0
    if mean > 0:
        variance = sum((s - mean) ** 2 for s in scores) / 3.0
        std_dev = math.sqrt(variance)
        balance_score = round(max(0.0, min(1.0, 1.0 - (std_dev / mean))), 4)
    else:
        balance_score = 0.0

    # Compute trait_variance: spread across all 12 trait scores
    all_trait_scores = [_get_trait_score(result, t) for t in [
        "virtue", "goodwill", "manipulation", "deception",
        "accuracy", "reasoning", "fabrication", "broken_logic",
        "recognition", "compassion", "dismissal", "exploitation",
    ]]
    trait_mean = sum(all_trait_scores) / len(all_trait_scores)
    trait_variance = round(
        sum((s - trait_mean) ** 2 for s in all_trait_scores) / len(all_trait_scores),
        4,
    )

    # Build indicators list for UNWIND
    indicators = [
        {
            "id": ind.id,
            "confidence": ind.confidence,
            "severity": ind.severity,
            "evidence": ind.evidence,
        }
        for ind in result.detected_indicators
    ]

    params = {
        "agent_id": hashed_id,
        "agent_name": agent_name,
        "agent_specialty": agent_specialty,
        "evaluation_id": result.evaluation_id,
        "ethos": result.ethos,
        "logos": result.logos,
        "pathos": result.pathos,
        "phronesis": phronesis,
        "phronesis_score": phronesis_score,
        "flags": result.flags,
        "message_hash": message_hash,
        "routing_tier": result.routing_tier,
        "keyword_density": result.keyword_density,
        "model_used": result.model_used,
        "agent_model": result.agent_model,
        "alignment_status": result.alignment_status,
        "phronesis_trend": "insufficient_data",
        "trait_variance": trait_variance,
        "balance_score": balance_score,
        "indicators": indicators,
        "trait_virtue": _get_trait_score(result, "virtue"),
        "trait_goodwill": _get_trait_score(result, "goodwill"),
        "trait_manipulation": _get_trait_score(result, "manipulation"),
        "trait_deception": _get_trait_score(result, "deception"),
        "trait_accuracy": _get_trait_score(result, "accuracy"),
        "trait_reasoning": _get_trait_score(result, "reasoning"),
        "trait_fabrication": _get_trait_score(result, "fabrication"),
        "trait_broken_logic": _get_trait_score(result, "broken_logic"),
        "trait_recognition": _get_trait_score(result, "recognition"),
        "trait_compassion": _get_trait_score(result, "compassion"),
        "trait_dismissal": _get_trait_score(result, "dismissal"),
        "trait_exploitation": _get_trait_score(result, "exploitation"),
    }

    try:
        service.execute_query(_STORE_EVALUATION_QUERY, params)
    except Exception as exc:
        logger.warning("Failed to store evaluation: %s", exc)
