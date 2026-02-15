"""Batch authenticity analysis of scraped Moltbook agent profiles.

Reads all agent profiles from data/moltbook/agents/*.json,
runs authenticity analysis, saves results to data/moltbook/authenticity_results.json.

Usage:
    uv run python scripts/analyze_agents.py
"""

import json
import sys
from pathlib import Path

from ethos_academy.evaluation.authenticity import (
    analyze_activity_pattern,
    analyze_burst_rate,
    analyze_identity_signals,
    analyze_temporal_signature,
    compute_authenticity,
    parse_timestamps,
)

_SCRIPT_DIR = Path(__file__).resolve().parent
_DATA_DIR = _SCRIPT_DIR.parent / "data" / "moltbook"
_AGENTS_DIR = _DATA_DIR / "agents"
_OUTPUT_FILE = _DATA_DIR / "authenticity_results.json"


def analyze_agent(data: dict) -> dict:
    """Analyze a single agent profile and return AuthenticityResult as dict."""
    agent = data.get("agent", {})
    posts = data.get("posts", [])
    comments = data.get("comments", [])

    # Collect all timestamps from posts and comments
    timestamps = []
    for post in posts:
        ts = post.get("created_at")
        if ts:
            timestamps.append(ts)
    for comment in comments:
        ts = comment.get("created_at")
        if ts:
            timestamps.append(ts)

    # Parse once, share across all sub-analyses
    parsed = parse_timestamps(timestamps)

    # Run sub-analyses
    temporal = analyze_temporal_signature(timestamps, _parsed=parsed)
    burst = analyze_burst_rate(timestamps, _parsed=parsed)
    activity = analyze_activity_pattern(timestamps, _parsed=parsed)

    # Build profile dict for identity signals
    profile = {
        "is_claimed": agent.get("is_claimed", False),
        "owner": agent.get("owner", {}),
        "karma": agent.get("karma", 0),
        "post_count": len(posts),
        "comment_count": len(comments),
    }
    identity = analyze_identity_signals(profile)

    # Compute final result
    result = compute_authenticity(
        temporal, burst, activity, identity, num_timestamps=len(timestamps)
    )

    return result.model_dump()


def main():
    agent_files = sorted(_AGENTS_DIR.glob("*.json"))
    if not agent_files:
        print(f"ERROR: No agent profiles found in {_AGENTS_DIR}", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing {len(agent_files)} agent profiles...")

    results = {}
    skipped = 0

    for i, filepath in enumerate(agent_files):
        try:
            with open(filepath) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARNING: Skipping {filepath}: {e}", file=sys.stderr)
            skipped += 1
            continue

        agent_name = data.get("agent", {}).get("name", "")
        if not agent_name:
            agent_name = filepath.stem

        result = analyze_agent(data)
        result["agent_name"] = agent_name
        results[agent_name] = result

        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(agent_files)} agents...")

    # Write results atomically via temp file
    tmp_path = _OUTPUT_FILE.with_suffix(".tmp")
    try:
        with open(tmp_path, "w") as f:
            json.dump(results, f, indent=2)
        tmp_path.replace(_OUTPUT_FILE)
    except OSError as e:
        print(f"ERROR: Failed to write results to {_OUTPUT_FILE}: {e}", file=sys.stderr)
        tmp_path.unlink(missing_ok=True)
        sys.exit(1)

    # Print summary
    classifications: dict[str, int] = {}
    for v in results.values():
        cls = v["classification"]
        classifications[cls] = classifications.get(cls, 0) + 1

    print(f"\nDone! Results saved to {_OUTPUT_FILE}")
    print(f"  Total analyzed: {len(results)}")
    if skipped:
        print(f"  Skipped (malformed): {skipped}")
    print("  Classification distribution:")
    for cls, count in sorted(classifications.items()):
        print(f"    {cls}: {count}")


if __name__ == "__main__":
    main()
