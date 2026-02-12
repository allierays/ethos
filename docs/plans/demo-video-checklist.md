# Ethos — Saturday Demo Video Checklist

**Format:** 3-minute video. **Judging:** Demo 30%, Impact 25%, Opus 4.6 Use 25%, Depth 20%.

**The story:** Phronesis answers four questions about any AI agent — is it getting better or worse, should I trust it, is it an outlier, does it need all three dimensions to be good?

---

## DONE

- [x] Evaluate engine — 12 traits, 3 dimensions, scoring, flags, alignment
- [x] Reflect — agent self-assessment + historical trend
- [x] Insights — Opus analyzes agent behavior over time (API only)
- [x] Pattern detection — 8 sabotage pathways via graph queries (API only)
- [x] Graph visualization endpoint — full taxonomy + episodic data for NVL
- [x] FastAPI — 11 endpoints, all typed
- [x] Neo4j schema + seed script
- [x] Academy: EvaluatorPanel — type a message, get radar chart + scores
- [x] Academy: AgentTimeline — select agent, see ethos/logos/pathos over time (Q1: history)
- [x] Academy: AlumniPanel — bar chart of 12 trait averages across all agents (Q3: outliers)
- [x] Academy: Full-page Phronesis graph (NVL) + agent detail sidebar (Q2: trust profile)
- [x] Academy: Graph preview on dashboard + nav header
- [x] Docker compose (API + Neo4j)
- [x] 259 tests passing
- [x] Moltbook data curated (500 posts)

---

## BUILD — Needed for demo

### Must Have (blocks the video)

- [ ] **Insights Panel** — No UI exists. Placeholder card but no component that calls `getInsights()` and displays Claude's behavioral analysis. This is the Opus 4.6 showcase moment (25% of score). Needs: summary text, list of insights with severity/trait/evidence.
- [ ] **Seed Neo4j with data** — Graph is currently empty. Run `seed_graph.py` with enough agents/evaluations to make the graph look impressive and insights meaningful.
- [ ] **End-to-end smoke test** — Verify: Docker up → API responds → Academy loads → evaluate works → graph renders → timeline populates → insights returns data. Fix anything broken.

### Should Have (makes the demo stronger)

- [ ] **Dimension Balance view** — Phronesis question #4 has no visualization. Even a simple comparison (balanced vs lopsided agents) would complete the story.
- [ ] **Richer agent sidebar** — Currently shows only dimension scores + trend. Adding trait-level detail or detected patterns would make graph clicks more impressive.
- [ ] **Polish loading/empty states** — No blank screens or console errors during recording.

### Nice to Have (if time allows)

- [ ] Show detected patterns (sabotage pathways) in the UI — currently API-only
- [ ] Show tier scores (safety/ethics/soundness/helpfulness) somewhere visible
- [ ] Reflect UI — currently just a card placeholder

---

## VIDEO — Production tasks

- [ ] **Write a script** — Talking points for each beat, timed to 3 minutes
- [ ] **Pick demo data** — Choose 1-2 agents with interesting stories (declining trust, manipulation patterns)
- [ ] **Pick a live evaluation example** — A message that produces a dramatic/clear result
- [ ] **Decide format** — Screencast + voiceover? Live terminal + UI side by side?
- [ ] **Record**
- [ ] **Edit to 3 minutes**

---

## Priority Order

1. Seed Neo4j (everything depends on data)
2. Build Insights Panel (biggest gap, highest scoring impact)
3. End-to-end smoke test
4. Write video script
5. Dimension Balance view (if time)
6. Record video
