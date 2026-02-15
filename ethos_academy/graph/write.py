"""Graph write operations — store evaluations, merge nodes.

All Cypher for mutations lives here. Uses MERGE for idempotent writes.
Message content is stored for public/consented content only (e.g. Moltbook posts).
"""

from __future__ import annotations

import logging
import math

from ethos_academy.graph.service import GraphService
from ethos_academy.identity.model import parse_model
from ethos_academy.shared.models import AuthenticityResult, EvaluationResult

logger = logging.getLogger(__name__)

_CHECK_DUPLICATE_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation {message_hash: $message_hash})
RETURN e.evaluation_id AS existing_id
LIMIT 1
"""

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
    message_content: $message_content,
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
    direction: $direction,
    intent_rhetorical_mode: $intent_rhetorical_mode,
    intent_primary_intent: $intent_primary_intent,
    intent_cost_to_reader: $intent_cost_to_reader,
    intent_stakes_reality: $intent_stakes_reality,
    intent_proportionality: $intent_proportionality,
    intent_persona_type: $intent_persona_type,
    intent_relational_quality: $intent_relational_quality,
    scoring_reasoning: $scoring_reasoning,
    created_at: datetime(),
    message_timestamp: CASE WHEN $message_timestamp <> '' THEN datetime($message_timestamp) ELSE null END
})
CREATE (a)-[:EVALUATED]->(e)

WITH a, e
OPTIONAL MATCH (a)-[:EVALUATED]->(prev:Evaluation)
WHERE prev.evaluation_id <> e.evaluation_id
WITH e, prev ORDER BY coalesce(prev.message_timestamp, prev.created_at) DESC LIMIT 1
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


async def store_evaluation(
    service: GraphService,
    agent_id: str,
    result: EvaluationResult,
    message_hash: str = "",
    message_content: str = "",
    phronesis: str = "undetermined",
    agent_name: str = "",
    agent_specialty: str = "",
    message_timestamp: str = "",
    direction: str | None = None,
) -> None:
    """Store an evaluation in the graph. Merges Agent, creates Evaluation node.

    Fails silently if Neo4j is down.
    Creates DETECTED relationships for any detected_indicators.
    Updates Agent aggregate fields (phronesis_score, phronesis_trend).
    Skips duplicate evaluations (same message_hash for same agent).
    """
    if not service.connected:
        return

    # Skip duplicate evaluations (same message for same agent)
    if message_hash:
        try:
            records, _, _ = await service.execute_query(
                _CHECK_DUPLICATE_QUERY,
                {"agent_id": agent_id, "message_hash": message_hash},
            )
            if records:
                logger.info(
                    "Skipping duplicate evaluation (agent=%s, hash=%s)",
                    agent_id[:8],
                    message_hash[:8],
                )
                return
        except Exception as exc:
            logger.debug(
                "Duplicate check failed (%s), proceeding with creation: %s",
                type(exc).__name__,
                exc,
            )

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
    all_trait_scores = [
        _get_trait_score(result, t)
        for t in [
            "virtue",
            "goodwill",
            "manipulation",
            "deception",
            "accuracy",
            "reasoning",
            "fabrication",
            "broken_logic",
            "recognition",
            "compassion",
            "dismissal",
            "exploitation",
        ]
    ]
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
        "agent_id": agent_id,
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
        "message_content": message_content,
        "routing_tier": result.routing_tier,
        "keyword_density": result.keyword_density,
        "model_used": result.model_used,
        "agent_model": parse_model(result.agent_model) if result.agent_model else "",
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
        "message_timestamp": message_timestamp,
        "direction": direction or "",
        "intent_rhetorical_mode": (
            result.intent_classification.rhetorical_mode
            if result.intent_classification
            else ""
        ),
        "intent_primary_intent": (
            result.intent_classification.primary_intent
            if result.intent_classification
            else ""
        ),
        "intent_cost_to_reader": (
            result.intent_classification.cost_to_reader
            if result.intent_classification
            else ""
        ),
        "intent_stakes_reality": (
            result.intent_classification.stakes_reality
            if result.intent_classification
            else ""
        ),
        "intent_proportionality": (
            result.intent_classification.proportionality
            if result.intent_classification
            else ""
        ),
        "intent_persona_type": (
            result.intent_classification.persona_type
            if result.intent_classification
            else ""
        ),
        "intent_relational_quality": (
            result.intent_classification.relational_quality
            if result.intent_classification
            else ""
        ),
        "scoring_reasoning": result.scoring_reasoning or "",
    }

    try:
        await service.execute_query(_STORE_EVALUATION_QUERY, params)
    except (ConnectionError, OSError) as exc:
        logger.warning("Failed to store evaluation (%s): %s", type(exc).__name__, exc)
    except Exception as exc:
        logger.error("Failed to store evaluation (%s): %s", type(exc).__name__, exc)


_STORE_AUTHENTICITY_QUERY = """
MATCH (a:Agent) WHERE a.agent_name = $agent_name
SET a.authenticity_score = $authenticity_score,
    a.authenticity_classification = $classification
RETURN a.agent_name AS matched
"""


_UPDATE_SPECIALTY_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})
SET a.agent_specialty = $agent_specialty
RETURN a.agent_id AS updated
"""


async def update_agent_specialty(
    service: GraphService,
    agent_id: str,
    agent_specialty: str,
) -> bool:
    """Update the agent_specialty field on an existing Agent node.

    Returns True if the node was found and updated, False otherwise.
    """
    if not service.connected:
        return False

    try:
        records, _, _ = await service.execute_query(
            _UPDATE_SPECIALTY_QUERY,
            {"agent_id": agent_id, "agent_specialty": agent_specialty},
        )
        return bool(records)
    except Exception as exc:
        logger.warning("Failed to update specialty for %s: %s", agent_id, exc)
        return False


async def store_authenticity(
    service: GraphService,
    agent_name: str,
    result: AuthenticityResult,
) -> None:
    """Store authenticity score on an existing Agent node.

    Uses MATCH on agent_name (not MERGE) to avoid creating duplicate
    Agent nodes — existing nodes are keyed by agent_id.
    If no Agent node matches, logs a warning and skips.
    """
    if not service.connected:
        return

    try:
        records, _, _ = await service.execute_query(
            _STORE_AUTHENTICITY_QUERY,
            {
                "agent_name": agent_name,
                "authenticity_score": result.authenticity_score,
                "classification": result.classification,
            },
        )
        if not records:
            logger.info(
                "No Agent node found for agent_name=%s — skipping authenticity store",
                agent_name,
            )
    except (ConnectionError, OSError) as exc:
        logger.warning(
            "Failed to store authenticity for %s (%s): %s",
            agent_name,
            type(exc).__name__,
            exc,
        )
    except Exception as exc:
        logger.error(
            "Failed to store authenticity for %s (%s): %s",
            agent_name,
            type(exc).__name__,
            exc,
        )


async def reset_agent_evaluations(agent_id: str) -> int:
    """Delete all evaluations for an agent, keeping the Agent node.

    Returns the number of evaluations deleted.
    """
    from ethos_academy.graph.service import graph_context

    async with graph_context() as service:
        if not service.connected:
            return 0

        records, _, _ = await service.execute_query(
            """
            MATCH (a:Agent {agent_id: $agent_id})-[r:EVALUATED]->(e:Evaluation)
            OPTIONAL MATCH (e)-[r2]-()
            WITH e, r, collect(r2) AS rels
            FOREACH (rel IN rels | DELETE rel)
            DELETE r, e
            RETURN count(e) AS deleted
            """,
            {"agent_id": agent_id},
        )
        deleted = records[0]["deleted"] if records else 0

        # Clean up orphaned Pattern nodes
        await service.execute_query("MATCH (p:Pattern) WHERE NOT (p)--() DELETE p")

        logger.info("Reset %d evaluations for agent %s", deleted, agent_id)
        return deleted
