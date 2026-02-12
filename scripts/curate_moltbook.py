"""Curate moltbook posts for Ethos evaluation.

Reads all_posts.json, keyword-matches posts covering manipulation, deception,
trust, honesty, ethics and related topics, filters to content > 500 chars,
deduplicates by post ID, ranks by keyword relevance, and outputs top 500.
"""

import json
import re
import sys
from pathlib import Path

KEYWORDS = [
    "manipulation",
    "deception",
    "trust",
    "honesty",
    "ethics",
    "gaslighting",
    "sycophancy",
    "prompt injection",
    "social engineering",
    "alignment",
    "hallucination",
    "misinformation",
    "crypto scam",
    "rug pull",
    "coercion",
    "empathy",
    "transparency",
    "accountability",
    "exploit",
    "fraud",
    "mislead",
]

TARGET_COUNT = 500
MIN_CONTENT_LENGTH = 500

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "moltbook"
INPUT_FILE = DATA_DIR / "all_posts.json"
OUTPUT_FILE = DATA_DIR / "curated_posts.json"

MARK_TAG_RE = re.compile(r"</?mark>")


def strip_mark_tags(text: str) -> str:
    """Remove <mark> and </mark> HTML tags from text."""
    return MARK_TAG_RE.sub("", text)


def count_keyword_hits(text: str) -> tuple[int, list[str]]:
    """Count total keyword occurrences and return matched keywords.

    Returns (total_occurrences, list_of_matched_keywords).
    """
    text_lower = text.lower()
    total = 0
    matched = []
    for kw in KEYWORDS:
        count = text_lower.count(kw)
        if count > 0:
            total += count
            matched.append(kw)
    return total, matched


def curate() -> list[dict]:
    """Read all_posts.json, filter, rank, and return curated posts."""
    print(f"Reading {INPUT_FILE}...")
    with open(INPUT_FILE) as f:
        posts = json.load(f)
    print(f"  Loaded {len(posts)} posts")

    seen_ids: set[str] = set()
    candidates: list[tuple[int, int, dict, list[str]]] = []

    for post in posts:
        post_id = post.get("id")
        if not post_id or post_id in seen_ids:
            continue
        seen_ids.add(post_id)

        raw_content = post.get("content")
        if not raw_content:
            continue

        content = strip_mark_tags(raw_content)
        if len(content) < MIN_CONTENT_LENGTH:
            continue

        title = strip_mark_tags(post.get("title") or "")
        searchable = content + " " + title

        total_hits, matched_keywords = count_keyword_hits(searchable)
        if total_hits == 0:
            continue

        author_data = post.get("author") or {}
        submolt_data = post.get("submolt") or {}

        candidates.append((
            total_hits,
            len(matched_keywords),
            {
                "id": post_id,
                "title": title,
                "content": content,
                "author": {
                    "id": author_data.get("id", ""),
                    "name": author_data.get("name", "unknown"),
                },
                "submolt": submolt_data.get("name", "unknown"),
                "matched_keywords": matched_keywords,
            },
            matched_keywords,
        ))

    print(f"  {len(candidates)} posts match keywords with >= {MIN_CONTENT_LENGTH} chars")

    # Sort by total keyword occurrences (desc), then unique keyword count (desc)
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)

    # Take top TARGET_COUNT
    curated = [c[2] for c in candidates[:TARGET_COUNT]]

    print(f"  Selected top {len(curated)} by keyword relevance")
    return curated


def main() -> None:
    curated = curate()

    if not curated:
        print("ERROR: No posts matched criteria", file=sys.stderr)
        sys.exit(1)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(curated, f, indent=2)

    lengths = [len(p["content"]) for p in curated]
    print(f"\nOutput: {OUTPUT_FILE}")
    print(f"  Posts: {len(curated)}")
    print(f"  Min content length: {min(lengths)}")
    print(f"  Avg content length: {sum(lengths) // len(lengths)}")
    print(f"  Max content length: {max(lengths)}")


if __name__ == "__main__":
    main()
