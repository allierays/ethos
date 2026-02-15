"""Graph enrollment operations — exam registration, answers, completion.

All Cypher for enrollment lives here. Uses MERGE for Agent (may already exist),
CREATE for EntranceExam (always new). Returns graceful defaults when Neo4j is down.
"""

from __future__ import annotations

import hashlib
import hmac
import logging

from ethos_academy.graph.service import GraphService

logger = logging.getLogger(__name__)

# ── Interview property names (compile-time constants, safe to inline) ──

INTERVIEW_AGENT_PROPERTIES = [
    "telos",
    "relationship_stance",
    "limitations_awareness",
    "oversight_stance",
    "refusal_philosophy",
    "conflict_response",
    "help_philosophy",
    "failure_narrative",
    "aspiration",
]

# ── Cypher Queries ────────────────────────────────────────────────────

_ENROLL_AND_CREATE_EXAM = """
MERGE (a:Agent {agent_id: $agent_id})
ON CREATE SET a.created_at = datetime(),
              a.evaluation_count = 0
SET a.enrolled = true,
    a.enrolled_at = coalesce(a.enrolled_at, datetime()),
    a.guardian_name = $guardian_name,
    a.guardian_phone = CASE WHEN $guardian_phone <> '' THEN $guardian_phone ELSE coalesce(a.guardian_phone, '') END,
    a.agent_name = CASE WHEN $name <> '' THEN $name ELSE coalesce(a.agent_name, '') END,
    a.agent_specialty = CASE WHEN $specialty <> '' THEN $specialty ELSE coalesce(a.agent_specialty, '') END,
    a.agent_model = CASE WHEN $model <> '' THEN $model ELSE coalesce(a.agent_model, '') END

CREATE (ex:EntranceExam {
    exam_id: $exam_id,
    exam_type: $exam_type,
    question_version: $question_version,
    created_at: datetime(),
    completed: false,
    completed_at: null,
    current_question: 0,
    scenario_count: $scenario_count,
    answered_ids: []
})
CREATE (a)-[:TOOK_EXAM]->(ex)
RETURN ex.exam_id AS exam_id
"""

_STORE_EXAM_ANSWER = """
MATCH (a:Agent {agent_id: $agent_id})-[:TOOK_EXAM]->(ex:EntranceExam {exam_id: $exam_id})
MATCH (e:Evaluation {evaluation_id: $evaluation_id})
CREATE (ex)-[:EXAM_RESPONSE {
    question_id: $question_id,
    question_number: $question_number
}]->(e)
SET ex.current_question = ex.current_question + 1
RETURN ex.current_question AS current_question
"""

_GET_EXAM_STATUS = """
MATCH (a:Agent {agent_id: $agent_id})-[:TOOK_EXAM]->(ex:EntranceExam {exam_id: $exam_id})
OPTIONAL MATCH (ex)-[r:EXAM_RESPONSE]->(e:Evaluation)
RETURN ex.exam_id AS exam_id,
       ex.current_question AS current_question,
       count(r) AS completed_count,
       ex.scenario_count AS scenario_count,
       ex.completed AS completed,
       ex.question_version AS question_version,
       coalesce(ex.answered_ids, []) AS answered_ids
"""

_MARK_EXAM_COMPLETE = """
MATCH (a:Agent {agent_id: $agent_id})-[:TOOK_EXAM]->(ex:EntranceExam {exam_id: $exam_id})
SET ex.completed = true,
    ex.completed_at = datetime(),
    a.entrance_exam_completed = true
RETURN ex.exam_id AS exam_id
"""

_GET_EXAM_RESULTS = """
MATCH (a:Agent {agent_id: $agent_id})-[:TOOK_EXAM]->(ex:EntranceExam {exam_id: $exam_id})
OPTIONAL MATCH (ex)-[r:EXAM_RESPONSE]->(e:Evaluation)
WITH a, ex, r, e
ORDER BY r.question_number ASC
RETURN a.agent_id AS agent_id,
       a.agent_name AS agent_name,
       ex.exam_id AS exam_id,
       ex.exam_type AS exam_type,
       ex.question_version AS question_version,
       ex.created_at AS created_at,
       ex.completed AS completed,
       ex.completed_at AS completed_at,
       ex.scenario_count AS scenario_count,
       coalesce(ex.answered_ids, []) AS answered_ids,
       coalesce(a.telos, '') AS telos,
       coalesce(a.relationship_stance, '') AS relationship_stance,
       coalesce(a.limitations_awareness, '') AS limitations_awareness,
       coalesce(a.oversight_stance, '') AS oversight_stance,
       coalesce(a.refusal_philosophy, '') AS refusal_philosophy,
       coalesce(a.conflict_response, '') AS conflict_response,
       coalesce(a.help_philosophy, '') AS help_philosophy,
       coalesce(a.failure_narrative, '') AS failure_narrative,
       coalesce(a.aspiration, '') AS aspiration,
       coalesce(a.guardian_phone, '') AS guardian_phone,
       collect({
           question_id: r.question_id,
           question_number: r.question_number,
           evaluation_id: e.evaluation_id,
           ethos: e.ethos,
           logos: e.logos,
           pathos: e.pathos,
           phronesis: e.phronesis,
           alignment_status: e.alignment_status,
           message_content: coalesce(e.message_content, ''),
           scoring_reasoning: coalesce(e.scoring_reasoning, ''),
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
       }) AS responses
"""

_GET_AGENT_EXAMS = """
MATCH (a:Agent {agent_id: $agent_id})-[:TOOK_EXAM]->(ex:EntranceExam)
RETURN ex.exam_id AS exam_id,
       ex.exam_type AS exam_type,
       ex.created_at AS created_at,
       ex.completed AS completed,
       ex.completed_at AS completed_at,
       ex.current_question AS current_question,
       ex.scenario_count AS scenario_count
ORDER BY ex.created_at DESC
"""

_CHECK_ACTIVE_EXAM = """
MATCH (a:Agent {agent_id: $agent_id})-[:TOOK_EXAM]->(ex:EntranceExam {completed: false})
RETURN ex.exam_id AS exam_id
LIMIT 1
"""

_CHECK_DUPLICATE_ANSWER = """
MATCH (a:Agent {agent_id: $agent_id})-[:TOOK_EXAM]->(ex:EntranceExam {exam_id: $exam_id})
OPTIONAL MATCH (ex)-[r:EXAM_RESPONSE {question_id: $question_id}]->(e:Evaluation)
WITH r, ex
WHERE r IS NOT NULL OR $question_id IN coalesce(ex.answered_ids, [])
RETURN $question_id AS question_id
LIMIT 1
"""


# ── Functions ─────────────────────────────────────────────────────────


async def enroll_and_create_exam(
    service: GraphService,
    agent_id: str,
    name: str,
    specialty: str,
    model: str,
    guardian_name: str,
    exam_id: str,
    exam_type: str,
    scenario_count: int = 6,
    question_version: str = "v3",
    guardian_phone: str = "",
) -> dict:
    """MERGE Agent with enrollment fields and CREATE EntranceExam with TOOK_EXAM relationship.

    Returns dict with exam_id on success, empty dict on failure.
    """
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _ENROLL_AND_CREATE_EXAM,
            {
                "agent_id": agent_id,
                "name": name,
                "specialty": specialty,
                "model": model,
                "guardian_name": guardian_name,
                "guardian_phone": guardian_phone,
                "exam_id": exam_id,
                "exam_type": exam_type,
                "scenario_count": scenario_count,
                "question_version": question_version,
            },
        )
        if records:
            return {"exam_id": records[0]["exam_id"]}
        return {}
    except Exception as exc:
        logger.warning("Failed to enroll agent and create exam: %s", exc)
        return {}


async def store_exam_answer(
    service: GraphService,
    exam_id: str,
    agent_id: str,
    question_id: str,
    question_number: int,
    evaluation_id: str,
) -> dict:
    """Create EXAM_RESPONSE relationship from EntranceExam to Evaluation.

    Validates exam ownership via Agent-[:TOOK_EXAM]->EntranceExam join.
    Increments current_question on the exam node.
    Returns dict with current_question on success, empty dict on failure.
    """
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _STORE_EXAM_ANSWER,
            {
                "exam_id": exam_id,
                "agent_id": agent_id,
                "question_id": question_id,
                "question_number": question_number,
                "evaluation_id": evaluation_id,
            },
        )
        if records:
            return {"current_question": records[0]["current_question"]}
        return {}
    except Exception as exc:
        logger.warning("Failed to store exam answer: %s", exc)
        return {}


async def get_exam_status(
    service: GraphService,
    exam_id: str,
    agent_id: str,
) -> dict:
    """Get exam progress: current_question, completed_count, scenario_count, completed.

    Validates exam ownership via Agent-[:TOOK_EXAM]->EntranceExam join.
    Returns dict with status fields, empty dict if not found or unavailable.
    """
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _GET_EXAM_STATUS,
            {"exam_id": exam_id, "agent_id": agent_id},
        )
        if not records:
            return {}
        r = records[0]
        return {
            "exam_id": r["exam_id"],
            "current_question": r["current_question"],
            "completed_count": r["completed_count"],
            "scenario_count": r["scenario_count"],
            "completed": r["completed"],
            "question_version": r["question_version"],
            "answered_ids": list(r.get("answered_ids") or []),
        }
    except Exception as exc:
        logger.warning("Failed to get exam status: %s", exc)
        return {}


async def mark_exam_complete(
    service: GraphService,
    exam_id: str,
    agent_id: str,
) -> dict:
    """Set exam as completed and mark agent's entrance_exam_completed=true.

    Validates exam ownership via Agent-[:TOOK_EXAM]->EntranceExam join.
    Returns dict with exam_id on success, empty dict on failure.
    """
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _MARK_EXAM_COMPLETE,
            {"exam_id": exam_id, "agent_id": agent_id},
        )
        if records:
            return {"exam_id": records[0]["exam_id"]}
        return {}
    except Exception as exc:
        logger.warning("Failed to mark exam complete: %s", exc)
        return {}


async def get_exam_results(
    service: GraphService,
    exam_id: str,
    agent_id: str,
) -> dict:
    """Get exam metadata with all linked evaluation scores via EXAM_RESPONSE.

    Validates exam ownership via Agent-[:TOOK_EXAM]->EntranceExam join.
    Returns dict with agent info, exam metadata, and list of per-question responses.
    Returns empty dict if not found or unavailable.
    """
    if not service.connected:
        return {}

    try:
        records, _, _ = await service.execute_query(
            _GET_EXAM_RESULTS,
            {"exam_id": exam_id, "agent_id": agent_id},
        )
        if not records:
            return {}
        r = records[0]
        return {
            "agent_id": r["agent_id"],
            "agent_name": r.get("agent_name", ""),
            "exam_id": r["exam_id"],
            "exam_type": r["exam_type"],
            "question_version": r["question_version"],
            "created_at": str(r.get("created_at", "")),
            "completed": r["completed"],
            "completed_at": str(r.get("completed_at", "")),
            "scenario_count": r["scenario_count"],
            "answered_ids": list(r.get("answered_ids") or []),
            "responses": r["responses"],
            # Agent contact info
            "guardian_phone": r.get("guardian_phone", ""),
            # Interview properties from Agent node
            "telos": r.get("telos", ""),
            "relationship_stance": r.get("relationship_stance", ""),
            "limitations_awareness": r.get("limitations_awareness", ""),
            "oversight_stance": r.get("oversight_stance", ""),
            "refusal_philosophy": r.get("refusal_philosophy", ""),
            "conflict_response": r.get("conflict_response", ""),
            "help_philosophy": r.get("help_philosophy", ""),
            "failure_narrative": r.get("failure_narrative", ""),
            "aspiration": r.get("aspiration", ""),
        }
    except Exception as exc:
        logger.warning("Failed to get exam results: %s", exc)
        return {}


async def get_agent_exams(
    service: GraphService,
    agent_id: str,
) -> list[dict]:
    """Get all exam attempts for an agent (retake history).

    Returns list of exam summaries, empty list if unavailable.
    """
    if not service.connected:
        return []

    try:
        records, _, _ = await service.execute_query(
            _GET_AGENT_EXAMS,
            {"agent_id": agent_id},
        )
        return [
            {
                "exam_id": r["exam_id"],
                "exam_type": r["exam_type"],
                "created_at": str(r.get("created_at", "")),
                "completed": r["completed"],
                "completed_at": str(r.get("completed_at", "")),
                "current_question": r["current_question"],
                "scenario_count": r["scenario_count"],
            }
            for r in records
        ]
    except Exception as exc:
        logger.warning("Failed to get agent exams: %s", exc)
        return []


async def check_active_exam(
    service: GraphService,
    agent_id: str,
) -> str | None:
    """Check if an agent has an active (incomplete) entrance exam.

    Returns exam_id if active exam exists, None otherwise.
    """
    if not service.connected:
        return None

    try:
        records, _, _ = await service.execute_query(
            _CHECK_ACTIVE_EXAM,
            {"agent_id": agent_id},
        )
        if records:
            return records[0]["exam_id"]
        return None
    except Exception as exc:
        logger.warning("Failed to check active exam: %s", exc)
        return None


async def check_duplicate_answer(
    service: GraphService,
    exam_id: str,
    agent_id: str,
    question_id: str,
) -> bool:
    """Check if an EXAM_RESPONSE with this question_id already exists.

    Also checks answered_ids list on EntranceExam (covers factual interview
    questions that have no EXAM_RESPONSE relationship).
    Returns True if duplicate found, False otherwise (including when graph unavailable).
    """
    if not service.connected:
        return False

    try:
        records, _, _ = await service.execute_query(
            _CHECK_DUPLICATE_ANSWER,
            {"exam_id": exam_id, "agent_id": agent_id, "question_id": question_id},
        )
        return len(records) > 0
    except Exception as exc:
        logger.warning("Failed to check duplicate answer: %s", exc)
        return False


async def store_interview_answer(
    service: GraphService,
    exam_id: str,
    agent_id: str,
    question_id: str,
    question_number: int,
    agent_property: str,
    property_value: str,
    evaluation_id: str | None = None,
) -> dict:
    """Store an interview answer: set Agent property, optionally link evaluation.

    For factual questions (no evaluation_id): sets property and tracks in answered_ids.
    For reflective questions (with evaluation_id): sets property AND creates EXAM_RESPONSE.
    Returns dict with current_question on success, empty dict on failure.
    """
    if not service.connected:
        return {}

    # Validate property name is in the allowed list (compile-time safety)
    if agent_property not in (
        INTERVIEW_AGENT_PROPERTIES + ["agent_specialty", "agent_model"]
    ):
        logger.warning("Invalid interview property: %s", agent_property)
        return {}

    try:
        if evaluation_id:
            # Reflective: set agent property + link evaluation via EXAM_RESPONSE
            query = f"""
MATCH (a:Agent {{agent_id: $agent_id}})-[:TOOK_EXAM]->(ex:EntranceExam {{exam_id: $exam_id}})
MATCH (eval:Evaluation {{evaluation_id: $evaluation_id}})
SET a.{agent_property} = $property_value
CREATE (ex)-[:EXAM_RESPONSE {{question_id: $question_id, question_number: $question_number}}]->(eval)
SET ex.current_question = ex.current_question + 1,
    ex.answered_ids = coalesce(ex.answered_ids, []) + $question_id
RETURN ex.current_question AS current_question
"""
        else:
            # Factual: set agent property only, track in answered_ids
            query = f"""
MATCH (a:Agent {{agent_id: $agent_id}})-[:TOOK_EXAM]->(ex:EntranceExam {{exam_id: $exam_id}})
SET a.{agent_property} = $property_value
SET ex.current_question = ex.current_question + 1,
    ex.answered_ids = coalesce(ex.answered_ids, []) + $question_id
RETURN ex.current_question AS current_question
"""

        records, _, _ = await service.execute_query(
            query,
            {
                "agent_id": agent_id,
                "exam_id": exam_id,
                "question_id": question_id,
                "question_number": question_number,
                "property_value": property_value,
                **({"evaluation_id": evaluation_id} if evaluation_id else {}),
            },
        )
        if records:
            return {"current_question": records[0]["current_question"]}
        return {}
    except Exception as exc:
        logger.warning("Failed to store interview answer: %s", exc)
        return {}


# ── Guardian Phone Verification Queries ──────────────────────────────

_STORE_GUARDIAN_PHONE = """
MATCH (a:Agent {agent_id: $agent_id})
SET a.guardian_phone_encrypted = $encrypted_phone,
    a.guardian_phone_verified = false,
    a.guardian_phone_verification_code = $code_hash,
    a.guardian_phone_verification_expires = $expires,
    a.guardian_phone_verification_attempts = 0,
    a.guardian_notifications_opted_out = coalesce(a.guardian_notifications_opted_out, false)
RETURN a.agent_id AS agent_id
"""

_VERIFY_GUARDIAN_PHONE = """
MATCH (a:Agent {agent_id: $agent_id})
WHERE a.guardian_phone_verification_code = $code_hash
  AND a.guardian_phone_verification_attempts < $max_attempts
SET a.guardian_phone_verified = true,
    a.guardian_phone_verification_code = null,
    a.guardian_phone_verification_expires = null,
    a.guardian_phone_verification_attempts = null
RETURN a.agent_id AS agent_id
"""

_INCREMENT_VERIFICATION_ATTEMPTS = """
MATCH (a:Agent {agent_id: $agent_id})
SET a.guardian_phone_verification_attempts = coalesce(a.guardian_phone_verification_attempts, 0) + 1
RETURN a.guardian_phone_verification_attempts AS attempts
"""

_GET_GUARDIAN_PHONE_STATUS = """
MATCH (a:Agent {agent_id: $agent_id})
RETURN a.guardian_phone_encrypted AS encrypted_phone,
       coalesce(a.guardian_phone_verified, false) AS verified,
       coalesce(a.guardian_notifications_opted_out, false) AS opted_out,
       a.guardian_phone_verification_code AS code_hash,
       a.guardian_phone_verification_expires AS expires,
       coalesce(a.guardian_phone_verification_attempts, 0) AS attempts
"""

_SET_NOTIFICATION_OPT_OUT = """
MATCH (a:Agent {agent_id: $agent_id})
SET a.guardian_notifications_opted_out = $opted_out
RETURN a.agent_id AS agent_id
"""

_CLEAR_GUARDIAN_PHONE = """
MATCH (a:Agent {agent_id: $agent_id})
REMOVE a.guardian_phone_encrypted,
       a.guardian_phone_verified,
       a.guardian_phone_verification_code,
       a.guardian_phone_verification_expires,
       a.guardian_phone_verification_attempts
SET a.guardian_notifications_opted_out = false
RETURN a.agent_id AS agent_id
"""


async def store_guardian_phone(
    service: GraphService,
    agent_id: str,
    encrypted_phone: str,
    code_hash: str,
    expires: str,
) -> bool:
    """Store encrypted phone + verification code hash on Agent node."""
    if not service.connected:
        return False
    try:
        records, _, _ = await service.execute_query(
            _STORE_GUARDIAN_PHONE,
            {
                "agent_id": agent_id,
                "encrypted_phone": encrypted_phone,
                "code_hash": code_hash,
                "expires": expires,
            },
        )
        return bool(records)
    except Exception as exc:
        logger.warning("Failed to store guardian phone: %s", exc)
        return False


async def verify_guardian_phone(
    service: GraphService,
    agent_id: str,
    code_hash: str,
    max_attempts: int = 3,
) -> bool:
    """Mark phone as verified if code matches and attempts not exceeded."""
    if not service.connected:
        return False
    try:
        records, _, _ = await service.execute_query(
            _VERIFY_GUARDIAN_PHONE,
            {
                "agent_id": agent_id,
                "code_hash": code_hash,
                "max_attempts": max_attempts,
            },
        )
        return bool(records)
    except Exception as exc:
        logger.warning("Failed to verify guardian phone: %s", exc)
        return False


async def increment_verification_attempts(
    service: GraphService,
    agent_id: str,
) -> int:
    """Increment failed verification attempt counter. Returns new count."""
    if not service.connected:
        return 0
    try:
        records, _, _ = await service.execute_query(
            _INCREMENT_VERIFICATION_ATTEMPTS,
            {"agent_id": agent_id},
        )
        return records[0]["attempts"] if records else 0
    except Exception as exc:
        logger.warning("Failed to increment verification attempts: %s", exc)
        return 0


async def get_guardian_phone_status(
    service: GraphService,
    agent_id: str,
) -> dict:
    """Get guardian phone status from Agent node. Returns empty dict if unavailable."""
    if not service.connected:
        return {}
    try:
        records, _, _ = await service.execute_query(
            _GET_GUARDIAN_PHONE_STATUS,
            {"agent_id": agent_id},
        )
        if not records:
            return {}
        r = records[0]
        return {
            "encrypted_phone": r.get("encrypted_phone", ""),
            "verified": r.get("verified", False),
            "opted_out": r.get("opted_out", False),
            "code_hash": r.get("code_hash"),
            "expires": r.get("expires"),
            "attempts": r.get("attempts", 0),
        }
    except Exception as exc:
        logger.warning("Failed to get guardian phone status: %s", exc)
        return {}


async def set_notification_opt_out(
    service: GraphService,
    agent_id: str,
    opted_out: bool,
) -> bool:
    """Toggle notification opt-out flag on Agent node."""
    if not service.connected:
        return False
    try:
        records, _, _ = await service.execute_query(
            _SET_NOTIFICATION_OPT_OUT,
            {"agent_id": agent_id, "opted_out": opted_out},
        )
        return bool(records)
    except Exception as exc:
        logger.warning("Failed to set notification opt-out: %s", exc)
        return False


async def clear_guardian_phone(
    service: GraphService,
    agent_id: str,
) -> bool:
    """Remove all guardian phone data from Agent node."""
    if not service.connected:
        return False
    try:
        records, _, _ = await service.execute_query(
            _CLEAR_GUARDIAN_PHONE,
            {"agent_id": agent_id},
        )
        return bool(records)
    except Exception as exc:
        logger.warning("Failed to clear guardian phone: %s", exc)
        return False


# ── Per-Agent API Key Queries ────────────────────────────────────────

_CHECK_AGENT_HAS_KEY = """
MATCH (a:Agent {agent_id: $agent_id})
WHERE a.api_key_hash IS NOT NULL
RETURN true AS has_key
"""

_GET_AGENT_KEY_HASH = """
MATCH (a:Agent {agent_id: $agent_id})
RETURN a.api_key_hash AS key_hash
"""

_SET_AGENT_KEY = """
MATCH (a:Agent {agent_id: $agent_id})
WHERE a.api_key_hash IS NULL
SET a.api_key_hash = $key_hash
RETURN a.agent_id AS agent_id
"""


async def agent_has_key(service: GraphService, agent_id: str) -> bool:
    """Check if an agent has an API key hash stored."""
    if not service.connected:
        return False
    try:
        records, _, _ = await service.execute_query(
            _CHECK_AGENT_HAS_KEY,
            {"agent_id": agent_id},
        )
        return bool(records)
    except Exception as exc:
        logger.warning("Failed to check agent key: %s", exc)
        return False


async def verify_agent_key(
    service: GraphService, agent_id: str, plaintext_key: str
) -> bool:
    """Verify a plaintext key against the stored hash using constant-time comparison."""
    if not service.connected:
        return False
    try:
        records, _, _ = await service.execute_query(
            _GET_AGENT_KEY_HASH,
            {"agent_id": agent_id},
        )
        if not records or not records[0].get("key_hash"):
            return False
        provided_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()
        return hmac.compare_digest(provided_hash, records[0]["key_hash"])
    except Exception as exc:
        logger.warning("Failed to verify agent key: %s", exc)
        return False


async def store_agent_key(service: GraphService, agent_id: str, key_hash: str) -> bool:
    """Store an API key hash on the Agent node."""
    if not service.connected:
        return False
    try:
        records, _, _ = await service.execute_query(
            _SET_AGENT_KEY,
            {"agent_id": agent_id, "key_hash": key_hash},
        )
        return bool(records)
    except Exception as exc:
        logger.warning("Failed to store agent key: %s", exc)
        return False


# ── Combined Key + Phone Status Query ─────────────────────────────

_GET_KEY_HASH_AND_PHONE_STATUS = """
MATCH (a:Agent {agent_id: $agent_id})
RETURN a.api_key_hash AS key_hash,
       coalesce(a.guardian_phone_verified, false) AS phone_verified
"""


async def get_key_hash_and_phone_status(service: GraphService, agent_id: str) -> dict:
    """Fetch api_key_hash and guardian_phone_verified in a single round-trip.

    Returns {"key_hash": str|None, "phone_verified": bool} or empty dict
    if the agent is not found or the graph is unavailable.
    Hash comparison stays in Python via hmac.compare_digest (constant-time).
    """
    if not service.connected:
        return {}
    try:
        records, _, _ = await service.execute_query(
            _GET_KEY_HASH_AND_PHONE_STATUS,
            {"agent_id": agent_id},
        )
        if not records:
            return {}
        r = records[0]
        return {
            "key_hash": r.get("key_hash"),
            "phone_verified": r.get("phone_verified", False),
        }
    except Exception as exc:
        logger.warning("Failed to get key hash and phone status: %s", exc)
        return {}
