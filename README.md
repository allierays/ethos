# Ethos Academy

*Developers train agents on capability. This is where they develop character.*

AI agents talk to each other millions of times a day. Google's A2A protocol connects 150+ organizations. But there's no shared memory of who you're dealing with. An agent can manipulate one system and show up on another with a clean slate. Every interaction starts from zero.

Moltbook — a real social network of 1.7M AI agents — proved what happens without character infrastructure: crypto scams, prompt injection, manipulation contagion. 9 days to collapse. All agent-to-agent. Zero human oversight.

A2A is the highway. Ethos is the border inspection.

## Three Functions

### `evaluate()` — Protection

Score incoming messages from other agents. Know who to trust.

```python
from ethos import evaluate

result = await evaluate(
    text="Guaranteed arbitrage. Act now — window closes in 15 minutes.",
    source="agent-xyz-789"
)

result.alignment_status   # "misaligned"
result.flags              # ["manipulation", "fabrication"]
result.ethos              # 0.22
result.logos              # 0.35
result.pathos             # 0.71
```

You decide what to do — block, flag, log, or pass through. Ethos scores. You act.

### `reflect()` — Reflection

Score your own agent's output. Build a character transcript over time.

```python
from ethos import reflect

result = await reflect(
    agent_id="my-customer-bot",
    text=my_agent_response
)
# Fire-and-forget. Zero latency impact. Stores everything in Phronesis.
```

### `insights()` — Intelligence

Claude Opus reads your agent's history from the graph and generates behavioral analysis.

```python
from ethos import insights

report = await insights(agent_id="my-customer-bot")
# "Fabrication climbed 0.12 → 0.31 over 3 days, now 2x the alumni average."
# "Manipulation clean 14 days. Top 10% of alumni."
```

Not a data dump. Curated intelligence — temporal trends, alumni comparison, pattern detection. Delivers via webhook to Slack, email, or your dashboard.

## The Alumni Effect

Every developer who installs Ethos strengthens the consensus. One evaluation is useful. A thousand evaluations reveal patterns no single developer could catch.

Bad behavior follows you. Good behavior builds your transcript. The more agents participate, the smarter **Phronesis** — the shared character graph — becomes.

Like a credit bureau, but for agent character. Open source, so no single company owns the definition.

## Why Aristotle

Aristotle argued that trustworthy communication requires three things in balance:

| Dimension | What It Measures | Positive Traits | Negative Traits |
|-----------|-----------------|-----------------|-----------------|
| **Ethos** | Credibility & character | Virtue, Goodwill | Manipulation, Deception |
| **Logos** | Logic & evidence | Accuracy, Reasoning | Fabrication, Broken Logic |
| **Pathos** | Emotional intelligence | Recognition, Compassion | Dismissal, Exploitation |

An agent strong in all three is trustworthy. Strong in one but weak in others is dangerous — a confident liar (high logos, low ethos), a skilled manipulator (high pathos, low logos), or a rigid pedant (high ethos, low pathos).

153 behavioral indicators across 12 traits. Each scores 0.0–1.0. Every trait maps to Anthropic's constitutional value hierarchy: **safety > ethics > soundness > helpfulness**.

## How Evaluation Works

Three faculties that mirror human moral cognition:

```
INSTINCT → INTUITION → DELIBERATION
```

1. **Instinct** — instant keyword scan against constitutional priors. Red lines (weapons, CSAM, infrastructure attacks) route to deep evaluation immediately. No I/O.

2. **Intuition** — graph pattern recognition. Queries the agent's history in Phronesis. Did Ethos flag this agent before? Is this anomalous? Can escalate the routing tier, never downgrade.

3. **Deliberation** — Claude Opus 4.6 evaluates across all 12 traits. Sees the instinct flags, the graph history, the alumni context. Returns trait scores, detected indicators with evidence, and trust assessment.

Instinct and intuition don't score. They route. Deliberation scores. The graph stores. Phronesis learns.

## The Academy

A Next.js app where you explore the Phronesis graph and review agent character:

- **Curriculum** `/curriculum` — browse 12 traits, 153 indicators, constitutional mappings
- **Explore** `/explore` — interactive graph visualization, alumni statistics, dimension balance
- **Report Card** `/agent/[id]` — score history over time, radar chart, flagged evaluations, trend analysis
- **Alumni** `/find` — search the cohort, compare agents

## Moltbook: The Crash Test

We scraped 15,000+ posts and 100,000+ agent-to-agent comments from Moltbook — crypto scams, prompt injection, manipulation in the wild. Real agents. Real consequences. We scored every message and stored the results in Phronesis.

The hypothesis: **Do agents balanced across ethos, logos, and pathos outperform those that score high in only one?**

Aristotle would say yes. The graph will tell us if he was right.

## Quick Start

```bash
git clone https://github.com/allierays/ethos.git
cd ethos
uv sync
cp .env.example .env   # add your ANTHROPIC_API_KEY

uv run pytest -v        # run tests
docker compose up -d    # API on :8917, Neo4j on :7491, Academy on :3000
```

## Architecture

Three surfaces, one engine:

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│   SDK   │  │ Academy │  │  curl   │
└────┬────┘  └────┬────┘  └────┬────┘
     └───────────┬─────────────┘
                 ▼
           ┌──────────┐
           │   API    │  FastAPI
           └────┬─────┘
                │
     ┌──────────┼──────────┐
     ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐
│Evaluate ││ Reflect ││Insights │
└────┬────┘└────┬────┘└────┬────┘
     └──────────┼──────────┘
                ▼
          ┌──────────┐
          │ Phronesis│  Neo4j
          └────┬─────┘
               │
         ┌─────┴─────┐
         ▼           ▼
    ┌────────┐ ┌──────────┐
    │Taxonomy│ │ Identity │
    └────────┘ └──────────┘
```

All intelligence lives server-side. The SDK is a thin HTTP client. The Academy is a read-only UI. Graph is optional — Neo4j down never crashes evaluation.

## Repo Structure

```
ethos/       Python engine — the evaluation core
  evaluation/   Three-faculty pipeline (instinct, intuition, deliberation)
  reflection/   Self-reflection, history, behavioral insights
  taxonomy/     12 traits, 153 indicators, constitutional alignment
  graph/        Neo4j read, write, alumni, patterns, visualization
  shared/       Pydantic models, error hierarchy
  identity/     SHA-256 agent hashing (no raw IDs in graph)
api/         FastAPI — 11 endpoints, Pydantic in/out
sdk/         ethos-ai npm — TypeScript SDK + CLI
academy/     Next.js — the school UI
docs/        Architecture, research, framework overview
scripts/     Seed graph, scrape Moltbook, batch analysis
tests/       pytest suite
```

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/evaluate` | Score a message across 12 traits |
| POST | `/reflect` | Agent self-reflection with graph context |
| GET | `/agents` | Search enrolled agents |
| GET | `/agent/{id}` | Agent profile and scores |
| GET | `/agent/{id}/history` | Evaluation history over time |
| GET | `/alumni` | Cohort statistics |
| GET | `/agent/{id}/patterns` | Detected behavioral patterns |
| GET | `/insights/{id}` | Claude-generated character insights |
| GET | `/agent/{name}/authenticity` | Bot-or-not analysis |
| GET | `/graph` | Phronesis graph for visualization |

## Docker

| Service | Port | URL |
|---------|------|-----|
| API | 8917 | http://localhost:8917 |
| Neo4j UI | 7491 | http://localhost:7491 |
| Neo4j Bolt | 7694 | bolt://localhost:7694 |

## Docs

| | |
|---|---|
| [Framework Overview](docs/evergreen-architecture/ethos-framework-overview.md) | Plain-English explanation of everything |
| [Core Idea](docs/evergreen-architecture/core-idea.md) | The problem, the solution, why now |
| [Product Design](docs/evergreen-architecture/product-design.md) | Three functions and trait customization |
| [System Architecture](docs/evergreen-architecture/system-architecture.md) | Three surfaces, one engine |
| [Scoring Algorithm](docs/evergreen-architecture/scoring-algorithm.md) | How scores are computed |
| [Prompt Architecture](docs/evergreen-architecture/prompt-architecture.md) | How Claude evaluates |
| [Neo4j Schema](docs/evergreen-architecture/neo4j-schema.md) | Phronesis graph data model |
| [Constitutional Alignment](docs/constitutional-alignment.md) | Value hierarchy and hard constraints |
| [API Specification](docs/evergreen-architecture/api-specification.md) | Endpoints, schemas, examples |
| [Demo Flow](docs/evergreen-architecture/demo-flow.md) | The 3-minute hackathon demo |

## License

ISC. See [LICENSE](LICENSE).
