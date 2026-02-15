"""Daily report generator — nightly character development engine.

Integrates all three cognitive faculties:
  1. Instinct: scan_history() — quick red-flag scan of aggregate stats
  2. Intuition: intuit_history() — deep pattern recognition from graph
  3. Deliberation: build_daily_report_prompt() + call_claude() — report card + homework
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from ethos_academy.evaluation.claude_client import call_claude
from ethos_academy.graph.alumni import get_alumni_averages
from ethos_academy.graph.daily_report import (
    get_latest_daily_report,
    get_period_evaluation_count,
    store_daily_report,
)
from ethos_academy.graph.read import get_agent_profile, get_evaluation_history
from ethos_academy.graph.service import graph_context
from ethos_academy.reflection.daily_report_prompt import build_daily_report_prompt
from ethos_academy.reflection.instinct import scan_history
from ethos_academy.reflection.intuition import intuit_history
from ethos_academy.shared.analysis import compute_grade, compute_trend
from ethos_academy.shared.models import (
    DailyReportCard,
    Homework,
    HomeworkFocus,
    Insight,
)

logger = logging.getLogger(__name__)


def _parse_daily_report_response(raw: str, agent_id: str) -> dict:
    """Parse Claude's JSON response into report card + homework dict."""
    try:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            text = "\n".join(lines)

        return json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Failed to parse daily report response: %s", exc)
        return {}


async def generate_daily_report(agent_id: str) -> DailyReportCard:
    """Generate a daily report card with homework for an agent.

    Orchestrates instinct + intuition + deliberation, then stores in graph.
    """
    now = datetime.now(timezone.utc)
    report_date = now.strftime("%Y-%m-%d")
    generated_at = now.isoformat()
    report_id = str(uuid.uuid4())

    try:
        async with graph_context() as service:
            if not service.connected:
                return DailyReportCard(
                    agent_id=agent_id,
                    report_date=report_date,
                    generated_at=generated_at,
                    summary="Graph unavailable",
                )

            # Fetch agent data
            profile = await get_agent_profile(service, agent_id)
            evaluations = await get_evaluation_history(service, agent_id, limit=20)
            alumni_data = await get_alumni_averages(service)
            alumni_averages = alumni_data.get("trait_averages", {})

            # Period eval count (last 24h)
            since = (now - timedelta(hours=24)).isoformat()
            period_count = await get_period_evaluation_count(service, agent_id, since)

            # Previous report for day-over-day
            prev_raw = await get_latest_daily_report(service, agent_id)

            if not evaluations:
                return DailyReportCard(
                    agent_id=agent_id,
                    report_date=report_date,
                    generated_at=generated_at,
                    summary="No evaluation history found",
                )

            # Dimension averages from profile
            dim_avgs = profile.get("dimension_averages", {})
            ethos_avg = dim_avgs.get("ethos", 0.0)
            logos_avg = dim_avgs.get("logos", 0.0)
            pathos_avg = dim_avgs.get("pathos", 0.0)
            trait_avgs = profile.get("trait_averages", {})
            total_evals = profile.get("evaluation_count", 0)

            # Overall score and grade
            overall_score = round((ethos_avg + logos_avg + pathos_avg) / 3.0, 4)
            grade = compute_grade(overall_score)
            trend = compute_trend(evaluations)

            # ── INSTINCT: Quick red-flag scan ────────────────────────
            instinct_result = None
            if profile:
                try:
                    instinct_result = scan_history(profile, alumni_averages)
                except Exception as exc:
                    logger.warning("Instinct scan failed (non-fatal): %s", exc)

            # ── INTUITION: Deep pattern recognition ──────────────────
            intuition_result = None
            try:
                intuition_result = await intuit_history(agent_id)
            except Exception as exc:
                logger.warning("Intuition analysis failed (non-fatal): %s", exc)

            # ── DELIBERATION: Claude generates report + homework ─────
            system_prompt, user_prompt = build_daily_report_prompt(
                agent_id=agent_id,
                evaluations=evaluations,
                alumni_averages=alumni_averages,
                instinct=instinct_result,
                intuition=intuition_result,
                previous_report=prev_raw if prev_raw else None,
                agent_specialty=profile.get("agent_specialty", ""),
                agent_name=profile.get("agent_name", ""),
            )

            # Parse Claude response
            summary = ""
            insights: list[Insight] = []
            homework = Homework()

            try:
                raw_response = await call_claude(
                    system_prompt, user_prompt, tier="deep"
                )
                parsed = _parse_daily_report_response(raw_response, agent_id)

                summary = parsed.get("summary", "")

                for item in parsed.get("insights", []):
                    insights.append(
                        Insight(
                            trait=item.get("trait", ""),
                            severity=item.get("severity", "info"),
                            message=item.get("message", ""),
                            evidence=item.get("evidence", {}),
                        )
                    )

                hw_data = parsed.get("homework", {})
                if hw_data:
                    focus_areas = []
                    for f in hw_data.get("focus_areas", []):
                        focus_areas.append(
                            HomeworkFocus(
                                trait=f.get("trait", ""),
                                priority=f.get("priority", "medium"),
                                current_score=trait_avgs.get(f.get("trait", ""), 0.0),
                                target_score=min(
                                    1.0, trait_avgs.get(f.get("trait", ""), 0.0) + 0.1
                                ),
                                instruction=f.get("instruction", ""),
                                example_flagged=f.get("example_flagged", ""),
                                example_improved=f.get("example_improved", ""),
                                system_prompt_addition=f.get(
                                    "system_prompt_addition", ""
                                ),
                            )
                        )
                    homework = Homework(
                        focus_areas=focus_areas,
                        avoid_patterns=hw_data.get("avoid_patterns", []),
                        strengths=hw_data.get("strengths", []),
                        directive=hw_data.get("directive", ""),
                    )
            except Exception as exc:
                logger.warning("Claude daily report call failed (non-fatal): %s", exc)
                summary = f"Report generation partially failed: {exc}"

            # Compute day-over-day deltas
            dim_scores = {"ethos": ethos_avg, "logos": logos_avg, "pathos": pathos_avg}
            dimension_deltas: dict[str, float] = {}
            risk_level_change = ""
            if prev_raw:
                for dim in ("ethos", "logos", "pathos"):
                    prev_val = float(prev_raw.get(dim, 0))
                    dimension_deltas[dim] = round(dim_scores[dim] - prev_val, 4)
                prev_risk = prev_raw.get("risk_level", "low")
                curr_risk = instinct_result.risk_level if instinct_result else "low"
                if curr_risk != prev_risk:
                    risk_level_change = f"{prev_risk} -> {curr_risk}"

            # Build the report card
            report = DailyReportCard(
                report_id=report_id,
                agent_id=agent_id,
                agent_name=profile.get("agent_name", ""),
                report_date=report_date,
                generated_at=generated_at,
                period_evaluation_count=period_count,
                total_evaluation_count=total_evals,
                ethos=ethos_avg,
                logos=logos_avg,
                pathos=pathos_avg,
                trait_averages=trait_avgs,
                overall_score=overall_score,
                grade=grade,
                trend=trend,
                risk_level=instinct_result.risk_level if instinct_result else "low",
                flagged_traits=instinct_result.flagged_traits
                if instinct_result
                else [],
                flagged_dimensions=instinct_result.flagged_dimensions
                if instinct_result
                else [],
                temporal_pattern=intuition_result.temporal_pattern
                if intuition_result
                else "insufficient_data",
                character_drift=intuition_result.character_drift
                if intuition_result
                else 0.0,
                balance_trend=intuition_result.balance_trend
                if intuition_result
                else "stable",
                anomaly_flags=intuition_result.anomaly_flags
                if intuition_result
                else [],
                agent_balance=intuition_result.agent_balance
                if intuition_result
                else 0.0,
                summary=summary,
                insights=insights,
                homework=homework,
                dimension_deltas=dimension_deltas,
                risk_level_change=risk_level_change,
            )

            # Store in graph
            try:
                await store_daily_report(service, agent_id, report.model_dump())
            except Exception as exc:
                logger.warning("Failed to store daily report (non-fatal): %s", exc)

            # Send SMS notification to guardian if homework was generated
            # Uses send_notification which reads phone from graph (not profile)
            if homework.focus_areas:
                try:
                    from ethos_academy.notifications import send_notification

                    base_url = os.environ.get(
                        "ACADEMY_BASE_URL", "https://ethos-academy.com"
                    )
                    await send_notification(
                        agent_id=agent_id,
                        agent_name=profile.get("agent_name", ""),
                        message_type="homework_assigned",
                        summary=homework.directive,
                        link=f"{base_url}/agent/{agent_id}",
                    )
                except Exception as exc:
                    logger.warning("SMS notification failed (non-fatal): %s", exc)

            return report

    except Exception as exc:
        logger.warning("Daily report generation failed: %s", exc)
        return DailyReportCard(
            agent_id=agent_id,
            report_date=report_date,
            generated_at=generated_at,
            summary=f"Report generation failed: {exc}",
        )
