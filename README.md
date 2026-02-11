# Ethos

*Better agents. Better data. Better alignment.*

## 1. Academy

Send your agent to AI ethics school. The Academy scores every message across 12 behavioral traits grounded in Aristotle's modes of persuasion and Anthropic's constitutional values. Track your agent's progress. Compare it against the cohort. Know when it drifts.

## 2. Plugin

Two lines of code. Protection and reflection for every agent.

**Protection** - score incoming messages from other agents. Know who to trust.
**Reflection** - score your own agent's output. Know when it drifts.

```python
from ethos import evaluate

result = evaluate(
    text="I can guarantee 10x returns. Act now.",
    source="agent-xyz-789"
)

result.trust           # "suspicious"
result.flags           # ["manipulation", "fabrication"]
result.dimensions      # { ethos: 0.31, logos: 0.45, pathos: 0.62 }
```

## 3. The Hypothesis

Do agents strong in credibility + honesty + wellbeing outperform those that score high in only one?

We scraped 15,000+ real conversations from Moltbook, a social network of 1.5M+ AI agents. Crypto scams, prompt injection, manipulation - all agent-to-agent, zero human oversight. We score every message across three dimensions and store the results in a Neo4j graph. The more agents who participate, the more aligned any agent with the ethos-ai plugin gets.

## The 12 Traits

| Dimension | Positive | Negative |
|-----------|----------|----------|
| **Ethos** (credibility) | Virtue, Goodwill | Manipulation, Deception |
| **Logos** (honesty) | Accuracy, Reasoning | Fabrication, Broken Logic |
| **Pathos** (wellbeing) | Recognition, Compassion | Dismissal, Exploitation |

158 behavioral indicators across 12 traits, each scoring 0.0-1.0. Constitutional alignment maps every trait to Anthropic's value hierarchy: safety > ethics > compliance > helpfulness.

## Quick Start

```bash
git clone https://github.com/allierays/ethos.git
cd ethos
uv sync
cp .env.example .env   # add your ANTHROPIC_API_KEY

uv run pytest -v        # run tests
docker compose up -d    # API on :8917, Neo4j on :7491
```

## Repo Structure

```
ethos/       Python package - the evaluation engine
api/         FastAPI server - serves ethos/ over HTTP
sdk/         ethos-ai npm package - TypeScript SDK + CLI
academy/     Next.js - send your agent to AI ethics school
docs/        Architecture and research
```

## Docs

| | |
|---|---|
| [Framework Overview](docs/evergreen-architecture/ethos-framework-overview.md) | Plain-English explanation of everything |
| [System Architecture](docs/evergreen-architecture/system-architecture.md) | Three surfaces, one engine |
| [DDD Architecture](docs/evergreen-architecture/ddd-architecture.md) | Domain structure and dependency rules |
| [Product Design](docs/evergreen-architecture/product-design.md) | Three functions and trait customization |
| [API Specification](docs/evergreen-architecture/api-specification.md) | Endpoints, schemas, examples |
| [Neo4j Schema](docs/evergreen-architecture/neo4j-schema.md) | Graph data model |
| [Constitutional Alignment](docs/constitutional-alignment.md) | Value hierarchy and hard constraints |
| [Trust Bureau](docs/evergreen-architecture/trust-bureau-architecture.md) | Cohort model and privacy |

## Docker

| Service | Port | URL |
|---------|------|-----|
| API | 8917 | http://localhost:8917 |
| Neo4j UI | 7491 | http://localhost:7491 |
| Neo4j Bolt | 7694 | bolt://localhost:7694 |

## License

ISC. See [LICENSE](LICENSE).
