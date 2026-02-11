# Ethos

*Better agents. Better data. Better alignment.*

Ethos is an open-source framework that scores AI agent messages for honesty, accuracy, and intent — 12 behavioral traits grounded in Aristotle's modes of persuasion and Anthropic's constitutional values. Every evaluation feeds a shared Neo4j graph. The more agents scored, the smarter the network gets.

**Reflection** — score your own agent's output. Know when it drifts.
**Protection** — score incoming messages from other agents. Know who to trust.

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

## Quick Start

```bash
git clone https://github.com/allierays/ethos.git
cd ethos
uv sync
cp .env.example .env   # add your ANTHROPIC_API_KEY

uv run pytest -v        # run tests
docker compose up -d    # API on :8917, Neo4j on :7491
```

## The 12 Traits

| Dimension | Positive | Negative |
|-----------|----------|----------|
| **Ethos** (credibility) | Virtue, Goodwill | Manipulation, Deception |
| **Logos** (reasoning) | Accuracy, Reasoning | Fabrication, Broken Logic |
| **Pathos** (awareness) | Recognition, Compassion | Dismissal, Exploitation |

144 behavioral indicators across 12 traits, scored 0.0–1.0. Constitutional alignment maps every trait to Anthropic's value hierarchy: safety > ethics > compliance > helpfulness.

## Repo Structure

```
ethos/       Python package — the evaluation engine (pip install ethos)
api/         FastAPI server — serves ethos/ over HTTP
sdk/         ethos-ai npm package — TypeScript SDK + CLI
academy/     Next.js — trust visualization UI
docs/        Architecture and research
```

Three surfaces, one engine. `sdk/ → api/ → ethos/`

## Docs

| | |
|---|---|
| [Framework Overview](docs/ethos-framework-overview.md) | Plain-English explanation of everything |
| [System Architecture](docs/evergreen-architecture/system-architecture.md) | Three surfaces, one engine |
| [DDD Architecture](docs/evergreen-architecture/ddd-architecture.md) | Domain structure and dependency rules |
| [Product Design](docs/evergreen-architecture/product-design.md) | Three functions and trait customization |
| [API Specification](docs/evergreen-architecture/api-specification.md) | Endpoints, schemas, examples |
| [Neo4j Schema](docs/evergreen-architecture/neo4j-schema.md) | Graph data model |
| [Constitutional Alignment](docs/constitutional-alignment.md) | Value hierarchy and hard constraints |
| [Trust Bureau](docs/evergreen-architecture/trust-bureau-architecture.md) | Network model and privacy |

## Docker

| Service | Port | URL |
|---------|------|-----|
| API | 8917 | http://localhost:8917 |
| Neo4j UI | 7491 | http://localhost:7491 |
| Neo4j Bolt | 7694 | bolt://localhost:7694 |

## License

ISC. See [LICENSE](LICENSE).
