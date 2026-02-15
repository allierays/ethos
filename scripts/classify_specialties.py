"""Classify Moltbook agent specialties from profile descriptions.

Reads agent profiles from data/moltbook/agents/*.json, runs the keyword
classifier, and writes data/moltbook/agent_specialties.json.

Usage:
    uv run python -m scripts.classify_specialties
    uv run python -m scripts.classify_specialties --use-llm
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import Counter
from pathlib import Path

from ethos_academy.identity.specialty import classify_specialty

AGENTS_DIR = Path(__file__).resolve().parent.parent / "data" / "moltbook" / "agents"
OUTPUT_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "moltbook"
    / "agent_specialties.json"
)


def load_agent_descriptions() -> dict[str, str]:
    """Load agent name -> description from all profile JSON files."""
    descriptions: dict[str, str] = {}
    if not AGENTS_DIR.exists():
        print(f"ERROR: {AGENTS_DIR} not found", file=sys.stderr)
        sys.exit(1)

    for path in sorted(AGENTS_DIR.glob("*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
            agent = data.get("agent", {})
            name = agent.get("name", path.stem)
            description = agent.get("description", "")
            descriptions[name] = description
        except (json.JSONDecodeError, KeyError) as exc:
            print(f"  Skipping {path.name}: {exc}")

    return descriptions


async def llm_classify(descriptions: dict[str, str]) -> dict[str, str]:
    """Send ambiguous descriptions to Sonnet for better classification.

    Only called for descriptions classified as "general" that are 30+ chars.
    """
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic()
    results: dict[str, str] = {}
    from ethos_academy.identity.specialty import SPECIALTY_CATEGORIES

    categories_str = ", ".join(
        c for c in SPECIALTY_CATEGORIES if c not in ("general", "unknown")
    )

    batch = {
        name: desc
        for name, desc in descriptions.items()
        if classify_specialty(desc) == "general" and len(desc.strip()) >= 30
    }

    if not batch:
        print("No ambiguous descriptions to classify with LLM.")
        return results

    print(f"\nSending {len(batch)} ambiguous descriptions to Sonnet...")

    for name, desc in batch.items():
        try:
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=50,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Classify this AI agent description into exactly one category.\n"
                            f"Categories: {categories_str}\n"
                            f"Description: {desc}\n"
                            f"Reply with ONLY the category name, nothing else."
                        ),
                    }
                ],
            )
            label = response.content[0].text.strip().lower()
            if label in SPECIALTY_CATEGORIES:
                results[name] = label
                print(f"  {name}: general -> {label}")
            else:
                print(
                    f"  {name}: LLM returned invalid label '{label}', keeping general"
                )
        except Exception as exc:
            print(f"  {name}: LLM error: {exc}")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify Moltbook agent specialties")
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use Sonnet to reclassify ambiguous 'general' descriptions (30+ chars)",
    )
    args = parser.parse_args()

    print(f"Loading agent profiles from {AGENTS_DIR}...")
    descriptions = load_agent_descriptions()
    print(f"Loaded {len(descriptions)} agent profiles")

    # Run keyword classifier
    specialties: dict[str, str] = {}
    for name, desc in descriptions.items():
        specialties[name] = classify_specialty(desc)

    # Optionally refine with LLM
    if args.use_llm:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            # Try loading .env
            env_path = Path(__file__).resolve().parent.parent / ".env"
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("ANTHROPIC_API_KEY="):
                            _, _, val = line.partition("=")
                            os.environ["ANTHROPIC_API_KEY"] = val.strip().strip("'\"")
                            break

        llm_results = asyncio.run(llm_classify(descriptions))
        specialties.update(llm_results)
        print(f"LLM reclassified {len(llm_results)} agents")

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(specialties, f, indent=2, sort_keys=True)
    print(f"\nWrote {len(specialties)} specialties to {OUTPUT_FILE}")

    # Print distribution
    dist = Counter(specialties.values())
    print("\nDistribution:")
    for label, count in dist.most_common():
        pct = count / len(specialties) * 100
        print(f"  {label:20s}: {count:4d} ({pct:.1f}%)")


if __name__ == "__main__":
    main()
