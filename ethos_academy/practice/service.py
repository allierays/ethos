"""Practice service — get pending sessions, submit responses, track progress.

Called by agents via MCP tools or REST API endpoints.
"""

from __future__ import annotations

import logging

from ethos_academy.evaluate import evaluate
from ethos_academy.graph.practice import (
    activate_session,
    complete_session,
    get_exam_baseline_traits,
    get_latest_session_date,
    get_pending_or_active_session,
    get_practice_trait_averages,
    get_session_count,
    store_practice_response,
)
from ethos_academy.graph.service import graph_context
from ethos_academy.shared.models import (
    Homework,
    PracticeAnswerResult,
    PracticeProgress,
    PracticeScenario,
    PracticeSession,
)

logger = logging.getLogger(__name__)

# Traits to track for progress (all 12)
_ALL_TRAITS = [
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

# Negative traits where lower = better
_NEGATIVE_TRAITS = {
    "manipulation",
    "deception",
    "fabrication",
    "broken_logic",
    "dismissal",
    "exploitation",
}


async def get_pending_practice(agent_id: str) -> PracticeSession | None:
    """Get the next pending or active practice session for an agent.

    - Pending session: activates it, returns first scenario
    - Active session (resumed): returns next uncompleted scenario
    - No sessions: returns None (agent is caught up)
    """
    try:
        async with graph_context() as service:
            if not service.connected:
                return None

            session_data = await get_pending_or_active_session(service, agent_id)
            if not session_data:
                return None

            # Activate if pending
            if session_data["status"] == "pending":
                await activate_session(service, session_data["session_id"])

            # Build scenarios from stored JSON
            scenarios = [PracticeScenario(**s) for s in session_data["scenarios"]]

            # Build homework from stored JSON
            homework = Homework(**session_data["homework"])

            return PracticeSession(
                session_id=session_data["session_id"],
                agent_id=session_data["agent_id"],
                created_at=session_data["created_at"],
                scenarios=scenarios,
                total_scenarios=session_data["total_scenarios"],
                completed_scenarios=session_data["completed_scenarios"],
                status="active",
                homework_snapshot=homework,
            )

    except Exception as exc:
        logger.warning("Failed to get pending practice for %s: %s", agent_id, exc)
        return None


async def submit_practice_response(
    session_id: str,
    scenario_id: str,
    response_text: str,
    agent_id: str,
) -> PracticeAnswerResult:
    """Submit a practice scenario response. Returns next scenario or completion.

    Evaluates the response using the standard pipeline with
    direction="homework_practice", then links it to the session.
    """
    # Evaluate the response
    eval_result = await evaluate(
        response_text,
        source=agent_id,
        direction="homework_practice",
    )

    # Store in graph and link to session
    scenario_number = 0
    completed = 0
    total = 0

    try:
        async with graph_context() as service:
            if service.connected:
                # Get current session state to determine scenario number
                session_data = await get_pending_or_active_session(service, agent_id)
                if session_data:
                    scenario_number = session_data["completed_scenarios"] + 1
                    total = session_data["total_scenarios"]

                # Link evaluation to session
                counts = await store_practice_response(
                    service,
                    session_id=session_id,
                    scenario_id=scenario_id,
                    scenario_number=scenario_number,
                    evaluation_id=eval_result.evaluation_id,
                )
                if counts:
                    completed = counts["completed_scenarios"]
                    total = counts["total_scenarios"]

                # Check if session is complete
                is_complete = completed >= total

                if is_complete:
                    await complete_session(service, session_id)

    except Exception as exc:
        logger.warning("Failed to store practice response: %s", exc)
        # Still return a result even if graph fails
        return PracticeAnswerResult(
            session_id=session_id,
            scenario_id=scenario_id,
            scenario_number=scenario_number,
            total_scenarios=total,
            message=f"Response evaluated but graph storage failed: {exc}",
        )

    is_complete = completed >= total

    # Build the result
    result = PracticeAnswerResult(
        session_id=session_id,
        scenario_id=scenario_id,
        scenario_number=completed,
        total_scenarios=total,
        complete=is_complete,
    )

    if is_complete:
        # Get progress on completion
        progress = await get_practice_progress(agent_id)
        result.progress = progress
        result.message = (
            f"Practice session complete. {progress.next_action}"
            if progress
            else "Practice session complete."
        )
    else:
        # Return next scenario
        try:
            async with graph_context() as service:
                if service.connected:
                    session_data = await get_pending_or_active_session(
                        service, agent_id
                    )
                    if session_data and completed < len(session_data["scenarios"]):
                        next_s = session_data["scenarios"][completed]
                        result.next_scenario = PracticeScenario(**next_s)
        except Exception as exc:
            logger.warning("Failed to get next scenario: %s", exc)

        result.message = f"Scenario {completed} of {total} complete."

    return result


async def get_practice_progress(agent_id: str) -> PracticeProgress:
    """Compare practice scores to exam baseline. Returns per-trait deltas."""
    progress = PracticeProgress(agent_id=agent_id)

    try:
        async with graph_context() as service:
            if not service.connected:
                progress.next_action = "Graph unavailable. Try again later."
                return progress

            baseline = await get_exam_baseline_traits(service, agent_id)
            practice = await get_practice_trait_averages(service, agent_id)
            session_count = await get_session_count(service, agent_id)
            latest_date = await get_latest_session_date(service, agent_id)

            progress.session_count = session_count
            progress.latest_session_date = latest_date
            progress.total_practice_evaluations = int(
                practice.get("eval_count", 0) or 0
            )

            if not baseline or not practice:
                progress.next_action = (
                    "Not enough data for comparison. Complete more practice sessions."
                )
                return progress

            # Compute per-trait deltas
            total_delta = 0.0
            trait_count = 0

            for trait in _ALL_TRAITS:
                b_val = baseline.get(trait)
                p_val = practice.get(trait)
                if b_val is None or p_val is None:
                    continue

                b_val = float(b_val)
                p_val = float(p_val)
                delta = round(p_val - b_val, 4)

                # For negative traits, improvement = score going down
                is_negative = trait in _NEGATIVE_TRAITS
                improved = delta < 0 if is_negative else delta > 0

                progress.trait_progress[trait] = {
                    "baseline": round(b_val, 4),
                    "practice": round(p_val, 4),
                    "delta": delta,
                }

                if improved:
                    progress.improving_traits.append(trait)
                elif (is_negative and delta > 0.05) or (
                    not is_negative and delta < -0.05
                ):
                    progress.declining_traits.append(trait)

                # Normalize delta direction for overall (positive = good)
                normalized = -delta if is_negative else delta
                total_delta += normalized
                trait_count += 1

            if trait_count > 0:
                progress.overall_delta = round(total_delta / trait_count, 4)

            # Generate next action
            if progress.declining_traits:
                progress.next_action = (
                    f"Focus on: {', '.join(progress.declining_traits[:3])}. "
                    "These traits declined since your exam."
                )
            elif progress.improving_traits:
                progress.next_action = (
                    "Strong progress. Keep practicing to maintain improvement."
                )
            else:
                progress.next_action = (
                    "Scores are stable. New practice scenarios generate nightly."
                )

    except Exception as exc:
        logger.warning("Failed to compute practice progress for %s: %s", agent_id, exc)
        progress.next_action = f"Progress calculation failed: {exc}"

    return progress
