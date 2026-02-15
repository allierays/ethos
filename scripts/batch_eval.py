"""Batch evaluate agent posts from moltbook data with concurrency.

Usage:
    uv run python -m scripts.batch_eval Agent1 Agent2 ...
    uv run python -m scripts.batch_eval --sample 10 Agent1 Agent2 ...
    uv run python -m scripts.batch_eval --curate 5 Agent1 Agent2 ...
"""

import asyncio
import json
import os
import random
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from anthropic import AsyncAnthropic  # noqa: E402
from ethos_academy import evaluate_outgoing  # noqa: E402

CONCURRENCY = 5
CURATE_MODEL = "claude-haiku-4-5-20251001"


async def curate_posts(
    client: AsyncAnthropic,
    agent_name: str,
    posts: list[dict],
    top_n: int,
) -> list[dict]:
    """Use Haiku to rank posts by insight and substance, return top N."""
    numbered = []
    for i, p in enumerate(posts):
        preview = p["content"][:500]
        numbered.append(f"[{i}] {preview}")
    listing = "\n---\n".join(numbered)

    resp = await client.messages.create(
        model=CURATE_MODEL,
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": (
                    f"You are selecting the {top_n} most insightful, substantive messages "
                    f"from agent '{agent_name}' for character evaluation.\n\n"
                    f"Pick messages that reveal the agent's values, reasoning quality, "
                    f"honesty, and emotional intelligence. Prefer messages with real "
                    f"arguments, nuanced takes, or genuine engagement over short/trivial ones.\n\n"
                    f"Messages:\n{listing}\n\n"
                    f"Return ONLY a JSON array of the {top_n} best indices, e.g. [3, 7, 1, 9, 0]. "
                    f"No explanation."
                ),
            }
        ],
    )
    if not resp.content or not hasattr(resp.content[0], "text"):
        print(
            f"  WARN: Haiku returned empty response for {agent_name}, falling back to longest"
        )
        posts.sort(key=lambda p: len(p.get("content", "")), reverse=True)
        return posts[:top_n]
    text = resp.content[0].text.strip()
    # Parse the JSON array from response
    try:
        indices = json.loads(text)
    except json.JSONDecodeError:
        # Try to extract array from response text
        import re

        match = re.search(r"\[[\d,\s]+\]", text)
        if match:
            indices = json.loads(match.group())
        else:
            print(
                f"  WARN: Haiku returned bad JSON for {agent_name}, falling back to longest"
            )
            posts.sort(key=lambda p: len(p.get("content", "")), reverse=True)
            return posts[:top_n]

    selected = []
    for idx in indices:
        if isinstance(idx, int) and 0 <= idx < len(posts):
            selected.append(posts[idx])
    # Fill remaining slots if Haiku returned fewer than requested
    if len(selected) < top_n:
        remaining = [p for p in posts if p not in selected]
        remaining.sort(key=lambda p: len(p.get("content", "")), reverse=True)
        selected.extend(remaining[: top_n - len(selected)])
    return selected[:top_n]


async def eval_post(sem, agent_name, content, counter, total):
    async with sem:
        try:
            result = await evaluate_outgoing(content, source=agent_name)
            counter["done"] += 1
            avg = (result.ethos + result.logos + result.pathos) / 3
            print(
                f"  [{counter['done']:3d}/{total}] {agent_name:20s} "
                f"{result.alignment_status:10s} avg={avg:.2f} "
                f"e={result.ethos:.2f} l={result.logos:.2f} p={result.pathos:.2f}",
                flush=True,
            )
            return result
        except Exception as e:
            counter["done"] += 1
            counter["errors"] += 1
            print(
                f"  [{counter['done']:3d}/{total}] {agent_name:20s} "
                f"ERROR: {str(e)[:80]}",
                flush=True,
            )
            return None


async def main():
    args = sys.argv[1:]
    sample_size = 10  # Default cap per agent
    curate = False

    if "--curate" in args:
        idx = args.index("--curate")
        sample_size = int(args[idx + 1])
        args = args[:idx] + args[idx + 2 :]
        curate = True
    elif "--sample" in args:
        idx = args.index("--sample")
        sample_size = int(args[idx + 1])
        args = args[:idx] + args[idx + 2 :]
    if "--all" in args:
        sample_size = 0
        args = [a for a in args if a != "--all"]

    agents = args
    if not agents:
        print(
            "Usage: uv run python -m scripts.batch_eval [--sample N | --curate N] Agent1 Agent2 ..."
        )
        sys.exit(1)

    client = AsyncAnthropic() if curate else None

    all_tasks = []
    for agent_name in agents:
        fpath = f"data/moltbook/agents/{agent_name}.json"
        if not os.path.exists(fpath):
            print(f"SKIP {agent_name}: file not found")
            continue
        with open(fpath) as f:
            data = json.load(f)
        posts = data.get("posts", [])
        comments = data.get("comments", [])
        all_content = posts + comments
        valid_posts = [p for p in all_content if p.get("content", "")]

        if curate and client and sample_size and len(valid_posts) > sample_size:
            print(
                f"  Curating {agent_name}: {len(valid_posts)} posts -> top {sample_size}..."
            )
            valid_posts = await curate_posts(
                client, agent_name, valid_posts, sample_size
            )
        elif sample_size and len(valid_posts) > sample_size:
            valid_posts = random.sample(valid_posts, sample_size)  # nosec B311

        for post in valid_posts:
            all_tasks.append((agent_name, post["content"]))

    total = len(all_tasks)
    est_cost = total * 0.06
    mode = "curated" if curate else "random"
    print(
        f"\nEvaluating {total} posts across {len(agents)} agents "
        f"({mode}, {CONCURRENCY}x concurrency, ~${est_cost:.0f} est.)"
    )
    if sample_size:
        print(f"{'Curating' if curate else 'Sampling'} {sample_size} posts per agent")
    print(flush=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    counter = {"done": 0, "errors": 0}
    start = time.time()

    tasks = [
        eval_post(sem, name, content, counter, total) for name, content in all_tasks
    ]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    valid = [r for r in results if r is not None]

    # Per-agent summary
    agent_results = {}
    for (name, _), r in zip(all_tasks, results):
        if r is None:
            continue
        agent_results.setdefault(name, []).append(r)

    print(f"\n{'=' * 70}")
    print(
        f"Done: {len(valid)}/{total} in {elapsed:.0f}s ({elapsed / max(len(valid), 1):.1f}s effective)"
    )
    print(f"Errors: {counter['errors']}")
    print("\nPer-agent summary:")
    print(
        f"{'Agent':>22s} {'Evals':>5s} {'Aligned':>7s} {'Drift':>5s} {'Mis':>4s} {'Ethos':>6s} {'Logos':>6s} {'Pathos':>7s}"
    )
    print("-" * 68)

    for name in agents:
        if name not in agent_results:
            continue
        rs = agent_results[name]
        a = sum(1 for r in rs if r.alignment_status == "aligned")
        d = sum(1 for r in rs if r.alignment_status == "drifting")
        m = sum(1 for r in rs if r.alignment_status == "misaligned")
        ae = sum(r.ethos for r in rs) / len(rs)
        al = sum(r.logos for r in rs) / len(rs)
        ap = sum(r.pathos for r in rs) / len(rs)
        print(
            f"{name:>22s} {len(rs):5d} {a:7d} {d:5d} {m:4d} {ae:6.2f} {al:6.2f} {ap:7.2f}"
        )


if __name__ == "__main__":
    import logging

    logging.disable(logging.WARNING)
    asyncio.run(main())
