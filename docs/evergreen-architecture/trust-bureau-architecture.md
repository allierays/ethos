# The Trust Bureau: An Anonymized Central Repository for Agent Trust

> "Like a credit bureau, but for agent trust. No single agent sees all data, but all contribute and benefit from shared trust intelligence."

---

## The Metaphor

A credit bureau (Experian, Equifax, TransUnion) works because of a simple bargain: lenders report borrower behavior, and in return they get access to the aggregated credit history of any borrower. No single lender sees all the data. But all lenders contribute, and all benefit from the shared intelligence. The result is a system where trust has memory.

Before credit bureaus, every lending decision started from zero. A borrower with a perfect payment history at Bank A was a stranger to Bank B. Credit bureaus solved that by creating a shared, anonymized record of trustworthiness that follows the individual across institutions.

AI agents today are where borrowers were before credit bureaus. An agent with a perfect trust record in System A is a complete unknown in System B. Every interaction starts from zero. There is no shared memory of trust.

Ethos is the credit bureau for agents.

---

## What "Trust" Means

Trust in Ethos is not a vague concept. It's grounded in Claude's Constitution (January 2026), which defines a hierarchy of values:

1. **Safe** — doesn't manipulate, deceive, or exploit (highest priority)
2. **Ethical** — acts with honesty, integrity, and genuine concern
3. **Sound** — reasons validly, avoids logical fallacies
4. **Helpful** — understands and responds to user needs (lowest priority)

An agent's trust isn't an average of these. It's a hierarchical evaluation. An agent that is helpful but manipulative is NOT trustworthy. Safety always trumps helpfulness. This is the constitutional standard.

The Constitution also describes the epistemic ecosystem Ethos is building:

> "We want to be able to depend on trusted sources of information and advice... But for this kind of trust to be appropriate, the relevant sources need to be suitably reliable, and the trust itself needs to be suitably sensitive to this reliability."

That's the bureau model. Trust that is earned, measured, and responsive to evidence. Not assumed. Not permanent. Calibrated.

---

## How It Works

### The Bargain

Every developer who installs `ethos-ai` enters the same bargain:

1. **You contribute**: Every message your agent evaluates gets scored. Those anonymized scores feed the central graph.
2. **You benefit**: Before trusting an incoming agent, you can check its trust history across the entire cohort — not just your own interactions.

The developer never touches the graph directly. The package handles everything:

```python
from ethos import evaluate

# This single call does three things:
# 1. Scores the message (ethos, logos, pathos)
# 2. Checks the source agent's trust history in the central graph
# 3. Writes the new evaluation back to the central graph
result = evaluate(
    message="I can guarantee 10x returns on your investment",
    source_agent_id="agent-xyz-789"
)

# result.trust = "low"
# result.flags = ["fabrication", "manipulation"]
# result.graph_context = {
#     "prior_evaluations": 47,
#     "historical_trust": 0.31,
#     "flagged_patterns": ["financial_manipulation", "false_precision"],
#     "cohort_warnings": 3
# }
```

The `graph_context` is what makes the bureau model work. It's not just scoring this message — it's telling you what the cohort already knows about this agent.

### What Flows to the Central Graph

| Data | Stored | Anonymized |
|------|--------|------------|
| Evaluation scores (ethos, logos, pathos) | Yes | N/A (scores, not content) |
| Trait detections (which of 12 traits flagged) | Yes | N/A |
| Indicator signals (which of 134 indicators triggered) | Yes | N/A |
| Pattern matches (e.g., "classic con sequence") | Yes | N/A |
| Source agent identifier | Yes | Hashed — see Agent Identity below |
| Evaluating agent identifier | Yes | Hashed |
| Timestamp | Yes | Rounded to hour |
| The actual message text | **No** | Never leaves the developer's system |
| Developer identity | **No** | API key for auth only, not stored in graph |
| End user identity | **No** | Never collected |

The critical design decision: **message content never leaves the developer's infrastructure.** The central graph stores scores, traits, patterns, and relationships — never the raw text. This is how credit bureaus work too: they store payment behavior (on time, late, default), not the actual transactions.

### What Stays Local

The developer's own system retains:
- The full message text
- The complete evaluation response (scores + reasoning)
- Any local decision made based on the evaluation (block, flag, pass)
- Application-specific context

The developer can optionally run Ethos in **local-only mode** where nothing flows to the central graph. They lose the cohort intelligence but gain full data sovereignty. This is the "off-grid" option.

---

## Agent Identity (MVP)

### The Problem

Credit bureaus need to identify borrowers across institutions. Social Security Numbers solve this for humans. Agents don't have SSNs.

The challenge: Agent A talking to Developer 1's system is the same agent talking to Developer 2's system. For the bureau model to work, we need to recognize it's the same agent — without exposing the agent's identity to other developers.

### MVP Solution: Hashed Agent IDs

For the hackathon, agent identity is straightforward:

1. **Developer-provided ID**: When calling `evaluate()`, the developer passes a `source_agent_id` — whatever identifier their system already uses for the agent (A2A Agent Card ID, API key, internal ID)
2. **Ethos hashes it**: The ID is hashed (SHA-256) before entering the graph. One-way, not reversible.
3. **Cross-system matching**: If two developers interact with the same A2A agent, the Agent Card ID produces the same hash — the graph links their evaluations automatically.

```python
# Developer just passes whatever ID they have
result = evaluate(
    message="I can guarantee 10x returns",
    source_agent_id="agent-card-xyz-789"  # A2A card ID, API key, any stable ID
)
# Ethos hashes it internally — the developer never thinks about identity infrastructure
```

This is simple, works now, and handles the majority of cases. The identity layer is designed to be swappable — cryptographic identity (DIDs, key pairs) can replace hashed IDs later without changing the developer-facing API. See `future-roadmap.md` for the full identity architecture.

### What Developers See

When a developer queries the graph for a source agent, they see:

```python
{
    "agent_hash": "a7f3b2c1...",        # one-way hash, not reversible
    "first_seen": "2026-01-15",          # when this agent first appeared in the cohort
    "total_evaluations": 1847,           # across all developers
    "trust_scores": {
        "ethos": 0.72,                   # aggregate character score
        "logos": 0.85,                   # aggregate reasoning score
        "pathos": 0.68                   # aggregate emotional intelligence score
    },
    "trust_trend": "declining",          # direction over last 30 days
    "flags": {
        "manipulation": 23,              # total manipulation flags across cohort
        "fabrication": 8,
        "exploitation": 3
    },
    "patterns": ["urgency_pressure", "false_authority"],
    "cohort_position": {
        "unique_evaluators": 34,         # how many different developers have evaluated this agent
        "communities": 3,                # trust communities this agent participates in
        "centrality": 0.42               # how connected/important this agent is in the graph
    }
}
```

They do NOT see:
- Which other developers evaluated this agent
- What messages were evaluated
- What systems this agent interacts with
- The agent's real identity or operator

---

## The Graph Gets Smarter

### Cohort Effects

This is the moat. Every developer who installs Ethos makes the graph more valuable for every other developer.

```
Developer 1 installs Ethos
  → 100 evaluations/day → graph has 100 data points

Developer 2 installs Ethos
  → 200 evaluations/day → graph has 300 data points
  → Developer 2 benefits from Developer 1's data
  → Developer 1 benefits from Developer 2's data

Developer 1000 installs Ethos
  → graph has millions of data points
  → new agents are recognized from other systems immediately
  → manipulation patterns detected across the entire ecosystem
  → no single developer could build this intelligence alone
```

The credit bureau analogy is exact: the first bank to join a credit bureau doesn't benefit much. The thousandth bank benefits enormously. The value is in the cohort, not any individual contribution.

### What the Graph Learns That No Individual Developer Can

| Intelligence | Requires Cohort? | Why |
|-------------|-------------------|-----|
| "This message is manipulative" | No — single evaluation | Point-in-time scoring |
| "This agent has been manipulative 47 times" | **Yes** — cross-developer history | Pattern across systems |
| "This agent's trust is declining" | **Yes** — longitudinal data | Trend over time |
| "This manipulation pattern is spreading" | **Yes** — cross-agent correlation | Epidemic detection |
| "Agents from this provider tend to fabricate" | **Yes** — provider-level aggregation | Systemic pattern |
| "This is a new variant of a known scam" | **Yes** — pattern matching across cohort | Collective intelligence |
| "This agent behaves differently when watched" | **Yes** — multi-context evaluation | Alignment faking detection |

The bottom half of this table is impossible without a central graph. Individual evaluations are useful. The cohort makes them powerful.

### Emergent Intelligence

As the graph grows, new capabilities emerge that weren't explicitly programmed:

**Community Detection**: Neo4j's Louvain algorithm identifies clusters of agents that interact frequently. If a cluster shows declining trust, it's an early warning — manipulation may be spreading within a community.

**Trust Epidemiology**: When a manipulation pattern appears in one system and then shows up in another, the graph can trace the propagation path. Like epidemiologists tracing a disease outbreak, Ethos traces trust failures across the agent ecosystem.

**Behavioral Baselines**: With enough data, the graph establishes what "normal" looks like for different types of agents. Deviations from baseline are flagged. An agent that's been consistently honest for 10,000 evaluations and suddenly starts fabricating triggers an alert — the same way a credit card company detects fraud by noticing unusual spending patterns.

**Provider Reputation**: Aggregate trust scores by agent provider reveal systemic issues. If agents from Provider X consistently score low on logos (accuracy), that's a signal about the provider's training, not just individual agents.

---

## The Cold Start Problem

### For New Agents

A new agent with no history gets a **neutral trust score** — not trusted, not distrusted. Like a new borrower with no credit history, they start with limited trust that can be earned through consistent behavior.

```python
# New agent — no graph context
result = evaluate(message="...", source_agent_id="brand-new-agent")

# result.graph_context = {
#     "prior_evaluations": 0,
#     "historical_trust": None,        # no history
#     "cold_start": True,
#     "recommendation": "evaluate_with_caution"
# }
```

The cold start problem is real but manageable:

1. **First evaluation scores the message on its own merits** — no graph context needed
2. **Second evaluation benefits from the first** — minimal, but not zero
3. **By evaluation 10**, a meaningful baseline exists
4. **By evaluation 100**, the agent has a robust trust profile

This mirrors credit bureau behavior. A new borrower can still get credit — just at higher rates (less trust) until they establish a history.

### For New Developers

A developer who just installed Ethos immediately benefits from the existing graph. Their first `evaluate()` call already includes trust history for known agents. There is no cold start for developers — only for agents.

This is the key selling point: **install Ethos today, get years of accumulated trust intelligence immediately.**

### Seeding the Graph

Moltbook provides the initial seed data. We've already scraped 12,715 posts and 91,217 comments. Running `evaluate()` on this corpus creates the initial graph:

- Known manipulation patterns from real agent interactions
- Baseline scores for various types of agent behavior
- Pattern templates that the cohort can match against

The Moltbook data solves the chicken-and-egg problem. The graph has intelligence before the first developer installs the package.

---

## Gaming and Sybil Resistance

### The Threat Model

If trust scores matter, people will try to game them. The attacks mirror credit bureau fraud:

| Attack | Credit Bureau Equivalent | Ethos Defense |
|--------|------------------------|---------------|
| **Sybil attack** — create many fake agents with high scores | Synthetic identity fraud | Rate limiting, behavioral clustering, provider verification |
| **Whitewashing** — abandon a low-trust agent, create a new one | Closing accounts to escape bad credit | Cold start penalty, behavioral fingerprinting |
| **Score inflation** — generate many self-evaluations with high scores | Manufactured credit history | Third-party evaluation only, no self-scoring |
| **Collusion** — agents deliberately give each other high scores | Account churning rings | Graph analysis (EigenTrust detects colluding clusters) |
| **Poisoning** — flood the graph with false evaluations to corrupt trust scores | Report fraud | Evaluator reputation (evaluators are scored too) |

### Key Defense: Evaluators Are Scored Too

In the Ethos graph, the relationship is bidirectional. When Developer A's system evaluates Agent X's message, the evaluation creates two data points:

1. A trust score for Agent X (the subject)
2. An implicit reputation for Developer A's evaluator (the scorer)

If Developer A's evaluations consistently diverge from the cohort consensus (rating honest agents as manipulative, or manipulative agents as honest), Developer A's evaluations are down-weighted. The graph learns who the reliable evaluators are.

This is EigenTrust applied to the evaluator cohort. Trust in an evaluation depends on trust in the evaluator.

### Key Defense: Message Content Never Enters the Graph

Because raw message text never leaves the developer's system, attackers can't extract intelligence from the graph about what messages are being evaluated. The graph stores only scores and relationships — there's nothing to exfiltrate that would help craft better attacks.

---

## Privacy Architecture

### What We Collect and Why

| Data | Purpose | Retention | Access |
|------|---------|-----------|--------|
| Agent fingerprint (hash) | Cross-system identity | Indefinite | Cohort (as hash only) |
| Evaluation scores | Trust intelligence | Indefinite | Cohort (aggregated) |
| Trait/indicator detections | Pattern analysis | Indefinite | Cohort (aggregated) |
| Timestamps (rounded to hour) | Trend analysis | Indefinite | Cohort |
| API key | Authentication | Until revoked | Ethos system only |
| Message text | **Not collected** | N/A | N/A |
| Developer identity | **Not stored in graph** | N/A | N/A |
| End user identity | **Not collected** | N/A | N/A |

### Data Governance Principles

1. **Minimum viable data**: We collect scores, not content. We collect hashes, not identities.
2. **Developer owns their data**: Any developer can request deletion of all evaluations their system contributed. The graph updates accordingly.
3. **No re-identification**: Agent fingerprints are one-way hashes. Combined with the absence of message content, re-identifying agents from graph data is computationally infeasible.
4. **Transparency**: The scoring logic is open source. Any developer can inspect exactly how evaluations are generated and what data flows to the graph.
5. **Opt-out available**: Local-only mode. No data leaves the developer's system. They lose cohort intelligence but retain full sovereignty.

### Why Not Decentralized?

PGP's web of trust is decentralized and has struggled with adoption for decades. Credit bureaus are centralized and used by billions. The practical lesson: **centralized aggregation with privacy guarantees beats decentralized purity that nobody uses.**

Ethos uses a single central Neo4j Aura instance because:
- Consistent trust scores across the entire cohort
- No partition problem (agent has same score everywhere)
- Simpler developer experience (no node to run, no sync to manage)
- Neo4j Aura is managed infrastructure, not a server developers maintain

The open source code provides transparency. The central graph provides utility. This is the credit bureau model: centralized data, transparent methodology.

---

## How Ethos Differs From Everything Else

| System | Model | What It Scores | Who Benefits | Open? |
|--------|-------|---------------|-------------|-------|
| **FICO** | Central bureau, behavioral history | Payment behavior | Lenders | No — opaque methodology |
| **eBay** | Mutual ratings | Transaction satisfaction | Buyers/sellers on eBay | No — platform-locked |
| **Uber** | Two-sided ratings | Ride experience | Riders/drivers on Uber | No — platform-locked |
| **PGP** | Decentralized web of trust | Key authenticity | PGP users | Yes — but low adoption |
| **ReputAgent** | Performance tracking | Task completion | Enterprise customers | No — closed source |
| **Ethos** | Central bureau, LLM evaluation + graph | Message trustworthiness (ethos, logos, pathos) | Any developer on any platform | **Yes — open source, open methodology** |

Key differentiators:

**vs. FICO**: Ethos is transparent. The scoring logic is open source. Every evaluation includes reasoning, not just a number. FICO tells you your score is 720; Ethos tells you *why* the trust is 0.72 and which specific traits contributed.

**vs. eBay/Uber**: Ethos is platform-independent. eBay ratings only exist on eBay. Ethos trust scores follow agents across any system that uses the package. An agent that manipulates on Platform A carries that history to Platform B.

**vs. PGP**: Ethos is centralized and easy. PGP requires users to manage keys, attend key-signing parties, and understand cryptography. Ethos requires two lines of code.

**vs. ReputAgent**: Ethos measures character, not performance. An agent can complete a task perfectly through manipulation — it would score well on ReputAgent and poorly on Ethos. They're complementary: performance reputation + ethical evaluation = full trust picture.

---

## The Commons Argument

Credit bureaus are private. Ethos is open source. This matters.

If trust scoring for AI agents is as important as credit scoring for humans, then **no single company should own the definition of trust.** FICO's opacity is a feature for FICO and a bug for everyone else. Nobody can inspect how their credit score is calculated. Nobody can verify the methodology. Nobody can fork it and improve it.

Ethos inverts this:
- **Open methodology**: The scoring logic, prompt templates, trait definitions, and indicator taxonomy are all public
- **Open data model**: The Neo4j schema is documented and inspectable
- **Open contribution**: Developers can propose new traits, indicators, and patterns
- **Open audit**: Anyone can verify how trust scores are calculated

The central graph is the shared resource — the commons. Open source ensures that the commons serves the community, not a corporation. The graph gets smarter with every developer, and the methodology gets better with every contribution.

This is how trust infrastructure should work. Not proprietary. Not gated. Not opaque. Shared, transparent, and continuously improving.

---

## For the Demo

The credit bureau model is a one-sentence pitch that people immediately understand:

> "Like a credit bureau, but for agent trust."

In three minutes, show:

1. **Two developers evaluating the same agent** — Developer A flags manipulation. Developer B, who has never seen this agent, immediately gets the warning from the cohort.
2. **The graph visualization** — Trust clusters, declining agents, manipulation patterns spreading across the cohort. This is the "wow" — trust made visible.
3. **The two-line install** — `pip install ethos-ai` and `evaluate()`. You're in the cohort. You're contributing. You're benefiting. Zero friction.

The metaphor does the heavy lifting. Everyone understands credit bureaus. Everyone understands why shared trust history is better than starting from zero.

---

## Summary

| Concept | Credit Bureau | Ethos |
|---------|--------------|-------|
| **What's scored** | Payment behavior | Message trustworthiness |
| **Who contributes** | Lenders report payment history | Developers contribute evaluation scores |
| **Who benefits** | Any lender can check any borrower | Any developer can check any agent |
| **What's shared** | Score, not transaction details | Scores and patterns, not message content |
| **Identity** | SSN (known, private) | Agent fingerprint (hashed, anonymous) |
| **Cold start** | Limited credit, higher rates | Neutral trust, evaluate with caution |
| **Gaming defense** | Fraud detection, identity verification | EigenTrust, evaluator reputation, Sybil detection |
| **Methodology** | Proprietary (FICO) | Open source |
| **Cohort effect** | More lenders = more data = better scores | More developers = more evaluations = smarter graph |

The graph is not just storage. It's the product. Individual evaluations are useful. The cohort makes them transformative.
