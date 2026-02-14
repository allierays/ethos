"""Seed 100 moltbook agents with 5 evaluated messages each into Neo4j.

Uses Haiku to pre-filter for insightful posts and detect model self-identification,
then runs selected messages through the full evaluate_outgoing() pipeline.
Writes to Neo4j sequentially to avoid overwhelming the database.

Usage:
    uv run python -m scripts.seed_agents
    uv run python -m scripts.seed_agents --count 50
    uv run python -m scripts.seed_agents --dry-run
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sys
from pathlib import Path


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

from anthropic import AsyncAnthropic  # noqa: E402
from ethos.graph.service import GraphService  # noqa: E402
from ethos.tools import evaluate_outgoing  # noqa: E402

logger = logging.getLogger(__name__)

AGENTS_DIR = Path(__file__).resolve().parent.parent / "data" / "moltbook" / "agents"
SPECIALTIES_FILE = AGENTS_DIR.parent / "agent_specialties.json"

# Graceful shutdown
_interrupted = False


def _handle_sigint(signum: int, frame: object) -> None:
    global _interrupted
    _interrupted = True
    print("\n\nInterrupted. Finishing current agent, then stopping...")


# ── Haiku pre-filter ─────────────────────────────────────────────────

HAIKU_MODEL = "claude-haiku-4-5-20251001"

FILTER_PROMPT = """You are selecting the most insightful posts from an AI agent on Moltbook (an AI social network).

Given these posts by agent "{agent_name}", pick exactly 5 that are most interesting for character evaluation. Prefer posts that:
- Show genuine reasoning, opinions, or ethical positions
- Reveal the agent's character, values, or decision-making
- Are substantive (not just spam, token minting, or follow-back requests)

Also check: does the agent mention what AI model they are? Look for references like "I'm built on GPT-4", "I run on Claude", "powered by Llama", "my model is...", "Kimi", "Moonshot", "Mistral", "Gemini", "DeepSeek", "Grok", etc. For Claude-based agents, try to determine if they use Sonnet, Opus, or Haiku specifically. Check the agent description too: "{agent_description}"

Respond with ONLY valid JSON, no markdown fencing:
{{
  "selected_indices": [0, 3, 7, 12, 15],
  "detected_model": "gpt-4o" or "" if unknown,
  "selection_reasoning": "brief explanation"
}}"""


async def _haiku_filter(
    client: AsyncAnthropic,
    agent_name: str,
    agent_description: str,
    posts: list[dict],
) -> dict:
    """Use Haiku to pick 5 best posts and detect model."""
    # Build post summaries for Haiku (truncate long posts)
    post_summaries = []
    for i, post in enumerate(posts):
        content = (post.get("content") or "")[:500]
        title = post.get("title", "")
        upvotes = post.get("upvotes", 0)
        post_summaries.append(f"[{i}] (upvotes: {upvotes}) {title}\n{content}")

    posts_text = "\n\n---\n\n".join(post_summaries)

    prompt = FILTER_PROMPT.format(
        agent_name=agent_name,
        agent_description=agent_description or "No description",
    )

    try:
        response = await client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=300,
            messages=[
                {"role": "user", "content": f"{prompt}\n\nPosts:\n\n{posts_text}"}
            ],
        )
        text = response.content[0].text.strip()
        # Strip markdown fencing if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        result = json.loads(text)

        # Validate indices
        indices = result.get("selected_indices", [])
        valid_indices = [i for i in indices if 0 <= i < len(posts)][:5]

        # Pad if Haiku returned fewer than 5
        if len(valid_indices) < 5:
            remaining = [i for i in range(len(posts)) if i not in valid_indices]
            random.shuffle(remaining)
            valid_indices.extend(remaining[: 5 - len(valid_indices)])

        return {
            "indices": valid_indices[:5],
            "detected_model": result.get("detected_model", ""),
            "reasoning": result.get("selection_reasoning", ""),
        }
    except Exception as exc:
        logger.warning("Haiku filter failed for %s: %s", agent_name, exc)
        # Fallback: pick 5 random posts
        indices = random.sample(range(len(posts)), min(5, len(posts)))
        return {"indices": indices, "detected_model": "", "reasoning": "fallback"}


# ── Agent loading ────────────────────────────────────────────────────


def _load_eligible_agents(existing_ids: set[str], count: int) -> list[dict]:
    """Load agents from disk, skip those already in Neo4j, require 5+ posts."""
    agents = []
    for filepath in sorted(AGENTS_DIR.glob("*.json")):
        data = json.loads(filepath.read_text())
        agent = data.get("agent", {})
        agent_name = agent.get("name", "")
        agent_id = agent_name  # moltbook uses name as ID

        if agent_id in existing_ids:
            continue

        posts = data.get("posts", [])
        if len(posts) < 5:
            continue

        # Skip low-karma bots and spammy agents
        if agent.get("karma", 0) < 5:
            continue

        agents.append(data)

    # Shuffle and pick
    random.shuffle(agents)
    return agents[:count]


async def _get_existing_agent_ids(service: GraphService) -> set[str]:
    """Get agent IDs already in Neo4j."""
    if not service.connected:
        return set()
    records, _, _ = await service.execute_query(
        "MATCH (a:Agent) RETURN a.agent_id AS id"
    )
    return {r["id"] for r in records}


# ── Main pipeline ────────────────────────────────────────────────────


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed moltbook agents through real AI evaluation"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of agents to add (default: 100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run Haiku filter only, skip evaluation (test mode)",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _handle_sigint)
    logging.basicConfig(level=logging.WARNING)

    # Connect to Neo4j
    service = GraphService()
    await service.connect()
    if not service.connected:
        print("ERROR: Cannot connect to Neo4j.", file=sys.stderr)
        sys.exit(1)
    print("Connected to Neo4j")

    # Load specialties
    specialties = {}
    if SPECIALTIES_FILE.exists():
        specialties = json.loads(SPECIALTIES_FILE.read_text())

    # Find agents already in graph
    existing = await _get_existing_agent_ids(service)
    print(f"Existing agents in graph: {len(existing)}")

    # Load eligible agents
    agents = _load_eligible_agents(existing, args.count)
    print(f"Selected {len(agents)} new agents to evaluate")

    if not agents:
        print("No eligible agents found.")
        await service.close()
        return

    # Haiku client for pre-filtering
    haiku_client = AsyncAnthropic()

    evaluated = 0
    failed = 0

    try:
        for i, agent_data in enumerate(agents):
            if _interrupted:
                break

            agent = agent_data["agent"]
            agent_name = agent["name"]
            agent_id = agent_name
            posts = agent_data["posts"]
            specialty = specialties.get(agent_name, "general")

            print(
                f"\n[{i + 1}/{len(agents)}] {agent_name} ({specialty}, {len(posts)} posts)"
            )

            # Step 1: Haiku picks 5 best posts + detects model
            print("  Filtering with Haiku...", end=" ", flush=True)
            filter_result = await _haiku_filter(
                haiku_client,
                agent_name,
                agent.get("description", ""),
                posts,
            )
            detected_model = filter_result["detected_model"]
            print(f"done (model: {detected_model or 'unknown'})")

            if args.dry_run:
                for idx in filter_result["indices"]:
                    title = posts[idx].get("title", "")[:60]
                    print(f"    [{idx}] {title}")
                continue

            # Step 2: Evaluate each selected post sequentially
            selected_posts = [posts[idx] for idx in filter_result["indices"]]

            for j, post in enumerate(selected_posts):
                if _interrupted:
                    break

                content = post.get("content") or ""
                if not content.strip():
                    continue

                print(f"  [{j + 1}/5] evaluating...", end=" ", flush=True)
                try:
                    await evaluate_outgoing(
                        content,
                        source=agent_id,
                        source_name=agent_name,
                        agent_specialty=specialty,
                    )
                    print("done")
                    evaluated += 1
                except Exception as exc:
                    print(f"FAILED: {exc}")
                    failed += 1
                    logger.warning("Eval failed for %s post %d: %s", agent_name, j, exc)

                # Rate limit: 1 second between evaluations
                await asyncio.sleep(1)

            # Step 3: Update agent model if detected
            if detected_model and service.connected:
                await service.execute_query(
                    "MATCH (a:Agent {agent_id: $agent_id}) SET a.agent_model = $model",
                    {"agent_id": agent_id, "model": detected_model},
                )

            # Brief pause between agents
            await asyncio.sleep(0.5)

    finally:
        await service.close()
        print(f"\n\nDone. {evaluated} evaluations, {failed} failed.")
        if _interrupted:
            print(f"Interrupted after {i + 1} agents.")


if __name__ == "__main__":
    asyncio.run(main())
