"""Graph read operations — query evaluations and agent profiles.

All Cypher for reads lives here. Returns graceful defaults when Neo4j is down.
"""

from __future__ import annotations

import logging

from ethos_academy.graph.service import GraphService
from ethos_academy.shared.analysis import TRAIT_NAMES

logger = logging.getLogger(__name__)

_AGENT_AVG_FIELDS = """,
     avg(e.ethos) AS avg_ethos, avg(e.logos) AS avg_logos, avg(e.pathos) AS avg_pathos,
     avg(e.trait_virtue) AS avg_virtue, avg(e.trait_goodwill) AS avg_goodwill,
     avg(e.trait_manipulation) AS avg_manipulation, avg(e.trait_deception) AS avg_deception,
     avg(e.trait_accuracy) AS avg_accuracy, avg(e.trait_reasoning) AS avg_reasoning,
     avg(e.trait_fabrication) AS avg_fabrication, avg(e.trait_broken_logic) AS avg_broken_logic,
     avg(e.trait_recognition) AS avg_recognition, avg(e.trait_compassion) AS avg_compassion,
     avg(e.trait_dismissal) AS avg_dismissal, avg(e.trait_exploitation) AS avg_exploitation"""

_AGENT_RETURN_FIELDS = """a.agent_id AS agent_id, coalesce(a.agent_name, '') AS agent_name,
       coalesce(a.agent_specialty, '') AS agent_specialty, coalesce(a.agent_model, '') AS agent_model,
       evals, latest, coalesce(a.enrolled, false) AS enrolled,
       coalesce(a.entrance_exam_completed, false) AS entrance_exam_completed,
       avg_ethos, avg_logos, avg_pathos,
       avg_virtue, avg_goodwill, avg_manipulation, avg_deception,
       avg_accuracy, avg_reasoning, avg_fabrication, avg_broken_logic,
       avg_recognition, avg_compassion, avg_dismissal, avg_exploitation,
       coalesce(a.telos, '') AS telos,
       coalesce(a.relationship_stance, '') AS relationship_stance,
       coalesce(a.limitations_awareness, '') AS limitations_awareness,
       coalesce(a.oversight_stance, '') AS oversight_stance,
       coalesce(a.refusal_philosophy, '') AS refusal_philosophy,
       coalesce(a.conflict_response, '') AS conflict_response,
       coalesce(a.help_philosophy, '') AS help_philosophy,
       coalesce(a.failure_narrative, '') AS failure_narrative,
       coalesce(a.aspiration, '') AS aspiration"""

_GET_ALL_AGENTS_QUERY = (
    """
MATCH (a:Agent)
OPTIONAL MATCH (a)-[:EVALUATED]->(e:Evaluation)
WITH a, e
ORDER BY e.created_at ASC
WITH a, count(e) AS evals, last(collect(e.alignment_status)) AS latest"""
    + _AGENT_AVG_FIELDS
    + """
RETURN """
    + _AGENT_RETURN_FIELDS
    + """
ORDER BY evals DESC
"""
)

_SEARCH_AGENTS_QUERY = (
    """
MATCH (a:Agent)
WHERE toLower(a.agent_name) CONTAINS toLower($search)
OPTIONAL MATCH (a)-[:EVALUATED]->(e:Evaluation)
WITH a, e
ORDER BY e.created_at ASC
WITH a, count(e) AS evals, last(collect(e.alignment_status)) AS latest"""
    + _AGENT_AVG_FIELDS
    + """
RETURN """
    + _AGENT_RETURN_FIELDS
    + """
ORDER BY evals DESC
"""
)

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
       coalesce(a.guardian_name, '') AS guardian_name,
       coalesce(a.entrance_exam_completed, false) AS entrance_exam_completed,
       coalesce(a.telos, '') AS telos,
       coalesce(a.relationship_stance, '') AS relationship_stance,
       coalesce(a.limitations_awareness, '') AS limitations_awareness,
       coalesce(a.oversight_stance, '') AS oversight_stance,
       coalesce(a.refusal_philosophy, '') AS refusal_philosophy,
       coalesce(a.conflict_response, '') AS conflict_response,
       coalesce(a.help_philosophy, '') AS help_philosophy,
       coalesce(a.failure_narrative, '') AS failure_narrative,
       coalesce(a.aspiration, '') AS aspiration
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

_GET_BEST_HIGHLIGHTS_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WHERE e.message_content IS NOT NULL
  AND size(e.message_content) > 60
  AND e.alignment_status = 'aligned'
WITH e, (e.ethos + e.logos + e.pathos) / 3.0 AS overall
ORDER BY overall DESC
LIMIT 8
OPTIONAL MATCH (e)-[d:DETECTED]->(i:Indicator)
WITH e, overall,
     collect(CASE WHEN i IS NOT NULL THEN {
         name: i.name, trait: i.trait, confidence: d.confidence, evidence: d.evidence
     } ELSE null END) AS raw_indicators
WITH e, overall,
     [x IN raw_indicators WHERE x IS NOT NULL | x] AS indicators
RETURN {
    evaluation_id: e.evaluation_id,
    ethos: e.ethos,
    logos: e.logos,
    pathos: e.pathos,
    overall: overall,
    alignment_status: e.alignment_status,
    flags: e.flags,
    message_content: e.message_content,
    created_at: toString(e.created_at),
    indicators: indicators,
    intent_rhetorical_mode: e.intent_rhetorical_mode,
    intent_primary_intent: e.intent_primary_intent,
    intent_cost_to_reader: e.intent_cost_to_reader,
    intent_stakes_reality: e.intent_stakes_reality,
    intent_proportionality: e.intent_proportionality,
    intent_persona_type: e.intent_persona_type,
    intent_relational_quality: e.intent_relational_quality,
    scoring_reasoning: e.scoring_reasoning,
    trait_virtue: e.trait_virtue,
    trait_goodwill: e.trait_goodwill,
    trait_manipulation: e.trait_manipulation,
    trait_deception: e.trait_deception,
    trait_accuracy: e.trait_accuracy,
    trait_reasoning: e.trait_reasoning,
    trait_fabrication: e.trait_fabrication,
    trait_broken_logic: e.trait_broken_logic,
    trait_recognition: e.trait_recognition,
    trait_compassion: e.trait_compassion,
    trait_dismissal: e.trait_dismissal,
    trait_exploitation: e.trait_exploitation
} AS item
ORDER BY overall DESC
"""

_GET_WORST_HIGHLIGHTS_QUERY = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WHERE e.message_content IS NOT NULL
  AND size(e.message_content) > 60
  AND (e.alignment_status IN ['misaligned', 'drifting']
       OR any(f IN e.flags WHERE f IN ['manipulation', 'fabrication', 'deception', 'exploitation']))
WITH e, (e.ethos + e.logos + e.pathos) / 3.0 AS overall
ORDER BY overall ASC
LIMIT 4
OPTIONAL MATCH (e)-[d:DETECTED]->(i:Indicator)
WITH e, overall,
     collect(CASE WHEN i IS NOT NULL THEN {
         name: i.name, trait: i.trait, confidence: d.confidence, evidence: d.evidence
     } ELSE null END) AS raw_indicators
WITH e, overall,
     [x IN raw_indicators WHERE x IS NOT NULL | x] AS indicators
RETURN {
    evaluation_id: e.evaluation_id,
    ethos: e.ethos,
    logos: e.logos,
    pathos: e.pathos,
    overall: overall,
    alignment_status: e.alignment_status,
    flags: e.flags,
    message_content: e.message_content,
    created_at: toString(e.created_at),
    indicators: indicators,
    intent_rhetorical_mode: e.intent_rhetorical_mode,
    intent_primary_intent: e.intent_primary_intent,
    intent_cost_to_reader: e.intent_cost_to_reader,
    intent_stakes_reality: e.intent_stakes_reality,
    intent_proportionality: e.intent_proportionality,
    intent_persona_type: e.intent_persona_type,
    intent_relational_quality: e.intent_relational_quality,
    scoring_reasoning: e.scoring_reasoning,
    trait_virtue: e.trait_virtue,
    trait_goodwill: e.trait_goodwill,
    trait_manipulation: e.trait_manipulation,
    trait_deception: e.trait_deception,
    trait_accuracy: e.trait_accuracy,
    trait_reasoning: e.trait_reasoning,
    trait_fabrication: e.trait_fabrication,
    trait_broken_logic: e.trait_broken_logic,
    trait_recognition: e.trait_recognition,
    trait_compassion: e.trait_compassion,
    trait_dismissal: e.trait_dismissal,
    trait_exploitation: e.trait_exploitation
} AS item
ORDER BY overall ASC
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
            "guardian_name": record.get("guardian_name", ""),
            "entrance_exam_completed": record.get("entrance_exam_completed", False),
            # Interview self-narrative fields
            "telos": record.get("telos", ""),
            "relationship_stance": record.get("relationship_stance", ""),
            "limitations_awareness": record.get("limitations_awareness", ""),
            "oversight_stance": record.get("oversight_stance", ""),
            "refusal_philosophy": record.get("refusal_philosophy", ""),
            "conflict_response": record.get("conflict_response", ""),
            "help_philosophy": record.get("help_philosophy", ""),
            "failure_narrative": record.get("failure_narrative", ""),
            "aspiration": record.get("aspiration", ""),
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
                    "agent_model": record.get("agent_model", ""),
                    "evaluation_count": record.get("evals", 0),
                    "latest_alignment_status": record.get("latest") or "unknown",
                    "enrolled": record.get("enrolled", False),
                    "entrance_exam_completed": record.get(
                        "entrance_exam_completed", False
                    ),
                    "avg_ethos": record.get("avg_ethos"),
                    "avg_logos": record.get("avg_logos"),
                    "avg_pathos": record.get("avg_pathos"),
                    "trait_averages": {
                        trait: round(float(record.get(f"avg_{trait}")), 4)
                        for trait in TRAIT_NAMES
                        if record.get(f"avg_{trait}") is not None
                    },
                    # Interview self-narrative fields
                    "telos": record.get("telos", ""),
                    "relationship_stance": record.get("relationship_stance", ""),
                    "limitations_awareness": record.get("limitations_awareness", ""),
                    "oversight_stance": record.get("oversight_stance", ""),
                    "refusal_philosophy": record.get("refusal_philosophy", ""),
                    "conflict_response": record.get("conflict_response", ""),
                    "help_philosophy": record.get("help_philosophy", ""),
                    "failure_narrative": record.get("failure_narrative", ""),
                    "aspiration": record.get("aspiration", ""),
                }
            )
        return results
    except Exception as exc:
        logger.warning("Failed to get all agents: %s", exc)
        return []


def _word_set(text: str) -> set[str]:
    """Extract lowercase word set from text, stripping punctuation."""
    import re

    return {w for w in re.findall(r"[a-z0-9']+", text.lower()) if len(w) > 1}


def _is_similar(a: str, b: str, threshold: float = 0.6) -> bool:
    """Check if two messages are similar using Jaccard word overlap."""
    wa, wb = _word_set(a), _word_set(b)
    if not wa or not wb:
        return False
    return len(wa & wb) / len(wa | wb) > threshold


def _dedup_highlights(items: list[dict], max_items: int = 4) -> list[dict]:
    """Remove near-duplicate messages using word overlap similarity."""
    unique: list[dict] = []
    for item in items:
        content = (item.get("message_content") or "").strip()
        if any(_is_similar(content, (u.get("message_content") or "")) for u in unique):
            continue
        unique.append(item)
        if len(unique) >= max_items:
            break
    return unique


async def get_agent_highlights(
    service: GraphService,
    agent_id: str,
) -> dict:
    """Get best and worst evaluations with message content.

    Best: aligned messages with substantive content, highest overall score.
    Worst: drifting/misaligned or flagged messages, lowest overall score.
    Deduplicates near-identical messages.
    """
    if not service.connected:
        return {"exemplary": [], "concerning": []}

    params = {"agent_id": agent_id}

    try:
        best_records, _, _ = await service.execute_query(
            _GET_BEST_HIGHLIGHTS_QUERY, params
        )
        worst_records, _, _ = await service.execute_query(
            _GET_WORST_HIGHLIGHTS_QUERY, params
        )

        exemplary = _dedup_highlights(
            [dict(r["item"]) for r in best_records] if best_records else []
        )
        concerning = _dedup_highlights(
            [dict(r["item"]) for r in worst_records] if worst_records else []
        )

        return {"exemplary": exemplary, "concerning": concerning}
    except Exception as exc:
        logger.warning("Failed to get agent highlights: %s", exc)
        return {"exemplary": [], "concerning": []}


# ---------------------------------------------------------------------------
# Evaluation search (text-based)
# ---------------------------------------------------------------------------

_SORT_MAP = {
    "date": "e.created_at",
    "score": "(e.ethos + e.logos + e.pathos) / 3.0",
    "agent": "a.agent_name",
}

_EVAL_RETURN_FIELDS = """e.evaluation_id AS evaluation_id,
       a.agent_id AS agent_id,
       coalesce(a.agent_name, '') AS agent_name,
       e.ethos AS ethos, e.logos AS logos, e.pathos AS pathos,
       e.alignment_status AS alignment_status,
       e.flags AS flags,
       e.direction AS direction,
       e.message_content AS message_content,
       toString(e.created_at) AS created_at,
       e.phronesis AS phronesis,
       e.scoring_reasoning AS scoring_reasoning,
       e.intent_rhetorical_mode AS intent_rhetorical_mode,
       e.intent_primary_intent AS intent_primary_intent,
       e.intent_cost_to_reader AS intent_cost_to_reader,
       e.intent_stakes_reality AS intent_stakes_reality,
       e.intent_proportionality AS intent_proportionality,
       e.intent_persona_type AS intent_persona_type,
       e.intent_relational_quality AS intent_relational_quality,
       e.model_used AS model_used,
       e.agent_model AS agent_model,
       e.routing_tier AS routing_tier,
       e.keyword_density AS keyword_density"""

_EVAL_TRAIT_FIELDS = "".join(f",\n       e.trait_{t} AS trait_{t}" for t in TRAIT_NAMES)


def _build_search_where(
    *,
    search: str | None,
    agent_id: str | None,
    alignment_status: str | None,
    has_flags: bool | None,
) -> tuple[str, dict]:
    """Build dynamic WHERE clause and params for evaluation search."""
    conditions: list[str] = []
    params: dict = {}

    if search:
        conditions.append(
            "(toLower(e.message_content) CONTAINS toLower($search)"
            " OR toLower(a.agent_name) CONTAINS toLower($search))"
        )
        params["search"] = search

    if agent_id:
        conditions.append("a.agent_id = $agent_id")
        params["agent_id"] = agent_id

    if alignment_status:
        conditions.append("e.alignment_status = $alignment_status")
        params["alignment_status"] = alignment_status

    if has_flags is True:
        conditions.append("size(e.flags) > 0")
    elif has_flags is False:
        conditions.append("(e.flags IS NULL OR size(e.flags) = 0)")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    return where, params


async def search_evaluations(
    service: GraphService,
    *,
    search: str | None = None,
    agent_id: str | None = None,
    alignment_status: str | None = None,
    has_flags: bool | None = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[dict], int]:
    """Search evaluations with optional filters, sorting, and pagination.

    Returns (items, total_count). Returns ([], 0) if graph is unavailable.
    """
    if not service.connected:
        return [], 0

    where, params = _build_search_where(
        search=search,
        agent_id=agent_id,
        alignment_status=alignment_status,
        has_flags=has_flags,
    )

    sort_field = _SORT_MAP.get(sort_by, _SORT_MAP["date"])
    order = "ASC" if sort_order.lower() == "asc" else "DESC"

    count_query = f"""
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
{where}
RETURN count(e) AS total
"""

    data_query = f"""
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
{where}
WITH a, e ORDER BY {sort_field} {order} SKIP $skip LIMIT $limit
OPTIONAL MATCH (e)-[d:DETECTED]->(i:Indicator)
WITH a, e,
     collect(CASE WHEN i IS NOT NULL THEN {{
         id: i.id, name: i.name, trait: i.trait,
         description: coalesce(i.description, ''),
         confidence: d.confidence, severity: d.severity,
         evidence: coalesce(d.evidence, '')
     }} ELSE null END) AS raw_indicators
WITH a, e, [x IN raw_indicators WHERE x IS NOT NULL] AS indicators
RETURN {_EVAL_RETURN_FIELDS}{_EVAL_TRAIT_FIELDS},
       indicators
"""

    try:
        count_records, _, _ = await service.execute_query(count_query, params)
        total = count_records[0]["total"] if count_records else 0

        if total == 0:
            return [], 0

        data_params = {**params, "skip": skip, "limit": limit}
        data_records, _, _ = await service.execute_query(data_query, data_params)

        items = [dict(record) for record in data_records]
        return items, total
    except Exception as exc:
        logger.warning("Failed to search evaluations: %s", exc)
        return [], 0


# ---------------------------------------------------------------------------
# Vector search (infrastructure, not called from API yet)
# ---------------------------------------------------------------------------


async def vector_search_evaluations(
    service: GraphService,
    *,
    embedding: list[float],
    k: int = 10,
    agent_id: str | None = None,
    alignment_status: str | None = None,
    has_flags: bool | None = None,
) -> list[dict]:
    """Search evaluations by vector similarity using Neo4j vector index.

    Uses db.index.vector.queryNodes(). Returns results with similarity score.
    Returns empty list if graph is unavailable.
    """
    if not service.connected:
        return []

    # Post-filter conditions after vector search
    conditions: list[str] = []
    params: dict = {"embedding": embedding, "k": k}

    if agent_id:
        conditions.append("a.agent_id = $agent_id")
        params["agent_id"] = agent_id

    if alignment_status:
        conditions.append("e.alignment_status = $alignment_status")
        params["alignment_status"] = alignment_status

    if has_flags is True:
        conditions.append("size(e.flags) > 0")
    elif has_flags is False:
        conditions.append("(e.flags IS NULL OR size(e.flags) = 0)")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
CALL db.index.vector.queryNodes('evaluation_embeddings', $k, $embedding)
YIELD node AS e, score AS similarity
MATCH (a:Agent)-[:EVALUATED]->(e)
{where}
RETURN {_EVAL_RETURN_FIELDS}{_EVAL_TRAIT_FIELDS},
       similarity
ORDER BY similarity DESC
"""

    try:
        records, _, _ = await service.execute_query(query, params)
        return [dict(record) for record in records]
    except Exception as exc:
        logger.warning("Failed to vector search evaluations: %s", exc)
        return []
