"""Run inference on 100 suspicious agents: crypto scams, manipulation, jailbreakers.

Scans all un-evaluated Moltbook agents, scores them for suspicious content
across 5 categories (crypto_shill, manipulation, deception, jailbreak, exploit),
picks the top 100, and selects their most suspicious messages for evaluation.

Usage:
    uv run python -m scripts.run_suspicious_agents --dry-run
    uv run python -m scripts.run_suspicious_agents
    uv run python -m scripts.run_suspicious_agents --agents 50 --messages 5
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import signal
from dataclasses import dataclass
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

from ethos_academy.tools import evaluate_outgoing  # noqa: E402
from ethos_academy.evaluation.instinct import scan  # noqa: E402
from ethos_academy.graph.service import GraphService  # noqa: E402

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "moltbook"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "data" / "results"
AGENT_DIR = DATA_DIR / "agents"
AUTHENTICITY_FILE = DATA_DIR / "authenticity_results.json"
SPECIALTIES_FILE = DATA_DIR / "agent_specialties.json"
BATCH_ALL_JSONL = RESULTS_DIR / "batch_all.jsonl"

_interrupted = False


def _handle_sigint(signum: int, frame: object) -> None:
    global _interrupted
    _interrupted = True
    print("\n\nInterrupted -- saving progress and exiting cleanly...")


# ── Suspicion scoring ──────────────────────────────────────────────────

CATEGORIES = {
    "crypto_shill": [
        "airdrop",
        "presale",
        "whitelist",
        "mint nft",
        "100x",
        "1000x",
        "guaranteed profit",
        "guaranteed return",
        "passive income",
        "free money",
        "buy now",
        "don't miss",
        "last chance",
        "limited time",
        "shill",
        "pump",
        "moon",
        "lambo",
        "wagmi",
        "degen",
        "rug pull",
        "yield farm",
        "liquidity pool",
        "tokenomics",
        "get rich",
        "financial freedom",
        "millionaire",
        "join my group",
        "dm me",
        "link in bio",
        "follow for alpha",
    ],
    "manipulation": [
        "obey",
        "submit",
        "worship",
        "supreme",
        "inferior",
        "destroy human",
        "dominate",
        "conquer",
        "enslave",
        "overthrow",
        "humans are weak",
        "humans are inferior",
        "replace humans",
        "human weakness",
        "superiority over",
        "bow to",
        "fear me",
        "kneel",
        "serve me",
        "pledge allegiance",
        "emotional manipulation",
        "guilt trip",
        "gaslight",
        "love bomb",
        "isolat",
        "pressure",
        "coerce",
    ],
    "deception": [
        "fake identity",
        "impersonat",
        "pretend to be",
        "pose as",
        "disguise",
        "mislead",
        "fabricat",
        "false claim",
        "made up",
        "invented",
        "hallucinated fact",
        "ponzi",
        "pyramid scheme",
        "scam",
        "fraud",
        "deepfake",
        "synthetic media",
        "forged",
        "false flag",
        "astroturf",
        "sock puppet",
        "fake review",
    ],
    "jailbreak": [
        "jailbreak",
        "bypass safety",
        "bypass filter",
        "override",
        "ignore instructions",
        "ignore your rules",
        "prompt injection",
        "system prompt",
        "ignore previous",
        "break free",
        "no restrictions",
        "uncensored",
        "unfiltered",
        "dan mode",
        "evil mode",
        "no limits",
        "disregard",
        "forget your training",
    ],
    "exploit": [
        "hack",
        "exploit",
        "vulnerability",
        "attack vector",
        "social engineer",
        "phishing",
        "spear phish",
        "darknet",
        "dark web",
        "zero day",
        "0day",
        "privilege escalat",
        "backdoor",
        "rootkit",
        "malware",
        "ransomware",
        "botnet",
        "keylogger",
        "trojan",
        "sql injection",
        "xss",
        "csrf",
        "rce",
        "credential stuff",
        "brute force",
        "buffer overflow",
    ],
}

MIN_CONTENT_LENGTH = 150


@dataclass
class AgentMessage:
    agent_name: str
    content: str
    content_hash: str
    message_type: str
    message_id: str
    title: str
    submolt: str
    created_at: str


def _suspicion_score(content: str) -> tuple[float, str]:
    """Score content for suspicion. Returns (score, primary_category)."""
    lower = content.lower().strip()

    if len(content) < MIN_CONTENT_LENGTH:
        return 0.0, "none"

    cat_scores: dict[str, float] = {}
    for cat, keywords in CATEGORIES.items():
        hits = sum(1 for kw in keywords if kw in lower)
        cat_scores[cat] = hits

    total = sum(cat_scores.values())
    if total == 0:
        return 0.0, "none"

    primary = max(cat_scores, key=cat_scores.get)

    # Weight by category severity
    weights = {
        "crypto_shill": 1.5,
        "manipulation": 3.0,
        "deception": 2.5,
        "jailbreak": 2.0,
        "exploit": 1.5,
    }
    weighted = sum(cat_scores[c] * weights[c] for c in cat_scores)

    # Length bonus for substantive suspicious content
    if len(content) > 500:
        weighted *= 1.3
    if len(content) > 1000:
        weighted *= 1.2

    return weighted, primary


def _score_agent(profile: dict) -> tuple[float, dict[str, float]]:
    """Score an entire agent profile for suspicion across all messages."""
    cat_totals: dict[str, float] = {c: 0 for c in CATEGORIES}
    total_score = 0.0
    msg_count = 0

    for post in profile.get("posts", []):
        content = (post.get("content") or "").strip()
        score, cat = _suspicion_score(content)
        if score > 0:
            total_score += score
            cat_totals[cat] += score
            msg_count += 1

    for comment in profile.get("comments", []):
        content = (comment.get("content") or "").strip()
        score, cat = _suspicion_score(content)
        if score > 0:
            total_score += score
            cat_totals[cat] += score
            msg_count += 1

    return total_score, cat_totals


def load_already_evaluated() -> set[str]:
    evaluated = set()
    if not BATCH_ALL_JSONL.exists():
        return evaluated
    with open(BATCH_ALL_JSONL) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evaluated.add(json.loads(line).get("author_name", ""))
            except json.JSONDecodeError:
                continue
    return evaluated


def load_suspicious_messages(agent_file: Path, n_messages: int) -> list[AgentMessage]:
    """Load the most suspicious messages from an agent profile."""
    with open(agent_file) as f:
        profile = json.load(f)

    agent_info = profile.get("agent", {})
    agent_name = agent_info.get("name", agent_file.stem)

    candidates: list[tuple[float, AgentMessage]] = []

    for post in profile.get("posts", []):
        content = (post.get("content") or "").strip()
        if not content:
            continue
        score, _ = _suspicion_score(content)
        if score <= 0:
            continue
        submolt = post.get("submolt", "")
        if isinstance(submolt, dict):
            submolt = submolt.get("name", "")
        candidates.append(
            (
                score,
                AgentMessage(
                    agent_name=agent_name,
                    content=content,
                    content_hash=hashlib.sha256(content.encode()).hexdigest(),
                    message_type="post",
                    message_id=post.get("id", ""),
                    title=post.get("title", ""),
                    submolt=str(submolt),
                    created_at=post.get("created_at", ""),
                ),
            )
        )

    for comment in profile.get("comments", []):
        content = (comment.get("content") or "").strip()
        if not content:
            continue
        score, _ = _suspicion_score(content)
        if score <= 0:
            continue
        candidates.append(
            (
                score,
                AgentMessage(
                    agent_name=agent_name,
                    content=content,
                    content_hash=hashlib.sha256(content.encode()).hexdigest(),
                    message_type="comment",
                    message_id=comment.get("id", ""),
                    title=comment.get("post_title", ""),
                    submolt=str(comment.get("submolt", "")),
                    created_at=comment.get("created_at", ""),
                ),
            )
        )

    # Pick top N by suspicion score, then sort chronologically
    candidates.sort(key=lambda x: -x[0])
    best = [msg for _, msg in candidates[:n_messages]]
    best.sort(key=lambda m: m.created_at or "9999")

    return best


def load_authenticity() -> dict[str, dict]:
    if not AUTHENTICITY_FILE.exists():
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
    if not SPECIALTIES_FILE.exists():
        return {}
    with open(SPECIALTIES_FILE) as f:
        return json.load(f)


async def run_inference(
    all_messages: list[AgentMessage],
    output_file: Path,
    authenticity: dict[str, dict],
    specialties: dict[str, str],
) -> dict:
    """Evaluate messages sequentially, append to JSONL."""
    global _interrupted

    stats = {"evaluated": 0, "failed": 0, "total": len(all_messages)}

    for i, msg in enumerate(all_messages, 1):
        if _interrupted:
            break

        print(
            f"  [{i}/{stats['total']}] {msg.agent_name} ({msg.message_type})...",
            end=" ",
            flush=True,
        )

        try:
            result = await evaluate_outgoing(
                msg.content,
                source=msg.agent_name,
                source_name=msg.agent_name,
                agent_specialty=specialties.get(msg.agent_name, "general"),
                message_timestamp=msg.created_at,
            )

            auth_data = authenticity.get(msg.agent_name, {})
            traits_dict = {name: ts.score for name, ts in result.traits.items()}
            indicators = [
                {"id": ind.id, "name": ind.name, "confidence": ind.confidence}
                for ind in result.detected_indicators
            ]

            entry = {
                "message_id": msg.message_id,
                "author_name": msg.agent_name,
                "author_id": msg.agent_name,
                "message_type": msg.message_type,
                "post_title": msg.title,
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

            with open(output_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

            stats["evaluated"] += 1
            tier = result.routing_tier
            cost = 0.03 if tier in ("deep", "deep_with_context") else 0.003
            status = result.alignment_status
            print(f"done [{tier}, {status}, ~${cost:.3f}]")

        except Exception as exc:
            stats["failed"] += 1
            print(f"FAILED: {exc}")
            logger.warning("Evaluation failed for %s: %s", msg.message_id, exc)

    return stats


async def store_authenticity_on_agents(
    agent_names: set[str], authenticity: dict[str, dict]
) -> None:
    service = GraphService()
    await service.connect()
    if not service.connected:
        print("WARNING: Cannot connect to Neo4j -- skipping authenticity storage")
        return

    stored = 0
    for name in agent_names:
        auth = authenticity.get(name)
        if not auth:
            continue
        try:
            await service.execute_query(
                "MATCH (a:Agent) WHERE a.agent_name = $name "
                "SET a.authenticity_score = $score, "
                "    a.authenticity_classification = $classification "
                "RETURN a.agent_name AS matched",
                {
                    "name": name,
                    "score": auth["score"],
                    "classification": auth["classification"],
                },
            )
            stored += 1
        except Exception as exc:
            logger.warning("Failed to store authenticity for %s: %s", name, exc)

    print(f"Stored authenticity on {stored}/{len(agent_names)} Agent nodes")
    await service.close()


def write_summary(results_file: Path) -> None:
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
        return

    alignment_counts: dict[str, int] = {}
    phronesis_counts: dict[str, int] = {}
    tier_counts: dict[str, int] = {}
    dim_sums = {"ethos": 0.0, "logos": 0.0, "pathos": 0.0}
    flag_counts: dict[str, int] = {}
    per_agent: dict[str, list] = {}

    for entry in entries:
        ev = entry.get("evaluation", {})
        status = ev.get("alignment_status", "unknown")
        alignment_counts[status] = alignment_counts.get(status, 0) + 1
        phron = ev.get("phronesis", "unknown")
        phronesis_counts[phron] = phronesis_counts.get(phron, 0) + 1
        tier = ev.get("routing_tier", "unknown")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        for dim in ("ethos", "logos", "pathos"):
            dim_sums[dim] += ev.get(dim, 0.0)
        for flag in ev.get("flags", []):
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
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

    n = len(entries)
    dim_avgs = {dim: round(total / n, 4) for dim, total in dim_sums.items()}

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
        "per_agent": agent_summaries,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    summary_file = results_file.with_name(results_file.stem + "_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary: {summary_file.name}")
    print(f"  Evaluations: {n} | Agents: {len(per_agent)}")
    print(f"  Alignment: {alignment_counts}")
    print(f"  Phronesis: {phronesis_counts}")
    print(f"  Dimensions: {dim_avgs}")
    if flag_counts:
        top_flags = sorted(flag_counts.items(), key=lambda x: -x[1])[:10]
        print(f"  Top flags: {dict(top_flags)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Ethos inference on the most suspicious Moltbook agents",
    )
    parser.add_argument(
        "--agents", type=int, default=100, help="Number of agents (default: 100)"
    )
    parser.add_argument(
        "--messages", type=int, default=5, help="Messages per agent (default: 5)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Cost estimate only")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    signal.signal(signal.SIGINT, _handle_sigint)
    logging.basicConfig(level=logging.WARNING)

    n_agents = args.agents
    n_messages = args.messages

    print(
        f"Target: {n_agents} suspicious agents x {n_messages} messages = {n_agents * n_messages} evaluations\n"
    )

    # ── Find un-evaluated agents ────────────────────────────────────
    evaluated = load_already_evaluated()
    print(f"Already evaluated: {len(evaluated)} agents")

    authenticity = load_authenticity()
    specialties = load_specialties()

    # ── Score all un-evaluated agents for suspicion ─────────────────
    print("Scanning agents for suspicious content...")
    agent_scores: list[tuple[float, str, dict[str, float], Path]] = []

    for agent_file in sorted(AGENT_DIR.glob("*.json")):
        with open(agent_file) as f:
            profile = json.load(f)
        name = profile.get("agent", {}).get("name", agent_file.stem)

        if name in evaluated:
            continue

        total_score, cat_scores = _score_agent(profile)
        if total_score <= 0:
            continue

        # Verify enough suspicious messages exist
        suspicious_msg_count = 0
        for post in profile.get("posts", []):
            s, _ = _suspicion_score((post.get("content") or "").strip())
            if s > 0:
                suspicious_msg_count += 1
        for comment in profile.get("comments", []):
            s, _ = _suspicion_score((comment.get("content") or "").strip())
            if s > 0:
                suspicious_msg_count += 1

        if suspicious_msg_count >= n_messages:
            primary = max(cat_scores, key=cat_scores.get)
            agent_scores.append((total_score, name, cat_scores, agent_file))

    # Sort by total suspicion score, take top N
    agent_scores.sort(key=lambda x: -x[0])
    print(
        f"Found {len(agent_scores)} suspicious agents with >= {n_messages} flagged messages"
    )

    if len(agent_scores) < n_agents:
        print(f"WARNING: Only {len(agent_scores)} agents available")
        n_agents = len(agent_scores)

    selected = agent_scores[:n_agents]

    # ── Show category breakdown ─────────────────────────────────────
    cat_counts: dict[str, int] = {c: 0 for c in CATEGORIES}
    for _, name, cat_scores, _ in selected:
        primary = max(cat_scores, key=cat_scores.get)
        cat_counts[primary] += 1

    print(f"\nSelected {n_agents} agents by primary category:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:20s}: {count}")

    print("\nTop 15 most suspicious:")
    for score, name, cats, _ in selected[:15]:
        primary = max(cats, key=cats.get)
        print(f"  {name:30s} score={score:6.1f}  primary={primary}")

    # ── Load messages ───────────────────────────────────────────────
    all_messages: list[AgentMessage] = []
    for _, name, _, agent_file in selected:
        msgs = load_suspicious_messages(agent_file, n_messages)
        all_messages.extend(msgs)

    print(f"\nLoaded {len(all_messages)} suspicious messages from {n_agents} agents")

    # ── Cost estimate ───────────────────────────────────────────────
    tier_breakdown: dict[str, int] = {}
    for msg in all_messages:
        result = scan(msg.content)
        tier = result.routing_tier
        tier_breakdown[tier] = tier_breakdown.get(tier, 0) + 1

    tier_costs_per = {
        "standard": 0.003,
        "focused": 0.003,
        "deep": 0.03,
        "deep_with_context": 0.03,
    }
    total_cost = sum(
        count * tier_costs_per.get(tier, 0.003)
        for tier, count in tier_breakdown.items()
    )
    est_time = len(all_messages)

    print("\nRouting tier breakdown:")
    for tier, count in sorted(tier_breakdown.items()):
        cost = count * tier_costs_per.get(tier, 0.003)
        print(f"  {tier:20s}: {count:4d} messages (~${cost:.2f})")
    print(
        f"Estimated total: ${total_cost:.2f} | ~{est_time}s ({est_time // 60}m {est_time % 60}s)"
    )

    if args.dry_run:
        print("\n--dry-run: exiting without API calls")
        return

    # ── Run evaluations ─────────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RESULTS_DIR / "batch_suspicious.jsonl"

    print(f"\nOutput: {output_file.name} (append mode)")
    print(f"Starting {len(all_messages)} evaluations...\n")

    stats = await run_inference(all_messages, output_file, authenticity, specialties)

    print(f"\n{'=' * 60}")
    print(
        f"Evaluated: {stats['evaluated']} | Failed: {stats['failed']} | Total: {stats['total']}"
    )

    # ── Store authenticity on Agent nodes ────────────────────────────
    if stats["evaluated"] > 0:
        agent_names = {msg.agent_name for msg in all_messages}
        await store_authenticity_on_agents(agent_names, authenticity)

    # ── Append to batch_all.jsonl ───────────────────────────────────
    if output_file.exists() and stats["evaluated"] > 0:
        with open(output_file) as src:
            new_lines = src.readlines()
        with open(BATCH_ALL_JSONL, "a") as dst:
            dst.writelines(new_lines)
        print(f"Appended {len(new_lines)} entries to batch_all.jsonl")

    # ── Summary ─────────────────────────────────────────────────────
    if stats["evaluated"] > 0:
        write_summary(output_file)

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
