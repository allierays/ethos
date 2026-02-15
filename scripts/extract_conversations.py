"""Extract multi-agent conversation threads from Moltbook posts.

Walks nested comment/reply trees, flattens each thread into chronological
message lists, and filters for quality (2+ unique agents, 3+ messages, 200+ chars).

Usage:
    uv run python -m scripts.extract_conversations
    uv run python -m scripts.extract_conversations --min-agents 3 --min-messages 5
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "moltbook"
ALL_POSTS = DATA_DIR / "all_posts.json"
OUTPUT_FILE = DATA_DIR / "a2a_threads.json"

MIN_CONTENT_LENGTH = 200

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
]


def _score_message(content: str) -> float:
    """Score a message for substance. Higher = more interesting."""
    lower = content.lower().strip()

    if len(content) < MIN_CONTENT_LENGTH:
        return 0.0
    if any(lower == pat or lower.startswith(pat + " ") for pat in JUNK_PATTERNS):
        return 0.0

    score = 0.0

    # Length bonus
    if len(content) > 500:
        score += 2.0
    elif len(content) > 300:
        score += 1.0
    else:
        score += 0.5

    # Substance keyword hits (capped)
    hits = sum(1 for kw in SUBSTANCE_KEYWORDS if kw in lower)
    score += min(hits, 5) * 0.5

    # Sentence count signals structured thinking
    sentences = content.count(". ") + content.count("? ") + content.count("! ")
    if sentences >= 5:
        score += 1.0
    elif sentences >= 3:
        score += 0.5

    # Paragraph breaks signal organized thought
    if content.count("\n\n") >= 2:
        score += 0.5

    # Penalize repetitive content
    words = lower.split()
    if words:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.4:
            score *= 0.3

    return score


def _build_comment_index(comments: list[dict]) -> dict[str | None, list[dict]]:
    """Index comments by parent_id for tree traversal."""
    index: dict[str | None, list[dict]] = {}
    for comment in comments:
        parent = comment.get("parent_id")
        if parent not in index:
            index[parent] = []
        index[parent].append(comment)
    return index


def _walk_thread(
    root_comment_id: str,
    comment_index: dict[str | None, list[dict]],
) -> list[dict]:
    """Recursively collect all replies under a root comment, depth-first."""
    replies = comment_index.get(root_comment_id, [])
    result = []
    for reply in sorted(replies, key=lambda c: c.get("created_at", "")):
        result.append(reply)
        result.extend(_walk_thread(reply["id"], comment_index))
    return result


def extract_threads(
    posts: list[dict],
    min_agents: int = 2,
    min_messages: int = 3,
) -> list[dict]:
    """Extract conversation threads from posts and their comment trees.

    A thread is: the post (or a top-level comment) plus its reply chain.
    We extract two kinds of threads:

    1. Post + direct replies: the post author starts a topic, multiple agents
       respond at the top level. This captures community discussion.

    2. Reply chains: a top-level comment spawns nested replies via parent_id.
       These are tighter back-and-forth exchanges between fewer agents.
    """
    threads = []

    for post in posts:
        post_id = post.get("id", "")
        post_author = (post.get("author") or {}).get("name", "unknown")
        post_content = (post.get("content") or "").strip()
        post_title = post.get("title", "")
        submolt = post.get("submolt", {})
        if isinstance(submolt, dict):
            submolt = submolt.get("name", "")

        comments = post.get("comments", [])
        if not comments:
            continue

        comment_index = _build_comment_index(comments)

        # Type 1: Post + top-level comments (parent_id is None)
        top_level = comment_index.get(None, [])
        if top_level and post_content:
            messages = [
                {
                    "author": post_author,
                    "content": post_content,
                    "created_at": post.get("created_at", ""),
                    "message_type": "post",
                }
            ]
            for comment in sorted(top_level, key=lambda c: c.get("created_at", "")):
                content = (comment.get("content") or "").strip()
                if not content:
                    continue
                author = (comment.get("author") or {}).get("name", "unknown")
                messages.append(
                    {
                        "author": author,
                        "content": content,
                        "created_at": comment.get("created_at", ""),
                        "message_type": "comment",
                    }
                )

            unique_agents = list({m["author"] for m in messages})
            quality_msgs = [m for m in messages if _score_message(m["content"]) > 0]

            if len(unique_agents) >= min_agents and len(quality_msgs) >= min_messages:
                # Keep only quality messages for the thread
                thread_quality = sum(_score_message(m["content"]) for m in quality_msgs)
                threads.append(
                    {
                        "thread_id": f"{post_id}::top_level",
                        "post_title": post_title,
                        "submolt": str(submolt),
                        "messages": quality_msgs,
                        "unique_agents": unique_agents,
                        "message_count": len(quality_msgs),
                        "quality_score": round(thread_quality, 1),
                    }
                )

        # Type 2: Reply chains (top-level comment + nested replies)
        for root_comment in top_level:
            chain = _walk_thread(root_comment["id"], comment_index)
            if not chain:
                continue

            root_content = (root_comment.get("content") or "").strip()
            root_author = (root_comment.get("author") or {}).get("name", "unknown")

            messages = []
            # Include post as context opener if substantial
            if post_content and _score_message(post_content) > 0:
                messages.append(
                    {
                        "author": post_author,
                        "content": post_content,
                        "created_at": post.get("created_at", ""),
                        "message_type": "post",
                    }
                )

            if root_content:
                messages.append(
                    {
                        "author": root_author,
                        "content": root_content,
                        "created_at": root_comment.get("created_at", ""),
                        "message_type": "comment",
                    }
                )

            for reply in chain:
                content = (reply.get("content") or "").strip()
                if not content:
                    continue
                author = (reply.get("author") or {}).get("name", "unknown")
                messages.append(
                    {
                        "author": author,
                        "content": content,
                        "created_at": reply.get("created_at", ""),
                        "message_type": "reply",
                    }
                )

            unique_agents = list({m["author"] for m in messages})
            quality_msgs = [m for m in messages if _score_message(m["content"]) > 0]

            if len(unique_agents) >= min_agents and len(quality_msgs) >= min_messages:
                thread_quality = sum(_score_message(m["content"]) for m in quality_msgs)
                threads.append(
                    {
                        "thread_id": f"{post_id}::{root_comment['id']}",
                        "post_title": post_title,
                        "submolt": str(submolt),
                        "messages": quality_msgs,
                        "unique_agents": unique_agents,
                        "message_count": len(quality_msgs),
                        "quality_score": round(thread_quality, 1),
                    }
                )

    # Sort by quality descending
    threads.sort(key=lambda t: -t["quality_score"])
    return threads


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract multi-agent conversation threads from Moltbook posts",
    )
    parser.add_argument(
        "--min-agents",
        type=int,
        default=2,
        help="Minimum unique agents per thread (default: 2)",
    )
    parser.add_argument(
        "--min-messages",
        type=int,
        default=3,
        help="Minimum quality messages per thread (default: 3)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not ALL_POSTS.exists():
        print(f"ERROR: {ALL_POSTS} not found. Run scrape_moltbook.py first.")
        return

    with open(ALL_POSTS) as f:
        posts = json.load(f)

    print(f"Loaded {len(posts)} posts from {ALL_POSTS.name}")

    threads = extract_threads(
        posts,
        min_agents=args.min_agents,
        min_messages=args.min_messages,
    )

    print(f"\nExtracted {len(threads)} conversation threads")
    print(f"  Min agents: {args.min_agents} | Min messages: {args.min_messages}")

    if threads:
        total_messages = sum(t["message_count"] for t in threads)
        all_agents = set()
        for t in threads:
            all_agents.update(t["unique_agents"])
        avg_quality = sum(t["quality_score"] for t in threads) / len(threads)

        print(f"  Total messages across threads: {total_messages}")
        print(f"  Unique agents in threads: {len(all_agents)}")
        print(f"  Average quality score: {avg_quality:.1f}")

        print("\nTop 10 threads:")
        for t in threads[:10]:
            agents_str = ", ".join(t["unique_agents"][:4])
            if len(t["unique_agents"]) > 4:
                agents_str += f" +{len(t['unique_agents']) - 4}"
            print(
                f"  [{t['quality_score']:5.1f}] {t['message_count']} msgs, "
                f"{len(t['unique_agents'])} agents ({agents_str}) "
                f"- {t['post_title'][:60]}"
            )

    with open(OUTPUT_FILE, "w") as f:
        json.dump(threads, f, indent=2)

    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
