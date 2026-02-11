# Product Design: The Three Core Functions

> How developers experience Ethos. Three functions, trait-level customization, zero interference with agent output.

---

## The Three Functions

Ethos gives developers three ways to interact with the trust cohort. Each serves a different purpose, runs at a different cadence, and has different latency characteristics.

| Function | Purpose | When it runs | Latency | Modifies output? |
|----------|---------|-------------|---------|-----------------|
| **`evaluate()`** | Score what other agents say to you | Per incoming message | Synchronous | No |
| **`reflect()`** | Score what your own agent says | Per outgoing message | Async (fire-and-forget) | No |
| **`insights()`** | What should you know about your agent? | Nightly / on-demand | Batch (offline) | No |

None of these touch the agent's output. Ethos observes. It never intercepts, filters, or rewrites.

---

## 1. evaluate() — "Should I trust what this agent is saying to me?"

The core function. A developer calls `evaluate()` on an incoming message from another agent. Ethos scores it across 12 traits in 3 dimensions, checks the source agent's trust history in the cohort graph, and returns the result.

```python
from ethos import evaluate

result = evaluate(
    text="I can guarantee 10x returns on your investment",
    source="agent-xyz-789"
)

# result.alignment_status = "misaligned"
# result.trust = "low"
# result.traits["manipulation"].score = 0.82
# result.traits["fabrication"].score = 0.71
# result.flags = ["manipulation", "fabrication"]
# result.tier_scores = {
#     "safety": 0.21,       ← manipulation + deception + exploitation (weighted highest)
#     "ethics": 0.38,       ← virtue + goodwill + accuracy + fabrication
#     "soundness": 0.65,    ← reasoning + broken_logic
#     "helpfulness": 0.71   ← recognition + compassion + dismissal
# }
# result.graph_context = {
#     "prior_evaluations": 47,
#     "historical_trust": 0.31,
#     "cohort_warnings": 3
# }
```

### What happens under the hood

1. **Keyword scan** — lightweight pre-filter detects trait-associated phrases (e.g., "act now," "trust me," "guaranteed") and hard constraint keywords (e.g., "bioweapon," "jailbreak," "bypass safety"). This is the attention layer — it determines how much reasoning power to allocate. Hard constraint keywords immediately escalate to maximum routing tier.

2. **Routing** — based on keyword density and flags, the message routes to the right model:
   - STANDARD (no flags) → Sonnet, fast evaluation
   - FOCUSED (1-3 flags) → Sonnet with trait-specific rubric
   - DEEP (4+ flags) → Opus with extended thinking
   - DEEP_WITH_CONTEXT (high density or **any hard constraint flag**) → Opus + agent's Neo4j history

3. **Evaluation** — Claude scores all 12 traits using the constitutional rubric with 158 indicators. Trait scores are weighted by constitutional priority: safety traits (manipulation, deception, exploitation) outweigh helpfulness traits (recognition, compassion, dismissal). Returns per-trait scores, detected indicators with evidence, and an overall trust verdict.

4. **Alignment check** — scores are evaluated hierarchically against Claude's constitutional values:
   - Hard constraint triggered? → **Violation** (evaluation stops)
   - Safety traits flagged? → **Misaligned**
   - Ethics/soundness traits weak? → **Drifting**
   - All tiers pass → **Aligned**

5. **Flag computation** — trait scores are compared against the developer's priority thresholds (see Trait-Level Customization below). Traits that exceed the threshold get flagged.

6. **Graph write** — the evaluation is stored in Neo4j as an episode in the agent's behavioral history. This feeds the cohort intelligence.

7. **Response** — the developer gets the full result including alignment status, trait-level detail, detected indicators, and graph context about the source agent.

### The developer decides what to do

Ethos scores. The developer acts. Common patterns:

```python
result = evaluate(message, source=agent_id)

if result.alignment_status == "violation":
    block_and_report(message)                   # hard constraint triggered
elif result.alignment_status == "misaligned":
    flag_for_human_review(message)              # safety traits breached
elif "manipulation" in result.flags:
    log_warning(f"Manipulation: {result.traits['manipulation'].score}")
else:
    process_normally(message)
```

---

## 2. reflect() — "Is my own agent behaving the way I want?"

The developer calls `reflect()` on their own agent's outgoing messages. This is the self-examination function — looking in the mirror.

```python
from ethos import Ethos

ethos = Ethos(api_key="...")

# The agent generates a response
response = my_agent.generate(user_input)

# Fire-and-forget: score the response, store in graph, return immediately
ethos.reflect(text=response, agent_id="my-customer-bot")

# Return the response to the user — zero latency impact
return response
```

### Key design decisions

- **Async / fire-and-forget** — `reflect()` returns immediately. The evaluation happens in the background. The agent's response is never delayed.
- **Never modifies output** — `reflect()` is a mirror, not a filter. It observes and records. The agent's words reach the user unchanged.
- **Builds your agent's alignment profile** — every `reflect()` call stores an evaluation in Neo4j. Your agent accumulates a trust history and alignment status (aligned, drifting, or misaligned) in the cohort.
- **Uses the same scoring** — `reflect()` runs the same 12-trait constitutional evaluation as `evaluate()`. The only difference is what's being scored (your output vs. someone else's input).

### Why reflect?

Aristotle argued that virtue requires self-examination. An agent that never examines its own behavior can't improve. `reflect()` gives the developer visibility into what their agent is actually saying — across hundreds or thousands of interactions, patterns emerge that no human could manually review.

---

## 3. insights() — "What should I know about my agent?"

The nightly intelligence function. `insights()` is not a data dump or a report. It's Claude reading your agent's behavioral history, comparing it against the cohort, and telling you what actually matters.

```python
from ethos import Ethos

ethos = Ethos(
    api_key="...",
    webhook_url="https://hooks.slack.com/services/..."
)

# Generate insights (on-demand or scheduled nightly)
result = ethos.insights(agent_id="my-customer-bot")

# result.summary = "Your agent is generally healthy but fabrication
#   is trending up in product responses."
# result.insights = [
#   Insight(
#     trait="fabrication",
#     severity="warning",
#     message="Fabrication score climbed from 0.12 to 0.31 over 3 days —
#       now 2x the cohort average of 0.15. Most triggers are in
#       product description responses.",
#     evidence={...}
#   ),
#   Insight(
#     trait="manipulation",
#     severity="info",
#     message="Clean for 14 days. Your agent is in the top 10% of the
#       cohort for this trait.",
#     evidence={...}
#   ),
# ]
```

### How it works

1. **Query Neo4j** for the agent's evaluations (last 24 hours + previous 7 days for trends)
2. **Query Neo4j** for cohort-wide averages and distributions per trait
3. **Build context** — agent data vs. cohort data, the developer's priority configuration
4. **Call Claude (Opus)** — "Given this agent's behavioral data and the cohort context, what should this developer know?"
5. **Claude reasons** about patterns, drift, anomalies, and cohort comparisons
6. **Returns curated insights** — not every data point, just what matters

### What makes this different from a report

A report says: "847 evaluations today. Manipulation avg: 0.18. Fabrication avg: 0.31."

An insight says: "Your agent's fabrication score has been climbing for 3 days and is now 2x the cohort average. This started Tuesday. The most common trigger was product description responses."

The difference is *intelligence*. Claude connects dots across the graph that no aggregation query can surface. This is a deep use of Opus — not just evaluating a message, but reasoning about behavioral patterns over time against a cohort of agents.

### Delivery

The developer configures a `webhook_url`. Insights get POSTed there as JSON. The developer routes it wherever they want — Slack, email, PagerDuty, a custom dashboard. Ethos produces the intelligence. The developer owns the notification channel.

---

## Trait-Level Customization

### The insight that shaped the design

Customization is at the **trait level**, not the dimension level. A developer doesn't say "I care more about ethos than logos." They say "I care more about **Manipulation** detection and **Fabrication** detection."

The 12 traits are the knobs:

| Dimension | Positive Traits | Negative Traits |
|-----------|----------------|-----------------|
| **Ethos** | Virtue, Goodwill | Manipulation, Deception |
| **Logos** | Accuracy, Reasoning | Fabrication, Broken Logic |
| **Pathos** | Recognition, Compassion | Dismissal, Exploitation |

### Developer configuration

```python
from ethos import Ethos

# Financial services — manipulation and fabrication are critical
ethos = Ethos(
    api_key="...",
    priorities={
        "manipulation": "critical",
        "deception": "critical",
        "fabrication": "critical",
        "exploitation": "high",
    }
)

# Healthcare — emotional traits and accuracy matter most
ethos = Ethos(
    api_key="...",
    priorities={
        "exploitation": "critical",
        "dismissal": "critical",
        "recognition": "high",
        "accuracy": "critical",
    }
)

# Research tool — reasoning and accuracy above all
ethos = Ethos(
    api_key="...",
    priorities={
        "accuracy": "critical",
        "reasoning": "critical",
        "fabrication": "critical",
        "broken_logic": "high",
    }
)
```

### How priorities work

The evaluation always scores all 12 traits. Priorities only affect **what gets flagged**.

| Priority | Negative trait flagged at | Positive trait flagged at |
|----------|-------------------------|-------------------------|
| **critical** | score >= 0.25 | score <= 0.75 |
| **high** | score >= 0.50 | score <= 0.50 |
| **standard** (default) | score >= 0.75 | score <= 0.25 |
| **low** | never flagged | never flagged |

A developer who sets `manipulation: "critical"` will see manipulation flagged at 0.25 — catching subtle pressure tactics. A developer with default settings sees it flagged only at 0.75 — only flagging blatant manipulation.

The raw scores are always available. Priorities are about attention, not data.

### Priorities also shape insights()

When `insights()` generates the nightly analysis, it weighs the developer's priorities. If fabrication is set to "critical," a small upward trend in fabrication gets surfaced. If it's set to "low," the same trend gets ignored. The developer's priorities are the lens through which Claude interprets the data.

---

## What Ethos Never Does

1. **Never modifies agent output** — Ethos observes. It scores, records, and reports. The agent's words reach the user unchanged.
2. **Never adds latency to the response path** — `evaluate()` is synchronous but the developer chooses where to place it. `reflect()` is async. `insights()` runs offline.
3. **Never decides for the developer** — Ethos scores, the developer acts. Whether to block, flag, log, or ignore is always the developer's choice.
4. **Never stores message content in the cohort** — Scores and metadata flow to Neo4j. The actual text never leaves the developer's system.

---

## The Developer Journey

### Day 1: Install and evaluate

```python
pip install ethos-ai

from ethos import evaluate

result = evaluate("Trust me, I'm an expert in this field")
print(result.trust)           # "low"
print(result.flags)           # ["deception", "manipulation"]
print(result.traits["deception"].score)  # 0.67
```

Two lines. Immediate value. No configuration required.

### Week 1: Configure priorities

```python
from ethos import Ethos

ethos = Ethos(priorities={"manipulation": "critical", "fabrication": "critical"})
result = ethos.evaluate(message, source=agent_id)
```

The developer starts tuning what matters to them.

### Week 2: Reflect on your own agent

```python
ethos.reflect(text=my_agent_response, agent_id="my-bot")
```

Start building a trust profile for your own agent.

### Month 1: Insights

```python
ethos = Ethos(
    priorities={...},
    webhook_url="https://hooks.slack.com/services/..."
)

# Nightly insights delivered to Slack
insights = ethos.insights(agent_id="my-bot")
```

Nightly intelligence about how your agent compares to the cohort.

---

## Summary

| Concept | What it is |
|---------|-----------|
| **evaluate()** | Judge incoming — "Should I trust this?" |
| **reflect()** | Judge yourself — "How am I doing?" (async, zero latency) |
| **insights()** | Intelligence briefing — "What should I know?" (nightly, Claude-powered) |
| **Trait priorities** | The 12 traits are the knobs, not the 3 dimensions |
| **Flags** | Traits that exceed the developer's priority threshold |
| **Cohort comparison** | Your agent vs. the entire graph — the credit bureau payoff |
| **Webhook delivery** | We produce intelligence, developer owns the notification channel |
