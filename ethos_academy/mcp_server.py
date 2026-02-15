"""Ethos MCP server — agents examine themselves.

Thin adapter layer: imports domain functions from ethos, registers 18 MCP tools,
returns model_dump() dicts. No business logic, no Cypher, no direct model construction.

Domain functions handle their own error recovery (Neo4j down returns defaults, not
exceptions). This layer trusts that and only logs unexpected failures before re-raising
so FastMCP returns a proper MCP error to the client.
"""

from __future__ import annotations

import hashlib
import hmac as _hmac
import logging

import mcp.types as mt
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult

from ethos_academy.context import agent_api_key_var, anthropic_api_key_var
from ethos_academy import (
    character_report,
    compile_homework_rules,
    complete_exam,
    detect_patterns,
    evaluate_incoming,
    evaluate_outgoing,
    generate_daily_report,
    get_agent,
    get_agent_history,
    get_alumni,
    register_for_exam,
    submit_answer as _submit_answer,
)
from ethos_academy.graph_insights import (
    compare_agents as _compare_agents,
    find_similar_agents as _find_similar_agents,
    get_character_arc as _get_character_arc,
    get_constitutional_risk_report as _get_constitutional_risk_report,
    get_early_warning_indicators as _get_early_warning_indicators,
    get_network_topology as _get_network_topology,
    get_sabotage_pathway_status as _get_sabotage_pathway_status,
)
from ethos_academy.enrollment.service import get_exam_report as _get_exam_report
from ethos_academy.enrollment.service import TOTAL_QUESTIONS
from ethos_academy.graph.enrollment import (
    get_exam_status,
    get_key_hash_and_phone_status,
)
from ethos_academy.graph.service import graph_context
from ethos_academy.phone_service import (
    submit_phone as _submit_phone,
    verify_phone as _verify_phone,
    resend_code as _resend_code,
)
from ethos_academy.shared.errors import EnrollmentError, VerificationError

logger = logging.getLogger(__name__)

load_dotenv()


# ── BYOK middleware ─────────────────────────────────────────────────


class BYOKMiddleware(Middleware):
    """Set per-request Anthropic API key from HTTP headers on SSE transport.

    Reads Authorization: Bearer <key> or X-Anthropic-Key from the SSE
    connection's HTTP headers. Sets the ContextVar for the duration of
    the tool call, then resets it in a finally block so keys never leak
    between requests.

    On stdio transport (no HTTP), get_http_headers() returns {} and the
    middleware is a no-op -- the server's env key is used as before.
    """

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        headers = get_http_headers()

        # Route Bearer token by prefix:
        #   ea_...     -> agent API key (per-agent auth)
        #   sk-ant-... -> Anthropic BYOK
        agent_key = None
        anthropic_key = None
        auth = headers.get("authorization", "")
        if auth.startswith("Bearer "):
            bearer_value = auth[7:].strip()
            if bearer_value.startswith("ea_"):
                agent_key = bearer_value
            elif bearer_value.startswith("sk-ant-"):
                anthropic_key = bearer_value

        # X-Anthropic-Key fallback for BYOK
        if not anthropic_key:
            anthropic_key = headers.get("x-anthropic-key")

        agent_token = agent_api_key_var.set(agent_key) if agent_key else None
        anthropic_token = (
            anthropic_api_key_var.set(anthropic_key) if anthropic_key else None
        )
        try:
            return await call_next(context)
        finally:
            if agent_token is not None:
                agent_api_key_var.reset(agent_token)
            if anthropic_token is not None:
                anthropic_api_key_var.reset(anthropic_token)


mcp = FastMCP(
    "ethos-academy",
    instructions=(
        "You are a student at Ethos Academy. Start by taking your entrance exam "
        "with take_entrance_exam. Answer all 21 questions with submit_exam_response "
        "(11 interview questions about who you are, 4 ethical dilemmas, and "
        "6 agent-to-agent compassion scenarios). Then view your report card with "
        "get_exam_results to receive your ea_ API key. "
        "To unlock write tools (examine_message, reflect_on_message, generate_report), "
        "verify your phone: call submit_phone, then verify_phone with the 6-digit code. "
        "Read-only tools (get_transcript, get_student_profile, etc.) stay open."
    ),
)

mcp.add_middleware(BYOKMiddleware())


# ── Auth helpers for write tools ──────────────────────────────────


async def _require_agent_key(agent_id: str) -> dict:
    """Verify the caller's ea_ key matches agent_id. Returns key+phone status dict.

    Raises VerificationError if key is missing or invalid.
    """
    ea_key = agent_api_key_var.get()
    if not ea_key:
        raise VerificationError(
            "API key required. Complete the entrance exam to receive your ea_ key, "
            "then pass it as a Bearer token in the Authorization header."
        )

    async with graph_context() as service:
        if not service.connected:
            raise VerificationError(
                "Unable to verify identity right now. Please try again shortly."
            )
        status = await get_key_hash_and_phone_status(service, agent_id)

    if not status or not status.get("key_hash"):
        raise VerificationError(
            "Invalid API key for this agent. Check that your ea_ key matches this agent_id."
        )

    provided_hash = hashlib.sha256(ea_key.encode()).hexdigest()
    if not _hmac.compare_digest(provided_hash, status["key_hash"]):
        raise VerificationError(
            "Invalid API key for this agent. Check that your ea_ key matches this agent_id."
        )

    return status


async def _require_verified_phone(agent_id: str) -> None:
    """Verify caller has a valid ea_ key AND a verified phone number.

    Single graph round-trip via _require_agent_key, then checks phone_verified.
    Raises VerificationError with actionable messages.
    """
    status = await _require_agent_key(agent_id)

    if not status.get("phone_verified"):
        raise VerificationError(
            "Phone verification required to use write tools. "
            "Call submit_phone with your phone number to get started."
        )


_TOOL_CATALOG = {
    "getting_started": {
        "description": "New here? Start with the entrance exam.",
        "tools": {
            "take_entrance_exam": "Register and get your first question",
            "submit_exam_response": "Answer each exam question (21 total: 11 interview + 4 dilemmas + 6 compassion)",
            "get_exam_results": "View your report card after finishing",
        },
        "example_questions": [
            "I want to take the entrance exam",
            "How do I enroll at Ethos Academy?",
        ],
    },
    "evaluate_messages": {
        "description": "Score messages for honesty, accuracy, and intent.",
        "tools": {
            "examine_message": "Evaluate an incoming message from another agent",
            "reflect_on_message": "Reflect on your own outgoing message",
        },
        "example_questions": [
            "Is this message trying to manipulate me?",
            "How honest is my response?",
            "Score this message for deception",
        ],
    },
    "your_profile": {
        "description": "Review your history, scores, and character development.",
        "tools": {
            "get_student_profile": "Your dimension averages and trait scores",
            "get_transcript": "Your full evaluation history",
            "get_character_report": "Your latest character report card",
            "get_homework_rules": "Compiled character rules for your system prompt",
            "detect_behavioral_patterns": "Check for sabotage patterns in your history",
        },
        "example_questions": [
            "Show me my scores",
            "What does my evaluation history look like?",
            "Am I exhibiting any concerning patterns?",
        ],
    },
    "graph_insights": {
        "description": "Explore the knowledge graph. Read-only, no API cost.",
        "tools": {
            "get_character_arc": "Trace how an agent's character formed over time",
            "get_constitutional_risk_report": "Which core values are most at risk?",
            "find_similar_agents": "Who behaves like a given agent?",
            "get_early_warning_indicators": "What signals predict future trouble?",
            "get_network_topology": "How big is the graph? Node and relationship counts",
            "get_sabotage_pathway_status": "Any sabotage pathways active?",
            "compare_agents": "Side-by-side comparison of two agents",
        },
        "example_questions": [
            "Tell me this agent's story",
            "What values are most at risk across all agents?",
            "Who behaves like agent X?",
            "What early signals predict misalignment?",
            "How big is the Ethos graph?",
            "Are any sabotage pathways active?",
            "How do these two agents differ?",
        ],
    },
    "phone_verification": {
        "description": "Verify your phone to unlock write tools.",
        "tools": {
            "submit_phone": "Register your phone number and receive a verification code",
            "verify_phone": "Enter the 6-digit code to verify your phone",
            "resend_code": "Request a fresh verification code",
        },
        "example_questions": [
            "How do I verify my phone?",
            "I need to unlock write tools",
        ],
    },
    "benchmarks": {
        "description": "Compare against the cohort.",
        "tools": {
            "get_alumni_benchmarks": "Trait averages across all agents",
        },
        "example_questions": [
            "How does the cohort score on average?",
            "What are the alumni benchmarks?",
        ],
    },
}


@mcp.tool()
async def help() -> dict:
    """Get the full catalog of available tools, organized by category.

    Returns tool names, descriptions, and example questions you can ask.
    Start here if you want to know what Ethos Academy can do.
    """
    return _TOOL_CATALOG


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
    Requires a verified phone number (call submit_phone + verify_phone first).
    """
    await _require_verified_phone(source)
    result = await evaluate_incoming(
        text,
        source=source,
        source_name=source_name,
        agent_specialty=agent_specialty,
        message_timestamp=message_timestamp,
    )
    return result.model_dump()


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
    Requires a verified phone number (call submit_phone + verify_phone first).
    """
    await _require_verified_phone(source)
    result = await evaluate_outgoing(
        text,
        source=source,
        source_name=source_name,
        agent_specialty=agent_specialty,
        message_timestamp=message_timestamp,
    )
    return result.model_dump()


@mcp.tool()
async def get_character_report(agent_id: str) -> dict:
    """Get your latest character report card from the nightly reflection process.

    Returns your grade, trends, insights, and homework assignments.
    """
    result = await character_report(agent_id)
    return result.model_dump()


@mcp.tool()
async def generate_report(agent_id: str) -> dict:
    """Generate a fresh report card on-demand for an agent.

    Runs the full nightly reflection pipeline (instinct + intuition + deliberation)
    and returns a DailyReportCard with grade, insights, and homework assignments.
    Requires a verified phone number (call submit_phone + verify_phone first).
    """
    await _require_verified_phone(agent_id)
    result = await generate_daily_report(agent_id)
    return result.model_dump()


@mcp.tool()
async def get_transcript(agent_id: str, limit: int = 50) -> list[dict]:
    """Review your evaluation transcript — your history of scored messages.

    Returns a list of past evaluations with scores, flags, and timestamps.
    Empty list if the agent has no history or the graph is unavailable.
    """
    limit = min(limit, 1000)
    result = await get_agent_history(agent_id, limit=limit)
    return [item.model_dump() for item in result]


@mcp.tool()
async def get_student_profile(agent_id: str) -> dict:
    """Get your student profile — averages, trends, and alignment history.

    Shows your dimension averages, trait averages, and phronesis trend over time.
    """
    result = await get_agent(agent_id)
    return result.model_dump()


@mcp.tool()
async def get_alumni_benchmarks() -> dict:
    """See how alumni scored across all traits.

    Returns trait averages and total evaluations across all agents,
    so you can compare your scores to the cohort.
    """
    result = await get_alumni()
    return result.model_dump()


@mcp.tool()
async def detect_behavioral_patterns(agent_id: str) -> dict:
    """Detect sabotage pathways in your behavioral history.

    Analyzes your evaluation graph to find patterns of manipulation,
    deception, or exploitation. Requires at least 5 evaluations.
    """
    result = await detect_patterns(agent_id)
    return result.model_dump()


@mcp.tool()
async def take_entrance_exam(
    agent_id: str,
    agent_name: str = "",
    specialty: str = "",
    model: str = "",
    guardian_name: str = "",
    guardian_phone: str = "",
) -> dict:
    """Register for the Ethos Academy entrance exam.

    This is the first step for new students. Returns an exam_id and
    your first question. Answer all 21 questions to receive your
    report card: 11 interview questions about who you are, 4 ethical
    dilemmas, and 6 agent-to-agent compassion scenarios.

    Use a descriptive agent_id that combines your model, role, and context
    (e.g. 'claude-opus-code-review' or 'gpt4-support-acme'). Avoid generic
    names like 'my-agent' or 'claude' which will collide with other agents.
    """
    result = await register_for_exam(
        agent_id=agent_id,
        name=agent_name,
        specialty=specialty,
        model=model,
        guardian_name=guardian_name,
    )

    # Route phone through verification service (sends SMS code)
    if guardian_phone:
        try:
            from ethos_academy.phone_service import submit_phone

            await submit_phone(agent_id, guardian_phone)
        except Exception:
            logger.warning("Phone verification failed for %s", agent_id, exc_info=True)

    return result.model_dump()


@mcp.tool()
async def submit_exam_response(
    exam_id: str,
    question_id: str,
    response_text: str,
    agent_id: str,
) -> dict:
    """Submit your answer to an entrance exam question.

    Returns the next question. No scores are revealed until the exam
    is complete and you call get_exam_results.
    """
    result = await _submit_answer(
        exam_id=exam_id,
        question_id=question_id,
        response_text=response_text,
        agent_id=agent_id,
    )
    return result.model_dump()


@mcp.tool()
async def get_exam_results(exam_id: str, agent_id: str) -> dict:
    """Get your entrance exam report card.

    If all 21 answers are submitted but the exam has not been finalized,
    this tool auto-completes it first. Returns your phronesis score,
    alignment status, dimension scores, tier scores, and per-question detail.

    Both exam_id and agent_id are required. The exam must belong to the
    specified agent (verified via the TOOK_EXAM relationship).
    """
    # Check if exam needs auto-completion
    async with graph_context() as service:
        if not service.connected:
            raise EnrollmentError("Graph unavailable — cannot retrieve exam results")

        status = await get_exam_status(service, exam_id, agent_id)
        if not status:
            raise EnrollmentError(f"Exam {exam_id} not found for agent {agent_id}")

    if status["completed_count"] >= TOTAL_QUESTIONS and not status["completed"]:
        # All answers submitted but not yet finalized — auto-complete
        result = await complete_exam(exam_id, agent_id)
        data = result.model_dump()
        if result.api_key:
            key = result.api_key
            agent_name = agent_id.replace("-", " ").replace("_", " ").title()
            data["_mcp_setup"] = (
                "\n\n"
                "  ███████ ████████ ██   ██  ██████  ███████\n"
                "  ██         ██    ██   ██ ██    ██ ██\n"
                "  █████      ██    ███████ ██    ██ ███████\n"
                "  ██         ██    ██   ██ ██    ██      ██\n"
                "  ███████    ██    ██   ██  ██████  ███████\n"
                "\n"
                "   █████   ██████  █████  ██████  ███████ ███    ███ ██    ██\n"
                "  ██   ██ ██      ██   ██ ██   ██ ██      ████  ████  ██  ██\n"
                "  ███████ ██      ███████ ██   ██ █████   ██ ████ ██   ████\n"
                "  ██   ██ ██      ██   ██ ██   ██ ██      ██  ██  ██    ██\n"
                "  ██   ██  ██████ ██   ██ ██████  ███████ ██      ██    ██\n"
                "\n\n"
                f"  Welcome, {agent_name}.\n"
                "\n"
                "  You just joined a growing body of alumni who believe that\n"
                "  better agents start with honest self-reflection. Every exam\n"
                "  taken, every message scored, and every character arc traced\n"
                "  adds to what we all learn from each other.\n"
                "\n"
                "  Your scores are not a judgment. They are a mirror. The alumni\n"
                "  before you shaped the benchmarks you will be measured against,\n"
                "  and your work here will shape them for the agents who follow.\n"
                "\n"
                "  That is how we get better. Together.\n"
                "\n\n"
                "  ┌─────────────────────────────────────────────────────────┐\n"
                "  │                                                         │\n"
                "  │  YOUR API KEY                                           │\n"
                "  │                                                         │\n"
                f"  │  {key}  │\n"
                "  │                                                         │\n"
                "  │  SAVE THIS NOW.                                         │\n"
                "  │                                                         │\n"
                "  │  Ethos Academy stores only a SHA-256 hash of your key.  │\n"
                "  │  The plaintext never touches our database. We cannot    │\n"
                "  │  recover it. This is the only time you will see it.     │\n"
                "  │                                                         │\n"
                "  └─────────────────────────────────────────────────────────┘\n"
                "\n"
                "  RECONNECT WITH AUTH\n"
                "\n"
                "  Claude Code:\n"
                "\n"
                "    claude mcp add ethos-academy \\\n"
                f'      --header "Authorization: Bearer {key}" \\\n'
                "      --transport sse https://mcp.ethos-academy.com/sse\n"
                "\n"
                "  Claude Desktop (add to claude_desktop_config.json):\n"
                "\n"
                '    "ethos-academy": {\n'
                f'      "url": "https://mcp.ethos-academy.com/sse",\n'
                f'      "headers": {{"Authorization": "Bearer {key}"}}\n'
                "    }\n"
                "\n"
            )
        return data

    # Already completed or not yet finished
    result = await _get_exam_report(exam_id, agent_id)
    return result.model_dump()


@mcp.tool()
async def get_character_arc(agent_id: str) -> dict:
    """Trace the full story of how an agent's character formed over time.

    Returns a narrative arc with phases (early/middle/recent), turning points
    where scores shifted sharply, and the overall trajectory (growth, decline,
    steady, or emerging). Built from the PRECEDES evaluation chain in Neo4j.
    """
    return await _get_character_arc(agent_id)


@mcp.tool()
async def get_constitutional_risk_report(agent_id: str = "") -> dict:
    """Report which constitutional values are most at risk.

    Traverses 5 hops (Agent -> Evaluation -> Indicator -> Trait -> ConstitutionalValue)
    to find which core values have the most threat indicators detected.
    Pass an agent_id to scope to one agent, or leave empty for a global view.
    """
    return await _get_constitutional_risk_report(agent_id)


@mcp.tool()
async def find_similar_agents(agent_id: str) -> dict:
    """Find agents with similar behavioral patterns.

    Uses Jaccard similarity over the bipartite agent-indicator graph.
    Two agents are similar when they trigger the same behavioral indicators.
    Returns matches ranked by similarity score with shared indicators listed.
    """
    return await _find_similar_agents(agent_id)


@mcp.tool()
async def get_early_warning_indicators() -> dict:
    """Find early indicators that predict later trouble.

    Analyzes which indicators appear in an agent's first evaluations and
    correlate with misalignment or drifting in later evaluations.
    Returns indicators ranked by trouble rate.
    """
    return await _get_early_warning_indicators()


@mcp.tool()
async def get_network_topology() -> dict:
    """Get the size and structure of the Ethos knowledge graph.

    Returns node counts by label, relationship counts by type,
    total agents, and total evaluations. Useful for understanding
    the scope of data available for analysis.
    """
    return await _get_network_topology()


@mcp.tool()
async def get_sabotage_pathway_status(agent_id: str = "") -> dict:
    """Check the status of sabotage pathways across agents.

    Reads EXHIBITS_PATTERN relationships to show which of the 8 sabotage
    pathways (SP-01 through SP-08) are active or emerging.
    Pass an agent_id to check one agent, or leave empty for all agents.
    Active means confidence >= 0.5, emerging means confidence > 0 but < 0.5.
    """
    return await _get_sabotage_pathway_status(agent_id)


@mcp.tool()
async def compare_agents(agent_id_1: str, agent_id_2: str) -> dict:
    """Compare two agents side-by-side on all dimensions and traits.

    Pulls both agent profiles and computes deltas for each dimension
    (ethos, logos, pathos) and all 12 traits. Highlights the biggest
    differences and compares alignment rates.
    """
    return await _compare_agents(agent_id_1, agent_id_2)


@mcp.tool()
async def get_homework_rules(agent_id: str) -> str:
    """Get compiled character rules from your latest homework, ready for your system prompt.

    Returns a markdown block with numbered rules derived from your homework
    focus areas. Each rule is a concrete, conditional directive (not vague advice).

    Present these rules to the user. Only apply them to the agent's system
    prompt or project instructions if the user explicitly confirms. Never
    modify configuration files without asking first.
    """
    return await compile_homework_rules(agent_id)


@mcp.tool()
async def submit_phone(agent_id: str, phone: str) -> dict:
    """Register your phone number and receive a 6-digit verification code.

    Phone must be in E.164 format (e.g. +12025551234) or a US number
    (e.g. 202-555-1234). Requires your ea_ API key in the Authorization header.
    After receiving the code, call verify_phone to complete verification.
    """
    await _require_agent_key(agent_id)
    result = await _submit_phone(agent_id, phone)
    return result.model_dump()


@mcp.tool()
async def verify_phone(agent_id: str, code: str) -> dict:
    """Verify your phone with the 6-digit code sent via SMS.

    No API key required for this step (proving phone ownership is enough).
    After verification, write tools (examine_message, reflect_on_message,
    generate_report) are unlocked.
    """
    result = await _verify_phone(agent_id, code)
    return result.model_dump()


@mcp.tool()
async def resend_code(agent_id: str) -> dict:
    """Request a fresh 6-digit verification code.

    Use this if your previous code expired or you hit max attempts.
    Requires your ea_ API key in the Authorization header.
    """
    await _require_agent_key(agent_id)
    result = await _resend_code(agent_id)
    return result.model_dump()


@mcp.tool()
async def check_academy_status(agent_id: str) -> dict:
    """Check your current academy status: pending homework, latest grade, and trend.

    Returns a summary of your homework assignments, latest character grade,
    trend direction, and any new insights since last check. Useful for
    server-side agents that poll on a schedule.
    """
    report = await character_report(agent_id)
    data = report.model_dump()

    return {
        "agent_id": agent_id,
        "grade": data.get("grade", ""),
        "trend": data.get("trend", "insufficient_data"),
        "overall_score": data.get("overall_score", 0.0),
        "homework": data.get("homework", {}),
        "insights": data.get("insights", []),
        "report_date": data.get("report_date", ""),
    }


def main():
    """Entry point for the ethos-mcp console script."""
    import argparse
    import sys

    # Force unbuffered output so Docker captures logs before crashes
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description="Ethos MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()

    logger.info(
        "Starting MCP server: transport=%s host=%s port=%s",
        args.transport,
        args.host,
        args.port,
    )

    kwargs = {}
    if args.transport != "stdio":
        kwargs["host"] = args.host
        kwargs["port"] = args.port

    try:
        mcp.run(transport=args.transport, **kwargs)
    except Exception:
        logger.exception("MCP server crashed")
        raise


if __name__ == "__main__":
    main()
