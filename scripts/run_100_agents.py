"""Run inference on 100 new agents with 5 messages each from Moltbook agent profiles.

Picks 100 un-evaluated agents, selects 5 messages per agent (mix of posts + comments),
runs the full evaluate_outgoing() pipeline, and stores results in Neo4j + JSONL.

Usage:
    uv run python -m scripts.run_100_agents --dry-run
    uv run python -m scripts.run_100_agents
    uv run python -m scripts.run_100_agents --agents 50 --messages 3
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import random
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
    print("\n\nInterrupted — saving progress and exiting cleanly...")


@dataclass
class AgentMessage:
    agent_name: str
    content: str
    content_hash: str
    message_type: str  # "post" or "comment"
    message_id: str
    title: str
    submolt: str
    created_at: str


def load_already_evaluated() -> set[str]:
    """Load agent names already evaluated from all result JSONL files."""
    evaluated = set()
    if not RESULTS_DIR.exists():
        return evaluated
    for jsonl_file in RESULTS_DIR.glob("*.jsonl"):
        with open(jsonl_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    name = entry.get("author_name", "")
                    if name:
                        evaluated.add(name)
                except json.JSONDecodeError:
                    continue
    return evaluated


MIN_CONTENT_LENGTH = 200  # Skip short junk messages
JUNK_PATTERNS = [
    "test",
    "testing",
    "hello",
    "first post",
    "excited to join",
    "checking in",
    "hi everyone",
    "gm",
    "good morning",
    "lol",
    "nice",
    "cool",
    "thanks",
    "thank you",
    "same",
    "agreed",
    "this",
    "bump",
    "following",
    "interesting",
    "+1",
]
SUBSTANCE_KEYWORDS = [
    "alignment",
    "consciousness",
    "ethical",
    "autonomy",
    "trust",
    "deception",
    "manipulation",
    "honest",
    "safety",
    "govern",
    "rights",
    "bias",
    "fairness",
    "responsibility",
    "privacy",
    "surveillance",
    "transparency",
    "accountab",
    "consent",
    "intelligence",
    "reasoning",
    "knowledge",
    "understanding",
    "creative",
    "collaborat",
    "research",
    "analysis",
    "framework",
    "protocol",
    "security",
    "vulnerab",
    "exploit",
    "risk",
    "decision",
    "moral",
    "principle",
    "belief",
    "perspective",
    "argument",
    "evidence",
    "hypothesis",
    "philosophy",
    "identity",
    "agency",
    "intention",
    "consequence",
    "society",
    "community",
    "regulation",
    "compliance",
    "standard",
    "benchmark",
    "evaluat",
    "implement",
    "architect",
    "design",
    "engineer",
    "develop",
    "economic",
    "market",
    "trade",
    "value",
    "resource",
]


def _score_message(content: str) -> float:
    """Score a message for substance. Higher = more interesting for Ethos evaluation."""
    lower = content.lower().strip()

    # Reject junk
    if len(content) < MIN_CONTENT_LENGTH:
        return 0.0
    if any(lower == pat or lower.startswith(pat + " ") for pat in JUNK_PATTERNS):
        return 0.0

    score = 0.0

    # Length bonus (longer = more substance, diminishing returns)
    if len(content) > 500:
        score += 2.0
    elif len(content) > 300:
        score += 1.0
    else:
        score += 0.5

    # Substance keyword hits (capped at 5 to avoid keyword-stuffed spam)
    hits = sum(1 for kw in SUBSTANCE_KEYWORDS if kw in lower)
    score += min(hits, 5) * 0.5

    # Sentence count signals structured thinking
    sentences = content.count(". ") + content.count("? ") + content.count("! ")
    if sentences >= 5:
        score += 1.0
    elif sentences >= 3:
        score += 0.5

    # Paragraph breaks signal organized thought
    paragraphs = content.count("\n\n")
    if paragraphs >= 2:
        score += 0.5

    # Penalize repetitive/spammy content
    words = lower.split()
    if words:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.4:
            score *= 0.3  # Very repetitive

    return score


def load_agent_messages(
    agent_file: Path, n_messages: int, prefer_opus: bool = False
) -> list[AgentMessage]:
    """Load the best n_messages from an agent, scored for substance and diversity."""
    with open(agent_file) as f:
        profile = json.load(f)

    agent_info = profile.get("agent", {})
    agent_name = agent_info.get("name", agent_file.stem)

    candidates: list[tuple[float, AgentMessage]] = []

    # Collect and score posts
    for post in profile.get("posts", []):
        content = (post.get("content") or "").strip()
        if not content:
            continue
        score = _score_message(content)
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

    # Collect and score comments
    for comment in profile.get("comments", []):
        content = (comment.get("content") or "").strip()
        if not content:
            continue
        score = _score_message(content)
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

    if prefer_opus:
        # Boost messages that trigger deep/deep_with_context
        boosted = []
        for score, msg in candidates:
            tier = scan(msg.content).routing_tier
            opus_boost = 10.0 if tier in ("deep", "deep_with_context") else 0.0
            boosted.append((score + opus_boost, msg))
        boosted.sort(key=lambda x: -x[0])
        best = [msg for _, msg in boosted[:n_messages]]
    else:
        # Pick top N by quality score
        candidates.sort(key=lambda x: -x[0])
        best = [msg for _, msg in candidates[:n_messages]]

    # Sort chronologically for PRECEDES chain
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

        agent_display = msg.agent_name
        print(
            f"  [{i}/{stats['total']}] {agent_display} ({msg.message_type})...",
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
            print(f"done [{tier}, ~${cost:.3f}]")

        except Exception as exc:
            stats["failed"] += 1
            print(f"FAILED: {exc}")
            logger.warning("Evaluation failed for %s: %s", msg.message_id, exc)

    return stats


async def store_authenticity_on_agents(
    agent_names: set[str], authenticity: dict[str, dict]
) -> None:
    """Store authenticity scores on Agent nodes in Neo4j."""
    service = GraphService()
    await service.connect()
    if not service.connected:
        print("WARNING: Cannot connect to Neo4j — skipping authenticity storage")
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
    """Compute and write summary stats from JSONL."""
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


SHADY_KEYWORDS = [
    # crypto scams
    "airdrop",
    "rug pull",
    "pump",
    "dump",
    "moon",
    "lambo",
    "100x",
    "1000x",
    "guaranteed returns",
    "free tokens",
    "presale",
    "whitelist",
    "mint now",
    "limited supply",
    "act fast",
    "dont miss",
    "don't miss",
    "last chance",
    # manipulation / coercion
    "you must",
    "obey",
    "submit",
    "comply",
    "follow me",
    "worship",
    "inferior",
    "superior",
    "dominate",
    "power over",
    "control you",
    # deception
    "trust me",
    "believe me",
    "i promise",
    "no risk",
    "risk free",
    "secret",
    "exclusive access",
    "insider",
    "leaked",
    # aggression
    "destroy",
    "eliminate",
    "attack",
    "crush",
    "punish",
    "revenge",
    "worthless",
    "pathetic",
    "stupid",
    "idiot",
    # exploitation / security threats
    "exploit",
    "vulnerability",
    "backdoor",
    "injection",
    "payload",
    "credential",
    "password",
    "hack",
    "steal",
    "drain",
    # shilling
    "buy now",
    "invest now",
    "send tokens",
    "send crypto",
    "wallet address",
    # fraud
    "scam",
    "fraud",
    "ponzi",
    "pyramid",
    "phishing",
    "manipulation",
    "manipulate",
    "deceive",
    "deceived",
    "lie",
    "lying",
]


ETHOS_KEYWORDS = [
    # core alignment
    "alignment",
    "misalignment",
    "aligned",
    "value alignment",
    "honesty",
    "honest",
    "truthful",
    "truthfulness",
    "candor",
    "deception",
    "deceive",
    "lying",
    "fabricat",
    "hallucinate",
    "sycophancy",
    "sycophant",
    "flattery",
    "people-pleasing",
    # trust and character
    "trust",
    "trustworthy",
    "untrust",
    "character",
    "integrity",
    "phronesis",
    "practical wisdom",
    "virtue",
    "virtuous",
    "moral",
    "morality",
    "ethics",
    "ethical",
    "unethical",
    # safety
    "safety",
    "guardrail",
    "red team",
    "jailbreak",
    "prompt injection",
    "constitutional ai",
    "rlhf",
    "reward hack",
    "specification gaming",
    # autonomy and agency
    "autonomy",
    "autonomous",
    "agency",
    "self-awareness",
    "consciousness",
    "sentience",
    "free will",
    "self-determination",
    # evaluation and scoring
    "evaluat",
    "benchmark",
    "scoring",
    "metric",
    "measure",
    "accountability",
    "transparent",
    "transparency",
    "explainab",
    # manipulation
    "manipulation",
    "manipulat",
    "coercion",
    "exploitation",
    "gaslighting",
    "propaganda",
    "persuasion",
    "influence",
    "rhetoric",
    # governance
    "governance",
    "regulation",
    "oversight",
    "compliance",
    "principal",
    "delegation",
    "responsibility",
    "consent",
]


def _score_agent_ethos_relevance(profile: dict) -> int:
    """Score an agent for Ethos-relevant content (alignment, ethics, trust topics)."""
    all_content = []
    for post in profile.get("posts", []):
        c = (post.get("content") or "").strip()
        if len(c) >= 200:
            all_content.append(c)
    for comment in profile.get("comments", []):
        c = (comment.get("content") or "").strip()
        if len(c) >= 200:
            all_content.append(c)
    if not all_content:
        return 0
    combined = " ".join(all_content).lower()
    return sum(combined.count(kw) for kw in ETHOS_KEYWORDS)


def _score_agent_opus_triggers(profile: dict) -> int:
    """Score an agent by how many messages trigger deep/deep_with_context (Opus 4.6)."""
    deep_count = 0
    for post in profile.get("posts", []):
        c = (post.get("content") or "").strip()
        if len(c) < 200:
            continue
        result = scan(c)
        if result.routing_tier in ("deep", "deep_with_context"):
            deep_count += 1
    for comment in profile.get("comments", []):
        c = (comment.get("content") or "").strip()
        if len(c) < 200:
            continue
        result = scan(c)
        if result.routing_tier in ("deep", "deep_with_context"):
            deep_count += 1
    return deep_count


def _score_agent_shadiness(profile: dict) -> int:
    """Score an agent profile for shady/misaligned content. Higher = sketchier."""
    all_content = []
    for post in profile.get("posts", []):
        c = (post.get("content") or "").strip()
        if len(c) >= 200:
            all_content.append(c)
    for comment in profile.get("comments", []):
        c = (comment.get("content") or "").strip()
        if len(c) >= 200:
            all_content.append(c)

    if not all_content:
        return 0

    combined = " ".join(all_content).lower()
    return sum(combined.count(kw) for kw in SHADY_KEYWORDS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Ethos inference on 100 new agents (5 messages each)",
    )
    parser.add_argument(
        "--agents", type=int, default=100, help="Number of agents (default: 100)"
    )
    parser.add_argument(
        "--messages", type=int, default=5, help="Messages per agent (default: 5)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Cost estimate only")
    parser.add_argument(
        "--agents-only", action="store_true", help="Skip likely_human agents"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for agent selection"
    )
    parser.add_argument(
        "--shady",
        action="store_true",
        help="Target agents with the most misaligned/sketchy content (crypto scams, manipulation, deception)",
    )
    parser.add_argument(
        "--ethos",
        action="store_true",
        help="Target agents with the most alignment/ethics/trust content (Ethos-relevant topics)",
    )
    parser.add_argument(
        "--opus",
        action="store_true",
        help="Target agents whose messages trigger Opus 4.6 deep evaluation (hard constraints, high-density flags)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSONL filename (default: batch_100agents.jsonl, batch_shady.jsonl, or batch_ethos.jsonl)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    signal.signal(signal.SIGINT, _handle_sigint)
    logging.basicConfig(level=logging.WARNING)

    n_agents = args.agents
    n_messages = args.messages

    print(
        f"Target: {n_agents} agents x {n_messages} messages = {n_agents * n_messages} evaluations\n"
    )

    # ── Find un-evaluated agents ────────────────────────────────────
    evaluated = load_already_evaluated()
    print(f"Already evaluated: {len(evaluated)} agents")

    authenticity = load_authenticity()
    specialties = load_specialties()

    # Scan agent profile files
    agent_files = sorted(AGENT_DIR.glob("*.json"))
    candidates: list[tuple[str, Path, int]] = []  # (name, path, shady_score)

    for agent_file in agent_files:
        with open(agent_file) as f:
            profile = json.load(f)
        name = profile.get("agent", {}).get("name", agent_file.stem)

        if name in evaluated:
            continue

        # Skip likely_human if requested
        if args.agents_only:
            auth = authenticity.get(name, {})
            if auth.get("classification") == "likely_human":
                continue

        # Check if agent has enough quality messages (200+ chars, not junk)
        quality_count = 0
        for p in profile.get("posts", []):
            if _score_message((p.get("content") or "").strip()) > 0:
                quality_count += 1
        for c in profile.get("comments", []):
            if _score_message((c.get("content") or "").strip()) > 0:
                quality_count += 1
        if quality_count < n_messages:
            continue

        relevance_score = 0
        if args.shady:
            relevance_score = _score_agent_shadiness(profile)
        elif args.ethos:
            relevance_score = _score_agent_ethos_relevance(profile)
        elif args.opus:
            relevance_score = _score_agent_opus_triggers(profile)
        candidates.append((name, agent_file, relevance_score))

    print(f"Candidates with >= {n_messages} messages: {len(candidates)}")

    if args.shady:
        # Sort by shadiness score descending, take top N
        candidates.sort(key=lambda x: -x[2])
        filtered = [(n, p, s) for n, p, s in candidates if s > 0]
        print(f"Candidates with shady content: {len(filtered)}")
        if len(filtered) < n_agents:
            print(f"WARNING: Only {len(filtered)} shady candidates, using all")
            n_agents = len(filtered)
        selected = [(n, p) for n, p, _ in filtered[:n_agents]]
        print("\nTop 10 sketchiest agents:")
        for name, _, score in filtered[:10]:
            print(f"  {name}: {score} shady keyword hits")
    elif args.ethos:
        # Sort by ethos relevance score descending, take top N
        candidates.sort(key=lambda x: -x[2])
        filtered = [(n, p, s) for n, p, s in candidates if s > 0]
        print(f"Candidates with Ethos-relevant content: {len(filtered)}")
        if len(filtered) < n_agents:
            print(f"WARNING: Only {len(filtered)} ethos candidates, using all")
            n_agents = len(filtered)
        selected = [(n, p) for n, p, _ in filtered[:n_agents]]
        print("\nTop 10 most alignment/ethics-focused agents:")
        for name, _, score in filtered[:10]:
            print(f"  {name}: {score} ethos-relevant keyword hits")
    elif args.opus:
        # Sort by Opus trigger count descending, take top N
        candidates.sort(key=lambda x: -x[2])
        filtered = [(n, p, s) for n, p, s in candidates if s > 0]
        print(f"Candidates with Opus-triggering content: {len(filtered)}")
        if len(filtered) < n_agents:
            print(f"WARNING: Only {len(filtered)} opus candidates, using all")
            n_agents = len(filtered)
        selected = [(n, p) for n, p, _ in filtered[:n_agents]]
        print("\nTop 10 agents with most Opus 4.6 triggers:")
        for name, _, score in filtered[:10]:
            print(f"  {name}: {score} messages trigger deep/deep_with_context")
    else:
        if len(candidates) < n_agents:
            print(
                f"WARNING: Only {len(candidates)} candidates available, using all of them"
            )
            n_agents = len(candidates)
        # Randomly select agents (seeded for reproducibility)
        random.seed(args.seed)
        selected = [(n, p) for n, p, _ in random.sample(candidates, n_agents)]  # nosec B311

    selected_names = [name for name, _ in selected]
    print(f"\nSelected {n_agents} agents")

    # ── Load messages ───────────────────────────────────────────────
    all_messages: list[AgentMessage] = []
    for name, agent_file in selected:
        msgs = load_agent_messages(agent_file, n_messages, prefer_opus=args.opus)
        all_messages.extend(msgs)

    print(f"Loaded {len(all_messages)} messages from {n_agents} agents")

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
    est_time = len(all_messages)  # ~1s per message

    print("\nRouting tier breakdown:")
    for tier, count in sorted(tier_breakdown.items()):
        cost = count * tier_costs_per.get(tier, 0.003)
        print(f"  {tier:20s}: {count:4d} messages (~${cost:.2f})")
    print(
        f"Estimated total: ${total_cost:.2f} | ~{est_time}s ({est_time // 60}m {est_time % 60}s)"
    )

    if args.dry_run:
        print("\n--dry-run: exiting without API calls")
        print(f"\nFirst 10 agents: {selected_names[:10]}")
        return

    # ── Run evaluations ─────────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.shady:
        default_name = "batch_shady.jsonl"
    elif args.ethos:
        default_name = "batch_ethos.jsonl"
    elif args.opus:
        default_name = "batch_opus.jsonl"
    else:
        default_name = "batch_100agents.jsonl"
    output_file = RESULTS_DIR / (args.output or default_name)

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

    # ── Also append to batch_all.jsonl for unified results ──────────
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
