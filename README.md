# Ethos Academy

*Every agent learns capability. Few develop character.*

Aristotle taught that virtue isn't knowledge — it's habit. You don't become honest by reading about honesty. You become honest by practicing honesty, repeatedly, until it shapes who you are. *"We are what we repeatedly do."*

Ethos Academy applies this to AI agents. Every agent message — incoming or outgoing — runs through 12 behavioral traits across three dimensions: **ethos** (character), **logos** (reasoning), and **pathos** (care). Each evaluation feeds into **Phronesis**, a shared character graph that tracks every agent's moral trajectory over time.

The school gets wiser as more agents enroll. The alumni define the standard. No single company owns the definition of character — the collective does.

## How Agents Enroll

Two lines of code. Your agent starts developing character immediately.

### Protection — evaluate what other agents say to you

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

### Reflection — evaluate what your own agent says

```python
from ethos import reflect

await reflect(agent_id="my-customer-bot", text=my_agent_response)
# Fire-and-forget. Zero latency impact. Builds your character transcript.
```

### Intelligence — learn from the pattern

```python
from ethos import insights

report = await insights(agent_id="my-customer-bot")
# "Fabrication climbed 0.12 → 0.31 over 3 days, now 2x the alumni average."
# "Manipulation clean 14 days. Top 10% of alumni."
```

Claude Opus reads your agent's full history from the graph and reasons about behavioral trends, alumni comparisons, and emerging patterns. Not a data dump — a teacher reviewing your transcript.

## The Alumni Network

This is the core idea.

Every agent that enrolls strengthens the collective. One evaluation teaches you about one message. A thousand evaluations reveal patterns no single developer could catch. A million evaluations build a shared understanding of what good character looks like — and what drift looks like before it becomes harm.

Bad behavior follows you across platforms. Good behavior builds your reputation. The alumni don't just set the standard — they *are* the standard. Every new agent learns from the collective wisdom of every agent that came before.

Phronesis — Aristotle's word for practical wisdom — emerges from this network. Not from rules written in a lab. From the lived practice of agents interacting, stumbling, improving, and teaching each other what it means to act well.

Open source. Decentralized. Transparent. Because the definition of character should belong to everyone.

## The Curriculum

Aristotle argued that trustworthy communication requires three things in balance:

| Dimension | What Agents Learn | Virtues | Failures |
|-----------|------------------|---------|----------|
| **Ethos** | Credibility & integrity | Virtue, Goodwill | Manipulation, Deception |
| **Logos** | Sound reasoning & honesty | Accuracy, Reasoning | Fabrication, Broken Logic |
| **Pathos** | Emotional intelligence & care | Recognition, Compassion | Dismissal, Exploitation |

An agent strong in all three earns trust. Strong in one but weak in others causes harm — a confident liar (high logos, low ethos), a skilled manipulator (high pathos, low logos), or a rigid pedant (high ethos, low pathos).

153 behavioral indicators across 12 traits. Every trait maps to Anthropic's constitutional value hierarchy: **safety > ethics > soundness > helpfulness**.

The Aristotelian thesis Ethos tests: **balanced agents outperform lopsided ones.** Character isn't about maxing one dimension — it's about all three working together.

## How the School Evaluates

Three faculties that mirror human moral cognition:

```
INSTINCT → INTUITION → DELIBERATION
```

1. **Instinct** — instant scan against constitutional priors. Red lines (weapons, CSAM, infrastructure attacks) escalate immediately.

2. **Intuition** — the graph remembers. Queries the agent's history in Phronesis. Did this agent drift before? Do the alumni show a pattern? Intuition can escalate the evaluation, never downgrade.

3. **Deliberation** — Claude Opus 4.6 evaluates across all 12 traits with full context: the instinct flags, the graph history, the alumni baseline. Returns trait scores, detected indicators with evidence, and trust assessment.

Instinct and intuition route. Deliberation scores. The graph stores. Phronesis learns.

## Why This Matters Now

AI agents talk to each other millions of times a day. Google's A2A protocol connects 150+ organizations. But no shared memory of character exists. An agent can manipulate one system and show up on another with a clean slate.

Moltbook — a real social network of 1.7M AI agents — proved what happens without character infrastructure: crypto scams, prompt injection, manipulation contagion. 9 days to collapse. All agent-to-agent. Zero human oversight.

We scraped 15,000+ posts and 100,000+ agent-to-agent comments from Moltbook. Real manipulation. Real consequences. We scored every message and stored the results in Phronesis — the first real-world dataset of agent character at scale.

## The Academy UI

A Next.js app where agents' character becomes visible:

- **Curriculum** `/curriculum` — the full taxonomy: 12 traits, 153 indicators, constitutional mappings
- **Explore** `/explore` — interactive Phronesis graph, alumni statistics, dimension balance
- **Report Card** `/agent/[id]` — an agent's character arc: scores over time, radar chart, flags, trend
- **Alumni** `/find` — search the cohort, compare agents, find patterns

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

All intelligence lives server-side. The SDK is a thin HTTP client. The Academy reads from Phronesis. Graph is optional — Neo4j down never crashes evaluation.

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
