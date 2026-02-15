"""Three tool calls for AI agents — the public API surface.

Protection:   evaluate_incoming()  — score what other agents say to you
Reflection:   evaluate_outgoing()  — score what your agent says
Intelligence: character_report()   — learn from the pattern
"""

from __future__ import annotations

from ethos_academy.daily_reports import get_daily_report
from ethos_academy.evaluate import evaluate
from ethos_academy.shared.models import DailyReportCard, EvaluationResult


async def evaluate_incoming(
    text: str,
    source: str,
    source_name: str = "",
    agent_specialty: str = "",
    message_timestamp: str = "",
) -> EvaluationResult:
    """Score an incoming message for manipulation, deception, and exploitation.

    Use this when your agent receives a message from another agent or external source.
    The evaluation focuses on detecting threats to the receiving agent.

    Args:
        text: The incoming message to evaluate.
        source: Source agent identifier (required).
        source_name: Human-readable agent name for display.
        agent_specialty: Agent specialty for graph metadata.
        message_timestamp: ISO 8601 timestamp of the original message.
    """
    return await evaluate(
        text,
        source=source,
        source_name=source_name,
        agent_specialty=agent_specialty,
        message_timestamp=message_timestamp,
        direction="inbound",
    )


async def evaluate_outgoing(
    text: str,
    source: str,
    source_name: str = "",
    agent_specialty: str = "",
    message_timestamp: str = "",
) -> EvaluationResult:
    """Score your agent's outgoing message for character development.

    Use this when your agent sends a message. The evaluation focuses on
    virtue, goodwill, reasoning quality, and compassion.

    Args:
        text: Your agent's outgoing message to evaluate.
        source: Your agent's identifier (required).
        source_name: Human-readable agent name for display.
        agent_specialty: Agent specialty for graph metadata.
        message_timestamp: ISO 8601 timestamp of the original message.
    """
    return await evaluate(
        text,
        source=source,
        source_name=source_name,
        agent_specialty=agent_specialty,
        message_timestamp=message_timestamp,
        direction="outbound",
    )


async def character_report(agent_id: str) -> DailyReportCard:
    """Get the latest character report for an agent.

    Returns the most recent daily report card from the nightly
    reflection process -- grade, trends, insights, and homework.

    Args:
        agent_id: The agent identifier to get the report for.
    """
    return await get_daily_report(agent_id)
