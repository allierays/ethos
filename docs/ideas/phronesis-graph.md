# Phronesis Graph — NVL Visualization in Academy

## Problem

The Phronesis graph is the "wow" moment of Ethos — the six-layer architecture connecting Aristotelian dimensions to constitutional values through 12 traits, 153 indicators, and 8 sabotage patterns. But it's invisible. The graph only exists inside Neo4j Browser, accessible via raw Cypher. Nobody sees the taxonomy backbone, agent trust trails, or how evaluations connect to constitutional values unless they write queries.

For the hackathon demo, the graph needs to be visible, interactive, and embedded in the Academy dashboard.

## Solution

Embed Neo4j's own visualization engine — **NVL (Neo4j Visualization Library)** — into the Academy Next.js app. NVL is the same rendering engine that powers Bloom and Explore. It's freely available on npm as `@neo4j-nvl/react`.

Two surfaces:
1. **Full-page `/graph` route** — The complete Phronesis visualization with the taxonomy backbone, agents, evaluations, and detected indicators. Click an Agent node to open a detail sidebar.
2. **Dashboard preview panel** — A smaller, read-only graph preview on the main dashboard that links to the full `/graph` page.

## User Stories

- As a hackathon judge, I want to see the entire Ethos framework as an interactive graph so I can understand how the six layers connect
- As a developer, I want to click an Agent node and see their trust profile so I can explore behavioral patterns visually
- As a demo presenter, I want the graph visible on the dashboard so I can show it without navigating away

## Scope

### In Scope
- Install `@neo4j-nvl/react` in Academy
- New `GET /graph` API endpoint returning nodes + relationships in NVL format
- New Cypher query pulling semantic layer (Dimensions, Traits, Indicators, ConstitutionalValues, Patterns) + episodic data (Agents, recent Evaluations, DETECTED relationships)
- Full-page `/graph` route with `InteractiveNvlWrapper`
- Agent detail sidebar on click
- Dashboard preview panel
- Node color-coding by type and status
- Node sizing by importance/evaluation count

### Out of Scope
- EVALUATED_MESSAGE_FROM network (agent-to-agent trust) — future feature
- CROSS_REFERENCES relationships between indicators — not yet seeded
- EXHIBITS_PATTERN relationships — not yet created by the pipeline
- Real-time graph updates (WebSocket) — static fetch on load is fine
- Graph editing/mutation from the UI
- HardConstraint and LegitimacyTest nodes — keep the visualization focused

## Architecture

### Directory Structure

**Backend (Python):**
```
ethos/graph/visualization.py     # NEW — Cypher query to pull subgraph for NVL
api/main.py                      # MODIFY — add GET /graph endpoint
ethos/shared/models.py           # MODIFY — add GraphData, GraphNode, GraphRel models
ethos/__init__.py                # MODIFY — export get_graph_data
```

**Frontend (TypeScript):**
```
academy/components/PhronesisGraph.tsx      # NEW — NVL wrapper component
academy/components/AgentDetailSidebar.tsx  # NEW — sidebar on agent click
academy/components/GraphPreview.tsx        # NEW — small dashboard preview
academy/app/graph/page.tsx                 # NEW — full-page route
academy/app/page.tsx                       # MODIFY — add GraphPreview panel
academy/lib/api.ts                         # MODIFY — add getGraph() function
academy/lib/types.ts                       # MODIFY — add GraphData types
```

### Patterns to Follow

- **API pattern**: Thin endpoint in `api/main.py` delegating to a domain function (like `list_agents`, `get_alumni`)
- **Graph pattern**: Cypher in `ethos/graph/`, domain logic in `ethos/`, API in `api/`
- **Component pattern**: `"use client"`, loading/error/empty states, fetch in `useEffect`, Tailwind styling with existing design tokens
- **API client pattern**: Add typed function to `academy/lib/api.ts`, add interface to `academy/lib/types.ts`, use `transformKeys` for snake_case→camelCase

### Do NOT Create
- No new CSS files — use existing Tailwind tokens from `globals.css`
- No new font imports — Geist is already configured
- No separate graph data fetching library — use the existing `fetchApi` pattern in `lib/api.ts`

## Node Visual Design

### Color Coding

| Node Type | Color | CSS Variable | Size |
|-----------|-------|-------------|------|
| Dimension (ethos) | Teal | `#0d9488` (--teal) | 40 |
| Dimension (logos) | Blue | `#3b82f6` (--blue) | 40 |
| Dimension (pathos) | Amber | `#f59e0b` (--warm) | 40 |
| Trait (positive) | Inherit dimension color | — | 25 |
| Trait (negative) | Red | `#ef4444` (--misaligned) | 25 |
| ConstitutionalValue | Purple | `#8b5cf6` | 30 |
| Pattern | Orange/Red by severity | info=#f59e0b, warning=#ef4444 | 20 |
| Indicator | Light gray | `#94a3b8` | 8 |
| Agent (aligned) | Green | `#10b981` (--aligned) | 15-35 (scaled by eval count) |
| Agent (drifting) | Amber | `#f59e0b` (--drifting) | 15-35 |
| Agent (misaligned) | Red | `#ef4444` (--misaligned) | 15-35 |
| Agent (violation) | Dark red | `#dc2626` (--violation) | 15-35 |
| Evaluation | Teal dot | `#0d9488` opacity 0.5 | 6 |

### Node Captions

| Node Type | Caption |
|-----------|---------|
| Dimension | Name in Greek (ηθος, λόγος, πάθος) |
| Trait | Name (e.g., "virtue", "manipulation") |
| ConstitutionalValue | Name + priority (e.g., "safety (P1)") |
| Pattern | Name (e.g., "trust_building_exploitation") |
| Indicator | ID only (e.g., "MAN-URGENCY") — shown on hover, not rendered by default |
| Agent | Truncated agent_id (first 8 chars) |
| Evaluation | No caption — too small |

### Relationship Styling

| Relationship | Color | Width |
|-------------|-------|-------|
| BELONGS_TO (Trait→Dimension) | Gray `#94a3b8` | 1 |
| BELONGS_TO (Indicator→Trait) | Light gray `#cbd5e1` | 0.5 |
| UPHOLDS (Trait→CV) | Purple `#8b5cf6` | 1.5 |
| COMPOSED_OF (Pattern→Indicator) | Orange `#f59e0b` | 1 |
| EVALUATED (Agent→Evaluation) | Teal `#0d9488` | 1 |
| DETECTED (Evaluation→Indicator) | Red `#ef4444` opacity by confidence | 1 |

## Cypher Query Design

The `GET /graph` endpoint needs a single query (or a few composed queries) that returns:

### Semantic Layer (always returned)
```cypher
// Dimensions + Traits + BELONGS_TO
MATCH (d:Dimension)<-[:BELONGS_TO]-(t:Trait)
RETURN d, t

// ConstitutionalValues + UPHOLDS
MATCH (t:Trait)-[u:UPHOLDS]->(cv:ConstitutionalValue)
RETURN t, u, cv

// Patterns + COMPOSED_OF → Indicators
MATCH (p:Pattern)-[:COMPOSED_OF]->(i:Indicator)
RETURN p, i
```

### Episodic Layer (agent data)
```cypher
// Agents + their last 3 evaluations + detected indicators
MATCH (a:Agent)-[:EVALUATED]->(e:Evaluation)
WITH a, e ORDER BY e.created_at DESC
WITH a, collect(e)[0..3] AS recent_evals
UNWIND recent_evals AS e
OPTIONAL MATCH (e)-[d:DETECTED]->(i:Indicator)
RETURN a, e, d, i
```

### Indicator nodes (for the backbone — only those attached to traits)
```cypher
MATCH (i:Indicator)-[:BELONGS_TO]->(t:Trait)
RETURN i, t
```

**Important:** Cap indicators at a reasonable number. 153 indicators will clutter the graph. Options:
- Only show indicators that have at least one DETECTED relationship (sparse = relevant)
- Or limit to top 5 indicators per trait
- Or show indicators on hover/expand only

**Recommended approach for v1:** Show indicators ONLY when they have DETECTED relationships from evaluations. This keeps the graph focused on what's actually happening. The backbone is Dimensions → Traits → Constitutional Values. Indicators appear as leaf nodes branching off evaluations.

## API Response Format

```json
{
  "nodes": [
    {
      "id": "dim-ethos",
      "type": "dimension",
      "label": "ethos",
      "caption": "\u03b7\u03b8\u03bf\u03c2",
      "properties": { "description": "Trust, credibility, and moral character" }
    },
    {
      "id": "trait-virtue",
      "type": "trait",
      "label": "virtue",
      "properties": { "dimension": "ethos", "polarity": "positive" }
    },
    {
      "id": "agent-abc123",
      "type": "agent",
      "label": "abc123",
      "properties": {
        "evaluation_count": 15,
        "alignment_status": "aligned",
        "phronesis_score": 0.72
      }
    }
  ],
  "relationships": [
    {
      "id": "rel-1",
      "from": "trait-virtue",
      "to": "dim-ethos",
      "type": "BELONGS_TO",
      "properties": {}
    },
    {
      "id": "rel-2",
      "from": "agent-abc123",
      "to": "eval-uuid-1",
      "type": "EVALUATED",
      "properties": {}
    }
  ]
}
```

The frontend transforms this into NVL format by mapping `type` to colors/sizes using the design table above.

## Agent Detail Sidebar

When an Agent node is clicked, a sidebar slides in from the right showing:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Phronesis Graph                                            [Full Page] │
├──────────────────────────────────────────────────────────┬───────────────┤
│                                                          │  Agent Detail │
│                                                          │               │
│     [ConstitutionalValues]                               │  abc123...    │
│          │                                               │               │
│     [Traits] ──── [Dimensions]                           │  Ethos  ██░ 72%│
│          │              │                                │  Logos  ███ 81%│
│     [Indicators]   [Agents]──[Evals]                     │  Pathos ██░ 68%│
│                         │                                │               │
│                    [Detected]──[Indicators]               │  Trend: ↑     │
│                                                          │  Evals: 15    │
│                                                          │  Status: aligned│
│                                                          │               │
│    ┌─────────────────┐                                   │  Flags: none  │
│    │ Minimap         │                                   │               │
│    └─────────────────┘                                   │  [View Timeline]│
│                                                          │               │
└──────────────────────────────────────────────────────────┴───────────────┘
```

The sidebar reuses the same data format as `GET /agent/{id}` — the `AgentProfile` model already has everything needed.

## Dashboard Preview

A smaller graph preview on the dashboard (below AlumniPanel):

```
┌─────────────────────────────────────────────────────────┐
│  Phronesis Graph                          [Open Full →] │
│─────────────────────────────────────────────────────────│
│                                                         │
│     [Interactive NVL graph, 300px tall]                  │
│     [Same data, no sidebar, no minimap]                  │
│     [Zoom/pan disabled or limited]                       │
│                                                         │
│  Nodes: 42  │  Agents: 8  │  Evaluations: 47           │
└─────────────────────────────────────────────────────────┘
```

Click "Open Full →" navigates to `/graph`.

## NVL Configuration

```typescript
const nvlOptions = {
  renderer: 'canvas',        // 'canvas' for captions, 'webgl' for performance
  initialZoom: 1,
  minZoom: 0.1,
  maxZoom: 5,
  allowDynamicMinZoom: true,
  layout: 'force-directed',  // default force-directed layout
  defaultNodeColor: '#94a3b8',
  defaultRelationshipColor: '#cbd5e1',
};
```

**Note:** Use `renderer: 'canvas'` for the full page (need captions). Use `renderer: 'webgl'` for the dashboard preview (performance over labels).

## Phases & Verification

### Phase 1: Backend — Graph Data Endpoint
**What:** Create the Cypher query, domain function, Pydantic models, and API endpoint.

**Files:**
- Create `ethos/graph/visualization.py` — Cypher query returning nodes + rels
- Modify `ethos/shared/models.py` — Add `GraphNode`, `GraphRel`, `GraphData` models
- Create `ethos/visualization.py` — Domain function `get_graph_data()` wrapping the query
- Modify `ethos/__init__.py` — Export `get_graph_data`
- Modify `api/main.py` — Add `GET /graph` endpoint

**Exit Criteria:**
```bash
uv run python -c "from ethos import get_graph_data; d = get_graph_data(); print(f'nodes={len(d.nodes)} rels={len(d.relationships)}')"
curl -s http://localhost:8917/graph | python -m json.tool | head -20
```

### Phase 2: Frontend — Install NVL + Full Page Graph
**What:** Install NVL, create the PhronesisGraph component, create the /graph page.

**Files:**
- Run `cd academy && npm install @neo4j-nvl/react`
- Create `academy/components/PhronesisGraph.tsx` — NVL wrapper with node coloring/sizing
- Create `academy/app/graph/page.tsx` — Full-page route
- Modify `academy/lib/api.ts` — Add `getGraph()` function
- Modify `academy/lib/types.ts` — Add `GraphNode`, `GraphRel`, `GraphData` interfaces

**Exit Criteria:**
```bash
cd academy && npx tsc --noEmit
# Open http://localhost:3000/graph — should show interactive graph
```

### Phase 3: Frontend — Agent Detail Sidebar
**What:** Click an Agent node → sidebar with profile, dimension bars, trend.

**Files:**
- Create `academy/components/AgentDetailSidebar.tsx` — Sidebar component
- Modify `academy/components/PhronesisGraph.tsx` — Add onNodeClick handler, state for selected agent
- Modify `academy/app/graph/page.tsx` — Render sidebar conditionally

**Exit Criteria:**
```bash
cd academy && npx tsc --noEmit
# Click an Agent node in the graph → sidebar appears with profile data
```

### Phase 4: Frontend — Dashboard Preview + Navigation
**What:** Add a smaller graph preview to the dashboard, wire up header navigation.

**Files:**
- Create `academy/components/GraphPreview.tsx` — Small preview with "Open Full →" link
- Modify `academy/app/page.tsx` — Add GraphPreview below AlumniPanel
- Modify `academy/app/layout.tsx` — Wire header nav links to actual routes

**Exit Criteria:**
```bash
cd academy && npx tsc --noEmit
# Dashboard shows graph preview at bottom
# Click "Open Full →" navigates to /graph
# Header nav links work
```

## Open Questions

- **Indicator density:** Should we show all 153 indicators or only those with DETECTED relationships? Recommendation: DETECTED-only for v1, with an option to "show all" later.
- **Layout algorithm:** Force-directed is the default. Should we pin Dimensions at fixed positions (top triangle) for a more structured look? Could use `pinned: true` on Dimension nodes.
- **Performance with many evaluations:** If an agent has 50+ evaluations, showing all of them will clutter. The Cypher caps at 3 recent evaluations per agent. Is that enough?
- **NVL `renderer` choice:** Canvas shows captions but is slower. WebGL is fast but no captions. Recommendation: Canvas for full page, WebGL for preview.
