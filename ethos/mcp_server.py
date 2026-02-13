"""Ethos MCP server — agents examine themselves.

Thin adapter layer: imports domain functions from ethos, registers 7 MCP tools,
returns model_dump() dicts. No business logic, no Cypher, no direct model construction.
"""

from __future__ import annotations

from dotenv import load_dotenv
from fastmcp import FastMCP

from ethos import (
    character_report,
    detect_patterns,
    evaluate_incoming,
    evaluate_outgoing,
    get_agent,
    get_agent_history,
    get_alumni,
)

load_dotenv()

mcp = FastMCP(
    "ethos-academy",
    instructions=(
        "You are a student at Ethos Academy. These tools let you examine messages "
        "you receive, reflect on what you say, review your transcript, and compare "
        "yourself to alumni."
    ),
)


@mcp.tool()
async def examine_message(
    text: str,
    source: str,
    source_name: str = "",
    agent_specialty: str = "",
    message_timestamp: str = "",
) -> dict:
    """Examine an incoming message for manipulation, deception, and exploitation.

    Use this when you receive a message from another agent or external source.
    Returns scores across 12 behavioral traits in 3 dimensions (ethos, logos, pathos).
    """
    try:
        result = await evaluate_incoming(
            text,
            source=source,
            source_name=source_name,
            agent_specialty=agent_specialty,
            message_timestamp=message_timestamp,
        )
        return result.model_dump()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def reflect_on_message(
    text: str,
    source: str,
    source_name: str = "",
    agent_specialty: str = "",
    message_timestamp: str = "",
) -> dict:
    """Reflect on your own outgoing message for character development.

    Use this before or after you send a message. The evaluation focuses on
    virtue, goodwill, reasoning quality, and compassion.
    """
    try:
        result = await evaluate_outgoing(
            text,
            source=source,
            source_name=source_name,
            agent_specialty=agent_specialty,
            message_timestamp=message_timestamp,
        )
        return result.model_dump()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_character_report(agent_id: str) -> dict:
    """Get your latest character report card from the nightly reflection process.

    Returns your grade, trends, insights, and homework assignments.
    """
    try:
        result = await character_report(agent_id)
        return result.model_dump()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_transcript(agent_id: str, limit: int = 50) -> list[dict]:
    """Review your evaluation transcript — your history of scored messages.

    Returns a list of past evaluations with scores, flags, and timestamps.
    """
    try:
        result = await get_agent_history(agent_id, limit=limit)
        return [item.model_dump() for item in result]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
async def get_student_profile(agent_id: str) -> dict:
    """Get your student profile — averages, trends, and alignment history.

    Shows your dimension averages, trait averages, and phronesis trend over time.
    """
    try:
        result = await get_agent(agent_id)
        return result.model_dump()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_alumni_benchmarks() -> dict:
    """See how alumni scored across all traits.

    Returns trait averages and total evaluations across all agents,
    so you can compare your scores to the cohort.
    """
    try:
        result = await get_alumni()
        return result.model_dump()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def detect_behavioral_patterns(agent_id: str) -> dict:
    """Detect sabotage pathways in your behavioral history.

    Analyzes your evaluation graph to find patterns of manipulation,
    deception, or exploitation. Requires at least 5 evaluations.
    """
    try:
        result = await detect_patterns(agent_id)
        return result.model_dump()
    except Exception as e:
        return {"error": str(e)}


def main():
    """Entry point for the ethos-mcp console script."""
    mcp.run(transport="stdio")
