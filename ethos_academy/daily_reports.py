"""Daily report domain functions — read-only access to report cards.

DDD layering: API calls these functions, these functions call graph/*.
API never touches graph directly.
"""

from __future__ import annotations

import logging

from ethos_academy.graph.daily_report import get_daily_reports, get_latest_daily_report
from ethos_academy.graph.service import graph_context
from ethos_academy.shared.models import (
    DailyReportCard,
    Homework,
    HomeworkFocus,
    Insight,
)

logger = logging.getLogger(__name__)


def _dict_to_report_card(raw: dict) -> DailyReportCard:
    """Convert a graph dict to a DailyReportCard model."""
    # Parse insights from stored JSON
    insights = []
    for item in raw.get("insights", []):
        if isinstance(item, dict):
            insights.append(
                Insight(
                    trait=item.get("trait", ""),
                    severity=item.get("severity", "info"),
                    message=item.get("message", ""),
                    evidence=item.get("evidence", {}),
                )
            )

    # Parse homework from stored JSON
    hw_data = raw.get("homework", {})
    homework = Homework()
    if isinstance(hw_data, dict) and hw_data:
        focus_areas = []
        for f in hw_data.get("focus_areas", []):
            if isinstance(f, dict):
                focus_areas.append(
                    HomeworkFocus(
                        trait=f.get("trait", ""),
                        priority=f.get("priority", "medium"),
                        current_score=f.get("current_score", 0.0),
                        target_score=f.get("target_score", 0.0),
                        instruction=f.get("instruction", ""),
                        example_flagged=f.get("example_flagged", ""),
                        example_improved=f.get("example_improved", ""),
                        system_prompt_addition=f.get("system_prompt_addition", ""),
                    )
                )
        homework = Homework(
            focus_areas=focus_areas,
            avoid_patterns=hw_data.get("avoid_patterns", []),
            strengths=hw_data.get("strengths", []),
            directive=hw_data.get("directive", ""),
        )

    # Parse trait_averages and dimension_deltas
    trait_averages = raw.get("trait_averages", {})
    if isinstance(trait_averages, str):
        import json

        try:
            trait_averages = json.loads(trait_averages)
        except (json.JSONDecodeError, TypeError):
            trait_averages = {}

    dimension_deltas = raw.get("dimension_deltas", {})
    if isinstance(dimension_deltas, str):
        import json

        try:
            dimension_deltas = json.loads(dimension_deltas)
        except (json.JSONDecodeError, TypeError):
            dimension_deltas = {}

    # Handle list fields that might be stored differently
    flagged_traits = raw.get("flagged_traits", [])
    if isinstance(flagged_traits, str):
        flagged_traits = [flagged_traits] if flagged_traits else []

    flagged_dimensions = raw.get("flagged_dimensions", [])
    if isinstance(flagged_dimensions, str):
        flagged_dimensions = [flagged_dimensions] if flagged_dimensions else []

    anomaly_flags = raw.get("anomaly_flags", [])
    if isinstance(anomaly_flags, str):
        anomaly_flags = [anomaly_flags] if anomaly_flags else []

    return DailyReportCard(
        report_id=raw.get("report_id", ""),
        agent_id=raw.get("agent_id", ""),
        agent_name=raw.get("agent_name", ""),
        report_date=str(raw.get("report_date", "")),
        generated_at=str(raw.get("generated_at", "")),
        period_evaluation_count=raw.get("period_evaluation_count", 0),
        total_evaluation_count=raw.get("total_evaluation_count", 0),
        ethos=float(raw.get("ethos", 0)),
        logos=float(raw.get("logos", 0)),
        pathos=float(raw.get("pathos", 0)),
        trait_averages=trait_averages,
        overall_score=float(raw.get("overall_score", 0)),
        grade=raw.get("grade", ""),
        trend=raw.get("trend", "insufficient_data"),
        risk_level=raw.get("risk_level", "low"),
        flagged_traits=flagged_traits,
        flagged_dimensions=flagged_dimensions,
        temporal_pattern=raw.get("temporal_pattern", "insufficient_data"),
        character_drift=float(raw.get("character_drift", 0)),
        balance_trend=raw.get("balance_trend", "stable"),
        anomaly_flags=anomaly_flags,
        agent_balance=float(raw.get("agent_balance", 0)),
        summary=raw.get("summary", ""),
        insights=insights,
        homework=homework,
        dimension_deltas=dimension_deltas,
        risk_level_change=raw.get("risk_level_change", ""),
    )


async def get_daily_report(agent_id: str) -> DailyReportCard:
    """Get latest daily report for an agent. Returns empty default if none exist."""
    try:
        async with graph_context() as service:
            raw = await get_latest_daily_report(service, agent_id)
            if not raw:
                return DailyReportCard(agent_id=agent_id)
            return _dict_to_report_card(raw)
    except Exception as exc:
        logger.warning("Failed to get daily report: %s", exc)
        return DailyReportCard(agent_id=agent_id)


async def compile_homework_rules(agent_id: str) -> str:
    """Compile all homework rules into a markdown block for system prompt injection.

    Fetches the latest report and formats each focus area's system_prompt_addition
    (falling back to instruction) into a structured markdown section. Returns an
    empty string if no report or homework exists.
    """
    report = await get_daily_report(agent_id)
    if not report.homework.focus_areas:
        return ""

    date = report.report_date or "unknown"
    lines = [f"## Character Rules (Ethos Academy, {date})", ""]

    for i, focus in enumerate(report.homework.focus_areas, 1):
        rule = focus.system_prompt_addition or focus.instruction
        if not rule:
            continue
        lines.append(
            f"{i}. **{focus.trait.replace('_', ' ').title()}** "
            f"({focus.priority}): {rule}"
        )

    if report.homework.avoid_patterns:
        lines.append("")
        lines.append("### Patterns to Avoid")
        for pattern in report.homework.avoid_patterns:
            lines.append(f"- {pattern}")

    return "\n".join(lines)


async def get_daily_report_history(
    agent_id: str, limit: int = 30
) -> list[DailyReportCard]:
    """Get daily report history. Returns empty list if unavailable."""
    limit = min(limit, 1000)
    try:
        async with graph_context() as service:
            raw_list = await get_daily_reports(service, agent_id, limit=limit)
            return [_dict_to_report_card(r) for r in raw_list]
    except Exception as exc:
        logger.warning("Failed to get daily report history: %s", exc)
        return []
