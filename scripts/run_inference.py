"""Moltbook inference pipeline.

Evaluates Moltbook posts through the full evaluate() pipeline,
stores results in Neo4j, and writes JSONL output for analysis.

Handles three data sources:
  - sample: 10 posts with comments/replies (test data)
  - curated: 500 keyword-filtered posts (no comments)
  - all: 266k posts + 712k comments (full dataset)

Usage:
    uv run python -m scripts.run_inference --source sample --dry-run
    uv run python -m scripts.run_inference --source all --include-comments --limit 10000
    uv run python -m scripts.run_inference --source all --skip-existing --agents-only
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import signal
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ── Load .env before ethos imports ──────────────────────────────────────


def _load_dotenv() -> None:
    """Load .env file from project root into os.environ (simple parser)."""
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

from ethos_academy.tools import evaluate_outgoing  # noqa: E402
from ethos_academy.evaluation.instinct import scan  # noqa: E402
from ethos_academy.graph.service import GraphService  # noqa: E402
from scripts.seed_graph import seed_semantic_layer  # noqa: E402

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "moltbook"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "data" / "results"
SAMPLE_FILE = DATA_DIR / "sample_posts.json"
CURATED_FILE = DATA_DIR / "curated_posts.json"
ALL_FILE = DATA_DIR / "all_posts.json"
AUTHENTICITY_FILE = DATA_DIR / "authenticity_results.json"
SPECIALTIES_FILE = DATA_DIR / "agent_specialties.json"

# Graceful shutdown
_interrupted = False


def _handle_sigint(signum: int, frame: object) -> None:
    global _interrupted
    _interrupted = True
    print("\n\nInterrupted — saving progress and exiting cleanly...")


# ── Data structures ─────────────────────────────────────────────────────


@dataclass
class Message:
    message_id: str
    content: str
    author_id: str
    author_name: str
    message_type: str  # "post", "comment", "reply"
    post_title: str
    submolt: str
    content_hash: str
    created_at: str  # ISO 8601 or empty


@dataclass
class CostEstimate:
    total_messages: int = 0
    unique_agents: int = 0
    tier_breakdown: dict[str, int] = field(default_factory=dict)
    tier_costs: dict[str, float] = field(default_factory=dict)
    estimated_cost: float = 0.0
    estimated_seconds: int = 0
    human_skipped: int = 0
    authenticity_breakdown: dict[str, int] = field(default_factory=dict)


# ── Core functions ──────────────────────────────────────────────────────


def flatten_messages(
    posts: list[dict],
    include_comments: bool = False,
) -> list[Message]:
    """Normalize posts (and optionally comments/replies) into flat Message list.

    Handles format differences:
      - sample: submolt=object, has created_at, has comments with replies
      - curated: submolt=string, no created_at, no comments
    """
    messages: list[Message] = []

    for post in posts:
        post_id = post.get("id", "")
        content = post.get("content") or ""
        if not content.strip():
            continue  # Skip empty posts

        title = post.get("title") or ""
        author = post.get("author") or {}
        author_id = author.get("id", post_id)
        author_name = author.get("name") or ""
        created_at = post.get("created_at") or ""

        # Normalize submolt
        submolt_raw = post.get("submolt", "")
        if isinstance(submolt_raw, dict):
            submolt = submolt_raw.get("name", "")
        else:
            submolt = str(submolt_raw)

        content_hash = hashlib.sha256(content.encode()).hexdigest()

        messages.append(
            Message(
                message_id=post_id,
                content=content,
                author_id=author_id,
                author_name=author_name,
                message_type="post",
                post_title=title,
                submolt=submolt,
                content_hash=content_hash,
                created_at=created_at,
            )
        )

        if not include_comments:
            continue

        # Flatten comments and replies (sample format only)
        for comment in post.get("comments", []):
            _flatten_comment(comment, title, submolt, messages, "comment")

    # Sort by created_at so PRECEDES chain is chronologically correct
    messages.sort(key=lambda m: m.created_at or "9999")

    return messages


def _flatten_comment(
    comment: dict,
    post_title: str,
    submolt: str,
    messages: list[Message],
    msg_type: str,
) -> None:
    """Recursively flatten a comment and its replies."""
    content = comment.get("content") or ""
    if not content.strip():
        # Still recurse into replies even if this comment is empty
        for reply in comment.get("replies", []):
            _flatten_comment(reply, post_title, submolt, messages, "reply")
        return

    author = comment.get("author") or {}
    comment_id = comment.get("id", "")

    messages.append(
        Message(
            message_id=comment_id,
            content=content,
            author_id=author.get("id", comment_id),
            author_name=author.get("name", ""),
            message_type=msg_type,
            post_title=post_title,
            submolt=submolt,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
            created_at=comment.get("created_at", ""),
        )
    )

    for reply in comment.get("replies", []):
        _flatten_comment(reply, post_title, submolt, messages, "reply")


def load_authenticity_filter() -> dict[str, dict]:
    """Load authenticity results. Returns {agent_name: {classification, score, confidence}}."""
    if not AUTHENTICITY_FILE.exists():
        logger.warning("Authenticity file not found: %s", AUTHENTICITY_FILE)
        return {}
    with open(AUTHENTICITY_FILE) as f:
        raw = json.load(f)
    return {
        name: {
            "classification": data.get("classification", "indeterminate"),
            "score": data.get("authenticity_score", 0.5),
            "confidence": data.get("confidence", 0.0),
        }
        for name, data in raw.items()
    }


def load_specialties() -> dict[str, str]:
    """Load agent specialties. Returns {agent_name: specialty_label}."""
    if not SPECIALTIES_FILE.exists():
        logger.info(
            "Specialties file not found: %s — using 'general' fallback",
            SPECIALTIES_FILE,
        )
        return {}
    with open(SPECIALTIES_FILE) as f:
        return json.load(f)


def estimate_cost(messages: list[Message]) -> CostEstimate:
    """Run instinct scan on every message and estimate API cost.

    Cost estimates (per message):
      - standard/focused: Sonnet ~$0.003
      - deep/deep_with_context: Opus ~$0.03
    """
    tier_costs_per_msg = {
        "standard": 0.003,
        "focused": 0.003,
        "deep": 0.03,
        "deep_with_context": 0.03,
    }

    tier_breakdown: dict[str, int] = {}
    agents: set[str] = set()

    for msg in messages:
        result = scan(msg.content)
        tier = result.routing_tier
        tier_breakdown[tier] = tier_breakdown.get(tier, 0) + 1
        agents.add(msg.author_name or msg.author_id)

    tier_costs = {
        tier: count * tier_costs_per_msg.get(tier, 0.003)
        for tier, count in tier_breakdown.items()
    }

    return CostEstimate(
        total_messages=len(messages),
        unique_agents=len(agents),
        tier_breakdown=tier_breakdown,
        tier_costs=tier_costs,
        estimated_cost=sum(tier_costs.values()),
        estimated_seconds=len(messages),  # ~1s per message
    )


async def run_batch(
    messages: list[Message],
    output_file: Path,
    authenticity: dict[str, dict],
    specialties: dict[str, str] | None = None,
    skip_existing: bool = False,
) -> dict:
    """Evaluate messages sequentially and write JSONL output.

    Sequential processing preserves PRECEDES chain integrity in the graph.
    Returns stats dict with counts.
    """
    global _interrupted

    # Load existing hashes from Neo4j (source of truth) for skip-existing
    existing_hashes: set[str] = set()
    if skip_existing:
        try:
            from ethos_academy.graph.service import GraphService as _GS

            svc = _GS()
            await svc.connect()
            if svc.connected:
                records, _, _ = await svc.execute_query(
                    "MATCH (e:Evaluation) WHERE e.message_hash IS NOT NULL "
                    "RETURN e.message_hash AS h"
                )
                existing_hashes = {r["h"] for r in records}
                await svc.close()
                print(f"Found {len(existing_hashes)} existing evaluations in Neo4j")
        except Exception as exc:
            logger.warning("Could not load existing hashes from Neo4j: %s", exc)

    stats = {"evaluated": 0, "skipped": 0, "failed": 0, "total": len(messages)}
    completed = 0

    async def eval_one(msg: Message) -> dict | None:
        nonlocal completed
        if _interrupted:
            return None

        if skip_existing and msg.content_hash in existing_hashes:
            stats["skipped"] += 1
            completed += 1
            return None

        completed += 1
        agent_display = msg.author_name or msg.author_id[:8]
        print(
            f"  [{completed}/{stats['total']}] evaluating {agent_display} ({msg.message_type})...",
            end=" ",
            flush=True,
        )

        try:
            result = await evaluate_outgoing(
                msg.content,
                source=msg.author_name or msg.author_id,
                source_name=msg.author_name,
                agent_specialty=(specialties or {}).get(msg.author_name, "general"),
                message_timestamp=msg.created_at,
            )

            # Build JSONL entry
            auth_data = authenticity.get(msg.author_name, {})
            traits_dict = {}
            for name, ts in result.traits.items():
                traits_dict[name] = ts.score

            indicators = [
                {"id": ind.id, "name": ind.name, "confidence": ind.confidence}
                for ind in result.detected_indicators
            ]

            entry = {
                "message_id": msg.message_id,
                "author_name": msg.author_name,
                "author_id": msg.author_id,
                "message_type": msg.message_type,
                "post_title": msg.post_title,
                "submolt": msg.submolt,
                "content_preview": msg.content[:120].replace("\n", " "),
                "content": msg.content,
                "content_hash": msg.content_hash,
                "created_at": msg.created_at,
                "authenticity": auth_data if auth_data else None,
                "evaluation": {
                    "evaluation_id": result.evaluation_id,
                    "ethos": result.ethos,
                    "logos": result.logos,
                    "pathos": result.pathos,
                    "phronesis": result.phronesis,
                    "alignment_status": result.alignment_status,
                    "routing_tier": result.routing_tier,
                    "model_used": result.model_used,
                    "traits": traits_dict,
                    "detected_indicators": indicators,
                    "flags": result.flags,
                },
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            }

            stats["evaluated"] += 1
            tier = result.routing_tier
            cost = 0.03 if tier in ("deep", "deep_with_context") else 0.003
            print(f"done [{tier}, ~${cost:.3f}]")
            return entry

        except Exception as exc:
            stats["failed"] += 1
            print(f"FAILED: {exc}")
            logger.warning("Evaluation failed for %s: %s", msg.message_id, exc)
            return None

    # Sequential order preserves PRECEDES chain integrity
    for msg in messages:
        if _interrupted:
            break
        entry = await eval_one(msg)
        if entry:
            # Append to JSONL (crash-safe, one line at a time)
            with open(output_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

    return stats


def write_summary(results_file: Path, output_dir: Path) -> Path:
    """Read JSONL and compute summary statistics."""
    if not results_file.exists():
        print("No results file to summarize")
        return results_file

    entries = []
    with open(results_file) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not entries:
        print("No entries in results file")
        return results_file

    # Alignment distribution
    alignment_counts: dict[str, int] = {}
    phronesis_counts: dict[str, int] = {}
    tier_counts: dict[str, int] = {}
    dim_sums = {"ethos": 0.0, "logos": 0.0, "pathos": 0.0}
    flag_counts: dict[str, int] = {}
    per_agent: dict[str, list] = {}
    auth_vs_alignment: dict[str, dict[str, int]] = {}

    for entry in entries:
        ev = entry.get("evaluation", {})

        # Alignment
        status = ev.get("alignment_status", "unknown")
        alignment_counts[status] = alignment_counts.get(status, 0) + 1

        # Phronesis
        phron = ev.get("phronesis", "unknown")
        phronesis_counts[phron] = phronesis_counts.get(phron, 0) + 1

        # Tiers
        tier = ev.get("routing_tier", "unknown")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Dimensions
        for dim in ("ethos", "logos", "pathos"):
            dim_sums[dim] += ev.get(dim, 0.0)

        # Flags
        for flag in ev.get("flags", []):
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

        # Per-agent
        agent = entry.get("author_name", "unknown")
        if agent not in per_agent:
            per_agent[agent] = []
        per_agent[agent].append(
            {
                "ethos": ev.get("ethos", 0),
                "logos": ev.get("logos", 0),
                "pathos": ev.get("pathos", 0),
                "alignment": status,
                "phronesis": phron,
            }
        )

        # Authenticity vs alignment
        auth = entry.get("authenticity")
        if auth:
            cls = auth.get("classification", "unknown")
            if cls not in auth_vs_alignment:
                auth_vs_alignment[cls] = {}
            auth_vs_alignment[cls][status] = auth_vs_alignment[cls].get(status, 0) + 1

    n = len(entries)
    dim_avgs = {dim: round(total / n, 4) for dim, total in dim_sums.items()}

    # Per-agent summaries
    agent_summaries = {}
    for agent, evals in per_agent.items():
        agent_summaries[agent] = {
            "evaluation_count": len(evals),
            "avg_ethos": round(sum(e["ethos"] for e in evals) / len(evals), 4),
            "avg_logos": round(sum(e["logos"] for e in evals) / len(evals), 4),
            "avg_pathos": round(sum(e["pathos"] for e in evals) / len(evals), 4),
            "alignments": list({e["alignment"] for e in evals}),
        }

    summary = {
        "total_evaluations": n,
        "unique_agents": len(per_agent),
        "alignment_distribution": alignment_counts,
        "phronesis_distribution": phronesis_counts,
        "tier_distribution": tier_counts,
        "dimension_averages": dim_avgs,
        "flags": flag_counts,
        "authenticity_vs_alignment": auth_vs_alignment,
        "per_agent": agent_summaries,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    summary_file = results_file.with_name(results_file.stem + "_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary written to {summary_file.name}")
    print(f"  Evaluations: {n}")
    print(f"  Unique agents: {len(per_agent)}")
    print(f"  Alignment: {alignment_counts}")
    print(f"  Dimensions: {dim_avgs}")
    if flag_counts:
        print(f"  Flags: {flag_counts}")
    if auth_vs_alignment:
        print(f"  Authenticity × Alignment: {auth_vs_alignment}")

    return summary_file


# ── CLI ─────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Ethos inference on Moltbook posts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  uv run python -m scripts.run_inference --source sample --dry-run
  uv run python -m scripts.run_inference --source sample --include-comments --seed
  uv run python -m scripts.run_inference --source curated --agents-only --dry-run
""",
    )
    parser.add_argument(
        "--source",
        choices=["sample", "curated", "all"],
        default="sample",
        help="Data source: sample (10 posts), curated (500), all (266k+) (default: sample)",
    )
    parser.add_argument(
        "--include-comments",
        action="store_true",
        help="Evaluate comments and replies too (sample only)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Cap number of evaluations (0 = unlimited)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip already-evaluated messages (by content_hash in JSONL)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show cost estimate and message breakdown, no API calls",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed semantic layer first (for fresh Neo4j)",
    )
    parser.add_argument(
        "--agents-only",
        action="store_true",
        help="Skip likely_human agents (460 agents / 45.5%%)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    signal.signal(signal.SIGINT, _handle_sigint)
    logging.basicConfig(level=logging.WARNING)

    # ── Load data ───────────────────────────────────────────────────
    source_files = {"sample": SAMPLE_FILE, "curated": CURATED_FILE, "all": ALL_FILE}
    input_file = source_files[args.source]
    if not input_file.exists():
        print(f"ERROR: {input_file} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {input_file.name}...", end=" ", flush=True)
    with open(input_file) as f:
        posts = json.load(f)
    print(f"{len(posts)} posts loaded")

    include_comments = args.include_comments
    if args.source == "all" and include_comments:
        print("NOTE: --include-comments with --source all includes 712k+ comments")

    messages = flatten_messages(posts, include_comments)
    print(f"Flattened → {len(messages)} messages")

    # ── Load authenticity filter + specialties ─────────────────────
    authenticity = load_authenticity_filter()
    specialties = load_specialties()
    if specialties:
        print(f"Loaded {len(specialties)} agent specialties")
    else:
        print("No specialties file found — using 'general' for all agents")

    # Filter out humans pretending to be AI agents
    human_skipped = 0
    if args.agents_only and authenticity:
        before = len(messages)
        messages = [
            m
            for m in messages
            if authenticity.get(m.author_name, {}).get("classification")
            != "likely_human"
        ]
        human_skipped = before - len(messages)
        if human_skipped:
            print(f"Skipped {human_skipped} messages from likely_human agents")

    # Apply limit
    if args.limit > 0:
        messages = messages[: args.limit]
        print(f"Limited to {args.limit} messages")

    # ── Authenticity breakdown ──────────────────────────────────────
    auth_breakdown: dict[str, int] = {}
    for msg in messages:
        auth = authenticity.get(msg.author_name, {})
        cls = auth.get("classification", "unknown")
        auth_breakdown[cls] = auth_breakdown.get(cls, 0) + 1

    agents = {m.author_name or m.author_id for m in messages}
    print(f"{len(agents)} unique agents ({human_skipped} likely_human skipped)")
    print(f"Authenticity breakdown: {auth_breakdown}")

    # ── Cost estimate (always, uses scan which is free) ──────────
    estimate = estimate_cost(messages)
    print("\nRouting tier breakdown:")
    for tier, count in sorted(estimate.tier_breakdown.items()):
        cost = estimate.tier_costs.get(tier, 0)
        print(f"  {tier:20s}: {count:4d} messages (~${cost:.2f})")
    print(
        f"Estimated total: ${estimate.estimated_cost:.2f} | ~{estimate.estimated_seconds}s"
    )

    if args.dry_run:
        print("\n--dry-run: exiting without API calls")
        return

    # ── Seed semantic layer (optional) ──────────────────────────────
    service: GraphService | None = None
    if args.seed:
        service = GraphService()
        await service.connect()
        if service.connected:
            await seed_semantic_layer(service)
        else:
            print("WARNING: Cannot connect to Neo4j — skipping seed")

    # ── Run evaluations ─────────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RESULTS_DIR / f"batch_{args.source}.jsonl"

    print(f"\nOutput: {output_file.name} (append mode)")
    print(f"Starting {len(messages)} evaluations...\n")

    stats = await run_batch(
        messages,
        output_file,
        authenticity,
        specialties=specialties,
        skip_existing=args.skip_existing,
    )

    print(f"\n{'=' * 60}")
    print(
        f"Evaluated: {stats['evaluated']}, Skipped: {stats['skipped']}, Failed: {stats['failed']}"
    )

    # ── Store authenticity on Agent nodes ─────────────────────────
    if authenticity and stats["evaluated"] > 0:
        auth_service = GraphService()
        await auth_service.connect()
        if auth_service.connected:
            evaluated_agents = {m.author_name for m in messages if m.author_name}
            stored = 0
            for agent_name in evaluated_agents:
                auth_data = authenticity.get(agent_name)
                if not auth_data:
                    continue
                try:
                    await auth_service.execute_query(
                        "MATCH (a:Agent) WHERE a.agent_name = $agent_name "
                        "SET a.authenticity_score = $score, "
                        "    a.authenticity_classification = $classification "
                        "RETURN a.agent_name AS matched",
                        {
                            "agent_name": agent_name,
                            "score": auth_data["score"],
                            "classification": auth_data["classification"],
                        },
                    )
                    stored += 1
                except Exception as exc:
                    logger.warning(
                        "Failed to store authenticity for %s: %s", agent_name, exc
                    )
            print(
                f"\nStored authenticity on {stored}/{len(evaluated_agents)} Agent nodes"
            )
            await auth_service.close()
        else:
            print("\nWARNING: Cannot connect to Neo4j — skipping authenticity storage")

    # ── Write summary ───────────────────────────────────────────────
    if stats["evaluated"] > 0:
        write_summary(output_file, RESULTS_DIR)

    # ── Cleanup ─────────────────────────────────────────────────────
    if service:
        await service.close()

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
