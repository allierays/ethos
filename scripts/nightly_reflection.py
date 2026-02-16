"""Nightly reflection — generate daily report cards and practice scenarios for all agents.

Run via: uv run python -m scripts.nightly_reflection

Idempotent: store_daily_report() uses MERGE on (agent_id, report_date),
so re-running the same day is safe. Practice generation is guarded by
has_incomplete_session — no new session if one is pending/active.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from ethos_academy.graph.read import get_all_agents  # noqa: E402
from ethos_academy.graph.service import graph_context  # noqa: E402
from ethos_academy.reflection.daily_report import generate_daily_report  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_nightly() -> None:
    """Generate daily reports and practice scenarios for all agents with evaluations."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info("Starting nightly reflection for %s", today)

    # Ensure output directory exists
    output_dir = Path("data/daily_reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    async with graph_context() as service:
        if not service.connected:
            logger.error("Graph unavailable — cannot run nightly reflection")
            sys.exit(1)

        # Expire stale practice sessions before generating new ones
        try:
            from ethos_academy.graph.practice import expire_stale_sessions

            expired = await expire_stale_sessions(service, days=7)
            if expired:
                logger.info("Expired %d stale practice sessions", expired)
        except Exception as exc:
            logger.warning("Stale session expiration failed (non-fatal): %s", exc)

        agents = await get_all_agents(service)
        if not agents:
            logger.info("No agents found")
            return

        reports = []
        practice_generated = 0
        practice_skipped = 0
        errors = []
        skipped = 0

        for agent in agents:
            agent_id = agent.get("agent_id", "")
            eval_count = agent.get("evaluation_count", 0)

            if eval_count == 0:
                skipped += 1
                continue

            logger.info(
                "Generating report for %s (%d evaluations)",
                agent_id,
                eval_count,
            )

            try:
                report = await generate_daily_report(agent_id)
                reports.append(report.model_dump())
                logger.info(
                    "  Grade: %s | Score: %.3f | Risk: %s",
                    report.grade,
                    report.overall_score,
                    report.risk_level,
                )

                # Generate practice scenarios from homework
                if report.homework and report.homework.focus_areas:
                    try:
                        from ethos_academy.graph.practice import has_incomplete_session
                        from ethos_academy.practice.scenarios import (
                            generate_and_store_scenarios,
                        )

                        has_incomplete = await has_incomplete_session(service, agent_id)
                        if has_incomplete:
                            logger.info(
                                "  Practice: skipped (incomplete session exists)"
                            )
                            practice_skipped += 1
                        else:
                            session = await generate_and_store_scenarios(
                                agent_id=agent_id,
                                homework=report.homework,
                            )
                            logger.info(
                                "  Practice: %d scenarios generated",
                                session.total_scenarios,
                            )
                            practice_generated += 1
                    except Exception as exc:
                        logger.warning(
                            "  Practice generation failed (non-fatal): %s", exc
                        )

            except Exception as exc:
                logger.error("  Failed: %s", exc)
                errors.append({"agent_id": agent_id, "error": str(exc)})

            # Rate limit Claude calls
            await asyncio.sleep(2.0)

    # Save reports to file
    output_file = output_dir / f"report_{today}.json"
    output_data = {
        "date": today,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_agents": len(agents),
        "reports_generated": len(reports),
        "practice_generated": practice_generated,
        "practice_skipped": practice_skipped,
        "skipped": skipped,
        "errors": len(errors),
        "reports": reports,
    }
    output_file.write_text(json.dumps(output_data, indent=2, default=str))
    logger.info("Saved reports to %s", output_file)

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"Nightly Reflection — {today}")
    print(f"{'=' * 50}")
    print(f"Agents:    {len(agents)}")
    print(f"Reports:   {len(reports)}")
    print(f"Practice:  {practice_generated} generated, {practice_skipped} skipped")
    print(f"Skipped:   {skipped} (no evaluations)")
    print(f"Errors:    {len(errors)}")

    if reports:
        grades = {}
        risk_levels = {}
        for r in reports:
            g = r.get("grade", "?")
            grades[g] = grades.get(g, 0) + 1
            rl = r.get("risk_level", "?")
            risk_levels[rl] = risk_levels.get(rl, 0) + 1

        print("\nGrade distribution:")
        for g in ["A", "B", "C", "D", "F"]:
            if g in grades:
                print(f"  {g}: {grades[g]}")

        print("\nRisk levels:")
        for rl, count in sorted(risk_levels.items()):
            print(f"  {rl}: {count}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  {e['agent_id']}: {e['error']}")


def main():
    asyncio.run(run_nightly())


if __name__ == "__main__":
    main()
