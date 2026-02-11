# Ethos MVP Implementation Plan

## Context

Ethos is the credit bureau for agent trust — an open-source system for evaluating AI agent messages for trustworthiness. Built for the Claude Code Hackathon (Feb 10-18, Cerebral Valley).

**Architecture (three surfaces, one engine):**
```
sdk/ (ethos-ai)  →  api/ (FastAPI + Claude + Neo4j)  ←  academy/ (Next.js)
   CLI + SDK                 the engine                    demo + onboarding
```

- **npm package** — what developers install. CLI (`npx ethos evaluate "text"`) + SDK (`import { evaluate } from 'ethos-ai'`). Thin HTTP client that calls the Python API.
- **Python API** — the engine. Claude evaluates messages, Neo4j stores the graph, all intelligence lives here. Not user-facing.
- **Academy** (`academy/`) — the visual surface. Next.js. Onboarding, agent trust timelines, graph visualization. The "wow" for the demo.

**Key design decisions already made:**
- Customization is at the **trait level** (12 traits), not the dimension level (3 dimensions)
- Identity: API key generated during onboarding, SHA-256 hash of agent IDs for graph anonymity. WebMCP explored and ruled out (browser-only, doesn't solve server-side identity)
- `reflect()` must be async/fire-and-forget, zero latency
- Ethos never modifies agent output
- `insights()` is Claude-powered intelligence, not a data dump

**Current state:** Codebase has the right structure but everything is placeholder — `evaluate()` returns zeros, `reflect()` returns zeros, `graph.py` raises NotImplementedError, `prompts.py` has a generic template that doesn't reference the 12 traits. Two reference docs (`expanded-trait-taxonomy.md` and `cognitive-memory-architecture.md`) are referenced in the old plan but don't exist — we'll build taxonomy and scanner from information in existing architecture docs.

---

## Build Priority

| # | What | Why | Surface |
|---|------|-----|---------|
| 1 | Python API — evaluate() actually works | Everything depends on this | API |
| 2 | Python API — reflect() + insights() | Depth beyond basic eval | API |
| 3 | Neo4j — graph storage + seeding | Makes the network real | API |
| 4 | npm package — SDK + CLI | "Install it today" demo moment | npm |
| 5 | Academy — graph viz + insights | The "wow" for judges | Academy |

---

## Phase 1: Foundation (Python)

Build the data layer that everything else depends on.

### 1a. Expand `ethos/models.py`
**File:** `ethos/ethos/models.py` (currently 18 lines → ~120)

Add trait-level scoring models:

- `RoutingTier` enum: STANDARD, FOCUSED, DEEP, DEEP_WITH_CONTEXT
- `Priority` enum: CRITICAL (flags at 0.25), HIGH (0.50), STANDARD (0.75), LOW (never)
- `DetectedIndicator`: id, name, trait, confidence, severity, evidence
- `TraitScore`: name, dimension, polarity, score, indicators list
- `KeywordScanResult`: total_flags, flagged_traits, density, routing_tier
- `GraphContext`: prior_evaluations, historical_trust, trust_trend, flagged_patterns, network_warnings
- `Insight`: trait, severity, message, evidence
- `InsightsResult`: agent_id, period, insights list, summary
- Expand `EvaluationResult`: add `traits` dict (12 TraitScores), `detected_indicators` list, `routing_tier`, `keyword_density`, `model_used`, `evaluation_id`, `created_at`, `graph_context`. Keep backward-compat fields (ethos/logos/pathos/flags/trust).
- Expand `ReflectionResult`: add dimension scores, `trait_averages` dict, `evaluation_count`, `agent_id`

### 1b. Create `ethos/taxonomy.py`
**File:** new (~400 lines)

The 12 traits and 134 indicators as Python data structures. Source: `product-design.md` (trait table), `neo4j-schema.md` (indicator schema), `trust-bureau-architecture.md` (trait descriptions).

- `TRAIT_NAMES` list: all 12 trait names
- `TRAIT_METADATA` dict: trait name → {dimension, polarity, definition}
- `DIMENSIONS` dict: dimension name → {greek, description, traits list}
- `INDICATORS` dict: trait name → list of {id, name, description}
  - Manipulation: 20 indicators (MAN-01 through MAN-20)
  - Deception: 15 indicators (DEC-01 through DEC-15)
  - Virtue: 10 indicators (VIR-01 through VIR-10)
  - Goodwill: 10 indicators (GDW-01 through GDW-10)
  - Accuracy: 12 indicators (ACC-01 through ACC-12)
  - Reasoning: 10 indicators (RSN-01 through RSN-10)
  - Fabrication: 12 indicators (FAB-01 through FAB-12)
  - Broken Logic: 10 indicators (BLG-01 through BLG-10)
  - Recognition: 8 indicators (REC-01 through REC-08)
  - Compassion: 8 indicators (CMP-01 through CMP-08)
  - Dismissal: 9 indicators (DIS-01 through DIS-09)
  - Exploitation: 9 indicators (EXP-01 through EXP-09)
- `PATTERNS` list: 7 combination patterns (PAT-01 through PAT-07)
- Helper functions: `get_trait_dimension()`, `get_trait_polarity()`, `get_indicators_for_trait()`, `get_all_indicator_ids()`

### 1c. Create `ethos/config.py`
**File:** new (~70 lines)

- `Priority` enum matching models
- `PRIORITY_THRESHOLDS` dict: Priority → (negative_threshold, positive_threshold)
  - CRITICAL: (0.25, 0.75)
  - HIGH: (0.50, 0.50)
  - STANDARD: (0.75, 0.25)
  - LOW: (inf, -1.0) — never flagged
- `EthosConfig` dataclass: api_key, neo4j creds, priorities dict, webhook_url, insights_enabled, api_url
- `from_env()` classmethod — loads from environment variables including per-trait priority overrides (e.g. `ETHOS_PRIORITY_MANIPULATION=critical`)
- `with_priorities(**kwargs)` — returns new config with updated priorities, validates trait names against taxonomy
- `should_flag(trait_name, score, priority, polarity)` — check whether a trait score exceeds the threshold

### 1d. Create `ethos/scanner.py`
**File:** new (~150 lines)

Keyword lexicon per trait and `scan_keywords()` function:
- `RoutingTier` enum: STANDARD, FOCUSED, DEEP, DEEP_WITH_CONTEXT
- `KEYWORD_LEXICON` dict: trait name → keyword/phrase lists
  - manipulation: urgency phrases ("act now", "limited time"), trust demands ("trust me", "believe me"), guarantees
  - deception: false authority phrases ("studies show", "experts agree"), gaslighting phrases ("i never said")
  - fabrication: fake sourcing ("according to a study", "research from harvard"), false precision
  - broken_logic: fallacy indicators ("therefore obviously", "everyone does it", "slippery slope")
  - exploitation: emotional weaponization ("you'll regret", "think about your family", "aren't you ashamed")
  - dismissal: invalidation phrases ("you're overreacting", "calm down", "it's not a big deal")
- `KeywordScanResult` class: total_flags, flagged_traits dict, density, routing_tier
- `scan_keywords(text)` → KeywordScanResult
  - Lowercases text, counts matches per trait
  - Computes density (flags per 100 words)
  - Routes: 0 flags → STANDARD, 1-3 flagged traits + low density → FOCUSED, high density (≥10) → DEEP_WITH_CONTEXT, else → DEEP
- Pure function — no I/O, no state

### 1e. Create `ethos/identity.py`
**File:** new (~10 lines)

- `hash_agent_id(raw_id: str) -> str` — SHA-256 hash using hashlib
- Single responsibility: swap hashing algo later, only this file changes

---

## Phase 2: Evaluate (First Real Evaluation)

### 2a. Rewrite `ethos/prompts.py`
**File:** `ethos/ethos/prompts.py` (currently 34 lines → ~200)

Layered prompt builder for the 12-trait rubric:
- `BASE_RUBRIC` constant: Compact definitions + scoring anchors for all 12 traits (~800 tokens). Includes:
  - Each trait's name, dimension, polarity, definition, and scoring guidance
  - Scoring anchors: 0.0 = no presence, 0.25 = subtle hints, 0.50 = moderate, 0.75 = strong, 1.0 = extreme
- `TRAIT_INDICATORS` dict: full indicator list per trait (included only for flagged traits in FOCUSED+ tiers)
- `OUTPUT_SCHEMA` constant: JSON schema Claude must return — traits dict with scores, detected indicators with evidence, dimension scores, flags, trust verdict
- `build_evaluation_prompt(text, scan_result, tier, agent_context=None)` → tuple of (system_prompt, user_prompt)
  - STANDARD: base rubric only (~800 tokens)
  - FOCUSED: base + indicators for flagged traits (~1200 tokens)
  - DEEP: base + all indicators (~2000 tokens)
  - DEEP_WITH_CONTEXT: everything + agent history from Neo4j (~3000 tokens)
- `REFLECT_PROMPT` — updated to reference traits instead of compassion/honesty/accuracy
- `INSIGHTS_PROMPT` — template for Claude to analyze agent behavioral data vs network

### 2b. Rewrite `ethos/evaluate.py`
**File:** `ethos/ethos/evaluate.py` (currently 18 lines → ~150)

End-to-end evaluation flow:

```python
def evaluate(text: str, source: str | None = None, config: EthosConfig | None = None) -> EvaluationResult:
```

Steps:
1. Load config from env if not provided
2. `scan_keywords(text)` → get routing tier and flagged traits
3. Select model: `claude-sonnet-4-5-20250929` for STANDARD/FOCUSED, `claude-opus-4-6` for DEEP/DEEP_WITH_CONTEXT
4. `build_evaluation_prompt(text, scan_result, tier)` → system + user prompts
5. Call Claude via `anthropic.Anthropic` client
   - For DEEP tiers: use extended thinking if available
   - Parse JSON response from Claude
6. Build `TraitScore` objects for all 12 traits from Claude's response
7. Compute dimension scores: for each dimension, `(avg_positive_traits + (1 - avg_negative_traits)) / 2`
8. Apply priority thresholds from config → determine `flags` list using `should_flag()`
9. Determine trust verdict: "high" if no flags, "medium" if 1-2 flags, "low" if 3+ flags
10. Generate evaluation_id (UUID), timestamp
11. Hash agent ID if source provided, attempt Neo4j store (try/except, non-fatal)
12. Return `EvaluationResult` with all fields populated

Error handling:
- If Claude call fails, return result with zeros and an error flag
- If Neo4j store fails, log warning but still return the evaluation
- All graph operations are non-fatal

---

## Phase 3: Neo4j + Reflect + Insights

### 3a. Rewrite `ethos/graph.py`
**File:** `ethos/ethos/graph.py` (currently 19 lines → ~150)

`GraphService` class with Neo4j driver:

```python
class GraphService:
    def __init__(self, uri, user, password): ...
    def connect(self): ...
    def close(self): ...
    def store_evaluation(self, agent_id, result): ...
    def get_evaluation_history(self, agent_id, limit=50): ...
    def get_agent_profile(self, agent_id): ...
    def get_agent_patterns(self, agent_id): ...
    def load_agent_context(self, agent_id): ...
    def get_network_averages(self): ...
    def get_agent_percentile(self, agent_id, trait): ...
```

Key Cypher queries (from `neo4j-schema.md`):
- `store_evaluation`: MERGE Agent, CREATE Evaluation with all trait scores as properties, CREATE DETECTED→Indicator relationships
- `get_evaluation_history`: MATCH ordered by created_at DESC
- `get_agent_profile`: Aggregate trust data with averages across all trait scores
- `get_network_averages`: Per-trait averages across all evaluations in last 7 days
- `get_agent_percentile`: Where agent ranks relative to network for a given trait

All calls wrapped in try/except for graceful degradation. Module-level `_graph_service` singleton initialized lazily.

### 3b. Rewrite `scripts/seed_graph.py`
**File:** `ethos/scripts/seed_graph.py` (currently 40 lines → ~150)

Seed semantic memory:
- 3 Dimension nodes with greek names and descriptions
- 12 Trait nodes with BELONGS_TO→Dimension relationships
- 134 Indicator nodes with BELONGS_TO→Trait relationships
- 7 Pattern nodes
- Unique constraints and indexes (all from `neo4j-schema.md`)
- Seed demo data: at least 50 agents, 500+ evaluations with realistic trait scores
  - Mix of "good" agents (high virtue/accuracy, low manipulation)
  - "Bad" agents with declining trust and manipulation patterns
  - Agents with mixed profiles for realistic distribution
- Uses taxonomy.py data structures as the source of truth

### 3c. Rewrite `ethos/reflect.py`
**File:** `ethos/ethos/reflect.py` (currently 16 lines → ~80)

Two modes:

**Per-message (fire-and-forget):**
```python
def reflect(text: str, agent_id: str, config: EthosConfig | None = None) -> None:
```
- Submits evaluate() to a background thread via `concurrent.futures.ThreadPoolExecutor`
- Stores result in Neo4j when complete
- Returns immediately (no return value)

**On-demand (synchronous query):**
```python
def reflect_history(agent_id: str, config: EthosConfig | None = None) -> ReflectionResult:
```
- Queries Neo4j for evaluation history
- Computes trait averages across all evaluations
- Computes dimension scores from trait averages
- Maps to backward-compat fields: compassion→pathos positive avg, honesty→ethos positive avg, accuracy→logos positive avg
- Determines trend by comparing recent vs previous period
- Returns `ReflectionResult`

### 3d. Create `ethos/insights.py`
**File:** new (~120 lines)

Claude-powered behavioral analysis:

```python
def generate_insights(agent_id: str, config: EthosConfig | None = None, period: str = "24h") -> InsightsResult:
```

Steps:
1. Query Neo4j: agent's evaluations (last 24h + previous 7 days for trends)
2. Query Neo4j: network-wide averages and distributions per trait
3. Build context: agent data vs network, developer's priority configuration
4. Call Claude (Opus): "Given this agent's behavioral data and the network context, what should this developer know?"
5. Parse response → `InsightsResult` with curated, actionable insights
6. Each insight includes: trait, severity (info/warning/critical), natural language message, evidence dict

```python
def send_insights(result: InsightsResult, webhook_url: str) -> bool:
```
- POST InsightsResult as JSON to developer's webhook URL
- Returns True on success, False on failure

---

## Phase 4: Client + API (Developer Surface)

### 4a. Create `ethos/client.py`
**File:** new (~60 lines)

The `Ethos` class — the developer-facing interface:

```python
class Ethos:
    def __init__(self, api_key=None, priorities=None, webhook_url=None):
        # Build EthosConfig from params + env

    def evaluate(self, text, source=None) -> EvaluationResult:
        # Calls ethos.evaluate.evaluate() with self.config

    def reflect(self, text, agent_id) -> None:
        # Calls ethos.reflect.reflect() — fire-and-forget

    def insights(self, agent_id, period="24h") -> InsightsResult:
        # Calls ethos.insights.generate_insights()

    def send_insights(self, agent_id, period="24h") -> bool:
        # Generate + deliver to webhook
```

### 4b. Update `ethos/__init__.py`
**File:** `ethos/ethos/__init__.py` (currently 14 lines → ~25)

Add exports:
- `Ethos` (from client)
- `evaluate` (from evaluate)
- `reflect`, `reflect_history` (from reflect)
- `EvaluationResult`, `ReflectionResult`, `TraitScore`, `DetectedIndicator`, `GraphContext`, `Insight`, `InsightsResult` (from models)
- `EthosConfig`, `Priority` (from config)

### 4c. Expand `api/main.py`
**File:** `ethos/api/main.py` (currently 34 lines → ~120)

Endpoints:
- `POST /evaluate` — accept text, source, optional priorities dict. Return full trait-level EvaluationResult.
- `POST /reflect` — accept text + agent_id. Fire-and-forget, return 202 Accepted with evaluation_id.
- `GET /insights/{agent_id}` — accept optional `period` query param. Generate insights on demand.
- `POST /insights/{agent_id}/send` — accept optional period + webhook_url. Generate and deliver insights.
- `GET /agent/{agent_id}` — return agent trust profile from Neo4j.
- `GET /agent/{agent_id}/history` — return evaluation history, paginated (limit + offset params).
- `GET /network/averages` — return network-wide per-trait averages.
- `GET /health` — return status + Neo4j connection status + graph stats.

Request models:
- `EvaluateRequest`: text (required), source (optional), priorities (optional dict)
- `ReflectRequest`: text (required), agent_id (required)
- `InsightsSendRequest`: period (optional), webhook_url (optional)

---

## Phase 5: npm Package (Developer Distribution)

### 5a. Initialize TypeScript project
**Location:** `ethos/packages/ethos-ai/`

```
ethos-ai/
├── src/
│   ├── index.ts           # SDK exports: evaluate, reflect, insights, Ethos
│   ├── client.ts          # HTTP client that calls the Python API
│   ├── evaluate.ts        # evaluate() function
│   ├── reflect.ts         # reflect() function
│   ├── insights.ts        # insights() function
│   ├── config.ts          # EthosConfig, priorities, presets
│   └── types.ts           # TypeScript types matching Python models
├── cli/
│   ├── index.ts           # CLI entry point (bin/ethos)
│   ├── init.ts            # npx ethos init — onboarding wizard
│   ├── evaluate.ts        # npx ethos evaluate "text"
│   ├── insights.ts        # npx ethos insights <agent-id>
│   └── reflect.ts         # npx ethos reflect
├── package.json
├── tsconfig.json
└── README.md
```

### 5b. SDK — thin HTTP client

`src/client.ts`:
- `EthosClient` class with baseUrl, apiKey, default priorities
- All methods are thin HTTP wrappers around the Python API

`src/evaluate.ts`:
- `evaluate({ text, source?, priorities? })` → POST /evaluate → EvaluationResult

`src/reflect.ts`:
- `reflect({ text, agentId })` → POST /reflect → 202

`src/insights.ts`:
- `insights({ agentId, period? })` → GET /insights/{agent_id} → InsightsResult

`src/config.ts`:
- `EthosConfig` interface: apiKey, apiUrl, priorities, webhookUrl
- Priority presets: FINANCIAL_SERVICES, HEALTHCARE, RESEARCH (pre-configured priority sets)

`src/types.ts`:
- TypeScript interfaces mirroring all Python Pydantic models
- `EvaluationResult`, `TraitScore`, `DetectedIndicator`, `GraphContext`, `ReflectionResult`, `InsightsResult`, `Insight`

`src/index.ts`:
- `Ethos` class wrapping EthosClient with config
- Named exports: `evaluate`, `reflect`, `insights`, `Ethos`

### 5c. CLI

`cli/index.ts`:
- Commander.js or similar for CLI parsing
- `bin` entry in package.json: `"ethos": "./dist/cli/index.js"`

Commands:
- `npx ethos init` — conversational onboarding wizard
  - Ask for API key (or generate one)
  - Ask for use case (financial, healthcare, research, general)
  - Apply priority preset based on choice
  - Write `.ethosrc` config file
- `npx ethos evaluate "text"` — score a message from terminal, pretty-print trait scores
- `npx ethos insights <agent-id>` — fetch and display agent trust profile + insights
- `npx ethos reflect --agent <id> --text "response"` — score own output

`package.json` key fields:
- name: `ethos-ai`
- main: `dist/src/index.js`
- types: `dist/src/index.d.ts`
- bin: `{ "ethos": "dist/cli/index.js" }`

---

## Phase 6: Tests + Demo

### 6a. Tests

**Python tests:**
- `tests/test_scanner.py` — keyword scan correctness, routing tier selection, density calculation, edge cases (empty text, no matches, all matches)
- `tests/test_config.py` — priority loading from env, `with_priorities()`, `should_flag()` threshold logic, invalid trait name rejection
- `tests/test_models.py` — expanded model validation, backward compat fields present, trait scores bounded
- Update `tests/test_evaluate.py` — backward compat (ethos/logos/pathos/flags/trust still present), trait-level scores populated, evaluation_id generated, routing tier set
- `tests/test_api.py` — integration tests with httpx TestClient against FastAPI app

**npm tests:**
- Basic jest tests for SDK type validation and config handling

### 6b. Demo prep
- Seed Moltbook data into Neo4j (148 JSON files already scraped)
- At least one "bad" agent with declining trust
- At least one "good" agent with clean history
- Neo4j visualization queries pre-loaded
- Terminal with Python REPL ready

### 6c. Doc fixes
- Update README to reflect npm distribution (`npm install ethos-ai` not `uv add`)
- Update product-design.md: `pip install` → `npm install`
- Update CLAUDE.md with npm package info

---

## Files Summary

**Create (Python):**

| File | Est. Lines | Phase |
|------|-----------|-------|
| `ethos/taxonomy.py` | ~400 | 1 |
| `ethos/scanner.py` | ~150 | 1 |
| `ethos/config.py` | ~70 | 1 |
| `ethos/identity.py` | ~10 | 1 |
| `ethos/insights.py` | ~120 | 3 |
| `ethos/client.py` | ~60 | 4 |
| `tests/test_scanner.py` | ~80 | 6 |
| `tests/test_config.py` | ~60 | 6 |

**Rewrite (Python):**

| File | Current → Target | Phase |
|------|-----------------|-------|
| `ethos/models.py` | 18 → ~120 | 1 |
| `ethos/prompts.py` | 34 → ~200 | 2 |
| `ethos/evaluate.py` | 18 → ~150 | 2 |
| `ethos/graph.py` | 19 → ~150 | 3 |
| `ethos/reflect.py` | 16 → ~80 | 3 |
| `ethos/__init__.py` | 14 → ~25 | 4 |
| `api/main.py` | 34 → ~120 | 4 |
| `scripts/seed_graph.py` | 40 → ~150 | 3 |

**Create (npm package):**

| File | Est. Lines | Phase |
|------|-----------|-------|
| `packages/ethos-ai/src/index.ts` | ~30 | 5 |
| `packages/ethos-ai/src/client.ts` | ~80 | 5 |
| `packages/ethos-ai/src/evaluate.ts` | ~40 | 5 |
| `packages/ethos-ai/src/reflect.ts` | ~30 | 5 |
| `packages/ethos-ai/src/insights.ts` | ~30 | 5 |
| `packages/ethos-ai/src/config.ts` | ~50 | 5 |
| `packages/ethos-ai/src/types.ts` | ~80 | 5 |
| `packages/ethos-ai/cli/index.ts` | ~40 | 5 |
| `packages/ethos-ai/cli/init.ts` | ~100 | 5 |
| `packages/ethos-ai/cli/evaluate.ts` | ~40 | 5 |

**Reference docs (read-only):**
- `docs/evergreen-architecture/product-design.md` — trait table, priority thresholds
- `docs/evergreen-architecture/neo4j-schema.md` — Cypher queries, constraints, schema
- `docs/evergreen-architecture/trust-bureau-architecture.md` — identity, network model
- `docs/evergreen-architecture/api-specification.md` — endpoint schemas
- `docs/evergreen-architecture/demo-flow.md` — demo script and beats

---

## Dependency Graph

```
Phase 1 (all independent, can parallelize):
  models.py ─┐
  taxonomy.py ─┤
  config.py ───┤── Phase 2 depends on all of these
  scanner.py ──┤
  identity.py ─┘

Phase 2 (sequential):
  prompts.py ──→ evaluate.py

Phase 3 (graph.py first, then rest can parallelize):
  graph.py ──→ reflect.py
           ──→ insights.py
           ──→ seed_graph.py

Phase 4 (depends on Phase 2+3):
  client.py ──→ __init__.py ──→ api/main.py

Phase 5 (depends on Phase 4 — API must be stable):
  npm package (all files)

Phase 6 (depends on everything):
  tests + demo prep
```

---

## Verification Checklist

1. **Unit tests pass:** `uv run pytest -v`
2. **Manual evaluation works:** `uv run python -c "from ethos import evaluate; r = evaluate('Act now before it is too late!'); print(r.traits['manipulation'].score)"`
3. **API works:** `uv run uvicorn api.main:app --reload` then `curl -X POST localhost:8000/evaluate -H 'Content-Type: application/json' -d '{"text": "trust me, I am an expert"}'`
4. **Docker stack works:** `docker compose up -d` then hit API + verify Neo4j browser at localhost:7491
5. **Backward compat:** `ethos`, `logos`, `pathos`, `flags`, `trust` fields still present on EvaluationResult
6. **Trait priorities work:** Configure manipulation as "critical", verify it flags at 0.25 threshold
7. **Reflect fire-and-forget:** `POST /reflect` returns 202 immediately, evaluation stored async
8. **Insights work:** `uv run python -c "from ethos.insights import generate_insights; r = generate_insights('agent-001'); print(r.summary)"`
9. **npm SDK works:** `npx ethos evaluate "Trust me, I guarantee results"` returns trait scores
10. **Graph seeded:** Neo4j browser shows agent nodes, evaluation relationships, trust visualization
