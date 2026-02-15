---
description: Neo4j and Cypher best practices for the Ethos project. Query patterns, sync driver usage, and project conventions.
allowed-tools: [Read, Glob, Grep, Bash]
---

# Neo4j Reference

Load the Neo4j skill context and help the user with their graph-related question.

## Context

Read the following files to understand the current graph implementation:

1. `ethos/graph/service.py` — driver lifecycle
2. `ethos/graph/read.py` — read query patterns
3. `ethos/graph/write.py` — write query patterns
4. `ethos/graph/cohort.py` — aggregation patterns
5. `ethos/graph/balance.py` — computed property patterns
6. `docs/evergreen-architecture/neo4j-schema.md` — full schema reference

## Rules

- All Cypher lives in `ethos/graph/` — nowhere else
- All code is SYNC — no async driver
- Always hash agent IDs with `hash_agent_id()` before graph operations
- Always check `service.connected` before querying
- Always wrap in try/except, return graceful defaults
- Store message content on Evaluation nodes alongside scores and metadata
- Use `$param` parameters, never string interpolation
- MERGE for Agent nodes, CREATE for Evaluation nodes
- Log at `warning` level on failure, never raise

## User Question

$ARGUMENTS
