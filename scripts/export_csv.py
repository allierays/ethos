"""Export JSONL evaluation results to reviewable CSVs.

Joins full message content from source Moltbook data via content_hash.

Usage:
    uv run python -m scripts.export_csv
"""

import csv
import hashlib
import json
from pathlib import Path

# Trait ID prefix -> trait name mapping
PREFIX_TO_TRAIT = {
    "VIR": "virtue",
    "GDW": "goodwill",
    "MAN": "manipulation",
    "DEC": "deception",
    "ACC": "accuracy",
    "RSN": "reasoning",
    "FAB": "fabrication",
    "BLG": "broken_logic",
    "REC": "recognition",
    "CMP": "compassion",
    "DIS": "dismissal",
    "EXP": "exploitation",
}

TRAIT_NAMES = [
    "virtue",
    "goodwill",
    "manipulation",
    "deception",
    "accuracy",
    "reasoning",
    "fabrication",
    "broken_logic",
    "recognition",
    "compassion",
    "dismissal",
    "exploitation",
]

EVAL_COLUMNS = [
    "evaluation_id",
    "author_name",
    "ai_model",
    "specialty",
    "message_type",
    "post_title",
    "submolt",
    "content",
    "ethos",
    "logos",
    "pathos",
    *[f"trait_{t}" for t in TRAIT_NAMES],
    "alignment_status",
    "phronesis",
    "routing_tier",
    "flags",
    "indicator_count",
    "indicator_names",
    "authenticity_classification",
    "authenticity_score",
    "created_at",
    "evaluated_at",
]

INDICATOR_COLUMNS = [
    "evaluation_id",
    "author_name",
    "indicator_id",
    "indicator_name",
    "confidence",
    "trait",
]


def trait_from_prefix(indicator_id: str) -> str:
    """Derive trait name from indicator ID prefix (e.g. VIR-UNCERTAIN -> virtue)."""
    prefix = indicator_id.split("-")[0] if "-" in indicator_id else indicator_id
    return PREFIX_TO_TRAIT.get(prefix, "unknown")


def build_content_index(data_dir: Path) -> dict[str, str]:
    """Build content_hash -> full content lookup from Moltbook source files.

    Reads sample_posts.json and all_posts.json, hashing each post/comment
    to match against JSONL results.
    """
    index: dict[str, str] = {}

    for filename in ["sample_posts.json", "all_posts.json"]:
        path = data_dir / filename
        if not path.exists():
            continue
        print(f"  Indexing {filename}...", end=" ", flush=True)
        with open(path) as f:
            posts = json.load(f)

        count = 0
        for post in posts:
            content = post.get("content") or ""
            if content.strip():
                h = hashlib.sha256(content.encode()).hexdigest()
                if h not in index:
                    index[h] = content
                    count += 1

            for comment in post.get("comments", []):
                count += _index_comment(comment, index)

        print(f"{count} entries")

    return index


def _index_comment(comment: dict, index: dict[str, str]) -> int:
    """Recursively index a comment and its replies."""
    count = 0
    content = comment.get("content") or ""
    if content.strip():
        h = hashlib.sha256(content.encode()).hexdigest()
        if h not in index:
            index[h] = content
            count += 1
    for reply in comment.get("replies", []):
        count += _index_comment(reply, index)
    return count


def load_records(results_dir: Path) -> list[dict]:
    """Load all JSONL files from results directory, deduped by content_hash."""
    seen_hashes: set[str] = set()
    records: list[dict] = []

    for path in sorted(results_dir.glob("batch_*.jsonl")):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                content_hash = record.get("content_hash", "")
                if content_hash in seen_hashes:
                    continue
                seen_hashes.add(content_hash)
                records.append(record)

    return records


def readable_indicator_name(indicator: dict) -> str:
    """Turn an indicator into a readable label like 'context sensitivity'."""
    name = indicator.get("name", indicator.get("id", ""))
    return name.replace("_", " ")


def flatten_evaluation(
    record: dict,
    content_index: dict[str, str],
    specialties: dict[str, str],
) -> dict:
    """Flatten a JSONL record into a flat dict for the evaluations CSV."""
    ev = record.get("evaluation", {})
    traits = ev.get("traits", {})
    indicators = ev.get("detected_indicators", [])
    auth = record.get("authenticity") or {}
    flags = ev.get("flags", [])
    author = record.get("author_name", "")

    # Full content: prefer JSONL field, fall back to source index, then preview
    content_hash = record.get("content_hash", "")
    content = (
        record.get("content")
        or content_index.get(content_hash)
        or record.get("content_preview", "")
    )

    row = {
        "evaluation_id": ev.get("evaluation_id", ""),
        "author_name": author,
        "ai_model": ev.get("model_used", ""),
        "specialty": specialties.get(author, ""),
        "message_type": record.get("message_type", ""),
        "post_title": record.get("post_title", ""),
        "submolt": record.get("submolt", ""),
        "content": content,
        "ethos": ev.get("ethos", ""),
        "logos": ev.get("logos", ""),
        "pathos": ev.get("pathos", ""),
        "alignment_status": ev.get("alignment_status", ""),
        "phronesis": ev.get("phronesis", ""),
        "routing_tier": ev.get("routing_tier", ""),
        "flags": ",".join(flags),
        "indicator_count": len(indicators),
        "indicator_names": ", ".join(
            readable_indicator_name(ind) for ind in indicators
        ),
        "authenticity_classification": auth.get("classification", ""),
        "authenticity_score": auth.get("score", ""),
        "created_at": record.get("created_at", ""),
        "evaluated_at": record.get("evaluated_at", ""),
    }

    for trait in TRAIT_NAMES:
        row[f"trait_{trait}"] = traits.get(trait, "")

    return row


def extract_indicators(record: dict) -> list[dict]:
    """Extract one row per detected indicator from a JSONL record."""
    ev = record.get("evaluation", {})
    indicators = ev.get("detected_indicators", [])
    rows = []

    for ind in indicators:
        indicator_id = ind.get("id", "")
        rows.append(
            {
                "evaluation_id": ev.get("evaluation_id", ""),
                "author_name": record.get("author_name", ""),
                "indicator_id": indicator_id,
                "indicator_name": ind.get("name", ""),
                "confidence": ind.get("confidence", ""),
                "trait": trait_from_prefix(indicator_id),
            }
        )

    return rows


def load_specialties(moltbook_dir: Path) -> dict[str, str]:
    """Load agent specialties from agent_specialties.json."""
    path = moltbook_dir / "agent_specialties.json"
    if not path.exists():
        print("  Warning: agent_specialties.json not found")
        return {}
    with open(path) as f:
        return json.load(f)


def main():
    project_root = Path(__file__).resolve().parent.parent
    results_dir = project_root / "data" / "results"
    exports_dir = project_root / "data" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    records = load_records(results_dir)
    print(f"Loaded {len(records)} unique records (deduped by content_hash)")

    # Build content lookup from source Moltbook data
    moltbook_dir = project_root / "data" / "moltbook"
    print("Building content index from source data...")
    content_index = build_content_index(moltbook_dir)
    print(f"Content index: {len(content_index)} unique hashes")

    # Load agent specialties
    specialties = load_specialties(moltbook_dir)
    print(f"Loaded specialties for {len(specialties)} agents")

    # Count how many records got full content
    matched = sum(
        1
        for r in records
        if r.get("content") or r.get("content_hash", "") in content_index
    )
    print(f"Matched full content for {matched}/{len(records)} records")

    # Write evaluations CSV
    eval_path = exports_dir / "evaluations.csv"
    with open(eval_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EVAL_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(flatten_evaluation(record, content_index, specialties))
    print(f"Wrote {len(records)} rows to {eval_path}")

    # Write indicators CSV
    indicator_path = exports_dir / "indicators.csv"
    indicator_count = 0
    with open(indicator_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=INDICATOR_COLUMNS)
        writer.writeheader()
        for record in records:
            rows = extract_indicators(record)
            for row in rows:
                writer.writerow(row)
                indicator_count += 1
    print(f"Wrote {indicator_count} rows to {indicator_path}")


if __name__ == "__main__":
    main()
