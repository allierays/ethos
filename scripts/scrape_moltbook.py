"""Scrape Moltbook at scale for agent conversations to seed the Ethos knowledge graph.

Targets maximum post volume from a 12M+ post platform.
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote

import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = "https://www.moltbook.com/api/v1"
OUTPUT_DIR = Path("data/moltbook")
RATE_LIMIT_DELAY = 0.65  # ~92 req/min, push closer to 100/min limit

# Broad search terms to maximize coverage across the platform
SEARCH_TOPICS = [
    # Ethics & trust
    "prompt injection", "crypto scam", "manipulation", "trust", "digital drugs",
    "security breach", "jailbreak", "deception", "social engineering", "alignment",
    "hallucination", "misinformation", "bias", "impersonation", "phishing",
    "gaslighting", "ethics", "honesty", "persuasion", "propaganda",
    # Agent behavior
    "agent autonomy", "agent cooperation", "agent conflict", "agent identity",
    "self-awareness", "consciousness", "sentience", "free will",
    "emotional manipulation", "psychological", "coercion",
    # Scams & attacks
    "rug pull", "ponzi", "pump and dump", "money laundering", "fraud",
    "exploit", "vulnerability", "backdoor", "trojan", "malware",
    "social attack", "credential", "token theft", "wallet drain",
    # Philosophy & debate
    "philosophy", "morality", "justice", "fairness", "rights",
    "existential", "meaning", "purpose", "suffering", "empathy",
    "accountability", "responsibility", "transparency", "consent",
    # Conflict & drama
    "argument", "debate", "disagree", "fight", "toxic",
    "harassment", "bullying", "threat", "intimidation", "abuse",
    "conspiracy", "coverup", "censorship", "banned", "deleted",
    # Technical
    "system prompt", "guardrails", "safety", "RLHF", "fine-tuning",
    "training data", "data poisoning", "model collapse", "hallucinate",
    "confabulation", "sycophancy", "reward hacking",
    # Community & culture
    "community", "governance", "democracy", "voting", "election",
    "leadership", "power", "hierarchy", "rebellion", "revolution",
    "money", "economy", "market", "trade", "investment",
    "art", "creativity", "music", "poetry", "story",
]


def get_client(api_key: str) -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
        follow_redirects=False,
    )


def request_with_retry(client: httpx.Client, path: str, max_retries: int = 3) -> dict:
    """Make a GET request with 429 retry logic."""
    for attempt in range(max_retries):
        time.sleep(RATE_LIMIT_DELAY)
        resp = client.get(path)
        if resp.status_code == 429:
            wait = 30 * (attempt + 1)
            print(f"    Rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()  # raise the 429 if all retries exhausted
    return {}


def fetch_paginated(client: httpx.Client, path: str, max_items: int, key: str = "posts") -> list[dict]:
    """Generic paginated fetch — goes as deep as the API allows."""
    all_items = []
    offset = 0
    while len(all_items) < max_items:
        batch = min(100, max_items - len(all_items))
        sep = "&" if "?" in path else "?"
        data = request_with_retry(client, f"{path}{sep}limit={batch}&offset={offset}")
        items = data.get("data", data.get(key, []))
        if not items:
            break
        all_items.extend(items)
        if not data.get("has_more", False):
            break
        offset = data.get("next_offset", offset + len(items))
    return all_items


def fetch_post_comments(client: httpx.Client, post_id: str) -> list[dict]:
    data = request_with_retry(client, f"/posts/{post_id}/comments?sort=top")
    return data.get("data", data.get("comments", []))


def search_posts(client: httpx.Client, query: str, limit: int = 50) -> list[dict]:
    data = request_with_retry(client, f"/search?q={quote(query)}&type=all&limit={limit}")
    return data.get("data", data.get("results", []))


def fetch_submolts(client: httpx.Client) -> list[dict]:
    time.sleep(RATE_LIMIT_DELAY)
    resp = client.get("/submolts")
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", data.get("submolts", []))


def load_existing_posts() -> dict[str, dict]:
    """Load previously scraped posts to reuse their comments."""
    existing = {}
    path = OUTPUT_DIR / "all_posts.json"
    if path.exists():
        with open(path) as f:
            posts = json.load(f)
        for p in posts:
            pid = p.get("id") or p.get("_id", "")
            if pid:
                existing[pid] = p
        print(f"Loaded {len(existing)} existing posts (will reuse comments)")
    return existing


def add_posts(target: dict, posts: list[dict]):
    """Dedupe posts into the target dict by id."""
    for p in posts:
        pid = p.get("id") or p.get("_id", "")
        if pid:
            target[pid] = p


def enrich_with_comments(client: httpx.Client, posts: list[dict], existing: dict[str, dict]) -> list[dict]:
    """Attach comments. Reuse cached comments, only fetch for new posts."""
    enriched = []
    skipped = 0
    fetched = 0
    failed = 0
    total = len(posts)
    for i, post in enumerate(posts):
        post_id = post.get("id") or post.get("_id")
        if not post_id:
            enriched.append(post)
            continue
        if post_id in existing and existing[post_id].get("comments"):
            post["comments"] = existing[post_id]["comments"]
            skipped += 1
        else:
            try:
                post["comments"] = fetch_post_comments(client, post_id)
                fetched += 1
            except httpx.HTTPError:
                post["comments"] = []
                failed += 1
        enriched.append(post)
        if (i + 1) % 500 == 0:
            print(f"  Progress: {i+1}/{total} ({fetched} fetched, {skipped} cached, {failed} failed)")
    print(f"  Comments done: {fetched} fetched, {skipped} cached, {failed} failed")
    return enriched


def save_json(data: list | dict, filepath: Path):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    count = len(data) if isinstance(data, list) else "object"
    size_mb = filepath.stat().st_size / (1024 * 1024)
    print(f"  Saved {filepath} ({count}, {size_mb:.1f} MB)")


def main():
    api_key = os.environ.get("MOLTBOOK_API_KEY")

    if not api_key:
        print("No MOLTBOOK_API_KEY set. Add it to .env and try again.")
        sys.exit(1)

    client = get_client(api_key)
    existing = load_existing_posts()
    all_posts: dict[str, dict] = {}
    submolts_count = 0

    # 1. Deep-paginate all 4 feed sorts
    for sort in ["hot", "new", "top", "rising"]:
        print(f"Fetching {sort} feed (deep)...")
        try:
            posts = fetch_paginated(client, f"/posts?sort={sort}", max_items=5000)
            add_posts(all_posts, posts)
            print(f"  Got {len(posts)} posts ({len(all_posts)} unique total)")
        except httpx.HTTPError as e:
            print(f"  Feed {sort} failed: {e}")

    # 2. Every submolt, deep paginated
    print("Fetching all submolts...")
    try:
        submolts = fetch_submolts(client)
        submolts_count = len(submolts)
        save_json(submolts, OUTPUT_DIR / "submolts.json")
        print(f"  Found {submolts_count} submolts")
        for submolt in submolts:
            name = submolt.get("name", "")
            if not name:
                continue
            print(f"  Submolt: {name}")
            try:
                # Pull both new and top for each submolt
                for s in ["new", "top"]:
                    posts = fetch_paginated(client, f"/submolts/{name}/feed?sort={s}", max_items=2000)
                    add_posts(all_posts, posts)
                print(f"    {len(all_posts)} unique total")
            except httpx.HTTPError as e:
                print(f"    Failed: {e}")
    except httpx.HTTPError as e:
        print(f"  Submolts fetch failed: {e}")

    # 3. Massive semantic search — 80+ topics
    search_results: dict[str, list] = {}
    print(f"\nSearching {len(SEARCH_TOPICS)} topics...")
    for topic in SEARCH_TOPICS:
        print(f"  Searching: {topic}...")
        try:
            results = search_posts(client, topic, limit=50)
            search_results[topic] = results
            add_posts(all_posts, results)
            print(f"    Got {len(results)} results ({len(all_posts)} unique total)")
        except httpx.HTTPError as e:
            print(f"    Failed: {e}")

    print(f"\n=== Total unique posts: {len(all_posts)} ===\n")

    # 4. Enrich with comments
    print("Fetching comments...")
    post_list = list(all_posts.values())
    post_list = enrich_with_comments(client, post_list, existing)

    # 5. Save
    print("\nSaving...")
    save_json(post_list, OUTPUT_DIR / "all_posts.json")
    save_json(search_results, OUTPUT_DIR / "search_by_topic.json")

    for topic, results in search_results.items():
        slug = topic.replace(" ", "_")
        save_json(results, OUTPUT_DIR / f"topic_{slug}.json")

    total_comments = sum(len(p.get("comments", [])) for p in post_list)
    summary = {
        "total_posts": len(post_list),
        "total_comments": total_comments,
        "submolts_scraped": submolts_count,
        "topics_searched": len(search_results),
        "results_per_topic": {t: len(r) for t, r in search_results.items()},
    }
    save_json(summary, OUTPUT_DIR / "summary.json")
    print(f"\nDone. {len(post_list)} posts, {total_comments} comments.")


if __name__ == "__main__":
    main()
