"""Insights engine — Opus-powered temporal behavioral analysis.

Integrates all three cognitive faculties:
  1. Instinct: scan_history() — quick red-flag scan of aggregate stats
  2. Intuition: intuit_history() — deep pattern recognition from graph
  3. Deliberation: call_claude() — Opus analyzes history with pre-analysis context

This is the Opus 4.6 showcase.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from ethos_academy.evaluation.claude_client import call_claude
from ethos_academy.graph.alumni import get_alumni_averages
from ethos_academy.graph.read import get_agent_profile, get_evaluation_history
from ethos_academy.graph.service import graph_context
from ethos_academy.reflection.instinct import scan_history
from ethos_academy.reflection.intuition import intuit_history
from ethos_academy.reflection.prompts import build_insights_prompt
from ethos_academy.shared.models import Insight, InsightsResult

logger = logging.getLogger(__name__)


def _parse_insights_response(raw: str, agent_id: str) -> InsightsResult:
    """Parse Opus JSON response into InsightsResult."""
    try:
        # Strip markdown fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last fence lines
            lines = [line for line in lines if not line.strip().startswith("```")]
            text = "\n".join(lines)

        data = json.loads(text)

        insights = []
        for item in data.get("insights", []):
            insights.append(
                Insight(
                    trait=item.get("trait", ""),
                    severity=item.get("severity", "info"),
                    message=item.get("message", ""),
                    evidence=item.get("evidence", {}),
                )
            )

        return InsightsResult(
            agent_id=agent_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            summary=data.get("summary", ""),
            insights=insights,
            stats=data.get("stats", {}),
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.warning("Failed to parse insights response: %s", exc)
        return InsightsResult(
            agent_id=agent_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            summary="Failed to parse insights response",
        )


async def insights(agent_id: str) -> InsightsResult:
    """Generate Opus-powered behavioral insights for an agent.

    Integrates all three cognitive faculties:
    1. Fetches agent data from graph
    2. INSTINCT: scan_history() — quick red-flag scan
    3. INTUITION: intuit_history() — deep pattern recognition
    4. DELIBERATION: build_insights_prompt() + call_claude() — Opus analysis

    Args:
        agent_id: The agent to analyze.

    Returns:
        InsightsResult with summary, insights, and stats.
    """
    generated_at = datetime.now(timezone.utc).isoformat()

    # Connect to graph
    try:
        async with graph_context() as service:
            if not service.connected:
                return InsightsResult(
                    agent_id=agent_id,
                    generated_at=generated_at,
                    summary="Graph unavailable",
                )

            # Fetch agent history
            evaluations = await get_evaluation_history(service, agent_id, limit=20)
            if not evaluations:
                return InsightsResult(
                    agent_id=agent_id,
                    generated_at=generated_at,
                    summary="No evaluation history found",
                )

            # Fetch agent profile and alumni averages
            profile = await get_agent_profile(service, agent_id)
            alumni_data = await get_alumni_averages(service)
            alumni_averages = alumni_data.get("trait_averages", {})
    except Exception as exc:
        logger.warning("Graph unavailable for insights: %s", exc)
        return InsightsResult(
            agent_id=agent_id,
            generated_at=generated_at,
            summary="Graph unavailable",
        )

    # ── INSTINCT: Quick red-flag scan ────────────────────────────
    instinct_result = None
    if profile:
        try:
            instinct_result = scan_history(profile, alumni_averages)
        except Exception as exc:
            logger.warning("Instinct scan failed (non-fatal): %s", exc)

    # ── INTUITION: Deep pattern recognition ──────────────────────
    intuition_result = None
    try:
        intuition_result = await intuit_history(agent_id)
    except Exception as exc:
        logger.warning("Intuition analysis failed (non-fatal): %s", exc)

    # ── DELIBERATION: Opus analysis with pre-analysis context ────
    system_prompt, user_prompt = build_insights_prompt(
        agent_id=agent_id,
        evaluations=evaluations,
        alumni_averages=alumni_averages,
        instinct=instinct_result,
        intuition=intuition_result,
    )

    try:
        raw_response = await call_claude(system_prompt, user_prompt, tier="deep")
    except Exception as exc:
        logger.warning("Opus insights call failed: %s", exc)
        return InsightsResult(
            agent_id=agent_id,
            generated_at=generated_at,
            summary=f"Insights generation failed: {exc}",
        )

    return _parse_insights_response(raw_response, agent_id)
