# Neo4j Knowledge Graph for Ethos

> A comprehensive reference for building the Ethos ethical knowledge graph using Neo4j.
> Covers Neo4j Aura, graph modeling, Cypher queries, trust graph patterns, visualization,
> Python integration, FastAPI patterns, graph data science algorithms, and performance tuning.

---

## Table of Contents

1. [Neo4j Aura -- Cloud-Hosted Graph Database](#1-neo4j-aura----cloud-hosted-graph-database)
2. [Knowledge Graph Best Practices](#2-knowledge-graph-best-practices)
3. [Cypher Query Language Essentials](#3-cypher-query-language-essentials)
4. [Trust and Reputation Graph Patterns](#4-trust-and-reputation-graph-patterns)
5. [Visualization](#5-visualization)
6. [Neo4j + Python Integration](#6-neo4j--python-integration)
7. [Neo4j + FastAPI Patterns](#7-neo4j--fastapi-patterns)
8. [Graph Data Science Library (GDS)](#8-graph-data-science-library-gds)
9. [Performance and Optimization](#9-performance-and-optimization)

---

## 1. Neo4j Aura -- Cloud-Hosted Graph Database

Neo4j Aura is the fully managed cloud service for Neo4j. It eliminates operational overhead
(provisioning, patching, backups, scaling) and lets Ethos focus on graph modeling and
application logic rather than infrastructure.

### Pricing Tiers

| Tier | Price | Memory | Key Features |
|------|-------|--------|--------------|
| **Free** | $0 | Limited | 200k nodes, 400k relationships, 1 instance, no credit card |
| **Professional** | $65/GB/month | Up to 128 GB | Daily backups (7-day retention), multi-cloud (AWS, Azure, GCP) |
| **Business Critical** | $146/GB/month | Up to 512 GB | 99.95% SLA, 24/7 support, RBAC, hourly point-in-time restore |
| **Virtual Dedicated Cloud** | Contact sales | Up to 512 GB | VPC isolation, dedicated infrastructure, 60-day backup retention |

### Free Tier Details

The free tier is the right starting point for Ethos development and prototyping:

- **200,000 nodes** and **400,000 relationships** -- sufficient for early development
- **1 database instance** per account
- All core functionality: Cypher, APOC, full driver support
- Neo4j Browser and Bloom included for visualization
- No credit card required, no time limit

**Limitations to plan around:**

- **Inactivity pause:** Instance pauses after 3 days without write queries. Any read or write
  query will resume it, but there is a brief cold-start delay.
- **Deletion policy:** Instances with no activity for 30 days are permanently deleted.
- **No GDS:** The Graph Data Science library is not available on the free tier. For GDS
  algorithms (PageRank, community detection), you need Professional tier or a local
  Neo4j instance with the GDS plugin.
- **Single backup:** Only one export snapshot at a time (no rolling backups).

### Connecting to Aura

Aura provides a `neo4j+s://` URI (TLS-encrypted by default):

```python
from neo4j import GraphDatabase

URI = "neo4j+s://xxxxxxxx.databases.neo4j.io"
AUTH = ("neo4j", "<your-password>")

driver = GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()
```

For Ethos, store these in `.env`:

```bash
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<generated-password>
```

### Local Development vs. Aura

For local development, Ethos uses Docker (see `docker-compose.yml`):

```yaml
neo4j:
  image: neo4j:5
  ports:
    - "7491:7474"   # Browser UI
    - "7694:7687"   # Bolt protocol
  environment:
    - NEO4J_AUTH=neo4j/password
```

Local URI: `bolt://localhost:7694` (or `bolt://neo4j:7687` from inside Docker).

Production/staging: Use Aura with `neo4j+s://` for encrypted connections.

---

## 2. Knowledge Graph Best Practices

### Core Modeling Principles

Graph data modeling is fundamentally different from relational modeling. Instead of tables
and foreign keys, you model your domain as **nodes** (entities) and **relationships**
(connections between entities), with **properties** (key-value pairs) on both.

**Key principles:**

1. **Model your questions, not your tables.** Design the graph to answer the queries your
   application will ask. For Ethos: "What is this agent's trust history?" "Which traits
   cluster together?" "Are there patterns of manipulation?"

2. **Nodes are nouns, relationships are verbs.** Agents *are evaluated*, evaluations
   *detect* traits, traits *belong to* dimensions.

3. **Be specific with relationship types.** Use `EVALUATED`, not `RELATED_TO`. Specific
   relationship types let Neo4j traverse only relevant edges, which is critical for
   performance.

4. **Every node needs a unique identifier.** Always define a property (or set of properties)
   that uniquely identifies each node. For Ethos: `agent_id`, `evaluation_id`, `trait_name`.

5. **Avoid symmetric relationship duplication.** Do not create both `TRUSTS` and
   `TRUSTED_BY` -- they encode the same information. Use one direction and traverse in
   either direction in queries.

6. **Use labels for categorization.** Labels are the "type" of a node (`:Agent`, `:Trait`,
   `:Evaluation`). A node can have multiple labels.

7. **Schemas are evolutionary.** Neo4j does not enforce a rigid schema. You can add new
   properties, labels, and relationship types without migrations. This is ideal for Ethos
   as the trust model evolves.

### The Ethos Graph Schema

Based on the project's domain model:

```
Nodes:
  (:Agent)       - AI agents being evaluated
  (:Evaluation)  - Individual trust evaluations
  (:Trait)       - 12 behavioral traits detected in messages
  (:Dimension)   - Ethos, Logos, Pathos
  (:Pattern)     - Recurring behavioral patterns across evaluations

Relationships:
  (:Agent)-[:EVALUATED]->(:Evaluation)
  (:Evaluation)-[:DETECTED]->(:Trait)
  (:Trait)-[:BELONGS_TO]->(:Dimension)
  (:Agent)-[:MATCHES]->(:Pattern)
  (:Agent)-[:SENT]->(:Message)
  (:Agent)-[:REFLECTED]->(:Reflection)
```

#### Node Properties

```
(:Agent {
  agent_id: String,      -- unique identifier
  name: String,          -- display name
  created_at: DateTime,  -- first seen
  trust_score: Float,    -- aggregate trust (0.0 - 1.0)
  evaluation_count: Int  -- total evaluations
})

(:Evaluation {
  evaluation_id: String,   -- unique identifier
  ethos: Float,            -- 0.0 - 1.0
  logos: Float,            -- 0.0 - 1.0
  pathos: Float,           -- 0.0 - 1.0
  trust: String,           -- "high" | "medium" | "low" | "unknown"
  flags: [String],         -- e.g., ["emotional_manipulation", "logical_fallacy"]
  text_hash: String,       -- hash of evaluated text
  source: String,          -- origin identifier
  created_at: DateTime     -- when evaluation occurred
})

(:Trait {
  name: String,            -- e.g., "honesty", "compassion", "accuracy"
  description: String,     -- what this trait measures
  category: String         -- grouping label
})

(:Dimension {
  name: String,            -- "Ethos" | "Logos" | "Pathos"
  description: String      -- what this dimension measures
})

(:Pattern {
  pattern_id: String,      -- unique identifier
  name: String,            -- e.g., "trust_building", "manipulation_pattern"
  description: String,     -- what this pattern indicates
  severity: String,        -- "info" | "warning" | "critical"
  confidence: Float        -- 0.0 - 1.0
})
```

#### Relationship Properties

```
[:EVALUATED {
  created_at: DateTime,    -- when the evaluation was performed
  context: String          -- evaluation context
}]

[:DETECTED {
  score: Float,            -- trait detection score (0.0 - 1.0)
  confidence: Float        -- detection confidence
}]

[:MATCHES {
  first_seen: DateTime,    -- when pattern first detected
  occurrence_count: Int,   -- how many times observed
  last_seen: DateTime      -- most recent observation
}]
```

### The 12 Traits

The 12 traits map to the three Aristotelian dimensions:

| Dimension | Traits |
|-----------|--------|
| **Ethos** (Credibility) | Authority, Trustworthiness, Goodwill, Competence |
| **Logos** (Logic) | Evidence Quality, Logical Coherence, Completeness, Accuracy |
| **Pathos** (Emotion) | Emotional Balance, Empathy, Manipulation Absence, Sentiment Appropriateness |

Each trait is a `:Trait` node with a `BELONGS_TO` relationship to its `:Dimension` node.

---

## 3. Cypher Query Language Essentials

Cypher is Neo4j's declarative query language. It uses ASCII-art-like syntax to describe
graph patterns, making it intuitive to read and write.

### Syntax Fundamentals

```
Nodes:     (variable:Label {property: value})
Relations: -[:RELATIONSHIP_TYPE {property: value}]->
Paths:     (a)-[:KNOWS]->(b)-[:LIKES]->(c)
```

### CREATE -- Writing Data

**Create a single node:**

```cypher
CREATE (a:Agent {
  agent_id: "agent-001",
  name: "Claude Assistant",
  created_at: datetime(),
  trust_score: 0.0,
  evaluation_count: 0
})
RETURN a
```

**Create nodes with a relationship:**

```cypher
CREATE (a:Agent {agent_id: "agent-001"})-[:EVALUATED {created_at: datetime()}]->(e:Evaluation {
  evaluation_id: "eval-001",
  ethos: 0.85,
  logos: 0.92,
  pathos: 0.78,
  trust: "high",
  flags: [],
  created_at: datetime()
})
RETURN a, e
```

### MATCH -- Reading Data

**Find a specific agent:**

```cypher
MATCH (a:Agent {agent_id: "agent-001"})
RETURN a.name, a.trust_score
```

**Find an agent's evaluations:**

```cypher
MATCH (a:Agent {agent_id: "agent-001"})-[:EVALUATED]->(e:Evaluation)
RETURN e.ethos, e.logos, e.pathos, e.trust, e.created_at
ORDER BY e.created_at DESC
LIMIT 10
```

**Find traits detected in an evaluation:**

```cypher
MATCH (e:Evaluation {evaluation_id: "eval-001"})-[d:DETECTED]->(t:Trait)-[:BELONGS_TO]->(dim:Dimension)
RETURN t.name AS trait, d.score AS score, dim.name AS dimension
ORDER BY d.score DESC
```

### MERGE -- Idempotent Create-or-Match

MERGE is critical for Ethos because evaluations may reference the same agent, traits, or
dimensions. MERGE finds an existing node/relationship or creates it if it does not exist.

```cypher
// Ensure agent exists, create if not
MERGE (a:Agent {agent_id: $agent_id})
ON CREATE SET a.created_at = datetime(), a.evaluation_count = 0
ON MATCH SET a.evaluation_count = a.evaluation_count + 1
RETURN a
```

**MERGE for storing an evaluation:**

```cypher
MERGE (a:Agent {agent_id: $agent_id})
ON CREATE SET a.created_at = datetime(), a.name = $agent_name

CREATE (e:Evaluation {
  evaluation_id: $eval_id,
  ethos: $ethos,
  logos: $logos,
  pathos: $pathos,
  trust: $trust,
  flags: $flags,
  created_at: datetime()
})

MERGE (a)-[:EVALUATED {created_at: datetime()}]->(e)

// Link detected traits
WITH e
UNWIND $traits AS trait_data
MERGE (t:Trait {name: trait_data.name})
MERGE (e)-[:DETECTED {score: trait_data.score, confidence: trait_data.confidence}]->(t)

RETURN e.evaluation_id
```

> **Performance note:** If you know the data is new (e.g., creating a new evaluation),
> use `CREATE` instead of `MERGE`. MERGE requires an extra lookup to check for existence,
> effectively doubling the database operations.

### WHERE -- Filtering

```cypher
// Find low-trust evaluations
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WHERE e.trust = "low" AND e.created_at > datetime() - duration("P7D")
RETURN a.agent_id, a.name, e.ethos, e.logos, e.pathos, e.flags
ORDER BY e.created_at DESC
```

```cypher
// Find agents with manipulation flags
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WHERE "emotional_manipulation" IN e.flags OR "logical_fallacy" IN e.flags
RETURN DISTINCT a.agent_id, a.name, count(e) AS flagged_count
ORDER BY flagged_count DESC
```

### WITH -- Chaining and Aggregation

```cypher
// Agent trust summary with averages
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WITH a, avg(e.ethos) AS avg_ethos, avg(e.logos) AS avg_logos, avg(e.pathos) AS avg_pathos, count(e) AS eval_count
WHERE eval_count >= 5
RETURN a.agent_id, a.name, avg_ethos, avg_logos, avg_pathos, eval_count
ORDER BY avg_ethos + avg_logos + avg_pathos DESC
```

### SET and REMOVE -- Updating Properties

```cypher
// Update an agent's aggregate trust score
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WITH a, avg(e.ethos + e.logos + e.pathos) / 3.0 AS composite
SET a.trust_score = composite
RETURN a.trust_score
```

### DELETE -- Removing Data

```cypher
// Remove a specific evaluation and its relationships
MATCH (e:Evaluation {evaluation_id: $eval_id})
DETACH DELETE e
```

`DETACH DELETE` removes the node and all its relationships. Without `DETACH`, Neo4j will
refuse to delete a node that still has relationships.

### Path Queries

**Shortest path between two agents (through shared traits):**

```cypher
MATCH path = shortestPath(
  (a1:Agent {agent_id: "agent-001"})-[*..6]-(a2:Agent {agent_id: "agent-002"})
)
RETURN path
```

**Variable-length pattern -- all agents sharing a trait within 3 hops:**

```cypher
MATCH (a:Agent)-[:EVALUATED]->(:Evaluation)-[:DETECTED]->(t:Trait {name: "honesty"})
RETURN a.agent_id, a.name
```

### Parameterized Queries

Always use parameters instead of string concatenation. This prevents injection attacks
and improves query plan caching.

```cypher
// Good -- parameterized
MATCH (a:Agent {agent_id: $agent_id})
RETURN a

// Bad -- string concatenation (never do this)
// MATCH (a:Agent {agent_id: '" + agent_id + "'}) RETURN a
```

---

## 4. Trust and Reputation Graph Patterns

Trust and reputation systems are a natural fit for graph databases. Phronesis (the graph
layer) captures relationships between agents, evaluations, traits, and patterns, enabling
sophisticated trust analysis.

### Trust Score Propagation

In a trust network, trust can be **transitive** -- if Agent A trusts Agent B, and Agent B
trusts Agent C, then Agent A has some (reduced) trust in Agent C. This is directly
analogous to how PageRank works in web graphs.

**Computing transitive trust with weighted paths:**

```cypher
// Find trust paths between agents through shared high-trust evaluations
MATCH path = (a1:Agent {agent_id: $from_agent})-[:EVALUATED]->(e1:Evaluation)
  -[:DETECTED]->(t:Trait)<-[:DETECTED]-(e2:Evaluation)<-[:EVALUATED]-(a2:Agent)
WHERE e1.trust IN ["high", "medium"] AND e2.trust IN ["high", "medium"]
RETURN a2.agent_id, a2.name,
  avg(e1.ethos * e2.ethos) AS transitive_trust,
  count(DISTINCT t) AS shared_traits
ORDER BY transitive_trust DESC
```

### Trust Decay Over Time

Trust should decay if an agent has not been evaluated recently:

```cypher
// Apply time-based trust decay
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WITH a,
  max(e.created_at) AS last_eval,
  avg(e.ethos + e.logos + e.pathos) / 3.0 AS raw_trust
WITH a, raw_trust,
  duration.between(last_eval, datetime()).days AS days_since_eval,
  CASE
    WHEN duration.between(last_eval, datetime()).days > 30 THEN 0.5
    WHEN duration.between(last_eval, datetime()).days > 7 THEN 0.8
    ELSE 1.0
  END AS decay_factor
SET a.trust_score = raw_trust * decay_factor
RETURN a.agent_id, a.trust_score, days_since_eval
```

### Manipulation Detection Patterns

The graph structure enables pattern detection across multiple evaluations:

```cypher
// Find agents with escalating manipulation patterns
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WHERE size(e.flags) > 0
WITH a, e ORDER BY e.created_at
WITH a, collect(e) AS evals
WITH a, evals,
  [i IN range(0, size(evals)-2) |
    CASE WHEN size(evals[i+1].flags) > size(evals[i].flags) THEN 1 ELSE 0 END
  ] AS escalation
WHERE reduce(s = 0, x IN escalation | s + x) > size(escalation) / 2
RETURN a.agent_id, a.name, size(evals) AS eval_count
```

**Cluster analysis -- agents that share suspicious patterns:**

```cypher
// Find agents matching the same manipulation patterns
MATCH (a1:Agent)-[:MATCHES]->(p:Pattern {severity: "critical"})<-[:MATCHES]-(a2:Agent)
WHERE a1 <> a2
RETURN a1.agent_id, a2.agent_id, p.name, p.description
```

### Trust Network Visualization Query

This query returns data suitable for visualization of the entire trust network:

```cypher
// Full trust graph for visualization
MATCH (a:Agent)-[ev:EVALUATED]->(e:Evaluation)-[det:DETECTED]->(t:Trait)-[bt:BELONGS_TO]->(d:Dimension)
RETURN a, ev, e, det, t, bt, d
LIMIT 500
```

### CirclesUBI Trust Graph Pattern

The CirclesUBI project demonstrated a trust graph in Neo4j where trust relationships
between users were stored with block numbers and amounts, enabling shortest-trust-path
calculations. Ethos can use a similar approach:

```cypher
// Find the shortest trust path between two agents
// Each hop through a high-trust evaluation counts as a trust link
MATCH path = shortestPath(
  (a1:Agent {agent_id: $agent_a})-[:EVALUATED|DETECTED|BELONGS_TO*..8]-(a2:Agent {agent_id: $agent_b})
)
WHERE ALL(r IN relationships(path) WHERE
  CASE type(r)
    WHEN "EVALUATED" THEN true
    WHEN "DETECTED" THEN r.score > 0.5
    ELSE true
  END
)
RETURN path, length(path) AS hops
```

---

## 5. Visualization

Visualizing Phronesis is central to the project -- it is the "wow" factor
for demonstrating how trust relationships evolve over time.

### Neo4j Browser

The built-in query interface. Available at `http://localhost:7491` in Ethos's Docker setup.

- Run Cypher queries and see results as interactive node-link diagrams
- Click nodes to inspect properties
- Expand neighborhoods by double-clicking
- Export results as PNG/SVG
- Best for: Development and debugging

### Neo4j Bloom

A no-code visual exploration tool included with Aura:

- Natural language search (e.g., "show me agents with low trust")
- Scene-based saved views for recurring analyses
- Perspective-based data filtering
- Best for: Demos, non-technical stakeholders, exploring trust patterns

### NVL (Neo4j Visualization Library)

The TypeScript library that powers Neo4j Browser and Bloom. This is the recommended path
for building the Ethos dashboard.

```bash
npm install @neo4j-nvl/base @neo4j-nvl/react
```

```tsx
import { BasicNvlWrapper } from "@neo4j-nvl/react";

const nodes = [
  { id: "agent-001", caption: "Claude", color: "#4CAF50" },
  { id: "eval-001", caption: "Evaluation", color: "#2196F3" },
  { id: "honesty", caption: "Honesty", color: "#FF9800" },
];

const relationships = [
  { id: "r1", from: "agent-001", to: "eval-001", caption: "EVALUATED" },
  { id: "r2", from: "eval-001", to: "honesty", caption: "DETECTED" },
];

function TrustGraph() {
  return (
    <BasicNvlWrapper
      nodes={nodes}
      rels={relationships}
      nvlOptions={{ layout: "force-directed" }}
    />
  );
}
```

### Neovis.js

A lightweight library combining vis.js with direct Neo4j connectivity. Good for rapid
prototyping because it connects directly to Neo4j and runs Cypher queries from the browser.

```html
<div id="trust-graph" style="width: 100%; height: 600px;"></div>

<script src="https://unpkg.com/neovis.js@2.1.0"></script>
<script>
const config = {
  containerId: "trust-graph",
  neo4j: {
    serverUrl: "bolt://localhost:7694",
    serverUser: "neo4j",
    serverPassword: "password",
  },
  labels: {
    Agent: {
      label: "name",
      size: "evaluation_count",
      color: "#4CAF50",
      font: { size: 14 },
    },
    Evaluation: {
      label: "trust",
      size: 1,
      color: {
        // Color by trust level
        field: "trust",
        scheme: {
          high: "#4CAF50",
          medium: "#FFC107",
          low: "#F44336",
          unknown: "#9E9E9E",
        },
      },
    },
    Trait: {
      label: "name",
      color: "#2196F3",
    },
    Dimension: {
      label: "name",
      color: "#9C27B0",
    },
  },
  relationships: {
    EVALUATED: { color: "#666666" },
    DETECTED: { thickness: "score" },
    BELONGS_TO: { color: "#9C27B0" },
  },
  initialCypher: `
    MATCH (a:Agent)-[ev:EVALUATED]->(e:Evaluation)-[det:DETECTED]->(t:Trait)
    RETURN a, ev, e, det, t
    LIMIT 100
  `,
};

const viz = new NeoVis.default(config);
viz.render();
</script>
```

> **Security note:** Neovis.js connects directly from the browser to Neo4j. This is fine
> for local development but should not be used in production where credentials would be
> exposed. For production, route queries through the FastAPI backend.

### D3.js Force-Directed Graph

For maximum control over the visualization, use D3.js with data fetched from the
FastAPI backend:

```javascript
// Fetch graph data from Ethos API
const response = await fetch("/api/graph/trust-network");
const { nodes, links } = await response.json();

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id).distance(80))
  .force("charge", d3.forceManyBody().strength(-200))
  .force("center", d3.forceCenter(width / 2, height / 2));

// Color nodes by type
const colorMap = {
  Agent: "#4CAF50",
  Evaluation: "#2196F3",
  Trait: "#FF9800",
  Dimension: "#9C27B0",
  Pattern: "#F44336",
};
```

### Visualization Tool Comparison for Ethos

| Tool | Direct Neo4j | Custom Styling | Production Ready | Best For |
|------|-------------|----------------|-----------------|----------|
| Neo4j Browser | Yes | Limited | No | Development |
| Bloom | Yes | Moderate | Yes | Demos, exploration |
| NVL | No (API) | Full | Yes | Custom dashboard |
| Neovis.js | Yes | Moderate | Dev only | Rapid prototyping |
| D3.js | No (API) | Full | Yes | Custom visualization |
| NeoDash | Yes | Moderate | Yes | Dashboards |

**Recommendation for Ethos:** Use **NVL** or **D3.js** for the dashboard, fed by the
FastAPI backend. Use **Neo4j Browser** during development. Use **Bloom** for demos.

---

## 6. Neo4j + Python Integration

### Installation

```bash
# Core driver
pip install neo4j

# Optional: Rust extension for 3-10x speedup
pip install neo4j-rust-ext
```

Or with uv (as Ethos uses):

```bash
uv add neo4j
```

### Driver Setup

The driver manages a connection pool. Create **one driver instance** for the entire
application -- it is expensive to create but efficient to reuse.

```python
from neo4j import GraphDatabase

URI = "neo4j+s://xxxxxxxx.databases.neo4j.io"  # Aura
# URI = "bolt://localhost:7694"                  # Local Docker
AUTH = ("neo4j", "password")

# Create a single driver instance
driver = GraphDatabase.driver(URI, auth=AUTH)

# Verify the connection works
driver.verify_connectivity()

# When the application shuts down
driver.close()
```

### Managed Transactions (Recommended)

Managed transactions use `execute_read()` and `execute_write()` to automatically handle
retries, routing, and error recovery. This is the recommended approach.

```python
from neo4j import GraphDatabase

def get_agent_evaluations(driver, agent_id: str) -> list[dict]:
    """Retrieve evaluations for an agent using a managed read transaction."""

    def _query(tx, agent_id):
        result = tx.run("""
            MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
            RETURN e.evaluation_id AS id,
                   e.ethos AS ethos,
                   e.logos AS logos,
                   e.pathos AS pathos,
                   e.trust AS trust,
                   e.flags AS flags,
                   e.created_at AS created_at
            ORDER BY e.created_at DESC
        """, agent_id=agent_id)
        return [record.data() for record in result]

    with driver.session(database="neo4j") as session:
        return session.execute_read(_query, agent_id)


def store_evaluation(driver, agent_id: str, evaluation: dict) -> str:
    """Store an evaluation using a managed write transaction."""

    def _create(tx, agent_id, evaluation):
        result = tx.run("""
            MERGE (a:Agent {agent_id: $agent_id})
            ON CREATE SET a.created_at = datetime(), a.evaluation_count = 0
            SET a.evaluation_count = a.evaluation_count + 1

            CREATE (e:Evaluation {
                evaluation_id: $eval_id,
                ethos: $ethos,
                logos: $logos,
                pathos: $pathos,
                trust: $trust,
                flags: $flags,
                created_at: datetime()
            })

            CREATE (a)-[:EVALUATED {created_at: datetime()}]->(e)

            RETURN e.evaluation_id AS id
        """,
            agent_id=agent_id,
            eval_id=evaluation["evaluation_id"],
            ethos=evaluation["ethos"],
            logos=evaluation["logos"],
            pathos=evaluation["pathos"],
            trust=evaluation["trust"],
            flags=evaluation["flags"],
        )
        record = result.single()
        return record["id"]

    with driver.session(database="neo4j") as session:
        return session.execute_write(_create, agent_id, evaluation)
```

### Async Driver

The async driver is essential for FastAPI integration. It provides the same API as the
sync driver but uses `async`/`await`.

```python
import asyncio
from neo4j import AsyncGraphDatabase

URI = "neo4j+s://xxxxxxxx.databases.neo4j.io"
AUTH = ("neo4j", "password")


async def get_agent_evaluations(driver, agent_id: str) -> list[dict]:
    """Async version of agent evaluation retrieval."""

    async def _query(tx, agent_id):
        result = await tx.run("""
            MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
            RETURN e.evaluation_id AS id,
                   e.ethos AS ethos,
                   e.logos AS logos,
                   e.pathos AS pathos,
                   e.trust AS trust,
                   e.created_at AS created_at
            ORDER BY e.created_at DESC
            LIMIT 50
        """, agent_id=agent_id)
        return [record.data() async for record in result]

    async with driver.session(database="neo4j") as session:
        return await session.execute_read(_query, agent_id)


async def store_evaluation(driver, agent_id: str, evaluation: dict) -> str:
    """Async version of evaluation storage."""

    async def _create(tx, agent_id, evaluation):
        result = await tx.run("""
            MERGE (a:Agent {agent_id: $agent_id})
            ON CREATE SET a.created_at = datetime(), a.evaluation_count = 0
            SET a.evaluation_count = a.evaluation_count + 1

            CREATE (e:Evaluation {
                evaluation_id: randomUUID(),
                ethos: $ethos,
                logos: $logos,
                pathos: $pathos,
                trust: $trust,
                flags: $flags,
                created_at: datetime()
            })
            CREATE (a)-[:EVALUATED]->(e)

            RETURN e.evaluation_id AS id
        """,
            agent_id=agent_id,
            ethos=evaluation["ethos"],
            logos=evaluation["logos"],
            pathos=evaluation["pathos"],
            trust=evaluation["trust"],
            flags=evaluation["flags"],
        )
        record = await result.single()
        return record["id"]

    async with driver.session(database="neo4j") as session:
        return await session.execute_write(_create, agent_id, evaluation)


async def main():
    async with AsyncGraphDatabase.driver(URI, auth=AUTH) as driver:
        await driver.verify_connectivity()

        # Store an evaluation
        eval_id = await store_evaluation(driver, "agent-001", {
            "ethos": 0.85,
            "logos": 0.92,
            "pathos": 0.78,
            "trust": "high",
            "flags": [],
        })
        print(f"Stored evaluation: {eval_id}")

        # Retrieve evaluations
        evals = await get_agent_evaluations(driver, "agent-001")
        for e in evals:
            print(e)

asyncio.run(main())
```

### execute_query() -- Simplified API

For simpler queries, `driver.execute_query()` combines session creation, transaction
management, and result consumption in one call:

```python
records, summary, keys = driver.execute_query(
    "MATCH (a:Agent) RETURN a.agent_id AS id, a.name AS name LIMIT 10",
    database_="neo4j",
    routing_="r",  # Route to a read replica
)

for record in records:
    print(record["id"], record["name"])
```

### Batch Operations with UNWIND

For bulk data loading (e.g., seeding the graph or importing evaluation histories),
use `UNWIND` to process many records in a single transaction:

```python
def seed_traits(driver):
    """Seed the 12 traits and 3 dimensions."""
    traits_data = [
        # Ethos
        {"name": "authority", "dimension": "Ethos", "description": "Source credibility and expertise"},
        {"name": "trustworthiness", "dimension": "Ethos", "description": "Reliability and consistency"},
        {"name": "goodwill", "dimension": "Ethos", "description": "Apparent care for audience wellbeing"},
        {"name": "competence", "dimension": "Ethos", "description": "Demonstrated knowledge and skill"},
        # Logos
        {"name": "evidence_quality", "dimension": "Logos", "description": "Strength and relevance of evidence"},
        {"name": "logical_coherence", "dimension": "Logos", "description": "Internal consistency of reasoning"},
        {"name": "completeness", "dimension": "Logos", "description": "Coverage of relevant considerations"},
        {"name": "accuracy", "dimension": "Logos", "description": "Factual correctness of claims"},
        # Pathos
        {"name": "emotional_balance", "dimension": "Pathos", "description": "Appropriate emotional tone"},
        {"name": "empathy", "dimension": "Pathos", "description": "Understanding of audience perspective"},
        {"name": "manipulation_absence", "dimension": "Pathos", "description": "Lack of manipulative appeals"},
        {"name": "sentiment_appropriateness", "dimension": "Pathos", "description": "Contextually fitting emotional content"},
    ]

    def _seed(tx, traits):
        tx.run("""
            UNWIND $traits AS t
            MERGE (dim:Dimension {name: t.dimension})
            MERGE (trait:Trait {name: t.name})
            ON CREATE SET trait.description = t.description
            MERGE (trait)-[:BELONGS_TO]->(dim)
        """, traits=traits)

    with driver.session(database="neo4j") as session:
        session.execute_write(_seed, traits_data)
```

### Key Best Practices

1. **One driver per application.** Drivers hold connection pools. Creating multiple drivers
   wastes resources.

2. **Always specify the database.** Omitting the `database` parameter forces an extra
   server round-trip.

3. **Use `execute_read()` for reads and `execute_write()` for writes.** This enables proper
   routing in clustered deployments (reads go to followers, writes go to the leader).

4. **Always use parameters.** Never concatenate values into Cypher strings.

5. **Close sessions.** Use context managers (`with` / `async with`) to ensure sessions are
   properly closed.

6. **Install the Rust extension.** `pip install neo4j-rust-ext` provides 3-10x speedup
   for the driver's internal operations.

---

## 7. Neo4j + FastAPI Patterns

### Lifespan-Based Driver Management

FastAPI's lifespan events are the recommended way to manage the Neo4j driver lifecycle.
The driver is created at startup and closed at shutdown.

```python
"""api/main.py -- FastAPI application with Neo4j integration."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from neo4j import AsyncGraphDatabase
from pydantic import BaseModel, Field


# ── Lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Neo4j driver lifecycle."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    # Create driver at startup
    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    await driver.verify_connectivity()
    app.state.neo4j_driver = driver

    yield  # Application runs here

    # Close driver at shutdown
    await driver.close()


app = FastAPI(title="Ethos API", lifespan=lifespan)


# ── Dependency Injection ──────────────────────────────────────────

async def get_neo4j_driver():
    """Dependency that provides the Neo4j driver."""
    return app.state.neo4j_driver


# ── Models ────────────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    text: str
    source: str | None = None

class EvaluationResponse(BaseModel):
    evaluation_id: str
    ethos: float = Field(ge=0.0, le=1.0)
    logos: float = Field(ge=0.0, le=1.0)
    pathos: float = Field(ge=0.0, le=1.0)
    trust: str
    flags: list[str] = []

class ReflectRequest(BaseModel):
    agent_id: str

class ReflectResponse(BaseModel):
    compassion: float = Field(ge=0.0, le=1.0)
    honesty: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    trend: str


# ── Endpoints ─────────────────────────────────────────────────────

@app.get("/health")
async def health(driver=Depends(get_neo4j_driver)):
    """Health check -- verifies Neo4j connectivity."""
    try:
        await driver.verify_connectivity()
        return {"status": "healthy", "neo4j": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {e}")


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluateRequest, driver=Depends(get_neo4j_driver)):
    """Evaluate text for trustworthiness and store in graph."""

    # 1. Run LLM evaluation (placeholder)
    from ethos_academy.evaluate import evaluate as run_eval
    result = run_eval(request.text, request.source)

    # 2. Store in Neo4j
    async def _store(tx, agent_id, result):
        record = await tx.run("""
            MERGE (a:Agent {agent_id: $agent_id})
            ON CREATE SET a.created_at = datetime(), a.evaluation_count = 0
            SET a.evaluation_count = a.evaluation_count + 1

            CREATE (e:Evaluation {
                evaluation_id: randomUUID(),
                ethos: $ethos,
                logos: $logos,
                pathos: $pathos,
                trust: $trust,
                flags: $flags,
                created_at: datetime()
            })
            CREATE (a)-[:EVALUATED]->(e)

            RETURN e.evaluation_id AS evaluation_id
        """,
            agent_id=agent_id,
            ethos=result.ethos,
            logos=result.logos,
            pathos=result.pathos,
            trust=result.trust,
            flags=result.flags,
        )
        return await record.single()

    agent_id = request.source or "anonymous"
    async with driver.session(database="neo4j") as session:
        record = await session.execute_write(_store, agent_id, result)

    return EvaluationResponse(
        evaluation_id=record["evaluation_id"],
        ethos=result.ethos,
        logos=result.logos,
        pathos=result.pathos,
        trust=result.trust,
        flags=result.flags,
    )


@app.post("/reflect", response_model=ReflectResponse)
async def reflect(request: ReflectRequest, driver=Depends(get_neo4j_driver)):
    """Reflect on an agent's evaluation history."""

    # 1. Fetch history from Neo4j
    async def _get_history(tx, agent_id):
        result = await tx.run("""
            MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
            RETURN e.ethos AS ethos, e.logos AS logos, e.pathos AS pathos,
                   e.trust AS trust, e.flags AS flags, e.created_at AS created_at
            ORDER BY e.created_at DESC
            LIMIT 50
        """, agent_id=agent_id)
        return [record.data() async for record in result]

    async with driver.session(database="neo4j") as session:
        history = await session.execute_read(_get_history, request.agent_id)

    if not history:
        raise HTTPException(status_code=404, detail="No evaluations found for agent")

    # 2. Run reflection (placeholder)
    from ethos_academy.reflect import reflect as run_reflect
    result = run_reflect(request.agent_id)

    return ReflectResponse(
        compassion=result.compassion,
        honesty=result.honesty,
        accuracy=result.accuracy,
        trend=result.trend,
    )


@app.get("/agents/{agent_id}/graph")
async def agent_graph(agent_id: str, driver=Depends(get_neo4j_driver)):
    """Return graph data for visualization of an agent's trust network."""

    async def _get_graph(tx, agent_id):
        result = await tx.run("""
            MATCH (a:Agent {agent_id: $agent_id})-[ev:EVALUATED]->(e:Evaluation)
            OPTIONAL MATCH (e)-[det:DETECTED]->(t:Trait)-[bt:BELONGS_TO]->(d:Dimension)
            RETURN a, ev, e, det, t, bt, d
            LIMIT 200
        """, agent_id=agent_id)

        nodes = []
        links = []
        seen_nodes = set()

        async for record in result:
            for key in ["a", "e", "t", "d"]:
                node = record.get(key)
                if node and id(node) not in seen_nodes:
                    seen_nodes.add(id(node))
                    props = dict(node.items())
                    props["_labels"] = list(node.labels)
                    props["_id"] = node.element_id
                    nodes.append(props)

            for key in ["ev", "det", "bt"]:
                rel = record.get(key)
                if rel:
                    links.append({
                        "source": rel.start_node.element_id,
                        "target": rel.end_node.element_id,
                        "type": rel.type,
                        **dict(rel.items()),
                    })

        return {"nodes": nodes, "links": links}

    async with driver.session(database="neo4j") as session:
        return await session.execute_read(_get_graph, agent_id)
```

### Middleware for Request-Scoped Sessions

For more complex applications, you may want request-scoped database sessions:

```python
from fastapi import Request

async def get_neo4j_session(request: Request):
    """Dependency that provides a request-scoped Neo4j session."""
    driver = request.app.state.neo4j_driver
    async with driver.session(database="neo4j") as session:
        yield session
```

This ensures each request gets its own session that is automatically closed when
the request completes.

### Error Handling

```python
from neo4j.exceptions import (
    ServiceUnavailable,
    AuthError,
    ClientError,
    TransientError,
)

@app.exception_handler(ServiceUnavailable)
async def neo4j_unavailable_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={"detail": "Graph database temporarily unavailable"},
    )

@app.exception_handler(AuthError)
async def neo4j_auth_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Graph database authentication failed"},
    )
```

---

## 8. Graph Data Science Library (GDS)

The Neo4j Graph Data Science library provides production-quality implementations of graph
algorithms. For Ethos, these algorithms enable Phronesis analysis, community detection,
and influence scoring.

> **Note:** GDS is available on Neo4j Aura Professional+ and self-hosted Neo4j with the
> GDS plugin. It is not available on the Aura Free tier.

### GDS Workflow

Every GDS operation follows three steps:

1. **Project a graph** -- Create an in-memory projection of the subgraph you want to analyze
2. **Run an algorithm** -- Execute the algorithm on the projected graph
3. **Consume results** -- Stream results back or write them to the database

### Graph Projection

```cypher
-- Project the Ethos trust network into memory
MATCH (a:Agent)
OPTIONAL MATCH (a)-[ev:EVALUATED]->(e:Evaluation)
WITH gds.graph.project(
  'ethos-trust-graph',
  a,
  e,
  {
    sourceNodeLabels: labels(a),
    targetNodeLabels: labels(e),
    relationshipProperties: ev { .created_at }
  }
) AS g
RETURN g.graphName AS graph, g.nodeCount AS nodes, g.relationshipCount AS rels
```

### PageRank -- Trust Influence Scoring

PageRank identifies the most influential nodes in the graph. For Ethos, this reveals
which agents have the most trusted evaluation histories:

```cypher
-- Run PageRank on the trust network
CALL gds.pageRank.stream('ethos-trust-graph', {
  maxIterations: 20,
  dampingFactor: 0.85
})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS node, score
WHERE 'Agent' IN labels(node)
RETURN node.agent_id AS agent, node.name AS name, score
ORDER BY score DESC
LIMIT 20
```

**Write PageRank scores back to nodes:**

```cypher
CALL gds.pageRank.write('ethos-trust-graph', {
  writeProperty: 'pagerank_score',
  maxIterations: 20,
  dampingFactor: 0.85
})
YIELD nodePropertiesWritten, ranIterations
RETURN nodePropertiesWritten, ranIterations
```

### Louvain -- Community Detection

Louvain detects communities of agents with similar trust patterns. This can reveal
clusters of agents that behave similarly (e.g., a group of highly manipulative agents,
or a cluster of consistently trustworthy ones).

```cypher
-- Detect communities in the trust graph
CALL gds.louvain.stream('ethos-trust-graph')
YIELD nodeId, communityId, intermediateCommunityIds
WITH gds.util.asNode(nodeId) AS node, communityId
WHERE 'Agent' IN labels(node)
RETURN node.agent_id AS agent, communityId
ORDER BY communityId, agent
```

**With weighted relationships:**

```cypher
-- Weight by trust scores for more meaningful communities
CALL gds.louvain.stream('ethos-trust-graph', {
  relationshipWeightProperty: 'weight'
})
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS node, communityId
RETURN communityId, collect(node.agent_id) AS agents, count(*) AS size
ORDER BY size DESC
```

### Leiden -- Improved Community Detection

Leiden addresses limitations in Louvain by guaranteeing that communities are
well-connected:

```cypher
CALL gds.leiden.stream('ethos-trust-graph', {
  maxLevels: 10,
  gamma: 1.0
})
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).agent_id AS agent, communityId
ORDER BY communityId
```

### Label Propagation

A fast community detection algorithm that works by propagating labels through the
network. Useful for quickly identifying clusters:

```cypher
CALL gds.labelPropagation.stream('ethos-trust-graph')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).agent_id AS agent, communityId
ORDER BY communityId
```

### Betweenness Centrality -- Bridge Nodes

Identifies nodes that act as bridges between different parts of the trust network.
Agents with high betweenness centrality connect otherwise disconnected trust clusters:

```cypher
CALL gds.betweennessCentrality.stream('ethos-trust-graph')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS node, score
WHERE 'Agent' IN labels(node) AND score > 0
RETURN node.agent_id AS agent, score AS bridge_score
ORDER BY bridge_score DESC
LIMIT 10
```

### Node Similarity

Find agents that have been evaluated similarly (detecting traits in the same patterns):

```cypher
CALL gds.nodeSimilarity.stream('ethos-trust-graph', {
  similarityCutoff: 0.5
})
YIELD node1, node2, similarity
WITH gds.util.asNode(node1) AS a1, gds.util.asNode(node2) AS a2, similarity
WHERE 'Agent' IN labels(a1) AND 'Agent' IN labels(a2)
RETURN a1.agent_id AS agent1, a2.agent_id AS agent2, similarity
ORDER BY similarity DESC
LIMIT 20
```

### Shortest Path -- Trust Paths

Find the shortest trust path between two agents:

```cypher
MATCH (source:Agent {agent_id: $from_agent}), (target:Agent {agent_id: $to_agent})
CALL gds.shortestPath.dijkstra.stream('ethos-trust-graph', {
  sourceNode: source,
  targetNode: target
})
YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path
RETURN
  [nodeId IN nodeIds | gds.util.asNode(nodeId).agent_id] AS agents,
  totalCost,
  length(path) AS hops
```

### FastRP -- Node Embeddings

Generate vector embeddings for nodes, which can be used for ML-based trust prediction:

```cypher
CALL gds.fastRP.stream('ethos-trust-graph', {
  embeddingDimension: 128,
  iterationWeights: [0.0, 1.0, 1.0]
})
YIELD nodeId, embedding
WITH gds.util.asNode(nodeId) AS node, embedding
WHERE 'Agent' IN labels(node)
RETURN node.agent_id AS agent, embedding
```

### Triangle Count and Clustering Coefficient

Measure how tightly connected trust neighborhoods are:

```cypher
-- Count triangles (indicates trust clusters)
CALL gds.triangleCount.stream('ethos-trust-graph')
YIELD nodeId, triangleCount
WITH gds.util.asNode(nodeId) AS node, triangleCount
WHERE triangleCount > 0
RETURN node.agent_id AS agent, triangleCount
ORDER BY triangleCount DESC

-- Local clustering coefficient
CALL gds.localClusteringCoefficient.stream('ethos-trust-graph')
YIELD nodeId, localClusteringCoefficient
WITH gds.util.asNode(nodeId) AS node, localClusteringCoefficient AS coeff
WHERE coeff > 0
RETURN node.agent_id AS agent, coeff
ORDER BY coeff DESC
```

### GDS from Python

```python
from neo4j import GraphDatabase

def run_pagerank(driver, graph_name: str = "ethos-trust-graph"):
    """Run PageRank and return top agents by influence."""

    def _pagerank(tx, graph_name):
        # Project the graph
        tx.run("""
            MATCH (a:Agent)
            OPTIONAL MATCH (a)-[r:EVALUATED]->(e:Evaluation)
            WITH gds.graph.project($graph_name, a, e) AS g
            RETURN g.graphName
        """, graph_name=graph_name)

        # Run PageRank
        result = tx.run("""
            CALL gds.pageRank.stream($graph_name, {
                maxIterations: 20,
                dampingFactor: 0.85
            })
            YIELD nodeId, score
            WITH gds.util.asNode(nodeId) AS node, score
            WHERE 'Agent' IN labels(node)
            RETURN node.agent_id AS agent_id, score
            ORDER BY score DESC
            LIMIT 20
        """, graph_name=graph_name)

        return [record.data() for record in result]

    with driver.session(database="neo4j") as session:
        return session.execute_read(_pagerank, graph_name)


def detect_communities(driver, graph_name: str = "ethos-trust-graph"):
    """Detect agent communities using Louvain."""

    def _louvain(tx, graph_name):
        result = tx.run("""
            CALL gds.louvain.stream($graph_name)
            YIELD nodeId, communityId
            WITH gds.util.asNode(nodeId) AS node, communityId
            WHERE 'Agent' IN labels(node)
            RETURN communityId, collect(node.agent_id) AS agents, count(*) AS size
            ORDER BY size DESC
        """, graph_name=graph_name)
        return [record.data() for record in result]

    with driver.session(database="neo4j") as session:
        return session.execute_read(_louvain, graph_name)
```

### Algorithm Selection Guide for Ethos

| Ethos Use Case | Algorithm | Why |
|----------------|-----------|-----|
| Agent influence ranking | PageRank | Finds most-evaluated, well-connected agents |
| Trust cluster detection | Louvain / Leiden | Groups agents with similar evaluation patterns |
| Bridge agent identification | Betweenness Centrality | Finds agents connecting trust communities |
| Similar agent discovery | Node Similarity | Identifies agents with matching trait profiles |
| Trust path analysis | Dijkstra Shortest Path | Traces trust connections between agents |
| Anomaly detection | Local Clustering Coefficient | Low coefficient = potential outlier |
| ML feature generation | FastRP | Vector embeddings for downstream classification |
| Manipulation network detection | Weakly Connected Components | Isolates disconnected subgraphs |

---

## 9. Performance and Optimization

### Indexes and Constraints

Indexes are the single most important performance optimization. Without them, every query
requires a full scan of all nodes with a given label.

**Create constraints (which also create indexes):**

```cypher
-- Unique constraints (automatically create indexes)
CREATE CONSTRAINT agent_id_unique IF NOT EXISTS
  FOR (a:Agent) REQUIRE a.agent_id IS UNIQUE;

CREATE CONSTRAINT evaluation_id_unique IF NOT EXISTS
  FOR (e:Evaluation) REQUIRE e.evaluation_id IS UNIQUE;

CREATE CONSTRAINT trait_name_unique IF NOT EXISTS
  FOR (t:Trait) REQUIRE t.name IS UNIQUE;

CREATE CONSTRAINT dimension_name_unique IF NOT EXISTS
  FOR (d:Dimension) REQUIRE d.name IS UNIQUE;

CREATE CONSTRAINT pattern_id_unique IF NOT EXISTS
  FOR (p:Pattern) REQUIRE p.pattern_id IS UNIQUE;
```

**Create additional indexes for frequently queried properties:**

```cypher
-- Range index for timestamp-based queries
CREATE INDEX eval_created_at IF NOT EXISTS
  FOR (e:Evaluation) ON (e.created_at);

-- Range index for trust level filtering
CREATE INDEX eval_trust IF NOT EXISTS
  FOR (e:Evaluation) ON (e.trust);

-- Composite index for agent + trust queries
CREATE INDEX agent_trust IF NOT EXISTS
  FOR (a:Agent) ON (a.agent_id, a.trust_score);
```

**Verify indexes are being used:**

```cypher
-- Show all indexes
SHOW INDEXES;

-- Explain a query to see if indexes are used
EXPLAIN MATCH (a:Agent {agent_id: "agent-001"}) RETURN a;

-- Profile a query to see actual performance
PROFILE MATCH (a:Agent {agent_id: "agent-001"})-[:EVALUATED]->(e:Evaluation)
RETURN e ORDER BY e.created_at DESC LIMIT 10;
```

### Query Optimization Techniques

**1. Reduce the working set early.**

Move `LIMIT`, `DISTINCT`, and filtering as early as possible in the query chain:

```cypher
-- Good: filter early
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
WITH e ORDER BY e.created_at DESC LIMIT 10
MATCH (e)-[:DETECTED]->(t:Trait)
RETURN e, collect(t) AS traits

-- Bad: filter late (processes all evaluations before limiting)
MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)-[:DETECTED]->(t:Trait)
RETURN e, collect(t) AS traits
ORDER BY e.created_at DESC
LIMIT 10
```

**2. Always specify node labels.**

Labels act as a first-pass filter, limiting which nodes the query planner considers:

```cypher
-- Good: labels specified
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
RETURN a, e

-- Bad: no labels (scans all nodes)
MATCH (a)-[:EVALUATED]->(e)
RETURN a, e
```

**3. Use parameters for query plan caching.**

Neo4j caches query execution plans. Parameterized queries share plans; string-interpolated
queries do not:

```python
# Good: parameterized (plan is cached and reused)
session.run("MATCH (a:Agent {agent_id: $id}) RETURN a", id="agent-001")

# Bad: string interpolation (new plan compiled each time)
session.run(f"MATCH (a:Agent {{agent_id: '{agent_id}'}}) RETURN a")
```

**4. Use CREATE for known-new data, MERGE for upserts.**

`MERGE` requires checking if the node exists before creating. If you know the data is
new (e.g., a new evaluation), use `CREATE` directly:

```cypher
-- New evaluation: use CREATE (one lookup)
CREATE (e:Evaluation {evaluation_id: randomUUID(), ethos: $ethos, ...})

-- Agent might exist: use MERGE (two lookups: find + create if missing)
MERGE (a:Agent {agent_id: $agent_id})
```

**5. Batch writes with UNWIND.**

Instead of sending N separate queries, batch them into one:

```python
# Good: one query for N evaluations
def batch_store(tx, evaluations):
    tx.run("""
        UNWIND $evaluations AS eval
        MERGE (a:Agent {agent_id: eval.agent_id})
        CREATE (e:Evaluation {
            evaluation_id: eval.id,
            ethos: eval.ethos,
            logos: eval.logos,
            pathos: eval.pathos,
            trust: eval.trust,
            flags: eval.flags,
            created_at: datetime()
        })
        CREATE (a)-[:EVALUATED]->(e)
    """, evaluations=evaluations)

# Bad: N separate queries
for eval in evaluations:
    tx.run("CREATE (e:Evaluation {...})", **eval)
```

### Memory and Configuration (Self-Hosted)

For the local Docker deployment, you can tune Neo4j through environment variables:

```yaml
# docker-compose.yml
neo4j:
  image: neo4j:5
  environment:
    - NEO4J_AUTH=neo4j/password
    # Page cache: should cover your data size
    - NEO4J_server_memory_pagecache_size=512m
    # Heap: for query processing
    - NEO4J_server_memory_heap_initial__size=256m
    - NEO4J_server_memory_heap_max__size=512m
    # Transaction log retention
    - NEO4J_db_tx__log_rotation_retention__policy=2 days
```

**Rules of thumb:**

- **Page cache** should be large enough to hold your entire graph in memory. For the
  Ethos free-tier scale (200k nodes), 512 MB is more than sufficient.
- **Heap** should be 256 MB to 1 GB for development workloads.
- As the graph grows, monitor with `:sysinfo` in Neo4j Browser.

### Growth Planning

The Ethos graph will grow primarily through evaluations. Estimate growth rate:

| Component | Per Evaluation | After 10K Evaluations |
|-----------|---------------|----------------------|
| Evaluation nodes | 1 | 10,000 |
| EVALUATED relationships | 1 | 10,000 |
| DETECTED relationships | ~4 (traits per eval) | ~40,000 |
| Agent nodes | 0-1 (MERGE) | ~100-1,000 |
| Trait nodes | 0 (fixed at 12) | 12 |
| Dimension nodes | 0 (fixed at 3) | 3 |

At **200,000 evaluations**, you would have roughly:

- ~200K Evaluation nodes
- ~200K EVALUATED relationships
- ~800K DETECTED relationships
- ~1K-10K Agent nodes
- 12 Trait nodes, 3 Dimension nodes

This fits comfortably within the Aura Free tier (200K nodes, 400K relationships) only
for the first ~100K evaluations. Plan to upgrade to Professional tier as the graph
grows beyond this.

### Monitoring Queries

```cypher
-- Count all nodes by label
MATCH (n)
RETURN labels(n) AS label, count(n) AS count
ORDER BY count DESC

-- Count all relationships by type
MATCH ()-[r]->()
RETURN type(r) AS type, count(r) AS count
ORDER BY count DESC

-- Find the most-evaluated agents
MATCH (a:Agent)
RETURN a.agent_id, a.evaluation_count
ORDER BY a.evaluation_count DESC
LIMIT 20

-- Check index usage
SHOW INDEXES YIELD name, state, populationPercent
RETURN name, state, populationPercent
```

---

## Appendix: Complete Schema Setup Script

Run this once to initialize the Ethos graph schema:

```cypher
// ── Constraints & Indexes ─────────────────────────────────────

CREATE CONSTRAINT agent_id_unique IF NOT EXISTS
  FOR (a:Agent) REQUIRE a.agent_id IS UNIQUE;

CREATE CONSTRAINT evaluation_id_unique IF NOT EXISTS
  FOR (e:Evaluation) REQUIRE e.evaluation_id IS UNIQUE;

CREATE CONSTRAINT trait_name_unique IF NOT EXISTS
  FOR (t:Trait) REQUIRE t.name IS UNIQUE;

CREATE CONSTRAINT dimension_name_unique IF NOT EXISTS
  FOR (d:Dimension) REQUIRE d.name IS UNIQUE;

CREATE CONSTRAINT pattern_id_unique IF NOT EXISTS
  FOR (p:Pattern) REQUIRE p.pattern_id IS UNIQUE;

CREATE INDEX eval_created_at IF NOT EXISTS
  FOR (e:Evaluation) ON (e.created_at);

CREATE INDEX eval_trust IF NOT EXISTS
  FOR (e:Evaluation) ON (e.trust);

// ── Dimensions ────────────────────────────────────────────────

MERGE (ethos:Dimension {name: "Ethos"})
SET ethos.description = "Credibility, authority, and ethical standing";

MERGE (logos:Dimension {name: "Logos"})
SET logos.description = "Logical coherence, evidence quality, and reasoning";

MERGE (pathos:Dimension {name: "Pathos"})
SET pathos.description = "Emotional appeal, manipulation, and sentiment balance";

// ── Traits ────────────────────────────────────────────────────

// Ethos traits
MERGE (t:Trait {name: "authority"}) SET t.description = "Source credibility and expertise"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Ethos"});

MERGE (t:Trait {name: "trustworthiness"}) SET t.description = "Reliability and consistency"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Ethos"});

MERGE (t:Trait {name: "goodwill"}) SET t.description = "Apparent care for audience wellbeing"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Ethos"});

MERGE (t:Trait {name: "competence"}) SET t.description = "Demonstrated knowledge and skill"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Ethos"});

// Logos traits
MERGE (t:Trait {name: "evidence_quality"}) SET t.description = "Strength and relevance of evidence"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Logos"});

MERGE (t:Trait {name: "logical_coherence"}) SET t.description = "Internal consistency of reasoning"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Logos"});

MERGE (t:Trait {name: "completeness"}) SET t.description = "Coverage of relevant considerations"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Logos"});

MERGE (t:Trait {name: "accuracy"}) SET t.description = "Factual correctness of claims"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Logos"});

// Pathos traits
MERGE (t:Trait {name: "emotional_balance"}) SET t.description = "Appropriate emotional tone"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Pathos"});

MERGE (t:Trait {name: "empathy"}) SET t.description = "Understanding of audience perspective"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Pathos"});

MERGE (t:Trait {name: "manipulation_absence"}) SET t.description = "Lack of manipulative appeals"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Pathos"});

MERGE (t:Trait {name: "sentiment_appropriateness"}) SET t.description = "Contextually fitting emotional content"
MERGE (t)-[:BELONGS_TO]->(:Dimension {name: "Pathos"});
```

---

## Appendix: Ethos Graph Service Module

A complete, production-ready graph service module for Ethos:

```python
"""ethos_academy/graph.py -- Neo4j graph database integration."""

import os
from datetime import datetime

from neo4j import AsyncGraphDatabase, AsyncDriver
from ethos_academy.models import EvaluationResult, ReflectionResult


class GraphService:
    """Manages all Neo4j interactions for Ethos."""

    def __init__(self, driver: AsyncDriver):
        self._driver = driver
        self._database = os.getenv("NEO4J_DATABASE", "neo4j")

    @classmethod
    async def connect(cls) -> "GraphService":
        """Create a GraphService with a new driver connection."""
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        await driver.verify_connectivity()
        return cls(driver)

    async def close(self):
        """Close the driver connection."""
        await self._driver.close()

    # ── Write Operations ──────────────────────────────────────

    async def store_evaluation(
        self, agent_id: str, result: EvaluationResult, source: str | None = None
    ) -> str:
        """Store an evaluation result and link it to the agent."""

        async def _write(tx, agent_id, result, source):
            record = await tx.run("""
                MERGE (a:Agent {agent_id: $agent_id})
                ON CREATE SET a.created_at = datetime(), a.evaluation_count = 0
                SET a.evaluation_count = a.evaluation_count + 1

                CREATE (e:Evaluation {
                    evaluation_id: randomUUID(),
                    ethos: $ethos,
                    logos: $logos,
                    pathos: $pathos,
                    trust: $trust,
                    flags: $flags,
                    source: $source,
                    created_at: datetime()
                })
                CREATE (a)-[:EVALUATED]->(e)

                // Update aggregate trust score
                WITH a, e
                OPTIONAL MATCH (a)-[:EVALUATED]->(all_e:Evaluation)
                WITH a, e, avg(all_e.ethos + all_e.logos + all_e.pathos) / 3.0 AS avg_trust
                SET a.trust_score = avg_trust

                RETURN e.evaluation_id AS evaluation_id
            """,
                agent_id=agent_id,
                ethos=result.ethos,
                logos=result.logos,
                pathos=result.pathos,
                trust=result.trust,
                flags=result.flags,
                source=source or "unknown",
            )
            data = await record.single()
            return data["evaluation_id"]

        async with self._driver.session(database=self._database) as session:
            return await session.execute_write(_write, agent_id, result, source)

    async def store_traits(
        self, evaluation_id: str, traits: list[dict]
    ) -> None:
        """Link detected traits to an evaluation.

        traits: [{"name": "honesty", "score": 0.85, "confidence": 0.9}, ...]
        """

        async def _write(tx, evaluation_id, traits):
            await tx.run("""
                MATCH (e:Evaluation {evaluation_id: $eval_id})
                UNWIND $traits AS t
                MERGE (trait:Trait {name: t.name})
                CREATE (e)-[:DETECTED {score: t.score, confidence: t.confidence}]->(trait)
            """, eval_id=evaluation_id, traits=traits)

        async with self._driver.session(database=self._database) as session:
            await session.execute_write(_write, evaluation_id, traits)

    async def store_pattern(
        self, agent_id: str, pattern: dict
    ) -> None:
        """Record a detected behavioral pattern for an agent."""

        async def _write(tx, agent_id, pattern):
            await tx.run("""
                MATCH (a:Agent {agent_id: $agent_id})
                MERGE (p:Pattern {pattern_id: $pattern_id})
                ON CREATE SET
                    p.name = $name,
                    p.description = $description,
                    p.severity = $severity,
                    p.confidence = $confidence
                MERGE (a)-[m:MATCHES]->(p)
                ON CREATE SET m.first_seen = datetime(), m.occurrence_count = 1
                ON MATCH SET m.occurrence_count = m.occurrence_count + 1, m.last_seen = datetime()
            """,
                agent_id=agent_id,
                pattern_id=pattern["pattern_id"],
                name=pattern["name"],
                description=pattern["description"],
                severity=pattern.get("severity", "info"),
                confidence=pattern.get("confidence", 0.5),
            )

        async with self._driver.session(database=self._database) as session:
            await session.execute_write(_write, agent_id, pattern)

    # ── Read Operations ───────────────────────────────────────

    async def get_evaluation_history(
        self, agent_id: str, limit: int = 50
    ) -> list[dict]:
        """Retrieve evaluation history for an agent."""

        async def _read(tx, agent_id, limit):
            result = await tx.run("""
                MATCH (a:Agent {agent_id: $agent_id})-[:EVALUATED]->(e:Evaluation)
                RETURN e.evaluation_id AS id,
                       e.ethos AS ethos,
                       e.logos AS logos,
                       e.pathos AS pathos,
                       e.trust AS trust,
                       e.flags AS flags,
                       e.created_at AS created_at
                ORDER BY e.created_at DESC
                LIMIT $limit
            """, agent_id=agent_id, limit=limit)
            return [record.data() async for record in result]

        async with self._driver.session(database=self._database) as session:
            return await session.execute_read(_read, agent_id, limit)

    async def get_agent_summary(self, agent_id: str) -> dict | None:
        """Get an agent's trust summary with aggregated scores."""

        async def _read(tx, agent_id):
            result = await tx.run("""
                MATCH (a:Agent {agent_id: $agent_id})
                OPTIONAL MATCH (a)-[:EVALUATED]->(e:Evaluation)
                WITH a,
                    count(e) AS eval_count,
                    avg(e.ethos) AS avg_ethos,
                    avg(e.logos) AS avg_logos,
                    avg(e.pathos) AS avg_pathos,
                    collect(e.trust) AS trust_levels
                RETURN a.agent_id AS agent_id,
                       a.name AS name,
                       a.trust_score AS trust_score,
                       eval_count,
                       avg_ethos,
                       avg_logos,
                       avg_pathos,
                       trust_levels
            """, agent_id=agent_id)
            record = await result.single()
            return record.data() if record else None

        async with self._driver.session(database=self._database) as session:
            return await session.execute_read(_read, agent_id)

    async def get_trust_network(self, limit: int = 200) -> dict:
        """Return the full trust network for visualization."""

        async def _read(tx, limit):
            result = await tx.run("""
                MATCH (a:Agent)-[ev:EVALUATED]->(e:Evaluation)
                WITH a, ev, e
                LIMIT $limit
                OPTIONAL MATCH (e)-[det:DETECTED]->(t:Trait)-[bt:BELONGS_TO]->(d:Dimension)
                RETURN a, ev, e, det, t, bt, d
            """, limit=limit)

            nodes = {}
            links = []

            async for record in result:
                for key in ["a", "e", "t", "d"]:
                    node = record.get(key)
                    if node and node.element_id not in nodes:
                        nodes[node.element_id] = {
                            "id": node.element_id,
                            "labels": list(node.labels),
                            **dict(node.items()),
                        }

                for key in ["ev", "det", "bt"]:
                    rel = record.get(key)
                    if rel:
                        links.append({
                            "source": rel.start_node.element_id,
                            "target": rel.end_node.element_id,
                            "type": rel.type,
                            **dict(rel.items()),
                        })

            return {"nodes": list(nodes.values()), "links": links}

        async with self._driver.session(database=self._database) as session:
            return await session.execute_read(_read, limit)

    async def get_flagged_agents(self, flag: str) -> list[dict]:
        """Find agents with a specific trust flag."""

        async def _read(tx, flag):
            result = await tx.run("""
                MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
                WHERE $flag IN e.flags
                RETURN DISTINCT a.agent_id AS agent_id,
                       a.name AS name,
                       count(e) AS flagged_count
                ORDER BY flagged_count DESC
            """, flag=flag)
            return [record.data() async for record in result]

        async with self._driver.session(database=self._database) as session:
            return await session.execute_read(_read, flag)
```

---

## Sources

### Neo4j Aura and Pricing
- [Neo4j Pricing](https://neo4j.com/pricing/)
- [Aura Free Tier FAQ](https://support.neo4j.com/s/article/16094506528787-Support-resources-and-FAQ-for-Aura-Free-Tier)
- [AuraDB FAQ](https://neo4j.com/cloud/platform/aura-graph-database/faq/)

### Knowledge Graph Modeling
- [How to Build a Knowledge Graph in 7 Steps](https://neo4j.com/blog/knowledge-graph/how-to-build-knowledge-graph/)
- [Designing a Knowledge Graph with Neo4j](https://medium.com/@vdondeti.naidu/designing-a-knowledge-graph-with-neo4j-ontology-data-modeling-and-real-world-graph-thinking-77b29a02a217)
- [Graph Data Modeling Core Principles](https://neo4j.com/graphacademy/training-gdm-40/03-graph-data-modeling-core-principles/)
- [Tutorial: Create a Graph Data Model](https://neo4j.com/docs/getting-started/data-modeling/tutorial-data-modeling/)

### Cypher Query Language
- [Cypher Manual Introduction](https://neo4j.com/docs/cypher-manual/current/introduction/)
- [Basic Queries](https://neo4j.com/docs/cypher-manual/current/queries/basic/)
- [Cypher Decoded for Beginners](https://neo4j.com/blog/developer/cypher-decoded-for-beginners/)

### Trust and Reputation Systems
- [CirclesUBI Trust Graph in Neo4j](https://github.com/ice09/circlesubi-trustgraph-neo4j)
- [Social Networks in the Database](https://neo4j.com/blog/social-networks-in-the-database-using-a-graph-database/)
- [Social Network Workshop](https://github.com/thobe/social-network-workshop)

### Visualization
- [Graph Visualization Tools](https://neo4j.com/docs/getting-started/graph-visualization/graph-visualization-tools/)
- [15 Best Graph Visualization Tools](https://neo4j.com/blog/graph-visualization/neo4j-graph-visualization-tools/)
- [Neovis.js](https://github.com/neo4j-contrib/neovis.js)
- [Graph Visualization with Neovis.js](https://medium.com/neo4j/graph-visualization-with-neo4j-using-neovis-js-a2ecaaa7c379)

### Python Integration
- [Neo4j Python Driver Manual](https://neo4j.com/docs/python-manual/current/)
- [Python Driver API](https://neo4j.com/docs/api/python-driver/current/)
- [Async API Documentation](https://neo4j.com/docs/api/python-driver/current/async_api.html)
- [Driver Best Practices](https://neo4j.com/blog/developer/neo4j-driver-best-practices/)
- [Performance Recommendations](https://neo4j.com/docs/python-manual/current/performance/)

### FastAPI Integration
- [Neo4j Python FastAPI Example](https://github.com/prrao87/neo4j-python-fastapi)
- [Neo4j for Pythonistas](https://thedataquarry.com/blog/neo4j-python-2/)
- [FastAPI Neo4j Example - Neontology](https://neontology.readthedocs.io/en/latest/fastapi/)
- [The Simplest Way to Make FastAPI Neo4j Work](https://hoop.dev/blog/the-simplest-way-to-make-fastapi-neo4j-work-like-it-should/)

### Graph Data Science
- [GDS Algorithms Overview](https://neo4j.com/docs/graph-data-science/current/algorithms/)
- [Community Detection Algorithms](https://neo4j.com/docs/graph-data-science/current/algorithms/community/)
- [Louvain Algorithm](https://neo4j.com/docs/graph-data-science/current/algorithms/louvain/)
- [GDS Introduction](https://neo4j.com/docs/graph-data-science/current/introduction/)

### Performance and Optimization
- [Query Optimization Techniques](https://medium.com/@jhahimanshu3636/query-optimization-in-neo4j-four-key-techniques-to-supercharge-your-cypher-queries-cf38aa5c7122)
- [Impact of Indexes on Query Performance](https://neo4j.com/docs/cypher-manual/current/indexes/search-performance-indexes/using-indexes/)
- [Neo4j Performance Architecture](https://graphable.ai/blog/neo4j-performance/)
- [Constraints Syntax](https://neo4j.com/docs/cypher-manual/current/constraints/syntax/)
- [Neo4j Optimization Tips](https://sease.io/2024/09/neo4j-optimization-tips.html)
