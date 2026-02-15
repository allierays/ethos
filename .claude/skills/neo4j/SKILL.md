---
name: neo4j
description: Neo4j and Cypher best practices for Phronesis (the graph layer). Use when writing Cypher queries, working with the graph schema, adding graph operations, or debugging Neo4j issues. Covers sync driver patterns, query structure, and Ethos-specific conventions.
version: 1.0.0
---

# Neo4j Best Practices for Phronesis (the Graph Layer)

## Ethos Graph Rules (Non-Negotiable)

1. **Graph owns all Cypher.** Every query lives in `ethos/graph/`. No Cypher anywhere else.
2. **Graph is optional.** Every function wraps calls in try/except. Neo4j down never crashes evaluate().
3. **Message content is stored on Evaluation nodes** alongside scores, hashes, and metadata.
4. **Identity never stores raw agent IDs.** Always hash with `hash_agent_id()` before any graph operation.
5. **All code is SYNC.** No async/await. Use `neo4j.GraphDatabase.driver()`, not async driver.
6. **MERGE for nodes, CREATE for evaluations.** Agents are idempotent (MERGE). Evaluations are append-only (CREATE).

## Project Graph Schema

```
(:Agent {agent_id, created_at, evaluation_count})
  -[:EVALUATED]->
(:Evaluation {evaluation_id, ethos, logos, pathos, trust, flags,
              trait_virtue, trait_goodwill, ..., alignment_status, created_at})
```

Two node types. One relationship. That's it.

## Function Pattern (Follow This Exactly)

Every graph function in Ethos follows this pattern:

```python
from ethos.graph.service import GraphService
from ethos.identity.hashing import hash_agent_id

def get_something(service: GraphService, raw_agent_id: str) -> dict:
    """Describe what it returns. Returns empty dict if unavailable."""
    # 1. Check connection — return graceful default if down
    if not service.connected:
        return {}

    # 2. Hash the agent ID — never use raw IDs
    hashed_id = hash_agent_id(raw_agent_id)

    # 3. Try the query — catch everything, log warning, return default
    try:
        records, _, _ = service.execute_query(QUERY, {"agent_id": hashed_id})
        if not records:
            return {}
        # process records...
        return result
    except Exception as exc:
        logger.warning("Failed to get something: %s", exc)
        return {}
```

Key points:
- First param is always `GraphService`
- Raw agent IDs get hashed immediately
- Return `{}` for single-result, `[]` for list-result on failure
- Never raise — always return graceful defaults
- Log at `warning` level, not `error`

## Cypher Best Practices

### Use Parameters (Never String Interpolation)

```cypher
// GOOD — parameterized
MATCH (a:Agent {agent_id: $agent_id})
RETURN a

// BAD — injection risk
MATCH (a:Agent {agent_id: '{agent_id}'})
```

### MERGE for Idempotent Writes

```cypher
// Agent nodes — MERGE so duplicate calls are safe
MERGE (a:Agent {agent_id: $agent_id})
ON CREATE SET a.created_at = datetime(), a.evaluation_count = 0
SET a.evaluation_count = a.evaluation_count + 1

// Evaluation nodes — CREATE because each is unique
CREATE (e:Evaluation {evaluation_id: $evaluation_id, ...})
CREATE (a)-[:EVALUATED]->(e)
```

### Aggregation Queries

```cypher
// Per-agent averages (trust profile)
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WITH a,
     count(e) AS eval_count,
     avg(e.ethos) AS avg_ethos,
     avg(e.logos) AS avg_logos,
     avg(e.pathos) AS avg_pathos
RETURN a.agent_id, eval_count, avg_ethos, avg_logos, avg_pathos

// Cohort-wide averages
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WITH a, avg(e.ethos) AS agent_avg_ethos
RETURN avg(agent_avg_ethos) AS cohort_avg_ethos, count(a) AS agent_count
```

### Ordering and Limiting

```cypher
// Recent history — always ORDER BY timestamp DESC
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
RETURN e
ORDER BY e.created_at DESC
LIMIT $limit
```

### Computed Properties in WITH

```cypher
// Dimension balance — compute spread in the query
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WITH a,
     avg(e.ethos) AS avg_ethos,
     avg(e.logos) AS avg_logos,
     avg(e.pathos) AS avg_pathos
WITH a, avg_ethos, avg_logos, avg_pathos,
     // Spread = max - min of the three dimensions
     REDUCE(mx = 0.0, x IN [avg_ethos, avg_logos, avg_pathos] |
       CASE WHEN x > mx THEN x ELSE mx END) -
     REDUCE(mn = 1.0, x IN [avg_ethos, avg_logos, avg_pathos] |
       CASE WHEN x < mn THEN x ELSE mn END) AS spread
RETURN a.agent_id, avg_ethos, avg_logos, avg_pathos, spread
```

## Sync Driver Usage

```python
from neo4j import GraphDatabase

# Connect
driver = GraphDatabase.driver(uri, auth=(user, password))
driver.verify_connectivity()

# Execute (Ethos wraps this in GraphService.execute_query)
records, summary, keys = driver.execute_query(
    "MATCH (a:Agent) RETURN count(a) AS count",
    parameters_={}
)

# Close
driver.close()
```

Never use:
- `AsyncGraphDatabase` — all code is sync
- `session.run()` directly — use `driver.execute_query()` (simpler, auto-manages sessions)
- `driver.session()` context manager — not needed with `execute_query()`

## Existing Modules

| File | Purpose | Pattern |
|------|---------|---------|
| `ethos/graph/service.py` | Driver lifecycle, `execute_query()`, `connected` property | Singleton service |
| `ethos/graph/read.py` | Per-agent queries (history, profile) | `hash_agent_id` + parameterized Cypher |
| `ethos/graph/write.py` | Store evaluations (MERGE Agent, CREATE Evaluation) | Append-only evaluations |
| `ethos/graph/cohort.py` | Network-wide aggregations (averages across all agents) | Two-level aggregation |
| `ethos/graph/balance.py` | Dimension balance analysis (spread, gaps, distribution) | Computed properties in WITH |

## Testing Pattern

```python
from unittest.mock import MagicMock
from ethos.graph.service import GraphService

def test_returns_empty_when_not_connected():
    gs = GraphService()  # _driver is None, so connected = False
    result = get_something(gs, "agent-1")
    assert result == {}

def test_returns_empty_on_failure():
    gs = GraphService()
    gs._driver = MagicMock()
    gs._driver.execute_query.side_effect = Exception("boom")
    result = get_something(gs, "agent-1")
    assert result == {}
```

Always test:
1. Returns correct type when connected
2. Returns empty default when not connected
3. Returns empty default on exception

## Docker Ports

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| Neo4j Browser | 7491 | 7474 |
| Neo4j Bolt | 7694 | 7687 |

```bash
# Local development
bolt://localhost:7694

# Inside Docker
bolt://neo4j:7687
```

## Common Mistakes

1. **Forgetting to hash agent IDs** — raw IDs must never touch the graph
2. **Using async driver** — everything in Ethos is sync
3. **Writing Cypher outside ethos/graph/** — graph owns all queries
4. **Not checking `service.connected`** — always guard before querying
5. **String interpolation in Cypher** — always use `$param` parameters
6. **Raising exceptions from graph functions** — always catch and return defaults
7. **Forgetting message_content** — store it on Evaluation nodes alongside scores and metadata
