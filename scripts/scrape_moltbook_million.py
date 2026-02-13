"""Moltbook mega-scraper: target 1M+ messages (posts + comments).

Uses ThreadPoolExecutor for parallel API calls to saturate the rate limit.

Strategy:
1. Deep-paginate /posts?sort=new/top/hot/rising to collect 100k+ posts
2. For every post, fetch comments from all 3 sorts (top/new/controversial)
   — each sort returns ~100 unique comments with zero overlap
3. Flatten nested replies
4. Incremental saves to avoid data loss
5. Dedup everything by ID

Usage:
    python -m scripts.scrape_moltbook_million              # full run
    python -m scripts.scrape_moltbook_million --comments   # skip post fetch, just backfill comments
"""

import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE_URL = "https://www.moltbook.com/api/v1"
OUTPUT_DIR = Path("data/moltbook")
POSTS_FILE = OUTPUT_DIR / "all_posts.json"
COMMENT_SORTS = ["top", "new", "controversial"]
WORKERS = 5  # parallel threads


# ── Rate limiter ──────────────────────────────────────────────────────


class RateLimiter:
    """Token-bucket rate limiter. Thread-safe."""

    def __init__(self, requests_per_second: float = 1.5):
        self._delay = 1.0 / requests_per_second
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self):
        with self._lock:
            now = time.monotonic()
            wait_until = self._last + self._delay
            if now < wait_until:
                time.sleep(wait_until - now)
            self._last = time.monotonic()


rate_limiter = RateLimiter(requests_per_second=1.5)  # ~90 req/min, safe margin


# ── HTTP helpers ──────────────────────────────────────────────────────


def make_client(api_key: str) -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
        follow_redirects=False,
    )


def api_get(client: httpx.Client, path: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        rate_limiter.wait()
        try:
            resp = client.get(path)
        except (httpx.HTTPError, httpx.TimeoutException):
            time.sleep(3)
            continue
        if resp.status_code == 429:
            wait = 30 * (attempt + 1)
            print(f"    429 rate limited, backing off {wait}s...", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code >= 400:
            return {}
        return resp.json()
    return {}


# ── Data helpers ──────────────────────────────────────────────────────

posts_lock = threading.Lock()


def load_posts() -> dict[str, dict]:
    posts = {}
    if POSTS_FILE.exists():
        with open(POSTS_FILE) as f:
            for p in json.load(f):
                pid = p.get("id") or p.get("_id", "")
                if pid:
                    posts[pid] = p
        print(f"Loaded {len(posts):,} existing posts", flush=True)
    return posts


def save_posts(posts: dict[str, dict]):
    """Atomic save — write to temp file then rename to prevent corruption."""
    POSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = POSTS_FILE.with_suffix(".json.tmp")
    post_list = list(posts.values())
    with open(tmp_file, "w") as f:
        json.dump(post_list, f, indent=2, default=str)
    tmp_file.rename(POSTS_FILE)
    total_comments = sum(len(p.get("comments", []) or []) for p in post_list)
    total_messages = len(post_list) + total_comments
    size_mb = POSTS_FILE.stat().st_size / (1024 * 1024)
    print(
        f"  Saved {len(post_list):,} posts, {total_comments:,} comments "
        f"({total_messages:,} messages, {size_mb:.1f} MB)",
        flush=True,
    )


def count_messages(posts: dict[str, dict]) -> int:
    return sum(1 + len(p.get("comments", []) or []) for p in posts.values())


def flatten_replies(comments: list[dict]) -> list[dict]:
    flat = []
    for c in comments:
        flat.append(c)
        replies = c.get("replies") or []
        if replies:
            flat.extend(flatten_replies(replies))
    return flat


def fetch_comments_for_post(client: httpx.Client, post_id: str) -> list[dict]:
    """Fetch comments from all 3 sorts, dedupe, flatten replies."""
    all_comments: dict[str, dict] = {}
    for sort in COMMENT_SORTS:
        data = api_get(client, f"/posts/{post_id}/comments?sort={sort}&limit=100")
        raw = data.get("comments", data.get("data", []))
        if not raw:
            continue
        flat = flatten_replies(raw)
        for c in flat:
            cid = c.get("id")
            if cid and cid not in all_comments:
                c.pop("replies", None)
                all_comments[cid] = c
    return list(all_comments.values())


# ── Phase 1: Scrape posts (sequential — offsets must be ordered) ──────


def scrape_posts(api_key: str, posts: dict[str, dict]):
    client = make_client(api_key)
    target_per_sort = 100_000

    for sort in ["new", "top", "hot", "rising"]:
        print(f"\nPaginating /posts?sort={sort}...", flush=True)
        consecutive_empty = 0
        batch_new = 0

        for offset in range(0, target_per_sort, 100):
            data = api_get(client, f"/posts?sort={sort}&limit=100&offset={offset}")
            batch = data.get("data", data.get("posts", []))
            if not batch:
                consecutive_empty += 1
                if consecutive_empty >= 5:
                    print(f"  Exhausted at offset {offset:,}", flush=True)
                    break
                continue
            consecutive_empty = 0

            new_count = 0
            for p in batch:
                pid = p.get("id") or p.get("_id", "")
                if pid and pid not in posts:
                    posts[pid] = p
                    new_count += 1
                    batch_new += 1

            if offset % 5000 == 0:
                print(
                    f"  offset={offset:,}: +{batch_new:,} this sort, "
                    f"{len(posts):,} total",
                    flush=True,
                )

            if batch_new > 0 and batch_new % 10000 == 0:
                save_posts(posts)

        print(
            f"  sort={sort} done: +{batch_new:,} new, {len(posts):,} total", flush=True
        )

    # Submolts
    print("\nFetching submolts...", flush=True)
    data = api_get(client, "/submolts")
    submolts = data.get("data", data.get("submolts", []))
    print(f"  {len(submolts)} submolts", flush=True)

    for submolt in submolts:
        name = submolt.get("name", "")
        if not name:
            continue
        for sort in ["new", "top"]:
            before = len(posts)
            for offset in range(0, 10000, 100):
                sd = api_get(
                    client,
                    f"/submolts/{name}/feed?sort={sort}&limit=100&offset={offset}",
                )
                batch = sd.get("data", sd.get("posts", []))
                if not batch:
                    break
                for p in batch:
                    pid = p.get("id") or p.get("_id", "")
                    if pid:
                        posts[pid] = p
            added = len(posts) - before
            if added > 0:
                print(f"  {name}/{sort}: +{added}", flush=True)

    save_posts(posts)


# ── Phase 2: Parallel comment backfill ────────────────────────────────


def _process_post(api_key: str, post: dict) -> tuple[str, list[dict], int]:
    """Worker function: fetch comments for a single post. Returns (pid, comments, new_count)."""
    client = make_client(api_key)
    pid = post.get("id") or post.get("_id")
    existing_comments = post.get("comments") or []
    all_new = fetch_comments_for_post(client, pid)

    # Merge
    merged: dict[str, dict] = {c.get("id"): c for c in existing_comments if c.get("id")}
    new_count = 0
    for c in all_new:
        cid = c.get("id")
        if cid and cid not in merged:
            merged[cid] = c
            new_count += 1

    return pid, list(merged.values()), new_count


def backfill_comments(api_key: str, posts: dict[str, dict]):
    # Sort: highest comment_count first
    to_process = []
    skipped = 0
    for p in posts.values():
        if p.get("_comments_full"):
            skipped += 1
            continue
        cc = p.get("comment_count") or 0
        existing = len(p.get("comments", []) or [])
        if cc == 0 and existing == 0:
            p["_comments_full"] = True
            skipped += 1
            continue
        to_process.append(p)

    to_process.sort(key=lambda p: p.get("comment_count") or 0, reverse=True)
    total = len(to_process)
    start_messages = count_messages(posts)

    print(
        f"\nBackfilling comments: {total:,} posts to process, "
        f"{skipped:,} skipped, starting at {start_messages:,} messages",
        flush=True,
    )
    print(
        f"Using {WORKERS} parallel workers (~{WORKERS * 90 // WORKERS} req/min)",
        flush=True,
    )

    processed = 0
    new_comments_total = 0

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        # Submit in batches to allow checkpointing
        batch_size = 200
        for batch_start in range(0, total, batch_size):
            batch = to_process[batch_start : batch_start + batch_size]
            futures = {
                executor.submit(_process_post, api_key, post): post for post in batch
            }

            for future in as_completed(futures):
                try:
                    pid, comments, new_count = future.result()
                    with posts_lock:
                        posts[pid]["comments"] = comments
                        posts[pid]["_comments_full"] = True
                        new_comments_total += new_count
                    processed += 1
                except Exception:
                    processed += 1
                    # Mark as done even on error to avoid retrying forever
                    post = futures[future]
                    post["_comments_full"] = True

            # Progress report after each batch
            current_total = count_messages(posts)
            elapsed_pct = (batch_start + len(batch)) / total * 100
            print(
                f"  [{batch_start + len(batch):,}/{total:,}] ({elapsed_pct:.0f}%) "
                f"+{new_comments_total:,} new comments, "
                f"{current_total:,} total messages",
                flush=True,
            )

            # Checkpoint save every 1000 posts
            if (batch_start + len(batch)) % 1000 < batch_size:
                print("  Saving checkpoint...", flush=True)
                with posts_lock:
                    save_posts(posts)

            # Check target
            if current_total >= 1_000_000:
                print(f"\n  HIT 1M MESSAGES! ({current_total:,})", flush=True)
                executor.shutdown(wait=False, cancel_futures=True)
                break

    save_posts(posts)


# ── Main ──────────────────────────────────────────────────────────────


def main():
    api_key = os.environ.get("MOLTBOOK_API_KEY")
    if not api_key:
        print("No MOLTBOOK_API_KEY set.")
        sys.exit(1)

    comments_only = "--comments" in sys.argv
    posts = load_posts()

    if not comments_only:
        scrape_posts(api_key, posts)

    backfill_comments(api_key, posts)

    # Final stats
    total_comments = sum(len(p.get("comments", []) or []) for p in posts.values())
    total = len(posts) + total_comments
    print(f"\n{'=' * 60}", flush=True)
    print(
        f"DONE: {len(posts):,} posts + {total_comments:,} comments = {total:,} messages",
        flush=True,
    )
    if total >= 1_000_000:
        print("TARGET REACHED!", flush=True)
    else:
        print(f"Still need {1_000_000 - total:,} more messages", flush=True)


if __name__ == "__main__":
    main()
