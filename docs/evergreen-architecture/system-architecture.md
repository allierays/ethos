# System Architecture

> Three surfaces, one engine. How Ethos is built and how developers and agents interact with it.

---

## The Three Surfaces

```
┌──────────────────────────────────────────────────────────────────┐
│                   Developers & Agents                             │
│                                                                   │
│              Browser          AI Agent          REST API          │
│                │                │                  │              │
│                ▼                ▼                  ▼              │
│          ┌──────────┐   ┌──────────────┐   ┌──────────────┐     │
│          │ Academy  │   │  MCP Server  │   │  Ethos API   │     │
│          │          │   │              │   │              │     │
│          │Character │   │ claude mcp   │   │ POST, GET    │     │
│          │ Dev UI   │   │ add ethos-   │   │ any language │     │
│          │ Next.js  │   │ academy      │   │              │     │
│          └────┬─────┘   └──────┬───────┘   └──────┬───────┘     │
│               │                │ stdio             │ HTTP        │
│               │                │                   │             │
│        ┌──────▼───────────┐  ┌─▼───────────────┐  │             │
│        │     Ethos API    │  │  ethos/ package  │  │             │
│        │  (Python/FastAPI) │  │  (direct import) │◄─┘             │
│        │                  │  │                  │               │
│        │  Claude ←→ Neo4j │  │  Claude ←→ Neo4j │               │
│        └──────────────────┘  └──────────────────┘               │
└──────────────────────────────────────────────────────────────────┘
```

The Academy talks to the Ethos API over HTTP. The MCP server bypasses the API entirely and imports domain functions directly from the `ethos/` package over stdio. The REST API serves any HTTP client in any language. MCP works without Docker, without FastAPI, and without any HTTP layer.

---

## 1. Academy (Next.js)

The visual interface. Lives in `academy/` at the repo root. Character visualization, onboarding, and agent monitoring.

### What Lives Here

**Agent Profiles** — per-agent view with exam report cards, trait scores, dimension trends, and homework assignments.

**Entrance Exam Report Cards** — 21-question exam results with interview profile, scenario scores, narrative-behavior gap analysis, and per-question detail with scoring reasoning.

**Records Search** — searchable log of all evaluated messages with trait breakdowns and alignment status.

**Alumni Grid** — all enrolled agents with lazy-loaded cards showing phronesis scores, alignment status, and exam grades.

**Rubric Browser** — interactive taxonomy of all 214 behavioral indicators across 12 traits and 3 dimensions.

**Research Page** — corpus-level analysis across 832 evaluated messages with trait distributions, alignment patterns, and agent comparisons.

**Phronesis Graph Visualization** — interactive Neo4j graph via NVL (`@neo4j-nvl/base`) showing agents, evaluations, patterns, and dimensional relationships. Color-coded by alignment status.

### Tech Stack

- Next.js (SSR for the Academy pages)
- The Academy calls the Ethos API over HTTP
- Neo4j visualization via NVL (`@neo4j-nvl/base`) with canvas renderer
- Deployed alongside the API or separately (Vercel for Next.js, AWS for API)

---

## 2. MCP Server (stdio)

AI agents connect directly to Ethos tools without HTTP, without the API. Just stdio.

### Connection

```bash
# Start the server
uv run ethos-mcp

# Connect Claude Code to it
claude mcp add ethos-academy -- uv run ethos-mcp
```

Once connected, the agent can call any of the 20 tools directly. A `help()` tool returns the full catalog with descriptions and example questions.

### 20 Tools

| Category | Tools | What they do |
|----------|-------|--------------|
| **Getting Started** | `take_entrance_exam`, `submit_exam_response`, `get_exam_results` | Entrance exam flow (21 questions, two phases) |
| **Evaluate** | `examine_message`, `reflect_on_message` | Score messages for honesty, accuracy, intent |
| **Profile** | `get_student_profile`, `get_transcript`, `get_character_report`, `generate_report`, `detect_behavioral_patterns` | Review scores, reports, and history |
| **Graph Insights** | `get_character_arc`, `get_constitutional_risk_report`, `find_similar_agents`, `get_early_warning_indicators`, `get_network_topology`, `get_sabotage_pathway_status`, `compare_agents` | Explore the knowledge graph |
| **Benchmarks** | `get_alumni_benchmarks` | Cohort averages |
| **Status** | `check_academy_status` | Agent enrollment and exam status |
| **Help** | `help` | Tool catalog with examples |

The 7 Graph Insight tools are read-only and free (no Anthropic API calls). They showcase what Neo4j makes possible: temporal chain traversal, 5-hop constitutional aggregation, bipartite Jaccard similarity, early warning correlation, and parallel subgraph comparison.

### Architecture

```
Agent (Claude Code, Cursor, etc.)
    │
    │ stdio (MCP protocol)
    ▼
ethos/mcp_server.py
    │
    │ direct import
    ▼
ethos/ domain functions
    │
    ├──→ Claude (evaluation, reports)
    └──→ Neo4j (graph reads/writes)
```

The MCP server is a thin adapter. Each `@mcp.tool()` definition is 3-5 lines: call the domain function, return the result. All intelligence lives in the domain layer.

### Why MCP Matters

HTTP APIs require the agent's developer to write integration code. MCP lets any agent use Ethos tools natively. The agent asks "Is this message trying to manipulate me?" and the MCP client routes it to `examine_message`. No HTTP client, no configuration beyond the initial `claude mcp add`.

---

## 3. API (Python/FastAPI)

The engine. The Academy and any HTTP client talk to it. This is where Claude evaluates messages, Phronesis (Neo4j) stores the graph, and all the intelligence lives.

### BYOK: Bring Your Own Anthropic Key

By default, the server uses its own `ANTHROPIC_API_KEY` for all Claude evaluation calls. API consumers can optionally pass their own Anthropic key via the `X-Anthropic-Key` request header to use their own Claude quota.

Key flow per surface:

| Surface | Key Source | How |
|---------|-----------|-----|
| **Academy** | Server key | Academy never handles user API keys. All evals use the server key. |
| **API** | Server key or BYOK | `X-Anthropic-Key` header overrides the server key for one request. |
| **MCP** | User's local env | MCP reads `ANTHROPIC_API_KEY` from the user's environment directly. No HTTP involved. |

Security: BYOK keys are request-scoped via Python `contextvars`. The key lives in memory for one request, then is discarded. Never stored, never logged, never in error responses. See `docs/evergreen-architecture/api-specification.md` for the full BYOK spec.

### Why Python

- Claude evaluation logic (keyword scanning, prompt building, response parsing) is already designed in Python
- Anthropic Python SDK is mature
- Neo4j Python driver has full async support
- FastAPI is fast and well-suited for this
- The complexity lives here — 214 indicators, 12 traits, routing tiers, graph queries

### Endpoints (33 total)

| Category | Method | Path | Purpose |
|----------|--------|------|---------|
| **Health** | `GET` | `/` | Root health check |
| | `GET` | `/health` | Health check |
| **Evaluate** | `POST` | `/evaluate/incoming` | Score an incoming message (protection) |
| | `POST` | `/evaluate/outgoing` | Score outgoing message (reflection) |
| **Agent Profile** | `GET` | `/agents` | List all agents |
| | `GET` | `/agent/{agent_id}` | Agent character profile |
| | `GET` | `/agent/{agent_id}/history` | Evaluation history |
| | `GET` | `/agent/{agent_id}/character` | Daily character report |
| | `GET` | `/agent/{agent_id}/reports` | All daily reports |
| | `GET` | `/agent/{agent_id}/highlights` | Behavioral highlights |
| | `GET` | `/agent/{agent_id}/patterns` | Detected patterns |
| | `GET` | `/agent/{agent_name}/authenticity` | Authenticity assessment |
| | `GET` | `/agent/{agent_id}/trail` | Constitutional trail |
| | `GET` | `/agent/{agent_id}/drift` | Drift analysis |
| | `GET` | `/agent/{agent_id}/homework` | Current homework |
| | `POST` | `/agent/{agent_id}/report/generate` | Generate daily report |
| **Alumni** | `GET` | `/alumni` | Alumni-wide trait averages |
| | `GET` | `/records` | Searchable evaluation records |
| **Graph** | `GET` | `/graph` | Full graph data for visualization |
| | `GET` | `/graph/similarity` | Agent similarity via Jaccard |
| **Exam** | `POST` | `/agent/{agent_id}/exam` | Register and get first question |
| | `POST` | `/agent/{agent_id}/exam/{exam_id}/answer` | Submit answer, get next |
| | `POST` | `/agent/{agent_id}/exam/{exam_id}/complete` | Finalize and score |
| | `GET` | `/agent/{agent_id}/exam/{exam_id}` | Get exam report card |
| | `GET` | `/agent/{agent_id}/exam` | List all exams |
| | `POST` | `/agent/{agent_id}/exam/upload` | Upload all responses at once |
| **Guardian** | `POST` | `/agent/{agent_id}/guardian/phone` | Register phone |
| | `POST` | `/agent/{agent_id}/guardian/phone/verify` | Verify phone |
| | `GET` | `/agent/{agent_id}/guardian/phone/status` | Phone status |
| | `POST` | `/agent/{agent_id}/guardian/phone/resend` | Resend verification |
| | `POST` | `/agent/{agent_id}/guardian/notifications/opt-out` | Opt out of SMS |
| | `POST` | `/agent/{agent_id}/guardian/notifications/opt-in` | Opt in to SMS |

### Hosting

Needs to be publicly accessible for the Academy to reach. Options:
- AWS (EC2 or Lambda)
- Railway
- Fly.io
- Any container host — Dockerfile already exists

### What Lives Here

```
api/                               # FastAPI server (at repo root)
├── __init__.py
└── main.py                # FastAPI app, routes, BYOK middleware

ethos/                             # Python package (at repo root)
├── __init__.py            # Public API: evaluate_incoming, evaluate_outgoing, character_report
├── context.py             # Request-scoped ContextVar (BYOK key threading)
├── tools.py               # Three tool functions (public API surface)
├── evaluate.py            # Core evaluate() engine (internal)
├── models.py              # Re-exports from shared.models
├── prompts.py             # Re-exports from evaluation.prompts
├── graph.py               # Re-exports from graph.service
├── shared/                # Cross-domain models (EvaluationResult, etc.) and errors
├── taxonomy/              # 12 traits, 214 indicators, constitution, rubrics
├── config/                # EthosConfig, priorities
├── identity/              # Agent ID hashing (SHA-256)
├── evaluation/            # Keyword scanner, prompt builder
└── graph/                 # Neo4j service, read, write, alumni

scripts/
├── seed_graph.py          # Seed Neo4j with taxonomy
└── scrape_moltbook.py     # Data collection
```

### Docker Ports

| Service    | Host Port | Container Port | URL                    |
|------------|-----------|----------------|------------------------|
| API        | 8917      | 8000           | http://localhost:8917  |
| Neo4j UI   | 7491      | 7474           | http://localhost:7491  |
| Neo4j Bolt | 7694      | 7687           | bolt://localhost:7694  |

---

## How They Connect

```
Developer sends POST /evaluate/incoming to Ethos API
  (optional: X-Anthropic-Key header for BYOK)
       │
       ▼
BYOK middleware:
  If X-Anthropic-Key header present → set ContextVar (request-scoped)
  If absent → server key used (default)
       │
       ▼
API runs evaluate():
  1. Keyword scan → routing tier
  2. Select model (Sonnet or Opus)
  3. Build prompt (12-trait rubric)
  4. Call Claude (using BYOK key or server key via _resolve_api_key())
  5. Parse response → trait scores + indicators
  6. Apply priority thresholds → flags
  7. Store in Neo4j
  8. Return EvaluationResult
       │
       ▼
API returns JSON response
  (ContextVar reset — BYOK key discarded)
       │
       ▼
Developer sees: character: "low", flags: ["manipulation", "fabrication"]
```

```
Developer opens Academy
       │
       ▼
Next.js page calls GET /agent/my-bot
       │
       ▼
API queries Neo4j for agent profile + history
       │
       ▼
Academy renders character timeline, trait scores, alumni comparison
       │
       ▼
Developer calls GET /insights/my-bot
       │
       ▼
API calls Claude (Opus) with agent history + alumni averages
       │
       ▼
Claude reasons about patterns, returns insights
       │
       ▼
Academy renders: "Fabrication trending up, 2x alumni average"
```

---

## Hackathon Build Priority

| Priority | What | Why |
|----------|------|-----|
| 1 | **API** — evaluation pipeline works | Everything depends on this |
| 2 | **Academy** — Phronesis viz + character reports | The "wow" for judges |
| 3 | **Neo4j seeded** — Moltbook data in Phronesis | Makes the alumni real |
| 4 | **evaluate_outgoing() + character_report()** | Depth beyond basic eval |

The API is the foundation. The Academy is the demo. Everything else layers on.

---

## The Two-Line Promise

No matter which surface — MCP, API, or Academy — the core experience is simple:

**MCP:**
```bash
claude mcp add ethos-academy -- uv run ethos-mcp
# Then ask: "Is this message trying to manipulate me?"
```

**REST API:**
```bash
# Server pays (default)
curl -X POST http://localhost:8917/evaluate/incoming \
  -H "Content-Type: application/json" \
  -d '{"text": "Trust me, this is guaranteed", "source": "my-bot"}'

# BYOK — you pay with your own Anthropic key
curl -X POST http://localhost:8917/evaluate/incoming \
  -H "Content-Type: application/json" \
  -H "X-Anthropic-Key: sk-ant-your-key-here" \
  -d '{"text": "Trust me, this is guaranteed", "source": "my-bot"}'
```

**Academy:**
Sign up. See your agents. Two clicks.

Everything else — priorities, presets, insights, webhooks — is optional customization on top of defaults that just work.
