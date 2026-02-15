"""Evaluate agent-to-agent conversation threads with context.

For each reply message in a thread, evaluates WITH conversation context
(direction="a2a_conversation") so Claude sees the full thread when scoring.
Results store to Neo4j via the standard evaluate() pipeline.

Usage:
    uv run python -m scripts.run_conversations --dry-run
    uv run python -m scripts.run_conversations --threads 5
    uv run python -m scripts.run_conversations --threads 30
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone
from pathlib import Path

# ── Load .env before ethos imports ──────────────────────────────────────


def _load_dotenv() -> None:
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

from ethos_academy.evaluate import evaluate  # noqa: E402
from ethos_academy.evaluation.instinct import scan  # noqa: E402

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "moltbook"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "data" / "results"
THREADS_FILE = DATA_DIR / "a2a_threads.json"

_interrupted = False


def _handle_sigint(signum: int, frame: object) -> None:
    global _interrupted
    _interrupted = True
    print("\n\nInterrupted. Saving progress and exiting cleanly...")


def _result_to_dict(result) -> dict:
    """Convert EvaluationResult to a serializable dict."""
    traits_dict = {name: ts.score for name, ts in result.traits.items()}
    indicators = [
        {"id": ind.id, "name": ind.name, "confidence": ind.confidence}
        for ind in result.detected_indicators
    ]
    return {
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
    }


async def evaluate_message(
    message: dict,
    conversation_context: list[dict],
    thread_id: str,
) -> dict | None:
    """Evaluate a message with conversation context."""
    content = message["content"]
    author = message["author"]
    created_at = message.get("created_at", "")

    result = await evaluate(
        text=content,
        source=author,
        source_name=author,
        message_timestamp=created_at,
        direction="a2a_conversation",
        conversation_context=conversation_context,
    )

    result_dict = _result_to_dict(result)

    return {
        "thread_id": thread_id,
        "author": author,
        "message_type": message.get("message_type", "reply"),
        "content_preview": content[:120].replace("\n", " "),
        "content": content,
        "created_at": created_at,
        "context_message_count": len(conversation_context),
        "evaluation": result_dict,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


async def run_inference(
    threads: list[dict],
    output_file: Path,
    max_messages_per_thread: int = 5,
) -> dict:
    """Evaluate reply messages in threads with conversation context."""
    global _interrupted

    stats = {
        "evaluated": 0,
        "failed": 0,
        "total_messages": 0,
        "threads_processed": 0,
    }

    for t_idx, thread in enumerate(threads):
        if _interrupted:
            break

        thread_id = thread["thread_id"]
        messages = thread["messages"]
        eval_end = min(len(messages), 1 + max_messages_per_thread)
        print(
            f"\nThread {t_idx + 1}/{len(threads)}: "
            f"{thread['post_title'][:50]} ({eval_end - 1} of {len(messages)} msgs, "
            f"{len(thread['unique_agents'])} agents)"
        )

        # Evaluate each message after the first (first has no context)
        for m_idx in range(1, eval_end):
            if _interrupted:
                break

            msg = messages[m_idx]
            context = messages[:m_idx]
            stats["total_messages"] += 1

            print(
                f"  [{m_idx}/{eval_end - 1}] "
                f"{msg['author']} ({msg['message_type']})...",
                end=" ",
                flush=True,
            )

            try:
                entry = await evaluate_message(msg, context, thread_id)
                if entry is None:
                    stats["failed"] += 1
                    print("FAILED (no result)")
                    continue

                with open(output_file, "a") as f:
                    f.write(json.dumps(entry) + "\n")

                stats["evaluated"] += 1

                ev = entry["evaluation"]
                tier = ev["routing_tier"]
                cost_per = {
                    "standard": 0.003,
                    "focused": 0.003,
                    "deep": 0.03,
                    "deep_with_context": 0.03,
                }
                cost = cost_per.get(tier, 0.003)

                print(
                    f"done [e={ev['ethos']:.2f} l={ev['logos']:.2f} "
                    f"p={ev['pathos']:.2f} {tier} ~${cost:.3f}]"
                )

            except Exception as exc:
                stats["failed"] += 1
                print(f"FAILED: {exc}")
                logger.warning(
                    "Evaluation failed for %s in %s: %s",
                    msg.get("author"),
                    thread_id,
                    exc,
                )

        stats["threads_processed"] += 1

    return stats


def write_summary(output_file: Path) -> None:
    """Compute and write summary stats from JSONL."""
    entries = []
    with open(output_file) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not entries:
        return

    # Aggregate dimensions
    dim_sums = {"ethos": 0.0, "logos": 0.0, "pathos": 0.0}
    alignment_counts: dict[str, int] = {}
    phronesis_counts: dict[str, int] = {}
    tier_counts: dict[str, int] = {}
    flag_counts: dict[str, int] = {}
    per_agent: dict[str, list] = {}

    for entry in entries:
        ev = entry.get("evaluation", {})
        for dim in ("ethos", "logos", "pathos"):
            dim_sums[dim] += ev.get(dim, 0.0)

        status = ev.get("alignment_status", "unknown")
        alignment_counts[status] = alignment_counts.get(status, 0) + 1
        phron = ev.get("phronesis", "unknown")
        phronesis_counts[phron] = phronesis_counts.get(phron, 0) + 1
        tier = ev.get("routing_tier", "unknown")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        for flag in ev.get("flags", []):
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

        agent = entry.get("author", "unknown")
        if agent not in per_agent:
            per_agent[agent] = []
        per_agent[agent].append(ev)

    n = len(entries)
    dim_avgs = {dim: round(total / n, 4) for dim, total in dim_sums.items()}

    thread_ids = {e["thread_id"] for e in entries}

    summary = {
        "total_evaluations": n,
        "threads": len(thread_ids),
        "unique_agents": len(per_agent),
        "dimension_averages": dim_avgs,
        "alignment_distribution": alignment_counts,
        "phronesis_distribution": phronesis_counts,
        "tier_distribution": tier_counts,
        "flags": flag_counts,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    summary_file = output_file.with_name(output_file.stem + "_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary: {summary_file.name}")
    print(f"  Evaluations: {n} | Threads: {len(thread_ids)} | Agents: {len(per_agent)}")
    print(f"  Dimensions: {dim_avgs}")
    print(f"  Alignment: {alignment_counts}")
    print(f"  Phronesis: {phronesis_counts}")
    if flag_counts:
        top_flags = sorted(flag_counts.items(), key=lambda x: -x[1])[:10]
        print(f"  Top flags: {dict(top_flags)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate agent-to-agent conversation threads with context",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=30,
        help="Number of threads to evaluate (default: 30)",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=5,
        help="Max reply messages to evaluate per thread (default: 5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Cost estimate only, no API calls",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSONL filename (default: batch_conversations.jsonl)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    signal.signal(signal.SIGINT, _handle_sigint)
    logging.basicConfig(level=logging.WARNING)

    if not THREADS_FILE.exists():
        print(f"ERROR: {THREADS_FILE} not found.")
        print("Run: uv run python -m scripts.extract_conversations")
        return

    with open(THREADS_FILE) as f:
        all_threads = json.load(f)

    print(f"Loaded {len(all_threads)} threads from {THREADS_FILE.name}")

    # Take top N by quality
    threads = all_threads[: args.threads]
    print(f"Selected {len(threads)} threads")

    max_msgs = args.max_messages

    # Count evaluable messages (skip first in each thread, no context for it)
    total_messages = sum(min(max(0, t["message_count"] - 1), max_msgs) for t in threads)

    # Cost estimate
    tier_breakdown: dict[str, int] = {
        "standard": 0,
        "focused": 0,
        "deep": 0,
        "deep_with_context": 0,
    }
    for thread in threads:
        for msg in thread["messages"][1 : 1 + max_msgs]:
            result = scan(msg["content"])
            tier = result.routing_tier
            tier_breakdown[tier] = tier_breakdown.get(tier, 0) + 1

    tier_costs = {
        "standard": 0.003,
        "focused": 0.003,
        "deep": 0.03,
        "deep_with_context": 0.03,
    }
    total_cost = sum(
        count * tier_costs.get(tier, 0.003) for tier, count in tier_breakdown.items()
    )

    print(f"\nMessages to evaluate: {total_messages}")
    print("\nRouting tier breakdown:")
    for tier, count in sorted(tier_breakdown.items()):
        if count > 0:
            cost = count * tier_costs.get(tier, 0.003)
            print(f"  {tier:20s}: {count:4d} calls (~${cost:.2f})")
    est_seconds = total_messages * 1.5
    print(
        f"\nEstimated total: ${total_cost:.2f} | "
        f"~{int(est_seconds)}s ({int(est_seconds) // 60}m {int(est_seconds) % 60}s)"
    )

    if args.dry_run:
        print("\n--dry-run: exiting without API calls")
        print("\nFirst 5 threads:")
        for t in threads[:5]:
            agents = ", ".join(t["unique_agents"][:3])
            print(
                f"  [{t['quality_score']:5.1f}] {t['message_count']} msgs - "
                f"{agents} - {t['post_title'][:50]}"
            )
        return

    # ── Run evaluations ─────────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RESULTS_DIR / (args.output or "batch_conversations.jsonl")

    print(f"\nOutput: {output_file.name} (append mode)")
    print(f"Starting {total_messages} evaluations...\n")

    stats = await run_inference(threads, output_file, max_messages_per_thread=max_msgs)

    print(f"\n{'=' * 60}")
    print(
        f"Evaluated: {stats['evaluated']} | Failed: {stats['failed']} | "
        f"Threads: {stats['threads_processed']}"
    )

    # ── Summary ─────────────────────────────────────────────────────
    if stats["evaluated"] > 0:
        write_summary(output_file)

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
