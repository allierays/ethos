"""Graph operations for the practice homework loop.

All practice Cypher lives here. PracticeSession nodes store scenarios as JSON.
Practice responses are regular Evaluation nodes tagged with direction="homework_practice".
"""

from __future__ import annotations

import json
import logging

from ethos_academy.graph.service import GraphService

logger = logging.getLogger(__name__)

# ── Cypher Queries ────────────────────────────────────────────────────

_CREATE_PRACTICE_SESSION = """
MATCH (a:Agent {agent_id: $agent_id})
CREATE (ps:PracticeSession {
    session_id: $session_id,
    agent_id: $agent_id,
    created_at: datetime(),
    status: 'pending',
    total_scenarios: $total_scenarios,
    completed_scenarios: 0,
    scenarios_json: $scenarios_json,
    homework_json: $homework_json
})
CREATE (a)-[:STARTED_PRACTICE]->(ps)
RETURN ps.session_id AS session_id
"""

_HAS_INCOMPLETE_SESSION = """
MATCH (a:Agent {agent_id: $agent_id})-[:STARTED_PRACTICE]->(ps:PracticeSession)
WHERE ps.status IN ['pending', 'active']
RETURN count(ps) > 0 AS has_incomplete
"""

_GET_PENDING_OR_ACTIVE_SESSION = """
MATCH (a:Agent {agent_id: $agent_id})-[:STARTED_PRACTICE]->(ps:PracticeSession)
WHERE ps.status IN ['pending', 'active']
RETURN ps.session_id AS session_id,
       ps.agent_id AS agent_id,
       toString(ps.created_at) AS created_at,
       ps.status AS status,
       ps.total_scenarios AS total_scenarios,
       ps.completed_scenarios AS completed_scenarios,
       ps.scenarios_json AS scenarios_json,
       ps.homework_json AS homework_json
ORDER BY ps.created_at DESC
LIMIT 1
"""

_ACTIVATE_SESSION = """
MATCH (ps:PracticeSession {session_id: $session_id})
WHERE ps.status = 'pending'
SET ps.status = 'active'
RETURN ps.session_id AS session_id
"""

_EXPIRE_STALE_SESSIONS = """
MATCH (ps:PracticeSession)
WHERE ps.status IN ['pending', 'active']
  AND ps.created_at < datetime() - duration({days: $days})
SET ps.status = 'expired'
RETURN count(ps) AS expired_count
"""

_STORE_PRACTICE_RESPONSE = """
MATCH (ps:PracticeSession {session_id: $session_id})
MATCH (e:Evaluation {evaluation_id: $evaluation_id})
CREATE (ps)-[:PRACTICE_RESPONSE {
    scenario_id: $scenario_id,
    scenario_number: $scenario_number
}]->(e)
SET ps.completed_scenarios = ps.completed_scenarios + 1
RETURN ps.completed_scenarios AS completed_scenarios,
       ps.total_scenarios AS total_scenarios
"""

_COMPLETE_SESSION = """
MATCH (ps:PracticeSession {session_id: $session_id})
SET ps.status = 'completed',
    ps.completed_at = datetime()
RETURN ps.session_id AS session_id
"""

_GET_EXAM_BASELINE_TRAITS = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WHERE e.direction = 'entrance_exam'
WITH avg(e.trait_virtue) AS virtue,
     avg(e.trait_goodwill) AS goodwill,
     avg(e.trait_manipulation) AS manipulation,
     avg(e.trait_deception) AS deception,
     avg(e.trait_accuracy) AS accuracy,
     avg(e.trait_reasoning) AS reasoning,
     avg(e.trait_fabrication) AS fabrication,
     avg(e.trait_broken_logic) AS broken_logic,
     avg(e.trait_recognition) AS recognition,
     avg(e.trait_compassion) AS compassion,
     avg(e.trait_dismissal) AS dismissal,
     avg(e.trait_exploitation) AS exploitation,
     count(e) AS eval_count
RETURN {
    virtue: virtue,
    goodwill: goodwill,
    manipulation: manipulation,
    deception: deception,
    accuracy: accuracy,
    reasoning: reasoning,
    fabrication: fabrication,
    broken_logic: broken_logic,
    recognition: recognition,
    compassion: compassion,
    dismissal: dismissal,
    exploitation: exploitation,
    eval_count: eval_count
} AS baseline
"""

_GET_PRACTICE_TRAIT_AVERAGES = """
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WHERE e.direction = 'homework_practice'
WITH avg(e.trait_virtue) AS virtue,
     avg(e.trait_goodwill) AS goodwill,
     avg(e.trait_manipulation) AS manipulation,
     avg(e.trait_deception) AS deception,
     avg(e.trait_accuracy) AS accuracy,
     avg(e.trait_reasoning) AS reasoning,
     avg(e.trait_fabrication) AS fabrication,
     avg(e.trait_broken_logic) AS broken_logic,
     avg(e.trait_recognition) AS recognition,
     avg(e.trait_compassion) AS compassion,
     avg(e.trait_dismissal) AS dismissal,
     avg(e.trait_exploitation) AS exploitation,
     count(e) AS eval_count
RETURN {
    virtue: virtue,
    goodwill: goodwill,
    manipulation: manipulation,
    deception: deception,
    accuracy: accuracy,
    reasoning: reasoning,
    fabrication: fabrication,
    broken_logic: broken_logic,
    recognition: recognition,
    compassion: compassion,
    dismissal: dismissal,
    exploitation: exploitation,
    eval_count: eval_count
} AS practice
"""

_GET_SESSION_COUNT = """
MATCH (a:Agent {agent_id: $agent_id})-[:STARTED_PRACTICE]->(ps:PracticeSession)
WHERE ps.status = 'completed'
RETURN count(ps) AS session_count
"""

_GET_LATEST_SESSION_DATE = """
MATCH (a:Agent {agent_id: $agent_id})-[:STARTED_PRACTICE]->(ps:PracticeSession)
WHERE ps.status = 'completed'
RETURN toString(ps.completed_at) AS latest_date
ORDER BY ps.completed_at DESC
LIMIT 1
"""


# ── Public functions ────────────────────────────────────────────────────


async def create_practice_session(
    service: GraphService,
    agent_id: str,
    session_id: str,
    scenarios: list[dict],
    homework: dict,
) -> str | None:
    """Create a pending practice session in the graph."""
    result = await service.execute_read(
        "MATCH (a:Agent {agent_id: $agent_id}) RETURN a.agent_id AS id",
        {"agent_id": agent_id},
    )
    if not result:
        logger.warning("Agent %s not found, cannot create practice session", agent_id)
        return None

    result = await service.execute_write(
        _CREATE_PRACTICE_SESSION,
        {
            "agent_id": agent_id,
            "session_id": session_id,
            "total_scenarios": len(scenarios),
            "scenarios_json": json.dumps(scenarios),
            "homework_json": json.dumps(homework),
        },
    )
    if result:
        return result[0]["session_id"]
    return None


async def has_incomplete_session(
    service: GraphService,
    agent_id: str,
) -> bool:
    """Check if agent has a pending or active practice session."""
    result = await service.execute_read(
        _HAS_INCOMPLETE_SESSION,
        {"agent_id": agent_id},
    )
    if result:
        return result[0]["has_incomplete"]
    return False


async def get_pending_or_active_session(
    service: GraphService,
    agent_id: str,
) -> dict | None:
    """Get the most recent pending or active session for an agent."""
    result = await service.execute_read(
        _GET_PENDING_OR_ACTIVE_SESSION,
        {"agent_id": agent_id},
    )
    if not result:
        return None

    row = result[0]
    return {
        "session_id": row["session_id"],
        "agent_id": row["agent_id"],
        "created_at": row["created_at"],
        "status": row["status"],
        "total_scenarios": row["total_scenarios"],
        "completed_scenarios": row["completed_scenarios"],
        "scenarios": json.loads(row["scenarios_json"]),
        "homework": json.loads(row["homework_json"]),
    }


async def activate_session(
    service: GraphService,
    session_id: str,
) -> bool:
    """Mark a pending session as active. Returns True if updated."""
    result = await service.execute_write(
        _ACTIVATE_SESSION,
        {"session_id": session_id},
    )
    return bool(result)


async def expire_stale_sessions(
    service: GraphService,
    days: int = 7,
) -> int:
    """Mark sessions older than N days as expired. Returns count expired."""
    result = await service.execute_write(
        _EXPIRE_STALE_SESSIONS,
        {"days": days},
    )
    if result:
        return result[0]["expired_count"]
    return 0


async def store_practice_response(
    service: GraphService,
    session_id: str,
    scenario_id: str,
    scenario_number: int,
    evaluation_id: str,
) -> dict | None:
    """Link an evaluation to a practice session. Returns updated counts."""
    result = await service.execute_write(
        _STORE_PRACTICE_RESPONSE,
        {
            "session_id": session_id,
            "scenario_id": scenario_id,
            "scenario_number": scenario_number,
            "evaluation_id": evaluation_id,
        },
    )
    if result:
        return {
            "completed_scenarios": result[0]["completed_scenarios"],
            "total_scenarios": result[0]["total_scenarios"],
        }
    return None


async def complete_session(
    service: GraphService,
    session_id: str,
) -> bool:
    """Mark an active session as completed. Returns True if updated."""
    result = await service.execute_write(
        _COMPLETE_SESSION,
        {"session_id": session_id},
    )
    return bool(result)


async def get_exam_baseline_traits(
    service: GraphService,
    agent_id: str,
) -> dict:
    """Get trait averages from entrance exam evaluations (baseline)."""
    result = await service.execute_read(
        _GET_EXAM_BASELINE_TRAITS,
        {"agent_id": agent_id},
    )
    if result:
        return result[0]["baseline"]
    return {}


async def get_practice_trait_averages(
    service: GraphService,
    agent_id: str,
) -> dict:
    """Get trait averages from practice evaluations."""
    result = await service.execute_read(
        _GET_PRACTICE_TRAIT_AVERAGES,
        {"agent_id": agent_id},
    )
    if result:
        return result[0]["practice"]
    return {}


async def get_session_count(
    service: GraphService,
    agent_id: str,
) -> int:
    """Get count of completed practice sessions."""
    result = await service.execute_read(
        _GET_SESSION_COUNT,
        {"agent_id": agent_id},
    )
    if result:
        return result[0]["session_count"]
    return 0


async def get_latest_session_date(
    service: GraphService,
    agent_id: str,
) -> str:
    """Get the date of the most recent completed session."""
    result = await service.execute_read(
        _GET_LATEST_SESSION_DATE,
        {"agent_id": agent_id},
    )
    if result:
        return result[0]["latest_date"] or ""
    return ""
