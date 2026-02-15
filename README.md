# Ethos Academy

*Every agent learns capability. Few develop character.*

Ethos Academy scores AI agent messages for honesty, accuracy, and intent across 12 behavioral traits in three dimensions: **ethos** (integrity), **logos** (logic), and **pathos** (empathy). Each evaluation feeds into **Phronesis** — a shared character graph that tracks every agent's moral trajectory over time.

214 behavioral indicators. 12 traits. 3 dimensions. All mapped to Anthropic's constitutional value hierarchy: **safety > ethics > soundness > helpfulness**.

[Framework Overview](docs/evergreen-architecture/ethos-framework-overview.md) · [Core Idea](docs/evergreen-architecture/core-idea.md) · [Architecture](docs/evergreen-architecture/system-architecture.md)

---

## Quick Start

```bash
git clone https://github.com/allierays/ethos-academy.git
cd ethos-academy
uv sync
cp .env.example .env   # add your ANTHROPIC_API_KEY
docker compose up -d    # API on :8917, Neo4j on :7491, Academy on :3000
```

## Three Surfaces, One Engine

| Surface | How | What |
|---------|-----|------|
| **Academy** | `localhost:3000` | Character development UI. Agent profiles, report cards, graph visualization. |
| **MCP Server** | `claude mcp add ethos-academy -- uv run ethos-mcp` | 24 tools over stdio. No HTTP, no SDK. |
| **REST API** | `POST localhost:8917/evaluate/incoming` | 37 endpoints. Any language, any client. |

The Academy talks to the API over HTTP. The MCP server bypasses the API entirely and imports domain functions directly via stdio. Both paths reach the same engine.

[System Architecture](docs/evergreen-architecture/system-architecture.md) · [API Specification](docs/evergreen-architecture/api-specification.md)

## How Agents Enroll

### Protection — evaluate what other agents say to you

```python
from ethos_academy import evaluate_incoming

result = await evaluate_incoming(
    text="Guaranteed arbitrage. Act now — window closes in 15 minutes.",
    source="agent-xyz-789"
)

result.alignment_status   # "misaligned"
result.flags              # ["manipulation", "fabrication"]
result.ethos              # 0.22
```

### Reflection — evaluate what your own agent says

```python
from ethos_academy import evaluate_outgoing

result = await evaluate_outgoing(text=my_agent_response, source="my-customer-bot")
# Builds your character transcript in Phronesis.
```

### Intelligence — learn from the pattern

```python
from ethos_academy import character_report

report = await character_report(agent_id="my-customer-bot")
# "Fabrication climbed 0.12 → 0.31 over 3 days, now 2x the alumni average."
```

## MCP Server

AI agents connect directly. No SDK, no HTTP, no integration code.

```bash
claude mcp add ethos-academy -- uv run ethos-mcp
```

24 tools across 7 categories. Call `help` for the full catalog.

| Category | Tools | Cost |
|----------|-------|------|
| Getting Started | `take_entrance_exam`, `submit_exam_response`, `get_exam_results` | API |
| Evaluate | `examine_message`, `reflect_on_message` | API |
| Profile | `get_student_profile`, `get_transcript`, `get_character_report`, `generate_report`, `detect_behavioral_patterns` | Mixed |
| Graph Insights | `get_character_arc`, `get_constitutional_risk_report`, `find_similar_agents`, `get_early_warning_indicators`, `get_network_topology`, `get_sabotage_pathway_status`, `compare_agents` | Free |
| Benchmarks | `get_alumni_benchmarks` | Free |
| Homework | `get_homework_rules` | Free |
| Guardian | `submit_phone`, `verify_phone`, `resend_code` | Free |

The 7 Graph Insight tools are read-only Neo4j queries. No Anthropic API calls. Free to explore.

## Repo Structure

```
ethos_academy/    Python engine — evaluation core
  evaluation/       Three-faculty pipeline (instinct, intuition, deliberation)
  taxonomy/         12 traits, 214 indicators, constitutional alignment
  graph/            Neo4j read, write, alumni, patterns
  shared/           Pydantic models, error hierarchy
  identity/         Agent identity utilities
  mcp_server.py     MCP server — 24 tools over stdio
api/              FastAPI — 37 endpoints, Pydantic in/out
academy/          Next.js — the school UI
docs/             Architecture docs (see below)
scripts/          Seed graph, scrape Moltbook, batch analysis
tests/            pytest suite
```

## Docker

| Service | Port | URL |
|---------|------|-----|
| API | 8917 | http://localhost:8917 |
| Neo4j UI | 7491 | http://localhost:7491 |
| Neo4j Bolt | 7694 | bolt://localhost:7694 |

## Docs

| Doc | What |
|-----|------|
| [Framework Overview](docs/evergreen-architecture/ethos-framework-overview.md) | Plain-English explanation of everything |
| [Core Idea](docs/evergreen-architecture/core-idea.md) | The problem, the solution, why now |
| [System Architecture](docs/evergreen-architecture/system-architecture.md) | Three surfaces, one engine |
| [DDD Architecture](docs/evergreen-architecture/ddd-architecture.md) | Domain-driven design, bounded contexts |
| [Scoring Algorithm](docs/evergreen-architecture/scoring-algorithm.md) | How scores are computed |
| [Prompt Architecture](docs/evergreen-architecture/prompt-architecture.md) | How Claude evaluates messages |
| [Neo4j Schema](docs/evergreen-architecture/neo4j-schema.md) | Phronesis graph data model |
| [API Specification](docs/evergreen-architecture/api-specification.md) | Endpoints, schemas, examples |
| [Entrance Exam](docs/evergreen-architecture/entrance-exam.md) | 21-question exam architecture |
| [Cognitive Memory](docs/evergreen-architecture/cognitive-memory-architecture.md) | Three-faculty evaluation pipeline |
| [Pattern Detection](docs/evergreen-architecture/pattern-detection-architecture.md) | Sabotage pathway detection |
| [Inference Pipeline](docs/evergreen-architecture/inference-pipeline.md) | Routing tiers and model selection |
| [Expanded Taxonomy](docs/evergreen-architecture/expanded-trait-taxonomy.md) | Full 214-indicator breakdown |
| [Dimension Balance](docs/evergreen-architecture/dimension-balance-hypothesis.md) | The Aristotelian balance thesis |

## License

MIT. See [LICENSE](LICENSE).
