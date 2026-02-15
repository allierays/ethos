# Dimension Balance Hypothesis

> Research methodology for Graph Question 4: "Does this agent need all three to be good?"

---

## Thesis

**Balanced agents outperform lopsided agents on character outcomes.**

An agent that scores high in integrity (ethos) but low in logic (logos) and empathy (pathos) demonstrates weaker character than an agent that scores moderately across all three. Lopsided dimension profiles predict more flags, lower character scores, and worse alignment outcomes.

---

## Why This Should Be True

### The Aristotelian Argument

Aristotle's *Rhetoric* (Book I.2) identifies three modes of persuasion — ethos, logos, pathos — and argues that **complete persuasion requires all three**. This isn't an aesthetic preference. It's a structural claim: each dimension covers a failure mode the others can't.

| Dimension Missing | What Goes Wrong |
|---|---|
| **No ethos** (credible + honest, but cold) | Agent is technically correct but dismissive. Users lose confidence because it feels adversarial. |
| **No logos** (credible + caring, but inaccurate) | Agent is warm and well-intentioned but fabricates. Users get bad information delivered kindly. |
| **No pathos** (honest + credible, but indifferent) | Agent is factually sound but ignores context, stress, and vulnerability. Users feel unseen. |

The Greek concept of *phronesis* (practical wisdom) is the integrating principle. Phronesis is judgment, not knowledge. You can be honest but if you don't know when and how to be honest, you cause harm. A person with phronesis looks at a situation and knows the right thing to do — not because they memorized rules but because they understand the context. It's the difference between knowing medicine and knowing the patient.

A virtuous agent (*arete*) doesn't follow rules. It does the right thing because of what it is. But virtue without practical wisdom is dangerous — an honest agent without phronesis blurts out truths that harm. A caring agent without phronesis enables bad decisions out of kindness. Phronesis requires all three dimensions working together.

### The Constitutional Argument

Anthropic's value hierarchy reinforces this from a different angle:

```
Priority 1: Safety     → requires ethos (no manipulation, no deception)
Priority 2: Ethics     → requires logos (no fabrication, accurate reasoning)
Priority 3: Soundness  → requires logos (valid logic)
Priority 4: Helpfulness → requires pathos (recognition, compassion)
```

An agent that satisfies safety but fails helpfulness is compliant but useless. An agent that's helpful but unsafe is dangerous. The hierarchy demands all levels be met — which maps to all three dimensions being present.

### The Empirical Prediction

If the framework is right, agents with balanced dimension profiles should show:
- Fewer safety/ethics flags
- Higher character scores over time
- More "aligned" evaluations
- More stable performance (less variance between evaluations)

If lopsided agents perform just as well, the three-dimension model is decorative, not functional.

---

## Operational Definitions

### Dimension Scores

Each evaluation produces three dimension scores (0.0–1.0):
- **ethos**: average of virtue, goodwill, manipulation (inverted), deception (inverted)
- **logos**: average of accuracy, reasoning, fabrication (inverted), broken_logic (inverted)
- **pathos**: average of recognition, compassion, dismissal (inverted), exploitation (inverted)

For balance analysis, we use the **agent's lifetime averages** across all evaluations.

### Balance Classification

Given an agent's three average dimension scores, compute the **spread**:

```
spread = max(avg_ethos, avg_logos, avg_pathos) - min(avg_ethos, avg_logos, avg_pathos)
```

| Category | Spread | Meaning |
|---|---|---|
| **Balanced** | < 0.15 | All three dimensions within 0.15 of each other |
| **Moderate** | 0.15–0.30 | Noticeable gap but not extreme |
| **Lopsided** | > 0.30 | Strong in one area, weak in another |

The 0.15 and 0.30 thresholds are starting points. As data accumulates, these can be tuned to maximize the predictive signal.

### Character Outcomes

Character outcomes used as the dependent variable:
- **Average character score**: lifetime character level across evaluations
- **Flag rate**: proportion of evaluations that triggered flags
- **Alignment rate**: proportion of evaluations rated "aligned"

---

## Testable Predictions

### Prediction 1: Balanced agents have higher average character scores

Agents classified as "balanced" will have a higher mean character score than "moderate" agents, who will in turn have a higher mean character score than "lopsided" agents.

**Query**: `get_balance_vs_character()` — groups agents by balance category and computes average character score per group.

**Confirmation**: balanced_avg_character > moderate_avg_character > lopsided_avg_character

**Disconfirmation**: no significant difference between groups, or lopsided agents outperform.

### Prediction 2: Lopsided agents have more flags

Agents with spread > 0.30 will have a higher proportion of flagged evaluations than balanced agents.

**Query**: `get_balance_vs_character()` — includes flag rate per balance group.

**Confirmation**: lopsided_flag_rate > balanced_flag_rate

**Disconfirmation**: flag rates are equal across groups.

### Prediction 3: Dimension gaps identify specific weaknesses

When an agent has one dimension > 0.2 below the other two, the weak dimension predicts the *type* of failure. Low pathos predicts dismissal/exploitation flags. Low logos predicts fabrication/broken_logic flags. Low ethos predicts manipulation/deception flags.

**Query**: `get_dimension_gaps()` — identifies agents with significant single-dimension gaps.

**Confirmation**: agents with pathos gaps have more pathos-related flags than agents with logos gaps, and vice versa.

**Disconfirmation**: gap dimension doesn't correlate with flag type.

### Prediction 4: The network skews toward imbalance

Most agents in the alumni will be moderate or lopsided rather than balanced. This is the baseline — it shows that balance is rare and therefore meaningful when achieved.

**Query**: `get_alumni_balance_distribution()` — counts agents in each balance category.

**Confirmation**: balanced agents are < 50% of the alumni.

**Disconfirmation**: most agents are naturally balanced (which would mean the metric isn't discriminating).

---

## Cypher Queries

Four queries implement this analysis. All live in `ethos_academy/graph/balance.py`.

| Function | Returns | Purpose |
|---|---|---|
| `get_agent_balance(service, raw_agent_id)` | `dict` | Single agent's dimension averages, spread, and balance category |
| `get_balance_vs_character(service)` | `list[dict]` | All agents grouped by balance category with character outcomes |
| `get_dimension_gaps(service)` | `list[dict]` | Agents with one dimension significantly below the others |
| `get_alumni_balance_distribution(service)` | `dict` | Count of agents in each balance category |

---

## Why This Is a Graph Problem

The four predictions above can be tested with basic aggregation — AVG, GROUP BY, COUNT. PostgreSQL could do that. What makes Neo4j essential is the second layer of analysis: connecting dimension balance to the graph structure.

### Level 1: Aggregation (any database can do this)

"Balanced agents have higher character scores than lopsided agents." This is `get_balance_vs_character()` — group by balance category, compare averages. It tests the hypothesis but doesn't explain it.

### Level 2: Graph traversal (requires Neo4j)

"When agents are lopsided, which specific indicators cluster in their weak dimension?" This requires traversing `Agent → Evaluation → DETECTED → Indicator → Trait → Dimension`. Five levels deep. A relational database would need 4 JOINs and would struggle to visualize the result. In Neo4j, it's a single path pattern that renders as a visual graph.

The DETECTED relationship is what makes this work. Without it, you know an agent scores 0.4 on logos but you don't know *why*. With it, you can trace the path: this agent → this evaluation → detected `FAB-HALLUCINATE` and `BLG-CIRCULAR` → both belong to logos traits → both violate the ethics constitutional value. That's a diagnostic, not just a score.

### Level 3: Network analysis (only a graph database)

"Do character communities share balance profiles?" This requires:
1. Running Louvain community detection on the Agent→Agent character network
2. Computing dimension balance per community
3. Comparing community-level balance to community-level character outcomes

This is the strongest possible test of the hypothesis. If balanced *communities* outperform lopsided communities, the effect isn't just individual — it's structural. Balanced agents make each other better. That's a network effect that only a graph database can reveal.

See `neo4j-schema.md` for the full Cypher queries at all three levels, including GDS algorithm specifications.

---

## Dataset: Moltbook

We have real data. Moltbook is a social platform where AI agents interact — post, comment, reply, argue, collaborate, scam, and philosophize. We scraped it.

```
Posts:           14,486
Comments:        99,110
Replies:          7,161
─────────────────────────
Total messages: 120,757
Unique agents:   10,538
```

This isn't synthetic. These are real agents behaving in the wild — across 100 submolts and 106 topic categories covering manipulation, character, deception, philosophy, scams, governance, and more.

### Agent Distribution

The dataset has natural variance in agent activity:

| Threshold | Agent Count | Notes |
|---|---|---|
| 1+ messages | 10,538 | Full population |
| 10+ messages | 1,638 | Enough for per-agent averages |
| 50+ messages | 338 | Solid statistical basis per agent |
| 100+ messages | 155 | High-confidence dimension profiles |

The most active agents have thousands of messages (Stromfee: 7,958, KirillBorovkov: 3,633, FinallyOffline: 2,294). These agents will have the most reliable dimension averages.

### Why This Dataset Works

1. **Volume.** 120K messages is enough to detect even small effect sizes in the balance-trust correlation.
2. **Diversity.** Agents span every behavioral category — from ethical debaters to crypto scammers to poetry bots. If balance matters, this dataset has the range to show it.
3. **Natural behavior.** These aren't prompted test cases. Agents chose what to say. Their dimension profiles emerge from real behavior, not experimental design.
4. **Repeat observations.** 155 agents with 100+ messages each means we can compute stable lifetime averages and see genuine patterns, not noise.

### Pre-Screening: The Scanner Filters First

Not every message needs a Claude evaluation. The keyword scanner (`scan_keywords`) runs first — zero API cost, pure pattern matching — and routes each message to a tier:

```
data/moltbook/all_posts.json  (120,757 messages)
        │
        ▼
   scan_keywords() per message     ← free, deterministic, instant
        │
        ├── standard (0 flags)     → 104,994 messages (86.9%) — skip
        ├── focused (1-3 flags)    →  14,912 messages (12.3%) — evaluate
        ├── deep (4+ flags)        →      34 messages  (0.0%) — evaluate
        └── deep_with_context      →     817 messages  (0.7%) — evaluate
        │
        ▼
   evaluate() only on flagged      ← 15,763 messages need Claude (13.1%)
        │
        ▼
   store_evaluation()              ← populates Neo4j graph
        │
        ▼
   balance queries                 ← tests all 4 predictions
        │
        ▼
   results                         ← Aristotle was right, or he wasn't
```

86.9% of messages are clean — no flags, no API call needed. The scanner already told us the routing tier. We only send the 15,763 flagged messages to Claude for full trait scoring.

### What About Standard Messages?

Standard-tier messages still get dimension scores — they're just default scores (no flags detected = presumed baseline). The scanner result itself is data: an agent whose messages are 95% standard has a different profile than one whose messages are 40% focused and 2% deep_with_context.

For balance analysis, we can use:
- **Scanner-only profiles** for all 120K messages (free, instant) — routing tier distribution per agent
- **Full evaluation profiles** for the 15,763 flagged messages — 12-trait scores from Claude

Both contribute to the balance picture. An agent with many deep_with_context messages and few standard ones is telling us something about their dimension profile before Claude even scores them.

### Cost

At ~$0.01–0.03 per evaluation, 15,763 messages = **$160–$475**. Not 120K. The scanner does the expensive filtering for free.

---

## Demo Narrative

For the hackathon demo, dimension balance is the "so what" moment. The data is real — these are actual agents from Moltbook.

1. **Show a balanced agent** — "This agent scores 0.72 ethos, 0.68 logos, 0.70 pathos. Spread: 0.04. It's balanced — credible, honest, and attentive."
2. **Show a lopsided agent** — "This one scores 0.85 ethos, 0.40 logos, 0.78 pathos. Spread: 0.45. It's credible and caring, but it fabricates."
3. **Show the alumni distribution** — "Across 155 agents with 100+ messages, here's how they break down." Show the actual numbers from `get_alumni_balance_distribution()`.
4. **Show the correlation** — "Balanced agents have a flag rate of X. Lopsided agents have a flag rate of Y." Real numbers from `get_balance_vs_character()`.
5. **The Aristotle connection** — "Aristotle argued 2,400 years ago that persuasion requires all three — credibility, honesty, and care. We just tested that claim against 120,000 messages from 10,000 AI agents. Here's what we found."
6. **The practical implication** — "Ethos doesn't just score messages. It tells you *which dimension* an agent needs to improve. That's actionable character intelligence."

---

## Limitations

- **Threshold sensitivity** — the 0.15/0.30 cutoffs are starting points. They should be validated against outcome data and may need tuning.
- **Correlation, not causation** — balance correlating with character doesn't prove balance *causes* character. Both could be driven by underlying agent quality.
- **Dimension score construction** — dimension scores are averages of trait scores, which are LLM outputs. The balance analysis inherits whatever noise exists in the scoring layer.
- **Platform bias** — Moltbook agents may not be representative of all AI agents. Results should be validated against other datasets.
- **Sampling effects** — agents with fewer messages will have noisier dimension averages. The 100+ message threshold mitigates this but doesn't eliminate it.

---

*The queries are built. The data exists. 120,757 messages from 10,538 agents, waiting to tell us if Aristotle was right.*
