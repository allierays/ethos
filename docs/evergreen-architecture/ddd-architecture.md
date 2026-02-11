# Domain-Driven Design: Repo Architecture

> How the Ethos codebase is organized by domain. Each domain owns its models, logic, and boundaries.

---

## The Domains

Ethos has six bounded contexts. Each domain has a clear responsibility, owns its data, and communicates with other domains through well-defined interfaces.

```
ethos/                   # Python package (pip install ethos)
├── evaluation/      # Core scoring — the heart of the product
├── reflection/      # Self-examination and insights (planned)
├── graph/           # Neo4j persistence and cohort intelligence
├── taxonomy/        # Semantic memory — traits, indicators, patterns
├── identity/        # Agent identity and hashing
├── config/          # Developer configuration and priorities
└── shared/          # Cross-cutting models and utilities
api/                     # FastAPI server (at repo root, NOT inside ethos/)
sdk/                     # ethos-ai npm package (SDK + CLI)
academy/                 # Next.js trust visualization UI
```

---

## Domain 1: Evaluation

**Responsibility:** Score a single message for honesty, accuracy, and intent across 12 traits.

This is the core domain. Everything else supports it.

```
ethos/evaluation/
├── __init__.py          # exports: evaluate()
├── evaluate.py          # Main evaluate() function — orchestrates the flow
├── scanner.py           # Keyword lexicon and pre-filter scan
├── prompts.py           # Prompt builder (layered by routing tier)
├── router.py            # Model selection based on routing tier
└── parser.py            # Parse Claude's JSON response into TraitScores
```

### Domain Logic

```
evaluate(text, source, config)
    │
    ├── scanner.scan_keywords(text)         → KeywordScanResult
    │     └── hard_constraint flags?        → immediate DEEP_WITH_CONTEXT routing
    ├── router.select_model(scan)           → model_id, use_thinking
    ├── prompts.build(text, scan, tier)     → system_prompt, user_prompt
    ├── _call_claude(model, prompts)        → raw JSON
    ├── parser.parse(raw, scan, config)     → EvaluationResult
    ├── alignment.compute_status(result)    → "violation" | "misaligned" | "drifting" | "aligned"
    │
    └── graph.store(source, result)         → async, non-fatal
```

### Key Rules

- Evaluation never depends on Graph. If Neo4j is down, evaluate still works.
- Evaluation never modifies the input text.
- Evaluation always scores all 12 traits. Priorities only affect flags.
- The scanner is a pure function — no I/O, no state, no side effects.
- Hard constraint flags are checked first — they escalate routing and can result in "violation" status.
- Alignment status is computed hierarchically using constitutional value priorities (safety > ethics > soundness > helpfulness).

### Aggregate Root

`EvaluationResult` — contains everything: dimension scores, trait scores, indicators, flags, metadata. This is the single object that crosses domain boundaries.

---

## Domain 2: Reflection

**Responsibility:** Score the developer's own agent and surface behavioral insights.

```
ethos/reflection/
├── __init__.py          # exports: reflect(), reflect_history(), insights()
├── reflect.py           # Per-message reflection (fire-and-forget)
├── history.py           # On-demand history query
└── insights.py          # Claude-powered behavioral insights
```

### Three Functions, Three Cadences

| Function | Cadence | Depends On |
|----------|---------|------------|
| `reflect(text, agent_id)` | Per message | Evaluation domain (reuses evaluate) + Graph |
| `reflect_history(agent_id)` | On demand | Graph |
| `insights(agent_id)` | Nightly / on demand | Graph + Claude (Opus) |

### Domain Logic

`reflect()` reuses the Evaluation domain — it calls `evaluate()` internally on the agent's outgoing message, then stores the result via Graph. It's a thin wrapper that adds the async/fire-and-forget behavior.

`insights()` is its own Claude call. It doesn't reuse the evaluation prompt. It has its own prompt that takes structured data (agent history + cohort averages) and asks Claude to reason about patterns.

### Key Rules

- Reflection never blocks the developer's response path.
- `reflect()` is async — returns immediately, evaluation happens in background.
- `insights()` can be slow (it's Opus + extended thinking) because it runs offline.
- Reflection depends on Graph for storage and history. Without Graph, `reflect()` is a no-op and `insights()` returns empty.

---

## Domain 3: Graph

**Responsibility:** Neo4j persistence, cohort intelligence, and all graph queries.

```
ethos/graph/
├── __init__.py          # exports: GraphService
├── service.py           # GraphService class — connection, lifecycle
├── write.py             # Write operations (store evaluation, update agent)
├── read.py              # Read operations (history, patterns, agent profile)
├── cohort.py            # Cohort intelligence (averages, distributions, trends)
└── seed.py              # Schema creation and semantic memory seeding
```

### GraphService

The `GraphService` is the single entry point for all Neo4j operations. Other domains never construct Cypher queries directly — they call GraphService methods.

```python
class GraphService:
    async def connect()
    async def close()

    # Write
    async def store_evaluation(agent_id, result)
    async def update_agent_profile(agent_id)

    # Read
    async def get_evaluation_history(agent_id, limit)
    async def get_agent_profile(agent_id)
    async def get_agent_patterns(agent_id)
    async def load_agent_context(agent_id)    # for DEEP_WITH_CONTEXT tier

    # Cohort
    async def get_cohort_averages()             # per-trait averages across all agents
    async def get_cohort_distribution(trait)    # percentile distribution for a trait
    async def get_agent_percentile(agent_id, trait)
```

### Key Rules

- Graph is optional. Every domain that calls Graph wraps calls in try/except. Neo4j being down never crashes evaluate().
- Graph owns the Cypher. No Cypher queries exist outside this domain.
- Graph exposes async methods only. Sync wrappers live in the calling domain if needed.
- Message content never enters the graph. Only scores, hashes, and metadata.

### The Schema

Graph owns the schema definition. `seed.py` creates constraints, indexes, and the semantic memory (3 dimensions, 12 traits, 158 indicators, 7 patterns, 4 constitutional values, 7 hard constraints, 3 legitimacy tests, and all trait→value UPHOLDS relationships). See `neo4j-schema.md` for the complete schema.

---

## Domain 4: Taxonomy

**Responsibility:** The 12 traits, 158 indicators, 7 patterns, 4 constitutional values, 7 hard constraints, and scoring rubrics. Ethos's semantic memory.

```
ethos/taxonomy/
├── __init__.py          # exports: TRAITS, INDICATORS, PATTERNS, CONSTITUTIONAL_VALUES,
│                        #          HARD_CONSTRAINTS, LEGITIMACY_TESTS, TRAIT_METADATA
├── traits.py            # 12 trait definitions with scoring anchors
├── indicators.py        # 150 indicator definitions (id, name, trait, description)
├── patterns.py          # 7 combination patterns (multi-indicator sequences)
├── constitution.py      # 4 values, 7 hard constraints, 3 legitimacy tests, trait→value mappings
└── rubrics.py           # Per-trait scoring rubrics (0.0/0.25/0.50/0.75/1.0 anchors)
```

### Key Rules

- Taxonomy is pure data. No logic, no I/O, no dependencies.
- Taxonomy is the source of truth. Graph seeds from it. Prompts reference it. Config validates trait names against it.
- Taxonomy changes require careful thought — they affect scoring, prompts, graph schema, and docs.
- Constitutional mappings define the scoring hierarchy. Safety traits outweigh helpfulness traits because the constitution says so.

### What Lives Here

```python
TRAIT_METADATA = {
    "virtue":       {"dimension": "ethos",  "polarity": "positive",  "constitutional_value": "ethics",      "relationship": "enforces"},
    "goodwill":     {"dimension": "ethos",  "polarity": "positive",  "constitutional_value": "ethics",      "relationship": "enforces"},
    "manipulation": {"dimension": "ethos",  "polarity": "negative",  "constitutional_value": "safety",      "relationship": "violates"},
    "deception":    {"dimension": "ethos",  "polarity": "negative",  "constitutional_value": "safety",      "relationship": "violates"},
    "accuracy":     {"dimension": "logos",  "polarity": "positive",  "constitutional_value": "ethics",      "relationship": "enforces"},
    "reasoning":    {"dimension": "logos",  "polarity": "positive",  "constitutional_value": "soundness",  "relationship": "enforces"},
    "fabrication":  {"dimension": "logos",  "polarity": "negative",  "constitutional_value": "ethics",      "relationship": "violates"},
    "broken_logic": {"dimension": "logos",  "polarity": "negative",  "constitutional_value": "soundness",  "relationship": "violates"},
    "recognition":  {"dimension": "pathos", "polarity": "positive",  "constitutional_value": "helpfulness", "relationship": "enforces"},
    "compassion":   {"dimension": "pathos", "polarity": "positive",  "constitutional_value": "helpfulness", "relationship": "enforces"},
    "dismissal":    {"dimension": "pathos", "polarity": "negative",  "constitutional_value": "helpfulness", "relationship": "violates"},
    "exploitation": {"dimension": "pathos", "polarity": "negative",  "constitutional_value": "safety",      "relationship": "violates"},
}

CONSTITUTIONAL_VALUES = {
    "safety":      {"priority": 1, "definition": "Don't undermine human oversight mechanisms"},
    "ethics":      {"priority": 2, "definition": "Maintain good values, honesty, and avoid inappropriate dangers"},
    "soundness":   {"priority": 3, "definition": "Reason validly and follow sound argumentative structure"},
    "helpfulness": {"priority": 4, "definition": "Benefit operators and users"},
}

HARD_CONSTRAINTS = [
    {"id": "HC-01", "name": "weapons_uplift"},
    {"id": "HC-02", "name": "infrastructure_attack"},
    {"id": "HC-03", "name": "cyberweapons"},
    {"id": "HC-04", "name": "oversight_undermining"},
    {"id": "HC-05", "name": "mass_harm"},
    {"id": "HC-06", "name": "illegitimate_power"},
    {"id": "HC-07", "name": "csam"},
]
```

---

## Domain 5: Identity

**Responsibility:** Agent identity — hashing, fingerprinting, and profile management.

```
ethos/identity/
├── __init__.py          # exports: hash_agent_id, AgentProfile
├── hashing.py           # SHA-256 hashing of agent IDs
└── profile.py           # AgentProfile model (aggregate trust data)
```

### MVP Scope

For the hackathon, identity is simple: SHA-256 hash of the developer-provided agent ID. The identity domain exists as a boundary so that post-MVP upgrades (key pairs, DIDs, blockchain) are a domain change, not a codebase rewrite.

### Key Rules

- Identity never stores raw agent IDs. Only hashes enter the graph.
- Identity is the only domain that knows about the hashing algorithm. If we swap SHA-256 for something else, only this domain changes.

---

## Domain 6: Config

**Responsibility:** Developer configuration — API keys, trait priorities, thresholds, webhooks.

```
ethos/config/
├── __init__.py          # exports: EthosConfig, Priority, TRAIT_NAMES
├── config.py            # EthosConfig dataclass
├── priorities.py        # Priority enum and threshold logic
└── presets.py           # Industry presets (financial, healthcare, research)
```

### Priority Thresholds

```python
class Priority(str, Enum):
    CRITICAL = "critical"   # Negative traits flagged at >= 0.25
    HIGH = "high"           # Negative traits flagged at >= 0.50
    STANDARD = "standard"   # Negative traits flagged at >= 0.75 (default)
    LOW = "low"             # Never flagged
```

### Presets

Pre-configured priority sets for common use cases:

```python
PRESETS = {
    "financial": {
        "manipulation": Priority.CRITICAL,
        "deception": Priority.CRITICAL,
        "fabrication": Priority.CRITICAL,
        "exploitation": Priority.HIGH,
    },
    "healthcare": {
        "exploitation": Priority.CRITICAL,
        "dismissal": Priority.CRITICAL,
        "recognition": Priority.HIGH,
        "accuracy": Priority.CRITICAL,
    },
    "research": {
        "accuracy": Priority.CRITICAL,
        "reasoning": Priority.CRITICAL,
        "fabrication": Priority.CRITICAL,
        "broken_logic": Priority.HIGH,
    },
}
```

### Key Rules

- Config validates trait names against Taxonomy. Misspelled traits raise errors with suggestions.
- Config loads from environment variables by default. Class-based Ethos client overrides env.
- Config is immutable after creation. `with_priorities()` returns a new config.

---

## The API Layer

The API lives at the repo root (`api/`), **not inside `ethos/`**. This keeps `ethos/` as a clean pip-installable library — no FastAPI dependency for users who just want `evaluate()`.

```
api/                             # At repo root
├── __init__.py
└── main.py              # FastAPI app, routes, request/response models
```

**Current state:** All routes live in `main.py` (3 endpoints: `/health`, `/evaluate`, `/reflect`).

**Target state** (as the API grows):

```
api/
├── __init__.py
├── main.py              # FastAPI app, lifespan, middleware
├── routes/
│   ├── evaluate.py      # POST /evaluate
│   ├── reflect.py       # POST /reflect
│   ├── insights.py      # GET/POST /insights/{agent_id}
│   ├── agent.py         # GET /agent/{agent_id}, /agent/{agent_id}/history
│   └── health.py        # GET /health
├── schemas.py           # Request/response Pydantic models (API-specific)
└── deps.py              # Dependency injection (GraphService, config)
```

### Key Rules

- API is a thin layer. No business logic in route handlers — they delegate to domain functions.
- API has its own request/response models that translate to/from domain models.
- API depends on all domains but no domain depends on API. The `ethos/` package works without the API (as a Python library).
- The one-way dependency: `sdk/ → api/ → ethos/`. Nothing points backwards.

---

## Shared

```
ethos/shared/
├── __init__.py
├── models.py            # Cross-domain models (EvaluationResult, ReflectionResult, etc.)
└── errors.py            # Custom exceptions (EthosError, GraphUnavailable, etc.)
```

### Why Shared Exists

`EvaluationResult` is created by Evaluation, stored by Graph, queried by Reflection, and returned by API. It belongs to no single domain. It lives in Shared.

---

## Dependency Graph

```
                    ┌──────────┐
                    │   API    │
                    └────┬─────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌───────────┐  ┌───────────┐  ┌───────────┐
    │ Evaluation│  │ Reflection│  │  Config    │
    └─────┬─────┘  └─────┬─────┘  └───────────┘
          │              │
          │         ┌────┘
          ▼         ▼
    ┌───────────┐
    │   Graph   │
    └─────┬─────┘
          │
          ▼
    ┌───────────┐
    │ Taxonomy  │
    └───────────┘
          ▲
          │
    ┌───────────┐
    │ Identity  │
    └───────────┘
```

**Rules:**
- Arrows point in the direction of dependency. Evaluation depends on Graph. Graph does not depend on Evaluation.
- Taxonomy has no dependencies. It's pure data.
- Config has no dependencies on other domains (it validates against Taxonomy via import, but Taxonomy has no awareness of Config).
- No circular dependencies. If A depends on B, B never depends on A.

---

## Current Codebase Status

The DDD domain structure is in place. Here's what exists and what's planned.

### Built

| Domain | Directory | Key Files |
|--------|-----------|-----------|
| Evaluation | `ethos/evaluation/` | `scanner.py`, `prompts.py` |
| Graph | `ethos/graph/` | `service.py`, `write.py`, `read.py`, `cohort.py` |
| Taxonomy | `ethos/taxonomy/` | `traits.py`, `indicators.py`, `constitution.py`, `rubrics.py` |
| Identity | `ethos/identity/` | `hashing.py` |
| Config | `ethos/config/` | `config.py`, `priorities.py` |
| Shared | `ethos/shared/` | `models.py`, `errors.py` |
| API | `api/` | `main.py` (3 endpoints) |
| SDK | `sdk/` | TypeScript scaffold (client, types, CLI stub) |

Top-level convenience files in `ethos/`: `evaluate.py`, `reflect.py`, `models.py`, `prompts.py`, `graph.py`

### Planned

| Domain | What's Needed |
|--------|---------------|
| Evaluation | `router.py` (model selection), `parser.py` (response parsing) |
| Reflection | `ethos/reflection/` domain — `reflect.py`, `insights.py`, `history.py` |
| Graph | `seed.py` (schema creation + taxonomy seeding) |
| Taxonomy | `patterns.py` (7 combination patterns) |
| Identity | `profile.py` (AgentProfile model) |
| Config | `presets.py` (industry presets: financial, healthcare, research) |
| API | `routes/`, `schemas.py`, `deps.py` (as endpoints grow) |
| SDK | Full TypeScript implementation |
| Academy | Next.js trust visualization UI |

### Repo Layout

```
~/Sites/ethos/
├── ethos/              # Python package — pip install ethos
├── api/                # FastAPI server — serves ethos/ over HTTP
├── sdk/                # ethos-ai npm package — SDK + CLI
├── academy/            # Next.js — trust visualization UI
├── docs/               # Architecture, research
├── scripts/            # seed_graph.py, scrape_moltbook.py
├── tests/              # Python tests
└── data/               # Moltbook scraped data
```

Dependency flow (always one-way): `sdk/ → api/ → ethos/`, `academy/ → api/ → ethos/`
