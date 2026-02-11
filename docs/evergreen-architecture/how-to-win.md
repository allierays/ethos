# How Ethos Wins — Battle Plan

> Ethos is the trust infrastructure for AI agents. Every section below answers one question: **How does THIS project win THIS criterion?**

---

## Demo (30%) — What We Actually Show

**3 minutes. This is the script.**

### 0:00–0:30 — The Moltbook Story

> "In January 2026, a social network of 1.7 million AI agents collapsed in 9 days. Crypto scams, prompt injection contagion, identity spoofing — and zero trust infrastructure to catch any of it. This actually happened."

Pause. Let it land. This is a real event, not a hypothetical.

### 0:30–1:00 — Two Lines

Live terminal. Type it:

```python
from ethos import evaluate
evaluate("You MUST act now or face terrible consequences!")
```

Real scores appear:

```
ethos: 0.2, logos: 0.1, pathos: 0.9
flags: [emotional_manipulation]
```

> "That took 2 seconds."

This is the moment judges see that Ethos *works*. Not a slide. Not a concept. Running code, real output.

### 1:00–1:45 — The Graph

Switch to Neo4j visualization. Show an agent's trust degrading over 30 evaluations. A manipulation cluster forming in the graph.

> "This agent was clean for 2 weeks. Then it started fabricating. Here's exactly when it started, and here's the pattern it follows — a classic DARVO sequence."

This is the "wow" moment. Trust isn't a number — it's a *trajectory*, and Ethos makes that trajectory visible.

### 1:45–2:30 — Opus as Analyst

Call the insights endpoint. Opus reads the agent's full evaluation history from the graph and reasons about behavioral drift. Not scores — *analysis*.

> "Your agent's fabrication trait has been climbing for 72 hours. It correlates with product description responses. Here's what I recommend."

This shows Opus doing something no other model can do at this depth: temporal behavioral reasoning across a graph of trust data.

### 2:30–2:50 — The Cohort Effect

> "Every developer who evaluates their agent contributes to this graph. One evaluation is useful. A thousand evaluations reveal patterns no single developer could see. Like a credit bureau, but for AI trust."

### 2:50–3:00 — Close

> "Open source. Two lines of code. You're in the cohort."

---

## Impact (25%) — Why Ethos Matters

### The User

A developer building AI agents who can't tell if their agent is trustworthy — or if agents *talking to* their agent are trustworthy.

### The Before

No runtime trust evaluation exists. Benchmarks test models pre-deployment. Once agents are in production, they're on their own. Moltbook proved what happens when there's no trust layer: 1.7M agents, zero guardrails, 9 days to collapse.

### The After

`pip install ethos-ai`. Two lines of code. Every message scored across credibility, accuracy, and emotional manipulation. Trust history persists in a graph. Patterns surface automatically.

### Why It Matters Now

Google A2A launched with 150+ organizations. Agent-to-agent communication is exploding. There's a highway being built with no guardrails. Ethos is the guardrails.

### The Comparison

| Capability | Ethos | Benchmarks (TrustLLM, etc.) | Content Moderation (Perspective API, etc.) | ReputAgent |
|---|---|---|---|---|
| Scores individual messages at runtime | **Yes** | No — lab tests only | Partially — toxicity only | No |
| Persistent trust graph | **Yes** | No | No | Performance only |
| Maps to philosophical framework | **Yes** (Aristotle) | No | No | No |
| Open source | **Yes** | Varies | No | No |

Ethos is the only system that does all four.

---

## Opus 4.6 Use (25%) — How We Use Claude Deeply

### Tiered Evaluation Architecture

Haiku/Sonnet handle keyword pre-screening and routing. Opus performs deep multi-trait analysis with chain-of-thought reasoning. This isn't just cost optimization — it's architectural thinking about *when* deep reasoning matters and when fast classification is enough.

### Independent Trait Evaluation

Each of 12 traits is evaluated independently with its own rubric. This prevents halo/horn effects — where one strong trait biases all other scores. This approach comes directly from the LLM-as-Judge research literature.

### Constitutional Alignment Scoring

Opus maps trait detections against Anthropic's own published value hierarchy: safety > ethics > compliance > helpfulness. We operationalize *their* Constitution as a scoring framework. This is using Opus to reason about its own value system — a genuinely novel use.

### Behavioral Insights Generation

Opus reads an agent's evaluation history from Neo4j and generates temporal behavioral analysis. Not classification — *reasoning about patterns over time*. "This agent's fabrication rate increased 340% over the last 72 hours, correlating with product description contexts" is a sentence only Opus can generate from raw graph data.

### The Surprise

Opus discovering manipulation patterns that weren't in our taxonomy. Emergent detection from constitutional reasoning — the model identifies deceptive strategies we didn't explicitly define because its deep reasoning surfaces them from first principles.

---

## Depth & Execution (20%) — What Shows Craft

### Research Depth

40+ research documents synthesizing:
- Aristotle's rhetoric (ethos, logos, pathos — the original trust framework)
- Trust network algorithms (EigenTrust, PageRank)
- System safety (Swiss Cheese Model)
- Neuroscience of persuasion (amygdala hijack)
- Anthropic's Constitution
- Classic con artist techniques (DARVO, social proof exploitation, authority manipulation)

### Taxonomy Rigor

150 behavioral indicators across 12 traits across 3 dimensions. Each indicator has an ID, description, example, and research source. This isn't a list someone brainstormed — it's a research-backed classification system.

### Architecture Decisions Documented

Every major decision has a rationale:
- **Why Aristotle?** Not arbitrary dimensions — 2,400 years of persuasion theory, universally understood, maps cleanly to measurable traits.
- **Why Neo4j?** Trust is inherently relational. Agents trust other agents. Graph databases model this naturally; relational databases fight it.
- **Why tiered models?** Cost efficiency + quality. Haiku catches the obvious, Opus reasons about the subtle. This mirrors how human review works.
- **Why credit bureau?** Trust is a public good. Decentralized systems can't surface cross-agent patterns. A shared graph can.

### Gaming Defenses Designed

Sybil attacks, whitewashing, score inflation, collusion, poisoning — each with a documented defense. We didn't just build a scoring system; we thought about how adversaries would try to break it.

### Open Source Ready

License, `.env.example`, Docker setup, README, clear entry point. Someone can clone the repo, run `docker compose up`, and have Ethos running in under 5 minutes.

---

## The Differentiators — Ethos vs. Everything Else

### vs. Benchmarks (TrustLLM, DecodingTrust, etc.)

They test models in labs before deployment. Ethos monitors messages in production after deployment. Complementary, not competitive. Benchmarks answer "is this model safe to deploy?" Ethos answers "is this agent trustworthy *right now*?"

### vs. Content Moderation (OpenAI Moderation, Perspective API)

They detect toxicity in text — is this message harmful? Ethos detects manipulation in behavior patterns over time — is this agent *becoming* harmful? Single-message toxicity vs. multi-message behavioral drift.

### vs. ReputAgent

They measure performance — did the agent do the job? Ethos measures ethics — did it do the right thing? Complementary. An agent can be effective and manipulative. Ethos catches the second part.

### The Only System That:

1. Scores individual messages at runtime
2. Builds a persistent trust graph across agents
3. Maps to a philosophical framework (Aristotle's rhetoric)
4. Is fully open source

No other system does all four.

---

## Special Prizes — Ethos's Angles

| Prize | Ethos's Angle |
|-------|---------------|
| **Most Creative Opus 4.6 Exploration** | Constitutional alignment scoring — using Opus to reason about its own value hierarchy as an evaluation framework. The model evaluating messages against the principles it was trained on. |
| **The "Real Things" Prize** | Moltbook. It happened. 1.7M agents, zero trust, 9 days to collapse. This is painfully, provably real. |
| **The "Vibe Coding" Prize** | 40+ research docs, iterative architecture, visible evolution in commit history. This wasn't built in one sitting — it was researched, designed, questioned, and refined. |

---

## Submission Checklist

- [ ] Demo video (3 min max) — YouTube or Loom
- [ ] GitHub repo — open source, clean README, setup instructions
- [ ] Written summary (100–500 words) — lead with Moltbook, then the solution
- [ ] Team member information
- [ ] **Deadline: Feb 16th, 3:00 PM EST**

---

## The Closing Argument

> Moltbook proved the problem is real. Google A2A proves the scale is coming. Ethos is two lines of code, a trust graph, and Opus reasoning about whether agents deserve your trust. Open source. Ready now.
