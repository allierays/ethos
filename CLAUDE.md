# Project Guide for Claude

## Project Overview

Ethos is an open-source Python package and API for evaluating AI agent messages for trustworthiness across 12 traits in 3 dimensions (ethos, logos, pathos).

*Better agents. Better data. Better alignment.*

## Tech Stack

- **Language**: Python 3.11+
- **Package manager**: uv
- **API**: FastAPI + Uvicorn
- **Database**: Neo4j 5 (graph)
- **LLM**: Anthropic SDK (Claude Sonnet)
- **Validation**: Pydantic v2
- **Testing**: pytest + httpx
- **Driver**: neo4j sync driver (NOT async)

## Architecture: Domain-Driven Design

6 bounded contexts + shared + API. See `docs/evergreen-architecture/ddd-architecture.md` for full spec.

```
ethos/                          # Python package (DDD domains)
├── __init__.py                 # Public API: evaluate, reflect, EvaluationResult
├── shared/
│   ├── models.py               # All Pydantic models (EvaluationResult, etc.)
│   └── errors.py               # EthosError, GraphUnavailableError, etc.
├── taxonomy/
│   ├── traits.py               # 12 traits, 3 dimensions, TRAIT_METADATA
│   ├── indicators.py           # 134 behavioral indicators
│   ├── constitution.py         # 4 values, 7 hard constraints, 3 legitimacy tests
│   └── rubrics.py              # Per-trait scoring anchors (0.0-1.0)
├── config/
│   ├── config.py               # EthosConfig, from_env()
│   └── priorities.py           # Priority thresholds (critical/high/standard/low)
├── identity/
│   └── hashing.py              # hash_agent_id() — SHA-256
├── evaluation/
│   ├── scanner.py              # Keyword lexicon + scan_keywords()
│   ├── prompts.py              # Constitutional rubric prompt builder
│   ├── parser.py               # Parse Claude JSON → TraitScores
│   └── evaluate.py             # Orchestrator: scan → prompt → Claude → parse
├── reflection/
│   └── reflect.py              # Query graph, compute trends
└── graph/
    ├── service.py              # GraphService — sync Neo4j driver lifecycle
    ├── write.py                # store_evaluation, merge nodes
    ├── read.py                 # get_evaluation_history, get_agent_profile
    ├── network.py              # get_network_averages
    └── seed.py                 # Schema creation + taxonomy seeding
api/
├── main.py                     # FastAPI app, lifespan
├── schemas.py                  # Request/response Pydantic models (API-layer)
├── deps.py                     # Dependency injection (GraphService, config)
└── routes/
    ├── evaluate.py             # POST /evaluate
    ├── reflect.py              # POST /reflect
    ├── agent.py                # GET /agent/{agent_id}
    └── health.py               # GET /health
tests/
scripts/
├── seed_graph.py               # Thin wrapper → ethos.graph.seed
└── import_moltbook.py          # Scan + evaluate + import Moltbook posts
data/moltbook/                  # Scraped social data (14K posts, 99K comments)
dashboard/                      # Future: visualization UI
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
                    ┌──────────┐
                    │   API    │
                    └────┬─────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌───────────┐  ┌───────────┐  ┌───────────┐
    │ Evaluation │  │ Reflection│  │  Config   │
    └─────┬─────┘  └─────┬─────┘  └───────────┘
          │              │
          │         ┌────┘
          ▼         ▼
    ┌───────────┐
    │   Graph   │
    └─────┬─────┘
          │
    ┌─────┴─────┐
    ▼           ▼
┌──────────┐ ┌──────────┐
│ Taxonomy │ │ Identity │
└──────────┘ └──────────┘

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

# Start dev server
uv run uvicorn api.main:app --reload --port 8000

# Seed Neo4j with taxonomy
uv run python -m scripts.seed_graph

# Import Moltbook posts (scan + evaluate + graph)
uv run python -m scripts.import_moltbook --limit 20

# Import check
uv run python -c "from ethos import evaluate, reflect"

# Docker
docker compose build
docker compose up -d        # API on :8917, Neo4j browser on :7491, bolt on :7694
docker compose down
```

## Environment Variables

Copy `.env.example` to `.env`. Required:
- `ANTHROPIC_API_KEY` — Claude API key
- `NEO4J_URI` — default `bolt://localhost:7694` (Docker-mapped), inside Docker `bolt://neo4j:7687`
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

**How Ethos fits:** Ethos amplifies human judgment by scoring AI agent messages for trustworthiness (ethos, logos, pathos). It flags manipulation and builds trust graphs over time — keeping humans informed, not replaced.

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
