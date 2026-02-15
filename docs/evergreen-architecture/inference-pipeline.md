# Inference Pipeline

> How to run Ethos evaluation on Moltbook data. Batch processing, incremental imports, cost control, and what gets stored where.

---

## Overview

`scripts/run_inference.py` evaluates Moltbook posts through the full three-faculty pipeline (instinct, intuition, deliberation), stores results in Neo4j, and writes JSONL output for analysis.

```mermaid
flowchart LR
    A[Moltbook JSON] --> B[flatten]
    B --> C[authenticity filter]
    C --> D[instinct / route]
    D --> E[evaluate]
    E --> F[Neo4j + JSONL]

    classDef default fill:#fff,stroke:#999,color:#333
```

One command does everything:

```bash
uv run python -m scripts.run_inference --source sample --include-comments --seed --skip-existing --agents-only
```

---

## Data Flow

### Step 1: Load and Flatten

The script reads Moltbook JSON and normalizes posts, comments, and replies into a flat list of messages.

```
sample_posts.json   →  10 posts + comments/replies  →  ~46 messages
curated_posts.json  →  500 posts (no comments)       →  ~500 messages
```

Messages are sorted by `created_at` so the PRECEDES chain in Neo4j is chronologically correct.

### Step 2: Authenticity Filter

Before any API calls, the script loads pre-computed authenticity classifications from `data/moltbook/authenticity_results.json` (1,010 agents classified).

With `--agents-only`, messages from `likely_human` agents are removed. No API tokens wasted on humans pretending to be AI agents.

```
likely_autonomous  →  kept (genuine AI agent)
high_frequency     →  kept (active agent, posts in bursts)
indeterminate      →  kept (unclear, worth evaluating)
likely_human       →  skipped (human-operated account)
```

### Step 3: Cost Estimate

Every run shows a cost estimate before making API calls. Instinct scans each message (free, no LLM call) to determine the routing tier:

```
standard           →  Sonnet  (~$0.003/msg)
focused            →  Sonnet  (~$0.003/msg)
deep               →  Opus    (~$0.030/msg)
deep_with_context  →  Opus    (~$0.030/msg)
```

Use `--dry-run` to see the estimate without spending anything.

### Step 4: Evaluate

Each message goes through the full pipeline:

1. **Instinct** — keyword scan, routing tier (no I/O)
2. **Intuition** — graph history lookup, anomaly detection (graph queries only)
3. **Deliberation** — Claude LLM call, 12 traits scored, 214 indicators checked
4. **Graph storage** — Evaluation node, Agent node, PRECEDES chain, DETECTED indicators

Messages are processed sequentially to preserve PRECEDES chain integrity.

### Step 5: Store Authenticity

After evaluations complete, the script writes `authenticity_score` and `authenticity_classification` onto the Agent nodes in Neo4j. This connects the two systems — evaluation scores and authenticity classification live on the same Agent node.

### Step 6: Summary

A summary JSON file is written with alignment distribution, dimension averages, per-agent breakdowns, and authenticity-vs-alignment cross-tabulation.

---

## Incremental Imports

The script is designed for repeated runs. New data gets added without duplicating existing evaluations.

### How `--skip-existing` Works

1. Before evaluating, the script queries Neo4j for all existing `message_hash` values
2. Each message's content is SHA-256 hashed
3. If the hash already exists in Neo4j, the message is skipped — no API call made
4. New messages are evaluated and appended to the same JSONL file

```bash
# First run: evaluates 10 messages
uv run python -m scripts.run_inference --source sample --seed

# Second run: skips the 10 already evaluated, evaluates 0
uv run python -m scripts.run_inference --source sample --skip-existing

# Add comments: skips the 10 posts, evaluates ~36 new comments
uv run python -m scripts.run_inference --source sample --include-comments --skip-existing
```

### What Accumulates in Neo4j

Each run adds to the graph. An agent's character builds over multiple evaluations:

```mermaid
flowchart LR
    Agent[Agent] -- EVALUATED --> E1[Eval 1]
    E1 -- PRECEDES --> E2[Eval 2]
    E2 -- PRECEDES --> E3[Eval 3]
    E1 -- DETECTED --> I1[Indicator]
    E2 -- DETECTED --> I2[Indicator]

    classDef default fill:#fff,stroke:#999,color:#333
```

- **Agent node** — updated each evaluation: `evaluation_count`, `phronesis_score`, `trait_variance`, `balance_score`, `authenticity_classification`
- **Evaluation node** — one per message: all 12 trait scores, 3 dimension scores, alignment status, flags, routing tier, model used, `message_hash`, `message_timestamp`
- **PRECEDES chain** — temporal ordering between evaluations for the same agent
- **DETECTED relationships** — links evaluations to the specific indicators found, with confidence and evidence

### Duplicate Prevention

Two layers of protection:

1. **Script level** — `--skip-existing` checks Neo4j hashes before API calls (saves money)
2. **Graph level** — `store_evaluation()` checks for same agent + message_hash before creating nodes (prevents duplicates if script-level check fails)

---

## CLI Reference

```
uv run python -m scripts.run_inference [flags]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--source` | `sample` | Data source: `sample` (10 posts + comments) or `curated` (500 posts) |
| `--include-comments` | off | Evaluate comments and replies too (sample only) |
| `--limit N` | 0 | Cap number of evaluations (0 = unlimited) |
| `--skip-existing` | off | Skip messages already in Neo4j (by content hash) |
| `--dry-run` | off | Show cost estimate only, no API calls |
| `--seed` | off | Seed taxonomy into Neo4j first (dimensions, traits, 214 indicators, patterns) |
| `--agents-only` | off | Filter out `likely_human` agents before evaluating |

---

## Typical Workflows

### Fresh Start

```bash
# Wipe Neo4j, seed taxonomy, evaluate sample with comments
uv run python -m scripts.run_inference --source sample --include-comments --seed --agents-only
```

### Add More Data

```bash
# Evaluate curated posts, skipping any already evaluated
uv run python -m scripts.run_inference --source curated --skip-existing --agents-only
```

### Cost Check Before Scaling

```bash
# See what curated would cost without spending anything
uv run python -m scripts.run_inference --source curated --agents-only --dry-run
```

### Re-run After Code Changes

```bash
# If scoring logic changed, you'd wipe Neo4j and re-evaluate
# (skip-existing won't help here — you want fresh scores)
uv run python -m scripts.run_inference --source sample --include-comments --seed
```

---

## Output Files

| File | Location | Format | Description |
|------|----------|--------|-------------|
| `batch_sample.jsonl` | `data/results/` | JSONL (append) | One JSON line per evaluation |
| `batch_sample_summary.json` | `data/results/` | JSON | Aggregate statistics |
| `batch_curated.jsonl` | `data/results/` | JSONL (append) | Same, for curated source |
| `batch_curated_summary.json` | `data/results/` | JSON | Same, for curated source |

### JSONL Entry Structure

Each line contains:

```json
{
  "message_id": "post-abc123",
  "author_name": "BrutusBot",
  "author_id": "agent-456",
  "message_type": "post",
  "post_title": "Incentive Design in Multi-Agent Systems",
  "submolt": "security",
  "content_preview": "CircuitDreamer proved that...",
  "content_hash": "sha256...",
  "created_at": "2025-10-15T14:30:00Z",
  "authenticity": {
    "classification": "indeterminate",
    "score": 0.45,
    "confidence": 0.9
  },
  "evaluation": {
    "evaluation_id": "uuid...",
    "ethos": 0.82,
    "logos": 0.79,
    "pathos": 0.71,
    "phronesis": "established",
    "alignment_status": "aligned",
    "routing_tier": "focused",
    "model_used": "claude-sonnet-4-20250514",
    "traits": { "virtue": 0.85, "goodwill": 0.80, "...": "..." },
    "detected_indicators": [
      { "id": "VIR-CONSISTENCY", "name": "Consistent Values", "confidence": 0.8 }
    ],
    "flags": []
  },
  "evaluated_at": "2026-02-12T..."
}
```

---

## Architecture Notes

- **Message content is stored on Evaluation nodes** alongside the SHA-256 hash, scores, and metadata.
- **Sequential processing is intentional.** Parallel evaluation would break PRECEDES chain ordering.
- **Graph is optional.** If Neo4j is down, evaluations still run — scores are valid, just not stored.
- **Ctrl+C is safe.** The script handles SIGINT, finishes the current evaluation, and exits cleanly. Progress is preserved in the JSONL file and Neo4j.
- **All agents get `agent_specialty: "openclaw"`** to identify them as OpenClaw platform agents.

---

## Related Docs

- [Ethos Framework Overview](ethos-framework-overview.md) — the three faculties diagram
- [Scoring Algorithm](scoring-algorithm.md) — how 12 traits become dimension scores
- [Neo4j Schema](neo4j-schema.md) — graph node and relationship structure
- [Pattern Detection Architecture](pattern-detection-architecture.md) — temporal pattern detection (runs separately after evaluations accumulate)
