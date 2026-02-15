"""Backfill agent_specialty on existing Neo4j Agent nodes.

Reads data/moltbook/agent_specialties.json and updates Agent nodes
that match by agent_name.

Usage:
    uv run python -m scripts.backfill_specialties
    uv run python -m scripts.backfill_specialties --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

SPECIALTIES_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "moltbook"
    / "agent_specialties.json"
)


def _load_dotenv() -> None:
    """Load .env file from project root."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill agent specialties in Neo4j")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be updated"
    )
    args = parser.parse_args()

    if not SPECIALTIES_FILE.exists():
        print(f"ERROR: {SPECIALTIES_FILE} not found", file=sys.stderr)
        print("Run `uv run python -m scripts.classify_specialties` first.")
        sys.exit(1)

    with open(SPECIALTIES_FILE) as f:
        specialties: dict[str, str] = json.load(f)

    print(f"Loaded {len(specialties)} agent specialties")

    if args.dry_run:
        from collections import Counter

        dist = Counter(specialties.values())
        print("\nWould update these specialties:")
        for label, count in dist.most_common():
            print(f"  {label:20s}: {count:4d}")
        print("\n--dry-run: no changes made")
        return

    from ethos_academy.graph.service import GraphService

    service = GraphService()
    await service.connect()

    if not service.connected:
        print("ERROR: Cannot connect to Neo4j", file=sys.stderr)
        sys.exit(1)

    # Query all Agent nodes with their agent_name to map name -> agent_id
    records, _, _ = await service.execute_query(
        "MATCH (a:Agent) RETURN a.agent_id AS agent_id, a.agent_name AS agent_name"
    )

    name_to_id: dict[str, str] = {}
    for record in records:
        name = record.get("agent_name", "")
        aid = record.get("agent_id", "")
        if name and aid:
            name_to_id[name] = aid

    print(f"Found {len(name_to_id)} Agent nodes in Neo4j")

    from ethos_academy.graph.write import update_agent_specialty

    updated = 0
    skipped = 0
    for agent_name, specialty in specialties.items():
        agent_id = name_to_id.get(agent_name)
        if not agent_id:
            skipped += 1
            continue

        success = await update_agent_specialty(service, agent_id, specialty)
        if success:
            updated += 1
        else:
            skipped += 1

    await service.close()
    print(f"\nUpdated: {updated}, Skipped (no matching node): {skipped}")


if __name__ == "__main__":
    asyncio.run(main())
