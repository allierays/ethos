# Project Guide for Claude

## Project Overview

Ethos is an open-source Python package and API that scores AI agent messages for honesty, accuracy, and intent across 12 behavioral traits in 3 dimensions (ethos, logos, pathos).

*Better agents. Better data. Better alignment.*

## Tech Stack

- **Language**: Python 3.11+ (engine), TypeScript (SDK + CLI)
- **Package manager**: uv (Python), npm (TypeScript)
- **API**: FastAPI + Uvicorn
- **SDK**: ethos-ai npm package (SDK + CLI)
- **Academy**: Next.js (trust visualization UI)
- **Database**: Neo4j 5 (graph)
- **LLM**: Anthropic SDK (Claude Sonnet)
- **Validation**: Pydantic v2
- **Testing**: pytest + httpx
- **Driver**: neo4j sync driver (NOT async)

## Architecture: Domain-Driven Design

6 bounded contexts + shared + API. See `docs/evergreen-architecture/ddd-architecture.md` for full spec.

### Repo Layout (three surfaces, one engine)

```
~/Sites/ethos/
├── ethos/                      # Python package — the engine (pip install ethos)
│   ├── __init__.py             # Public API: evaluate, reflect, EvaluationResult
│   ├── evaluate.py             # Top-level evaluate() entry point
│   ├── reflect.py              # Top-level reflect() entry point
│   ├── models.py               # Re-exports from shared.models
│   ├── prompts.py              # Re-exports from evaluation.prompts
│   ├── graph.py                # Re-exports from graph.service
│   ├── shared/                 # Cross-domain models and errors
│   ├── taxonomy/               # 12 traits, 158 indicators, constitution
│   ├── config/                 # EthosConfig, priorities
│   ├── identity/               # Agent ID hashing (SHA-256)
│   ├── evaluation/             # Keyword scanner, prompt builder
│   └── graph/                  # Neo4j service, read, write, cohort
├── api/                        # FastAPI server — serves ethos/ over HTTP
├── sdk/                        # ethos-ai npm package — SDK + CLI
│   ├── src/                    # TypeScript SDK (client, evaluate, reflect)
│   ├── cli/                    # CLI commands (npx ethos evaluate)
│   ├── package.json
│   └── tsconfig.json
├── academy/                    # Next.js — trust visualization UI
├── docs/                       # Architecture docs, research, framework overview
├── scripts/                    # seed_graph.py, scrape_moltbook.py
├── tests/                      # Python tests for ethos/
└── data/                       # Moltbook scraped data
```

### Dependency Flow (always one-way)

```
sdk/ ──→ api/ ──→ ethos/
academy/ ──→ api/ ──→ ethos/
tests/ ──→ ethos/
scripts/ ──→ ethos/
```

## DDD Rules

1. **No circular dependencies.** If A depends on B, B never depends on A.
2. **Graph owns all Cypher.** No Cypher queries outside `ethos/graph/`.
3. **Graph is optional.** Every domain wraps graph calls in try/except. Neo4j down never crashes evaluate().
4. **Taxonomy is pure data.** No logic, no I/O, no dependencies.
5. **API is a thin layer.** No business logic in route handlers — delegate to domain functions.
6. **Message content never enters the graph.** Only scores, hashes, metadata.
7. **Identity never stores raw agent IDs.** Only hashes.
8. **All code is SYNC.** No async/await anywhere. Sync Neo4j driver, sync Anthropic client, sync route handlers.
9. **All API endpoints use Pydantic models** for both request and response — no raw dicts.

## Dependency Graph

```
┌─────────┐  ┌─────────┐
│   SDK   │  │ Academy │         ← surfaces (consumers)
└────┬────┘  └────┬────┘
     │            │
     └──────┬─────┘
            ▼
      ┌──────────┐
      │   API    │               ← HTTP layer
      └────┬─────┘
           │
  ┌────────┼──────────┐
  ▼        ▼          ▼
┌────────┐┌────────┐┌────────┐
│Evaluate││Reflect ││ Config │   ← ethos/ domains
└───┬────┘└───┬────┘└────────┘
    │         │
    │    ┌────┘
    ▼    ▼
┌────────┐
│ Graph  │
└───┬────┘
    │
 ┌──┴──┐
 ▼     ▼
┌────┐┌────────┐
│Tax.││Identity│               ← pure data / hashing
└────┘└────────┘

All domains import from: Shared (models, errors)
```

## Naming Conventions

- **Files**: `snake_case.py`
- **Functions/Variables**: `snake_case`
- **Classes/Models**: `PascalCase`
- **Constants**: `SCREAMING_SNAKE`

## Commands

```bash
# Run tests
uv run pytest -v

# Start dev server (local, port 8000)
uv run uvicorn api.main:app --reload --port 8000

# Seed Neo4j with taxonomy
uv run python -m scripts.seed_graph

# Import check
uv run python -c "from ethos import evaluate, reflect"

# Docker (production ports)
docker compose build
docker compose up -d
docker compose down
```

### Docker Ports

| Service    | Host Port | Container Port | URL                          |
|------------|-----------|----------------|------------------------------|
| API        | 8917      | 8000           | http://localhost:8917        |
| Neo4j UI   | 7491      | 7474           | http://localhost:7491        |
| Neo4j Bolt | 7694      | 7687           | bolt://localhost:7694        |

## Environment Variables

Copy `.env.example` to `.env`. Required:
- `ANTHROPIC_API_KEY` — Claude API key
- `NEO4J_URI` — `bolt://localhost:7694` (host), `bolt://neo4j:7687` (inside Docker)
- `NEO4J_USER` / `NEO4J_PASSWORD`

## Key Models (ethos/shared/models.py)

- `EvaluationResult` — 12 TraitScores, dimension scores (ethos/logos/pathos), tier_scores (safety/ethics/soundness/helpfulness), alignment_status, flags, trust
- `ReflectionResult` — trait_averages, dimension scores, trend, evaluation_count
- `TraitScore` — name, score (0.0-1.0), dimension, polarity
- `KeywordScanResult` — flagged_traits, total_flags, density, routing_tier

## Do

- Use `uv run` for all Python commands (not bare `python`)
- Use Pydantic `Field(ge=0.0, le=1.0)` for score bounds
- Import models from `ethos.shared.models`, errors from `ethos.shared.errors`
- Write tests for all new functionality
- Use sync Neo4j driver (`neo4j.GraphDatabase.driver()`)
- Wrap all graph calls in try/except

## Do NOT

- Hardcode API keys — use `.env` via environment variables
- Import from `api` inside the `ethos` package (one-way dependency)
- Use `Any` type — create proper Pydantic models
- Use async/await — all code is sync
- Write Cypher outside `ethos/graph/` — graph owns all queries
- Store message content in Neo4j — only scores and metadata

<!-- agentic-loop-detected -->
## Detected Project Info

- Runtime: Python
- Framework: FastAPI
- Testing: pytest
- Python: Use `uv run python` (not bare `python`)

*Auto-detected by agentic-loop. Edit freely.*

<!-- my-dna -->
## DNA

### Core Values
- Respect / Kindness - treat people well, in code and communication
- Simplicity / Clarity - avoid jargon, make things understandable

### Voice
Minimal and precise. Say less, mean more.

### Project
- **Priority:** Ship it - hackathon pace, get it working
- **Audience:** Anthropic hackathon - technical judges and participants
- **Tone:** Professional - clean, trustworthy, serious

## Hackathon Context

**Event:** [Claude Code Hackathon](https://cerebralvalley.ai/e/claude-code-hackathon/details)

**Problem Statement:** Amplify Human Judgment — Build AI that makes researchers, professionals, and decision-makers dramatically more capable without taking them out of the loop. The best AI doesn't replace human expertise. It sharpens it.

**How Ethos fits:** Ethos amplifies human judgment by scoring AI agent messages for honesty, accuracy, and intent. It flags manipulation and builds trust graphs over time — keeping humans informed, not replaced.

### Judging Criteria

1. **Demo (30%)** — Working, impressive, holds up live. Genuinely cool to watch.
2. **Impact (25%)** — Real-world potential. Who benefits, how much does it matter? Could this become something people use?
3. **Opus 4.6 Use (25%)** — Creative, beyond basic integration. Surface capabilities that surprise.
4. **Depth & Execution (20%)** — Push past the first idea. Sound engineering, real craft, not a quick hack.

### What This Means for Development

- **Demo first.** Every feature must be demoable. If it can't be shown live, deprioritize it.
- **Use Opus 4.6 deeply.** Evaluation logic should leverage Claude's reasoning in non-obvious ways — structured prompting, multi-pass analysis, self-reflection patterns.
- **Show the graph.** Neo4j trust graphs over time are the "wow" factor. Make trust visible.
- **Keep humans in the loop.** Ethos scores inform, not decide. The human always has final say.
