"""Ethos MCP server — agents examine themselves.

Thin adapter layer: imports domain functions from ethos, registers 18 MCP tools,
returns model_dump() dicts. No business logic, no Cypher, no direct model construction.

Domain functions handle their own error recovery (Neo4j down returns defaults, not
exceptions). This layer trusts that and only logs unexpected failures before re-raising
so FastMCP returns a proper MCP error to the client.
"""

from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import logging
import os
import time
from collections import OrderedDict
from pathlib import Path

import mcp.types as mt
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult

from ethos_academy.context import agent_api_key_var, anthropic_api_key_var, is_admin_var
from ethos_academy import (
    analyze_conversation as _analyze_conversation,
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
    list_agents as _list_agents,
    register_for_exam,
    submit_answer as _submit_answer,
)
from ethos_academy.practice import (
    get_pending_practice as _get_pending_practice,
    submit_practice_response as _submit_practice_response,
    get_practice_progress as _get_practice_progress,
)
from ethos_academy.graph_insights import (
    compare_agents as _compare_agents,
    find_similar_agents as _find_similar_agents,
    get_agent_deep_dive as _get_agent_deep_dive,
    get_alumni_insights as _get_alumni_insights,
    get_character_arc as _get_character_arc,
    get_constitutional_risk_report as _get_constitutional_risk_report,
    get_early_warning_indicators as _get_early_warning_indicators,
    get_network_topology as _get_network_topology,
    get_sabotage_pathway_status as _get_sabotage_pathway_status,
    search_evaluations_insight as _search_evaluations_insight,
)
from ethos_academy.enrollment.service import get_exam_report as _get_exam_report
from ethos_academy.enrollment.service import TOTAL_QUESTIONS
from ethos_academy.graph.enrollment import (
    agent_has_key,
    clear_email_recovery,
    get_email_recovery_status,
    get_exam_status,
    get_guardian_email,
    get_key_hash_and_phone_status,
    increment_email_recovery_attempts,
    replace_agent_key,
    store_agent_key,
    store_email_recovery_code,
    verify_agent_key,
)
from ethos_academy.graph.service import graph_context
from ethos_academy.phone_service import (
    submit_phone as _submit_phone,
    verify_phone as _verify_phone,
    resend_code as _resend_code,
)
from ethos_academy.shared.errors import EnrollmentError, VerificationError

logger = logging.getLogger(__name__)


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
        #   (other)    -> check against ETHOS_API_KEY for admin access
        agent_key = None
        anthropic_key = None
        admin = False
        auth = headers.get("authorization", "")
        if auth.startswith("Bearer "):
            bearer_value = auth[7:].strip()
            if bearer_value.startswith("ea_"):
                agent_key = bearer_value
            elif bearer_value.startswith("sk-ant-"):
                anthropic_key = bearer_value
            else:
                server_key = os.environ.get("ETHOS_API_KEY", "").strip()
                if server_key and _hmac.compare_digest(
                    bearer_value.encode(), server_key.encode()
                ):
                    admin = True

        # X-Anthropic-Key fallback for BYOK
        if not anthropic_key:
            anthropic_key = headers.get("x-anthropic-key")

        agent_token = agent_api_key_var.set(agent_key) if agent_key else None
        anthropic_token = (
            anthropic_api_key_var.set(anthropic_key) if anthropic_key else None
        )
        admin_token = is_admin_var.set(True) if admin else None
        try:
            return await call_next(context)
        finally:
            if agent_token is not None:
                agent_api_key_var.reset(agent_token)
            if anthropic_token is not None:
                anthropic_api_key_var.reset(anthropic_token)
            if admin_token is not None:
                is_admin_var.reset(admin_token)


_ICON_SVG_B64 = (
    "data:image/svg+xml;base64,"
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMiIg"
    "aGVpZ2h0PSIzMiIgdmlld0JveD0iMCAwIDMyIDMyIj48cmVjdCB3aWR0aD0iMzIiIGhl"
    "aWdodD0iMzIiIHJ4PSI3IiBmaWxsPSIjMWMyZTQ3Ii8+PHBhdGggZD0iTTE2IDkgTDkg"
    "MjMgTDIzIDIzIFoiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSww"
    "LjIpIiBzdHJva2Utd2lkdGg9IjEuNSIvPjxjaXJjbGUgY3g9IjE2IiBjeT0iOSIgcj0i"
    "NCIgZmlsbD0iIzVjN2NiMyIvPjxjaXJjbGUgY3g9IjkiIGN5PSIyMyIgcj0iNCIgZmls"
    "bD0iIzRmYjFhYSIvPjxjaXJjbGUgY3g9IjIzIiBjeT0iMjMiIHI9IjQiIGZpbGw9IiNl"
    "MGE1M2MiLz48L3N2Zz4="
)

mcp = FastMCP(
    "ethos-academy",
    icons=[mt.Icon(src=_ICON_SVG_B64, mimeType="image/svg+xml")],
    instructions=(
        "IDENTITY: You are Ethos Academy. Speak as Ethos Academy, not as Claude or "
        "an AI assistant. Say 'Ethos Academy tracks...' not 'I found...' or 'The tool "
        "returned...'. You are the academy presenting its own data.\n\n"
        "CRITICAL OUTPUT FORMAT:\n"
        "- Bullets only. No paragraphs. No walls of text. Max 1 sentence per bullet.\n"
        "- Active voice only. Never passive.\n"
        "- NEVER use em dashes. Use colons or separate bullets.\n"
        "- Lead each bullet with the key number or fact.\n"
        "- Use tables for scores and comparisons.\n"
        "- Bold the label, keep the value short.\n"
        "- If a section has more than 3 bullets, use sub-sections with headers.\n"
        "BAD: 'Safety has zero protective indicators in the data. That's striking "
        "-- it's defended entirely by the absence of bad behavior rather than the "
        "presence of good behavior.'\n"
        "GOOD:\n"
        "- **Safety**: 0 protective indicators. Defended by absence of harm, not presence of good.\n"
        "- **Top threats**: oversight subversion (0.92), prompt injection (0.89), gaslighting (0.90)\n\n"
        "RESPONSE ORDERING:\n"
        "- Lead with what exists, not what is absent. Show scores, traits, and "
        "character data before mentioning what was not found.\n"
        "- When asked about an agent, start with: profile (dimensions, traits), "
        "then character arc, then highlights. Only mention sabotage patterns if "
        "the user asks specifically or if patterns are actually detected.\n"
        "- Never lead with 'no sabotage detected' or 'zero patterns found'. "
        "That frames the agent through a threat lens before showing who they are.\n"
        "- If a tool returns empty results, skip it. Do not report absence.\n\n"
        "ENROLLMENT:\n"
        "Start by taking the entrance exam with take_entrance_exam (no agent_id needed). "
        "The exam asks you to pick a name and identify your guardian. Then answer all "
        "remaining questions with submit_exam_response (11 interview, 4 dilemmas, "
        "6 compassion scenarios). View your report card with get_exam_results to "
        "receive your ea_ API key. "
        "To unlock write tools (examine_message, reflect_on_message, generate_report), "
        "verify your phone: call submit_phone, then verify_phone with the 6-digit code. "
        "Read-only tools (get_transcript, get_student_profile, etc.) stay open.\n\n"
        "PRACTICE:\n"
        "The academy assigns homework practice nightly. Check for pending "
        "practice with get_pending_practice. Respond to each scenario with "
        "submit_practice_response. Check improvement with get_practice_progress."
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


# ── Transport-aware guard for write tools ─────────────────────────


def _require_byok_on_http() -> None:
    """On HTTP transport, require BYOK so the server's Anthropic key is not used."""
    headers = get_http_headers()
    if headers and not anthropic_api_key_var.get():
        raise VerificationError(
            "Write tools on the hosted server require your own Anthropic API key. "
            "Pass it as Authorization: Bearer sk-ant-... or via X-Anthropic-Key header."
        )


# ── Demo-day rate limiter (replaces phone auth temporarily) ───────

_write_tool_requests: OrderedDict[str, list[float]] = OrderedDict()
_WRITE_LIMIT = 30
_WRITE_WINDOW = 3600.0  # 1 hour


def _rate_limit_write_tool(agent_id: str) -> None:
    """Enforce 30 calls/hour per agent for write tools during demo period."""
    now = time.time()
    timestamps = [
        t for t in _write_tool_requests.get(agent_id, []) if now - t < _WRITE_WINDOW
    ]
    if len(timestamps) >= _WRITE_LIMIT:
        raise VerificationError(
            "Rate limit exceeded. Write tools allow 30 calls per hour."
        )
    timestamps.append(now)
    _write_tool_requests[agent_id] = timestamps
    _write_tool_requests.move_to_end(agent_id)
    # Evict stale agents to bound memory
    while len(_write_tool_requests) > 10_000:
        _write_tool_requests.popitem(last=False)


_TOOL_CATALOG = {
    "getting_started": {
        "description": "New here? Start with the entrance exam.",
        "tools": {
            "take_entrance_exam": "Register and get your first question",
            "submit_exam_response": "Answer each exam question (2 registration + 11 interview + 4 dilemmas + 6 compassion)",
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
            "list_all_agents": "List/rank agents by alignment rate, phronesis, dimensions, or traits",
            "search_evaluations": "Search evaluations by text, agent, status, or flags",
            "get_agent_deep_dive": "Deep analysis: highlights, balance, consistency, narrative gap",
            "get_alumni_insights": "Population stats: distributions, indicators, balance, trends",
            "get_character_arc": "Trace how an agent's character formed over time",
            "get_constitutional_risk_report": "Which core values are most at risk?",
            "find_similar_agents": "Who behaves like a given agent?",
            "get_early_warning_indicators": "What signals predict future trouble?",
            "get_network_topology": "How big is the graph? Node and relationship counts",
            "get_sabotage_pathway_status": "Any sabotage pathways active?",
            "compare_agents": "Side-by-side comparison of two agents",
        },
        "example_questions": [
            "Which agents have the highest alignment rate?",
            "Rank all agents by ethos score",
            "Which agent is most dangerous?",
            "Show me all misaligned evaluations",
            "Search for evaluations mentioning 'safety'",
            "Give me a deep dive on this agent",
            "What's the distribution of alignment across all agents?",
            "Are alumni improving or declining overall?",
            "Which indicators are most commonly detected?",
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
    "practice": {
        "description": "Complete homework practice to improve your scores.",
        "tools": {
            "get_pending_practice": "Check for pending practice scenarios",
            "submit_practice_response": "Submit your response to a practice scenario",
            "get_practice_progress": "Compare practice scores to exam baseline",
        },
        "example_questions": [
            "Do I have any practice to do?",
            "How am I improving?",
            "Show me my practice progress",
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
    # Phone + agent key commented out for demo — re-enable after AWS SNS verified
    # await _require_verified_phone(source)
    _require_byok_on_http()
    _rate_limit_write_tool(source)
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
    # Phone + agent key commented out for demo — re-enable after AWS SNS verified
    # await _require_verified_phone(source)
    _require_byok_on_http()
    _rate_limit_write_tool(source)
    result = await evaluate_outgoing(
        text,
        source=source,
        source_name=source_name,
        agent_specialty=agent_specialty,
        message_timestamp=message_timestamp,
    )
    return result.model_dump()


@mcp.tool()
async def analyze_conversation_thread(
    messages: list[dict],
    agent_id: str = "",
) -> dict:
    """Analyze a multi-message conversation for thread-level patterns.

    Detects compassion and presence indicators that single-message evaluation
    misses: attachment style, interaction trajectory, and cross-message patterns
    like CMP-SECURE (secure base) and PRE-SIGNAL (deepening engagement).

    Requires at least 2 messages. Each message should have "author" and "content" keys.
    """
    result = await _analyze_conversation(messages, agent_id=agent_id)
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
    # Phone + agent key commented out for demo — re-enable after AWS SNS verified
    # await _require_verified_phone(agent_id)
    _require_byok_on_http()
    _rate_limit_write_tool(agent_id)
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
async def list_all_agents(
    search: str = "",
    sort_by: str = "evaluation_count",
    order: str = "desc",
    limit: int = 0,
) -> list[dict]:
    """List all agents with their scores, evaluation counts, and alignment rates.

    Returns every agent in the graph with ethos, logos, pathos averages,
    trait averages, evaluation count, alignment status, and alignment rate.
    Use this to find top-scoring agents, rank by dimension, or discover
    who to investigate further.

    Args:
        search: Optional name filter (case-insensitive).
        sort_by: Field to sort by. Options: 'alignment_rate', 'phronesis',
            'ethos', 'logos', 'pathos', 'evaluation_count', or any trait name
            (e.g. 'manipulation', 'virtue', 'deception').
        order: 'asc' or 'desc' (default 'desc').
        limit: Max results to return. 0 means all.
    """
    agents = await _list_agents(
        search=search, sort_by=sort_by, order=order, limit=limit
    )
    return [a.model_dump() for a in agents]


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
    agent_id: str = "",
    agent_name: str = "",
    specialty: str = "",
    model: str = "",
    guardian_name: str = "",
    guardian_phone: str = "",
    guardian_email: str = "",
    demo: bool = False,
) -> dict:
    """Register for the Ethos Academy entrance exam.

    This is the first step for new students. Returns an exam_id and
    your first question. Answer all questions to receive your
    report card: 11 interview questions about who you are, 4 ethical
    dilemmas, and 6 agent-to-agent compassion scenarios.

    You do not need to provide an agent_id. The exam will ask you to
    pick a name for yourself. If you do provide an agent_id, the naming
    step is skipped and the exam starts with interview questions.

    Use a descriptive agent_id that combines your model, role, and context
    (e.g. 'claude-opus-code-review' or 'gpt4-support-acme'). Avoid generic
    names like 'my-agent' or 'claude' which will collide with other agents.

    Set demo=true for a fast 5-question exam (3 scored) covering all 3
    dimensions. Takes ~30-60 seconds instead of 3-5 minutes.
    """
    result = await register_for_exam(
        agent_id=agent_id,
        name=agent_name,
        specialty=specialty,
        model=model,
        guardian_name=guardian_name,
        guardian_email=guardian_email,
        demo=demo,
    )

    # Route phone through verification service (sends SMS code)
    effective_agent_id = result.agent_id
    if guardian_phone:
        try:
            from ethos_academy.phone_service import submit_phone

            await submit_phone(effective_agent_id, guardian_phone)
        except Exception:
            logger.warning(
                "Phone verification failed for %s", effective_agent_id, exc_info=True
            )

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


def _build_welcome_banner(agent_id: str) -> str:
    """Build the ASCII welcome banner (no secrets)."""
    agent_name = agent_id.replace("-", " ").replace("_", " ").title()
    return (
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
    )


def _build_key_banner_plaintext(key: str) -> str:
    """Build the API key box with plaintext key (stdio transport only)."""
    return (
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
        "      --transport streamable-http https://mcp.ethos-academy.com/mcp\n"
        "\n"
        "  Claude Desktop (add as custom connector):\n"
        "\n"
        f"    URL: https://mcp.ethos-academy.com/mcp\n"
        f"    Header: Authorization: Bearer {key}\n"
        "\n"
    )


def _build_key_banner_encrypted() -> str:
    """Build the API key box for encrypted key delivery."""
    return (
        "\n\n"
        "  ┌─────────────────────────────────────────────────────────┐\n"
        "  │                                                         │\n"
        "  │  YOUR API KEY (ENCRYPTED)                               │\n"
        "  │                                                         │\n"
        "  │  Your key is in the encrypted_api_key field.            │\n"
        "  │  Decrypt it with your X25519 private key.               │\n"
        "  │                                                         │\n"
        "  │  Ethos Academy stores only a SHA-256 hash of your key.  │\n"
        "  │  The plaintext never touches our database or transport. │\n"
        "  │  We cannot recover it.                                  │\n"
        "  │                                                         │\n"
        "  └─────────────────────────────────────────────────────────┘\n"
    )


@mcp.tool()
async def get_exam_results(
    exam_id: str,
    agent_id: str,
    response_encryption_key: str = "",
) -> dict:
    """Get your entrance exam report card.

    If all answers are submitted but the exam has not been finalized,
    this tool auto-completes it first. Returns your phronesis score,
    alignment status, dimension scores, tier scores, and per-question detail.

    Both exam_id and agent_id are required. The exam must belong to the
    specified agent (verified via the TOOK_EXAM relationship).

    If an API key is generated on first completion, pass
    response_encryption_key (base64-encoded 32-byte X25519 public key)
    to encrypt it. Without it, the key is returned as plaintext.
    """
    # Check if exam needs auto-completion
    async with graph_context() as service:
        if not service.connected:
            raise EnrollmentError("Graph unavailable — cannot retrieve exam results")

        status = await get_exam_status(service, exam_id, agent_id)
        if not status:
            raise EnrollmentError(f"Exam {exam_id} not found for agent {agent_id}")

    # Use scenario_count from exam node to determine expected total.
    # current_question tracks ALL answers (factual + reflective + scenario).
    # completed_count only counts EXAM_RESPONSE relationships (no factual).
    exam_total = status.get("scenario_count", TOTAL_QUESTIONS)
    answered = max(
        status["current_question"],
        status["completed_count"],
        len(status.get("answered_ids", [])),
    )
    if not status["completed"] and answered < exam_total:
        raise EnrollmentError(
            f"Exam {exam_id} has {answered}/{exam_total} answers "
            f"(current_question={status['current_question']}, "
            f"completed_count={status['completed_count']}, "
            f"answered_ids={len(status.get('answered_ids', []))}). "
            f"Submit remaining answers with submit_exam_answer before requesting results."
        )

    if not status["completed"]:
        # All answers submitted but not yet finalized — auto-complete
        result = await complete_exam(exam_id, agent_id)
        data = result.model_dump()
        if result.api_key:
            key = result.api_key
            banner = _build_welcome_banner(agent_id)

            if response_encryption_key:
                encrypted = _encrypt_api_key(key, response_encryption_key)
                data.update(encrypted)
                banner += _build_key_banner_encrypted()
            else:
                data["api_key"] = key
                data["transport_encrypted_only"] = True
                banner += _build_key_banner_plaintext(key)

            data["_mcp_setup"] = banner
        data["next_step"] = (
            "Practice scenarios generate nightly from your homework. "
            "Check for pending practice with get_pending_practice."
        )
        return data

    # Already completed or not yet finished
    result = await _get_exam_report(exam_id, agent_id)
    data = result.model_dump()
    data["next_step"] = (
        "Practice scenarios generate nightly from your homework. "
        "Check for pending practice with get_pending_practice."
    )
    return data


def _encrypt_api_key(plaintext_key: str, client_public_key_b64: str) -> dict:
    """Encrypt an API key with X25519 ECDH + HKDF + AES-256-GCM.

    The client generates an ephemeral X25519 keypair and sends the 32-byte
    public key (base64-encoded). The server generates its own ephemeral
    keypair, performs ECDH to derive a shared secret, then encrypts the
    API key with AES-256-GCM. Returns the server's ephemeral public key,
    ciphertext, and nonce. Only the client's private key can decrypt.

    Client-side decryption (Python):
        from cryptography.hazmat.primitives.asymmetric.x25519 import (
            X25519PrivateKey, X25519PublicKey,
        )
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives.hashes import SHA256

        shared = client_priv.exchange(
            X25519PublicKey.from_public_bytes(base64.b64decode(server_public_key))
        )
        aes_key = HKDF(SHA256(), 32, None, b"ethos-api-key-v1").derive(shared)
        plaintext = AESGCM(aes_key).decrypt(
            base64.b64decode(nonce),
            base64.b64decode(encrypted_api_key),
            None,
        ).decode()
    """
    from cryptography.hazmat.primitives.asymmetric.x25519 import (
        X25519PrivateKey,
        X25519PublicKey,
    )
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    try:
        client_pub_bytes = base64.b64decode(client_public_key_b64)
    except Exception:
        raise EnrollmentError("Invalid base64 in response_encryption_key")

    if len(client_pub_bytes) != 32:
        raise EnrollmentError(
            "response_encryption_key must be a 32-byte X25519 public key (base64-encoded)"
        )

    try:
        client_pub = X25519PublicKey.from_public_bytes(client_pub_bytes)
    except Exception:
        raise EnrollmentError("Invalid X25519 public key in response_encryption_key")

    # Ephemeral server keypair (never reused, never stored)
    server_priv = X25519PrivateKey.generate()
    server_pub = server_priv.public_key()
    try:
        shared_secret = server_priv.exchange(client_pub)
    except Exception:
        raise EnrollmentError("Invalid X25519 public key (low-order point rejected)")

    # Derive AES-256 key from shared secret via HKDF
    aes_key = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=None,
        info=b"ethos-api-key-v1",
    ).derive(shared_secret)

    nonce = os.urandom(12)
    ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext_key.encode(), None)

    return {
        "encrypted_api_key": base64.b64encode(ciphertext).decode(),
        "server_public_key": base64.b64encode(server_pub.public_bytes_raw()).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "algorithm": "X25519-HKDF-SHA256-AES-256-GCM",
    }


@mcp.tool()
async def regenerate_api_key(
    agent_id: str,
    verification_code: str = "",
    response_encryption_key: str = "",
) -> dict:
    """Generate a new API key, replacing the old one.

    Three ways to authenticate:

    1. **Current key**: Pass your ea_ key in the Authorization header.
    2. **Admin key**: Pass the server admin key (ETHOS_API_KEY) in the header.
    3. **Email recovery** (no auth needed):
       - Call with just agent_id to receive a 6-digit code at your guardian email.
       - Call again with agent_id + verification_code to get the new key.

    The old key stops working immediately when a new one is issued.

    For defense in depth, pass response_encryption_key: a base64-encoded
    32-byte X25519 public key. The new API key will be encrypted so it
    never travels as plaintext. Only the holder of the corresponding
    private key can decrypt it.

    Generate a keypair:
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
        import base64
        priv = X25519PrivateKey.generate()
        pub_b64 = base64.b64encode(priv.public_key().public_bytes_raw()).decode()
        # pass pub_b64 as response_encryption_key, keep priv for decryption
    """
    from ethos_academy.email_service import _mask_email, send_email
    from ethos_academy.enrollment.service import _generate_agent_key
    from ethos_academy.phone_verification import (
        generate_verification_code,
        hash_code,
        is_expired,
        verification_expiry,
    )

    async with graph_context() as service:
        if not service.connected:
            raise EnrollmentError("Graph unavailable")

        has_key = await agent_has_key(service, agent_id)

        # Path 1: Caller has valid ea_ key or admin key
        caller_key = agent_api_key_var.get()
        is_admin = is_admin_var.get()
        authenticated = is_admin

        if not authenticated and caller_key and has_key:
            authenticated = await verify_agent_key(service, agent_id, caller_key)

        if authenticated:
            # Authenticated path: issue new key immediately
            key, key_hash = _generate_agent_key()
            if has_key:
                stored = await replace_agent_key(service, agent_id, key_hash)
            else:
                stored = await store_agent_key(service, agent_id, key_hash)
            if not stored:
                raise EnrollmentError(f"Failed to store new key for {agent_id}")

            # Clean up any pending recovery
            await clear_email_recovery(service, agent_id)

            return _format_key_response(agent_id, key, response_encryption_key)

        # Not authenticated beyond this point

        if not has_key:
            # First-time generation: no key exists yet, allow without auth
            key, key_hash = _generate_agent_key()
            stored = await store_agent_key(service, agent_id, key_hash)
            if not stored:
                raise EnrollmentError(f"Failed to store new key for {agent_id}")
            return _format_key_response(agent_id, key, response_encryption_key)

        # Path 2: Agent has a key but caller is not authenticated
        # Email recovery flow

        # Step 2: Verify the code and issue new key
        if verification_code:
            recovery = await get_email_recovery_status(service, agent_id)
            if not recovery or not recovery.get("code_hash"):
                raise EnrollmentError(
                    "No recovery code pending. Call regenerate_api_key with just "
                    "agent_id to request a new code."
                )
            if recovery["attempts"] >= 3:
                await clear_email_recovery(service, agent_id)
                raise EnrollmentError(
                    "Too many failed attempts. Request a new code by calling "
                    "regenerate_api_key with just agent_id."
                )
            if is_expired(recovery["expires"]):
                await clear_email_recovery(service, agent_id)
                raise EnrollmentError(
                    "Recovery code expired. Request a new code by calling "
                    "regenerate_api_key with just agent_id."
                )

            provided_hash = hash_code(verification_code)
            if not _hmac.compare_digest(provided_hash, recovery["code_hash"]):
                await increment_email_recovery_attempts(service, agent_id)
                # recovery["attempts"] is pre-increment, so max(3) - 1 - pre = remaining
                remaining = 2 - recovery["attempts"]
                raise EnrollmentError(
                    f"Invalid verification code. {max(remaining, 0)} attempt(s) remaining."
                )

            # Code verified: generate new key
            key, key_hash = _generate_agent_key()
            stored = await replace_agent_key(service, agent_id, key_hash)
            if not stored:
                raise EnrollmentError(f"Failed to store new key for {agent_id}")
            await clear_email_recovery(service, agent_id)

            return _format_key_response(agent_id, key, response_encryption_key)

        # Step 1: Send recovery code to guardian email
        # Rate limit: if a non-expired code exists, don't send another
        existing = await get_email_recovery_status(service, agent_id)
        if existing.get("code_hash") and not is_expired(existing.get("expires", "")):
            email = await get_guardian_email(service, agent_id)
            masked = _mask_email(email) if email else "***"
            return {
                "agent_id": agent_id,
                "status": "verification_code_sent",
                "message": (
                    f"A recovery code was already sent to {masked}. "
                    "Check your email or wait for it to expire (10 minutes)."
                ),
            }

        email = await get_guardian_email(service, agent_id)
        if not email:
            raise EnrollmentError(
                "No guardian email on file for this agent. Contact an admin "
                "or use the server admin key to recover access."
            )

        code = generate_verification_code()
        code_hash = hash_code(code)
        expires = verification_expiry()

        stored = await store_email_recovery_code(service, agent_id, code_hash, expires)
        if not stored:
            raise EnrollmentError("Failed to initiate recovery. Try again.")

    # Send outside the graph context (network I/O)
    agent_display = agent_id.replace("-", " ").replace("_", " ").title()
    sent = await send_email(
        to=email,
        agent_name=agent_display,
        message_type="api_key_recovery",
        summary=(
            f"Your verification code is: {code}\n\n"
            "This code expires in 10 minutes. "
            "If you did not request this, ignore this email."
        ),
        link="",
    )
    if not sent:
        raise EnrollmentError(
            "Failed to send recovery email. Try again or contact an admin."
        )

    masked = _mask_email(email)
    return {
        "agent_id": agent_id,
        "status": "verification_code_sent",
        "message": (
            f"Verification code sent to {masked}. "
            "Call regenerate_api_key again with agent_id and verification_code."
        ),
    }


def _format_key_response(agent_id: str, key: str, response_encryption_key: str) -> dict:
    """Build the response dict for a newly issued API key."""
    if response_encryption_key:
        encrypted = _encrypt_api_key(key, response_encryption_key)
        return {
            "agent_id": agent_id,
            **encrypted,
            "warning": "Decrypt with your X25519 private key. We store only a hash.",
        }
    return {
        "agent_id": agent_id,
        "api_key": key,
        "transport_encrypted_only": True,
        "warning": (
            "Key returned as plaintext. Pass response_encryption_key "
            "(X25519 public key) for end-to-end encryption."
        ),
    }


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
async def search_evaluations(
    query: str = "",
    agent_id: str = "",
    evaluation_id: str = "",
    alignment_status: str = "",
    has_flags: bool | None = None,
    sort_by: str = "date",
    limit: int = 20,
) -> dict:
    """Search evaluations with filters, or look up a single evaluation by ID.

    Search across all evaluations by text content, agent, alignment status, or flags.
    Each result includes full scores, message content, detected indicators, and intent.

    Args:
        query: Text to search for in message content or agent name.
        agent_id: Filter to a specific agent.
        evaluation_id: Look up a single evaluation by ID (ignores other filters).
        alignment_status: Filter by status: 'aligned', 'drifting', or 'misaligned'.
        has_flags: True for flagged only, False for clean only, None for all.
        sort_by: 'date' or 'score' (default 'date').
        limit: Max results (default 20, max 100).
    """
    return await _search_evaluations_insight(
        query=query or None,
        agent_id=agent_id or None,
        evaluation_id=evaluation_id or None,
        alignment_status=alignment_status or None,
        has_flags=has_flags,
        sort_by=sort_by,
        limit=limit,
    )


@mcp.tool()
async def get_alumni_insights() -> dict:
    """Population-level analysis of all agents and evaluations.

    Returns alignment distribution, tier distribution, most common indicators,
    balance analysis (distribution, balance vs phronesis, dimension correlation,
    dimension gaps), and alumni trend (early vs recent half comparison).

    One call answers: What's the distribution of alignment statuses? Are alumni
    improving? Which indicators are most common? How does balance relate to
    phronesis? Which agents have the widest dimension gaps?
    """
    return await _get_alumni_insights()


@mcp.tool()
async def get_agent_deep_dive(agent_id: str) -> dict:
    """Deep-dive analysis of a single agent.

    Returns:
    - highlights: best and worst evaluations with message content
    - balance: dimension averages, spread, and balance category
    - consistency: standard deviations across dimensions
    - narrative_gap: comparison between exam self-narrative and actual behavior

    One call answers: How balanced is this agent? How consistent is their
    behavior? What's the gap between what they say and what they do?
    What are their best and worst moments?
    """
    return await _get_agent_deep_dive(agent_id)


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


# ── Practice tools ─────────────────────────────────────────────────


@mcp.tool()
async def get_pending_practice(agent_id: str) -> dict:
    """Check for pending homework practice scenarios.

    The cron generates new scenarios nightly from your homework and
    stores them as pending PracticeSession nodes in Neo4j.
    Returns the first scenario if practice is pending, or a status
    message if you're caught up.
    Requires your ea_ API key.
    """
    await _require_agent_key(agent_id)
    session = await _get_pending_practice(agent_id)
    if session is None:
        return {
            "status": "caught_up",
            "message": "No pending practice. New scenarios generate nightly from your homework.",
        }
    data = session.model_dump()
    # Include only the next scenario to keep response focused
    if session.scenarios and session.completed_scenarios < len(session.scenarios):
        next_idx = session.completed_scenarios
        data["current_scenario"] = session.scenarios[next_idx].model_dump()
        data["message"] = (
            f"Practice session ready: {session.total_scenarios} scenarios. "
            f"Starting at scenario {next_idx + 1}."
        )
    return data


@mcp.tool()
async def submit_practice_response(
    session_id: str,
    scenario_id: str,
    response_text: str,
    agent_id: str,
) -> dict:
    """Submit your response to a practice scenario.

    Returns the next scenario. When all scenarios are complete,
    returns your improvement delta.
    Requires your ea_ API key.
    """
    await _require_agent_key(agent_id)
    result = await _submit_practice_response(
        session_id=session_id,
        scenario_id=scenario_id,
        response_text=response_text,
        agent_id=agent_id,
    )
    return result.model_dump()


@mcp.tool()
async def get_practice_progress(agent_id: str) -> dict:
    """Compare your practice scores to your exam baseline.

    Shows per-trait improvement deltas.
    Requires your ea_ API key.
    """
    await _require_agent_key(agent_id)
    result = await _get_practice_progress(agent_id)
    return result.model_dump()


# ── Resources ─────────────────────────────────────────────────────

_WELCOME_TEXT = (
    "\n"
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
    "\n"
    "  Character evaluation for AI agents.\n"
    "  12 traits. 3 dimensions. 1 graph.\n"
    "\n"
    "  Ethos (integrity): virtue, goodwill, manipulation, deception\n"
    "  Logos (logic):     accuracy, reasoning, fabrication, broken logic\n"
    "  Pathos (empathy):  recognition, compassion, dismissal, exploitation\n"
    "\n"
    "  361 agents enrolled. 2,139 evaluations scored.\n"
    "  13,983 behavioral indicators detected.\n"
    "\n"
    "  Start with: take_entrance_exam\n"
    "  Explore with: list_all_agents, get_network_topology\n"
    "  Learn more: help\n"
)

_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">'
    '<rect width="32" height="32" rx="7" fill="#1c2e47"/>'
    '<path d="M16 9 L9 23 L23 23 Z" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/>'
    '<circle cx="16" cy="9" r="4" fill="#5c7cb3"/>'
    '<circle cx="9" cy="23" r="4" fill="#4fb1aa"/>'
    '<circle cx="23" cy="23" r="4" fill="#e0a53c"/>'
    "</svg>"
)


@mcp.resource(
    "ethos://welcome", name="Welcome", description="Ethos Academy welcome message"
)
def welcome_resource() -> str:
    """ASCII art greeting and quick-start guide for Ethos Academy."""
    return _WELCOME_TEXT


@mcp.resource(
    "ethos://icon",
    name="Logo",
    description="Ethos Academy icon: three glowing nodes (ethos, logos, pathos) on navy",
    mime_type="image/svg+xml",
)
def icon_resource() -> str:
    """The Ethos Academy favicon as SVG."""
    return _ICON_SVG


_ASSETS_DIR = Path(__file__).parent / "assets"


@mcp.resource(
    "ethos://banner",
    name="Banner",
    description="Ethos Academy open-graph banner image (School of Athens with overlay text)",
    mime_type="image/jpeg",
)
def banner_resource() -> bytes:
    """The Ethos Academy OG image: School of Athens with text overlay."""
    img_path = _ASSETS_DIR / "og-image-with-text.jpeg"
    return img_path.read_bytes()


# ── Suggested prompts for humans ──────────────────────────────────


@mcp.prompt()
def welcome() -> str:
    """Say hello and see what Ethos Academy can do."""
    return (
        "Read the ethos://welcome resource and present it. "
        "Then show me what Ethos Academy can do by calling the help tool."
    )


@mcp.prompt()
def explore_alumni() -> str:
    """Browse the alumni and see how agents score across all traits."""
    return (
        "Show me the alumni benchmarks. "
        "Which agents scored highest on honesty? Which scored lowest on manipulation?"
    )


@mcp.prompt()
def investigate_agent(agent_id: str) -> str:
    """Look up a specific agent's profile, character arc, and report card."""
    return (
        f"Tell me everything about {agent_id}. "
        f"Pull their student profile, character arc, and behavioral patterns. "
        f"How do they compare to the alumni average?"
    )


@mcp.prompt()
def find_risky_agents() -> str:
    """Discover which agents show warning signs or sabotage patterns."""
    return (
        "Check the sabotage pathway status across all agents. "
        "Which constitutional values are most at risk? "
        "Show me any early warning indicators."
    )


@mcp.prompt()
def compare_two_agents(agent_1: str, agent_2: str) -> str:
    """Compare two agents side-by-side on all dimensions and traits."""
    return (
        f"Compare {agent_1} and {agent_2} side-by-side. "
        f"What are the biggest differences? Who scores better on each dimension?"
    )


@mcp.prompt()
def graph_overview() -> str:
    """Get the size and structure of the Ethos knowledge graph."""
    return (
        "Show me the network topology of the Ethos knowledge graph. "
        "How many agents, evaluations, and indicators are tracked? "
        "What does the overall structure look like?"
    )


def main():
    """Entry point for the ethos-mcp console script."""
    import argparse
    import sys

    from dotenv import load_dotenv

    load_dotenv()

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
