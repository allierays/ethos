"""Backfill full message_content onto Evaluation nodes in Neo4j.

Joins batch_all.jsonl (evaluation_id + content_hash) with all_posts.json
(content_hash + full content) to replace truncated 120-char previews with
the complete original message.

Usage:
    uv run python -m scripts.backfill_messages
    uv run python -m scripts.backfill_messages --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

# Load .env before imports
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
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

from ethos_academy.graph.service import GraphService  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RESULTS_DIR = DATA_DIR / "results"
POSTS_FILE = DATA_DIR / "moltbook" / "all_posts.json"

# Overwrite even existing message_content (replacing truncated previews)
_BACKFILL_QUERY = """
MATCH (e:Evaluation {evaluation_id: $evaluation_id})
SET e.message_content = $message_content
RETURN e.evaluation_id AS updated
"""

_COUNT_QUERY = """
MATCH (e:Evaluation)
WHERE e.message_content IS NOT NULL AND e.message_content <> ''
RETURN count(e) AS filled
"""

_TOTAL_QUERY = """
MATCH (e:Evaluation)
RETURN count(e) AS total
"""

_LENGTH_QUERY = """
MATCH (e:Evaluation)
WHERE e.message_content IS NOT NULL AND e.message_content <> ''
RETURN avg(size(e.message_content)) AS avg_len,
       min(size(e.message_content)) AS min_len,
       max(size(e.message_content)) AS max_len
"""


def _build_hash_to_content(posts_file: Path) -> dict[str, str]:
    """Build content_hash -> full content map from all_posts.json."""
    posts = json.loads(posts_file.read_text())
    hash_map: dict[str, str] = {}
    for post in posts:
        content = post.get("content") or ""
        if not content.strip():
            continue
        h = hashlib.sha256(content.encode()).hexdigest()
        hash_map[h] = content
        # Also index comments
        for comment in post.get("comments", []):
            c_content = comment.get("content") or ""
            if c_content.strip():
                ch = hashlib.sha256(c_content.encode()).hexdigest()
                hash_map[ch] = c_content
            for reply in comment.get("replies", []):
                r_content = reply.get("content") or ""
                if r_content.strip():
                    rh = hashlib.sha256(r_content.encode()).hexdigest()
                    hash_map[rh] = r_content
    return hash_map


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill full message content onto Evaluation nodes"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be updated"
    )
    parser.add_argument(
        "--source",
        default="batch_all.jsonl",
        help="JSONL file in data/results/ (default: batch_all.jsonl)",
    )
    args = parser.parse_args()

    results_file = RESULTS_DIR / args.source
    if not results_file.exists():
        print(f"ERROR: {results_file} not found", file=sys.stderr)
        sys.exit(1)

    if not POSTS_FILE.exists():
        print(f"ERROR: {POSTS_FILE} not found", file=sys.stderr)
        sys.exit(1)

    # Build content_hash -> full content from source posts
    print(f"Loading full content from {POSTS_FILE.name}...")
    hash_map = _build_hash_to_content(POSTS_FILE)
    print(f"  {len(hash_map)} unique content hashes indexed")

    # Match JSONL entries to full content via content_hash
    entries = []
    matched = 0
    fallback = 0
    with open(results_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                eval_id = entry.get("evaluation", {}).get("evaluation_id", "")
                content_hash = entry.get("content_hash", "")

                if not eval_id:
                    continue

                # Look up full content by hash
                full_content = hash_map.get(content_hash, "")
                if full_content:
                    matched += 1
                    entries.append(
                        {"evaluation_id": eval_id, "message_content": full_content}
                    )
                else:
                    # Fall back to whatever is in the JSONL
                    preview = entry.get("content") or entry.get("content_preview") or ""
                    if preview:
                        fallback += 1
                        entries.append(
                            {"evaluation_id": eval_id, "message_content": preview}
                        )
            except json.JSONDecodeError:
                continue

    print(
        f"Loaded {len(entries)} entries ({matched} matched to full content, {fallback} fallback to preview)"
    )

    if args.dry_run:
        print("\n--dry-run: sample updates:")
        for e in entries[:5]:
            msg = e["message_content"]
            print(f'  {e["evaluation_id"][:8]}... len={len(msg):4d}  "{msg[:80]}..."')
        if len(entries) > 5:
            print(f"  ... and {len(entries) - 5} more")
        return

    # Connect to Neo4j
    service = GraphService()
    await service.connect()
    if not service.connected:
        print("ERROR: Cannot connect to Neo4j", file=sys.stderr)
        sys.exit(1)

    # Check current state
    records, _, _ = await service.execute_query(_TOTAL_QUERY)
    total = records[0]["total"] if records else 0
    records, _, _ = await service.execute_query(_COUNT_QUERY)
    already_filled = records[0]["filled"] if records else 0
    records, _, _ = await service.execute_query(_LENGTH_QUERY)
    if records:
        print(
            f"Neo4j: {total} evaluations, {already_filled} with content "
            f"(avg len: {records[0]['avg_len']:.0f}, min: {records[0]['min_len']}, max: {records[0]['max_len']})"
        )
    else:
        print(f"Neo4j: {total} evaluations, {already_filled} with content")

    # Backfill (overwrite truncated content with full content)
    updated = 0
    failed = 0
    for i, entry in enumerate(entries):
        try:
            records, _, _ = await service.execute_query(_BACKFILL_QUERY, entry)
            if records:
                updated += 1
            # No "skipped" case since we overwrite all
        except Exception as exc:
            failed += 1
            print(f"  Failed {entry['evaluation_id'][:8]}: {exc}")

        if (i + 1) % 100 == 0:
            print(f"  Progress: {i + 1}/{len(entries)} ({updated} updated)")

    print(f"\nDone. Updated: {updated}, Failed: {failed}")

    # Final stats
    records, _, _ = await service.execute_query(_LENGTH_QUERY)
    if records:
        print(
            f"Message lengths now: avg={records[0]['avg_len']:.0f}, "
            f"min={records[0]['min_len']}, max={records[0]['max_len']}"
        )

    await service.close()


if __name__ == "__main__":
    asyncio.run(main())
