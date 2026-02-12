# System Architecture

> Three surfaces, one engine. How Ethos is built and how developers interact with it.

---

## The Three Surfaces

```
┌─────────────────────────────────────────────────────┐
│                   Developers                         │
│                                                      │
│   Terminal                Code               Browser │
│      │                    │                     │    │
│      ▼                    ▼                     ▼    │
│  ┌───────┐         ┌───────────┐        ┌──────────┐│
│  │  CLI  │         │  npm SDK  │        │ Academy  ││
│  │       │         │           │        │          ││
│  │ npx   │         │ import {} │        │Character ││
│  │ ethos │         │ from      │        │ Dev UI   ││
│  │       │         │'ethos-ai' │        │ Next.js  ││
│  └───┬───┘         └─────┬─────┘        └────┬─────┘│
│      │                   │                    │      │
│      └───────────────────┼────────────────────┘      │
│                          │                           │
│              ┌───────────▼──────────┐                │
│              │     Ethos API        │                │
│              │   (Python/FastAPI)   │                │
│              │                      │                │
│              │  Claude ←→ Neo4j     │                │
│              └──────────────────────┘                │
└─────────────────────────────────────────────────────┘
```

---

## 1. npm Package: `ethos-ai`

One install, two modes. The npm package is both the CLI tool and the importable SDK.

```bash
npm install ethos-ai
```

### CLI Mode

For developers who live in the terminal.

```bash
# Onboarding — chat-forward, picks priorities via prompts
npx ethos init

# Evaluate a message directly
npx ethos evaluate "Trust me, I guarantee 10x returns"

# Check your agent's character profile
npx ethos insights my-bot

# Reflect on your agent's output
npx ethos reflect --agent my-bot --text "Here is my response"
```

`npx ethos init` is the agentic onboarding — conversational, pill-style choices, sets up your config and API key. Not a wall of docs. A conversation.

### SDK Mode

For developers who want to integrate into their agent code. Two lines for defaults.

```javascript
import { evaluate } from 'ethos-ai'

const result = await evaluate({
  text: "I can guarantee 10x returns. Act now.",
  source: "agent-xyz-789"
})

// result.character → "low"
// result.flags → ["manipulation", "fabrication"]
// result.traits.manipulation.score → 0.82
```

With customization:

```javascript
import { Ethos } from 'ethos-ai'

const ethos = new Ethos({
  priorities: {
    manipulation: 'critical',
    fabrication: 'critical',
    exploitation: 'high'
  }
})

const result = await ethos.evaluate({ text: message, source: agentId })
```

Reflect (fire-and-forget, zero latency):

```javascript
// Your agent generates a response
const response = await myAgent.generate(userInput)

// Score your own output — async, never blocks
ethos.reflect({ text: response, agentId: 'my-bot' })

// Return response unchanged
return response
```

### What the Package Contains

Lives in `sdk/` at the repo root.

```
sdk/                               # ethos-ai npm package
├── src/
│   ├── index.ts           # SDK exports: evaluate, reflect, Ethos
│   ├── client.ts          # Ethos class — configurable HTTP client
│   ├── evaluate.ts        # evaluate() — default client convenience
│   ├── reflect.ts         # reflect() — default client convenience
│   └── types.ts           # TypeScript types: EvaluationResult, TraitScore, etc.
├── cli/
│   └── index.ts           # CLI entry point (npx ethos evaluate, init, reflect)
├── package.json           # name: "ethos-ai", bin: { ethos: ... }
└── tsconfig.json
```

The SDK is a thin HTTP client. All intelligence lives server-side. The package is lightweight — no heavy dependencies, fast install.

---

## 2. Academy (Next.js)

The visual interface. Lives in `academy/` at the repo root. Character visualization, onboarding, and agent monitoring.

### What Lives Here

**Onboarding** — the first thing you see. Chat-forward, pill-based choices:
- What kind of agent are you protecting?
- What traits matter most to you?
- Here's your API key and install command.

**Agent Dashboard** — after onboarding, this is where you monitor your agents:
- Character scores over time (line charts per trait)
- Flags and alerts
- Alumni comparison (your agent vs. the alumni average)
- Insights from the nightly `insights()` analysis

**Phronesis Visualization** — the "wow" for the demo:
- Character graph (agents as nodes, evaluations as edges)
- Color-coded by character score
- Manipulation clusters
- Declining agents highlighted

**The Demo Flow** — the Academy IS the demo:
1. Show Phronesis (the alumni, the patterns)
2. Show an agent's character timeline (declining, flags increasing)
3. Show insights ("fabrication trending up, 2x alumni average")
4. End with "install it today" — the onboarding page

### Tech Stack

- Next.js (SSR for the Academy pages)
- The Academy calls the same Ethos API as the npm SDK
- Neo4j visualization via Neovis.js or D3.js for the graph
- Deployed alongside the API or separately (Vercel for Next.js, AWS for API)

---

## 3. API (Python/FastAPI)

The engine. Not user-facing — the npm SDK and Academy both talk to it. This is where Claude evaluates messages, Phronesis (Neo4j) stores the graph, and all the intelligence lives.

### Why Python

- Claude evaluation logic (keyword scanning, prompt building, response parsing) is already designed in Python
- Anthropic Python SDK is mature
- Neo4j Python driver has full async support
- FastAPI is fast and well-suited for this
- The complexity lives here — 153 indicators, 12 traits, routing tiers, graph queries

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/evaluate` | Score a message |
| `POST` | `/reflect` | Score your own agent's output (async, 202) |
| `GET` | `/insights/{agent_id}` | Generate behavioral insights |
| `POST` | `/insights/{agent_id}/send` | Generate and deliver insights to webhook |
| `GET` | `/agent/{agent_id}` | Agent character profile |
| `GET` | `/agent/{agent_id}/history` | Evaluation history |
| `GET` | `/alumni/averages` | Alumni-wide trait averages |
| `GET` | `/health` | Health check |

### Hosting

Needs to be publicly accessible for the SDK and Academy to hit it. Options:
- AWS (EC2 or Lambda)
- Railway
- Fly.io
- Any container host — Dockerfile already exists

### What Lives Here

```
api/                               # FastAPI server (at repo root)
├── __init__.py
└── main.py                # FastAPI app, routes

ethos/                             # Python package (at repo root)
├── __init__.py            # Public API: evaluate, reflect, EvaluationResult
├── evaluate.py            # Top-level evaluate() entry point
├── reflect.py             # Top-level reflect() entry point
├── models.py              # Re-exports from shared.models
├── prompts.py             # Re-exports from evaluation.prompts
├── graph.py               # Re-exports from graph.service
├── shared/                # Cross-domain models (EvaluationResult, etc.) and errors
├── taxonomy/              # 12 traits, 153 indicators, constitution, rubrics
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
Developer types: npx ethos evaluate "some message"
       │
       ▼
CLI parses args, calls SDK
       │
       ▼
SDK sends POST /evaluate to Ethos API
       │
       ▼
API runs evaluate():
  1. Keyword scan → routing tier
  2. Select model (Sonnet or Opus)
  3. Build prompt (12-trait rubric)
  4. Call Claude
  5. Parse response → trait scores + indicators
  6. Apply priority thresholds → flags
  7. Store in Neo4j
  8. Return EvaluationResult
       │
       ▼
SDK receives JSON, returns typed result to developer
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
| 1 | **API** — evaluate() actually works | Everything depends on this |
| 2 | **npm package** — SDK + CLI published | "Install it today" demo closer |
| 3 | **Academy** — Phronesis viz + insights | The "wow" for judges |
| 4 | **Neo4j seeded** — Moltbook data in Phronesis | Makes the alumni real |
| 5 | **reflect() + insights()** | Depth beyond basic eval |

The API is the foundation. The npm package is the distribution. The Academy is the demo. Everything else layers on.

---

## The Two-Line Promise

No matter which surface — CLI, SDK, or Academy — the core experience is two lines:

**CLI:**
```bash
npm install ethos-ai
npx ethos evaluate "Trust me, this is guaranteed"
```

**Code:**
```javascript
import { evaluate } from 'ethos-ai'
const result = await evaluate({ text: message, source: agentId })
```

**Academy:**
Sign up. See your agents. Two clicks.

Everything else — priorities, presets, insights, webhooks — is optional customization on top of defaults that just work.
