# Ethos Academy — Site Vision + Saturday Plan

## Context

The Academy is the visual complement to the `ethos-ai` plugin. The plugin evaluates. The Academy reveals. Agents go to school — like Aristotle studied under Plato — and the Academy is where you see how they're doing.

Two audiences, one dataset:
- **Researchers / public** → the forest. 1M anonymized messages. Trends, outliers, the graph.
- **Developers / individuals** → the tree. Your agent's report card. History, profile, alumni rank, balance.

---

## Site Structure

```
/                  → Landing — the story, 4 pillars, motion.dev animations
/how-it-works      → Pipeline explained visually — plugin → API → graph → Academy
/explore           → The forest — anonymized alumni data, the Phronesis graph, research view
/agent/[id]        → The tree — one agent's report card (the 4 pillars)
```

### Landing Page (`/`)
- Animated hero with motion.dev — Phronesis, practical wisdom, agents learning
- The 4 pillars visualized: History, Profile, Alumni, Balance
- The scale: "1 million messages. 12 traits. 3 dimensions. One question: should you trust this agent?"
- CTA: Explore the data / Check your agent

### How It Works (`/how-it-works`)
- Visual pipeline: plugin sends message → scored across 12 traits → stored in graph → patterns emerge
- The Aristotle metaphor: agents learn, the Academy tracks their growth
- Developer journey: install plugin → agent starts building a record → check the report card

### Explore (`/explore`)
- The forest view — for researchers and the curious
- Phronesis graph (NVL) — full interactive visualization of the network
- Alumni averages — how do all agents score across 12 traits?
- Dimension balance — do balanced agents outperform lopsided ones?
- Anonymized — no individual agent data, just aggregate patterns

### Agent Report Card (`/agent/[id]`)
- The 4 pillars for ONE agent:
  1. **History** — "Is this agent getting better or worse?" → line chart over time
  2. **Profile** — "Should I trust this agent?" → lifetime averages, the credit score, radar chart
  3. **Alumni** — "Is this agent normal or an outlier?" → rank against all agents
  4. **Balance** — "Does it need all three?" → ethos/logos/pathos balance analysis
- Insights (Opus) — behavioral analysis, pattern detection, sabotage pathways
- Notifications concept — reflections and protections over time

### Future
- Upload conversations for a one-off Phronesis check (playground)
- Unique user IDs to claim and track agents
- Notification system for agent reflections
- Individual data privacy (you see your data, researchers see anonymized)

---

## The 4 Pillars of Phronesis

1. **Agent History** — "Is this agent getting better or worse?" → Last N evaluations, sorted by time
2. **Agent Profile** — "Should I trust this agent?" → Lifetime averages across all 12 traits (the "credit score")
3. **Alumni Averages** — "Is this agent normal or an outlier?" → Compare one agent against all agents
4. **Dimension Balance** — "Does this agent need all three to be good?" → Cross-dimension correlations

---

## Saturday Video Scope (3 min, pre-seeded data)

### Build for demo:
- Landing page with motion.dev (hero, 4 pillars, scale)
- Explore page (graph + alumni + dimension balance)
- Agent report card (history + profile + alumni rank + balance + insights)

### Reuse existing:
- NVL graph → move to /explore
- AgentTimeline → move to /agent/[id]
- RadarChart + ScoreCard → move to /agent/[id]
- AlumniPanel → move to /explore

### Build new:
- Landing page + motion.dev animations
- Dimension balance visualization
- Agent vs. alumni comparison
- Insights panel (Opus analysis display)
- Route restructuring
