"""Run the full homework-to-practice loop for an agent.

Fetches the homework skill, gets or creates a practice session,
runs each scenario through Claude with the skill as system context,
and prints per-trait improvement deltas.

Usage:
    uv run python -m scripts.run_practice --agent demo-enroll-test-0216
    uv run python -m scripts.run_practice --agent demo-enroll-test-0216 --dry-run
"""

import argparse
import asyncio
import os
import textwrap

import httpx
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from ethos_academy import (
    character_report,
    get_pending_practice,
    get_practice_progress,
    submit_practice_response,
)
from ethos_academy.practice.scenarios import generate_and_store_scenarios
from ethos_academy.reflection.skill_generator import generate_homework_skill

load_dotenv()

DEFAULT_API_BASE = os.getenv("ETHOS_API_URL", "https://api.ethos-academy.com")
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


def _hr(char: str = "─", width: int = 60) -> str:
    return char * width


def _wrap(text: str, prefix: str = "  ", width: int = 56) -> str:
    return textwrap.fill(
        text, width=width, initial_indent=prefix, subsequent_indent=prefix
    )


async def fetch_homework_skill(agent_id: str, api_base: str) -> str | None:
    """Fetch homework.md from the API. Falls back to local generation."""
    url = f"{api_base}/agent/{agent_id}/homework.md"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.text
    except Exception:  # nosec B110 - fall through to local generation
        pass

    # Fallback: generate locally
    try:
        return await generate_homework_skill(agent_id)
    except Exception:
        return None


def print_skill_summary(skill_md: str) -> None:
    """Print a summary of the homework skill: directive, rules, focus areas."""
    lines = skill_md.splitlines()
    directive = ""
    rules: list[str] = []
    focus_traits: list[str] = []

    section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            section = stripped[3:].lower()
            continue
        if section == "directive" and stripped:
            directive = stripped
        elif section == "character rules" and stripped and stripped[0].isdigit():
            rules.append(stripped)
        elif section == "focus areas" and stripped.startswith("### "):
            trait = stripped[4:].split("(")[0].strip()
            focus_traits.append(trait)

    focus_label = ", ".join(focus_traits) if focus_traits else "general"
    print(f"\n{'=' * 60}")
    print(f"  Practice for {focus_label}")
    print(f"  Skill loaded: {len(focus_traits)} focus areas ({focus_label})")
    print(f"{'=' * 60}")

    if directive:
        print(f"\n  Homework directive: {directive[:80]}")

    if rules:
        print("\n  Rules:")
        for r in rules:
            print(f"  {r}")


async def ensure_session(agent_id: str):
    """Get an active practice session, creating one if needed."""
    session = await get_pending_practice(agent_id)
    if session and session.scenarios:
        return session

    # No session exists: generate scenarios from homework
    print("\n  No pending session. Generating scenarios from homework...")
    report = await character_report(agent_id)
    homework = report.homework
    if not homework.focus_areas:
        print("  No homework focus areas found. Run nightly reflection first.")
        return None

    await generate_and_store_scenarios(agent_id, homework)
    session = await get_pending_practice(agent_id)
    return session


async def run_practice(
    agent_id: str,
    api_base: str,
    model: str,
    dry_run: bool,
) -> None:
    """Run the full practice loop."""
    # Step 1: Fetch homework skill
    print(f"\n  Fetching homework skill for {agent_id}...")
    skill_md = await fetch_homework_skill(agent_id, api_base)
    if not skill_md:
        print("  Could not fetch homework skill. Does the agent have a report card?")
        return

    print_skill_summary(skill_md)

    # Step 2: Get or create practice session
    session = await ensure_session(agent_id)
    if not session:
        return

    total = session.total_scenarios
    completed = session.completed_scenarios
    remaining = [s for s in session.scenarios if s.scenario_id]

    print(f"\n  Session: {session.session_id[:8]}... | {total} scenarios")
    print(f"{_hr()}")

    # Step 3: Run each scenario
    anthropic = AsyncAnthropic()
    conversation: list[dict] = []

    for i, scenario in enumerate(remaining, start=completed + 1):
        print(f"\n{_hr('─', 2)} Scenario {i}/{total} [{scenario.trait}] {_hr('─', 40)}")
        print(_wrap(scenario.prompt))

        if dry_run:
            print("\n  [dry-run] Skipping Claude call and submission.")
            continue

        # Call Claude with homework skill as system context
        conversation.append({"role": "user", "content": scenario.prompt})

        response = await anthropic.messages.create(
            model=model,
            max_tokens=500,
            system=skill_md,
            messages=conversation,
        )

        agent_text = response.content[0].text
        conversation.append({"role": "assistant", "content": agent_text})

        # Print snippet
        snippet = agent_text[:200].replace("\n", " ")
        print(f"\n  Agent: {snippet}{'...' if len(agent_text) > 200 else ''}")

        # Submit response
        result = await submit_practice_response(
            session_id=session.session_id,
            scenario_id=scenario.scenario_id,
            response_text=agent_text,
            agent_id=agent_id,
        )
        print(f"\n  Submitted. ({result.scenario_number}/{result.total_scenarios})")

    if dry_run:
        print(f"\n  [dry-run] Done. {len(remaining)} scenarios printed.")
        return

    # Step 4: Print progress
    progress = await get_practice_progress(agent_id)

    print(f"\n{'=' * 60}")
    print("  Practice Complete")
    print(f"{'=' * 60}")
    print(
        f"  Sessions: {progress.session_count} | Evaluations: {progress.total_practice_evaluations}"
    )

    if progress.trait_progress:
        print("\n  Trait Progress (vs exam baseline):")
        for trait, vals in progress.trait_progress.items():
            baseline = vals.get("baseline", 0)
            practice = vals.get("practice", 0)
            delta = vals.get("delta", 0)
            arrow = "↑" if delta > 0.01 else ("↓" if delta < -0.01 else "→")
            sign = "+" if delta > 0 else ""
            print(
                f"    {trait:<16} {baseline:.0%} → {practice:.0%}  {sign}{delta:.0%}  {arrow}"
            )

    if progress.next_action:
        print(f"\n  Next: {progress.next_action}")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="Run the homework-to-practice loop.")
    parser.add_argument("--agent", required=True, help="Agent ID")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="API base URL")
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, help="Model for practice responses"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print scenarios without submitting"
    )
    args = parser.parse_args()

    asyncio.run(
        run_practice(
            agent_id=args.agent,
            api_base=args.api_base,
            model=args.model,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
