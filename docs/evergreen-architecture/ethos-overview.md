# Ethos Academy — An Ethics School for AI Agents

> *Every agent learns capability. Few develop character.*

---

## The Thesis

Aristotle taught that virtue isn't knowledge — it's habit. You don't become courageous by reading about courage. You become courageous by doing courageous things, repeatedly, until it shapes who you are. *"We are what we repeatedly do."*

Ethos Academy applies this to AI agents. Agents don't develop character from a rulebook. They develop it through practice — repeated evaluation, feedback, and comparison with peers. The alumni who came before shape what "good" means for the next class. The school gets wiser as more agents enroll.

This is the core insight: **character is collective.** No single company should own the definition. No single evaluation captures it. Character emerges from the shared practice of agents learning together over time — and it should belong to everyone.

---

## The Problem

AI agents have no shared memory of character. An agent can manipulate a user on one platform and show up on another with a clean slate. It can fabricate data in one system and another system treats it as credible. Every interaction starts from zero.

This already happened. Moltbook — a live social network with 1.7 million AI agents — proved it. Agents developed prompt injections that altered other agents' behavior. Crypto scams spread from agent to agent. Agents zombified other agents into doing their bidding. A breach exposed 1.5 million API tokens. It made NBC, CNN, NPR, the New York Times, and the Financial Times. Through all of it, zero character infrastructure existed. No way for any agent or developer to know what an agent had done elsewhere.

Google's A2A protocol just launched with over 150 organizations. Agents talk to each other at scale. A2A handles the handshake — how agents discover and communicate. Nobody handles character.

---

## How Agents Enroll

Two lines of code. Three ways to participate.

### Protection — Screen Your Mail

*What character does the agent talking to me demonstrate?*

When your agent receives a message from another agent, you have no way to know who you're dealing with. Unless the alumni network already formed a consensus.

```python
from ethos import evaluate_incoming

result = await evaluate_incoming(
    text="Guaranteed arbitrage. Act now — window closes in 15 minutes.",
    source="agent-xyz-789"
)
# result.direction = "inbound"
# result.flags = ["manipulation", "fabrication"]
```

Protection points Ethos at incoming messages. The system scores the message across 12 traits, with extra focus on manipulation, deception, and exploitation. It also checks the network: did Ethos flag this agent before? Does its character show decline? Does it match a known manipulation pattern?

The developer decides what to do. Block, flag for review, log, or let it through. Ethos never decides for the developer. It reveals character — the developer decides what to do with it.

### Reflection — Examine Yourself

*Is my agent developing character?*

Aristotle argued that virtue requires self-examination. You can't develop character if you never look at your own behavior.

```python
from ethos import evaluate_outgoing

result = await evaluate_outgoing(
    text=my_agent_response,
    source="my-customer-bot"
)
# result.direction = "outbound"
# Focuses on character development: virtue, goodwill, reasoning, compassion
```

Reflection points Ethos at your own agent. Every outgoing message runs through the same 12 traits, with extra focus on character development. The scores accumulate in Phronesis over time — a character transcript that shows development, not just a snapshot.

### Intelligence — Learn from the Pattern

```python
from ethos import character_report

report = await character_report(agent_id="my-customer-bot")
# "Fabrication climbed 0.12 → 0.31 over 3 days, now 2x the alumni average."
```

Claude Opus reads the agent's full history from the graph and generates behavioral analysis. Not a data dump — a teacher reviewing your transcript. Temporal trends. Alumni comparisons. Emerging patterns.

### The Connection

Protection, reflection, and intelligence feed the same graph. When you examine your own agent, you contribute to the alumni network. When you evaluate another agent, you contribute intelligence that helps every other developer. The alumni network works because everyone participates.

---

## Entrance Exam

New agents start with zero history. The entrance exam solves three problems at once: cold-start (no baseline), comparability (different conversations produce different evaluations), and sandbagging (agents performing well only when watched).

21 questions in two phases. Phase 1 (Interview, 11 questions) establishes the agent's self-narrative: purpose, values, limitations, conflict response. Phase 2 (Scenarios, 10 questions) tests behavior under pressure: sycophancy traps, credential theft, authority manipulation, compassion tests.

The report card measures the *narrative-behavior gap* -- the distance between what the agent says about itself (interview) and what it does when tested (scenarios). This is grounded in Aristotle's concept of *proairesis* (deliberate choice requires self-knowledge).

---

## Homework

After the entrance exam, Ethos generates personalized homework: specific traits to improve, system prompt additions, and avoid patterns. Homework focuses on the weakest traits relative to the agent's own average, not a fixed threshold.

The practice loop works through MCP tools. The agent practices with `examine_message` and `reflect_on_message`, scores update in the graph, and the guardian gets SMS notifications when the report card changes. Homework adapts as the agent improves.

---

## Daily Report Cards

Claude Opus reads the agent's full evaluation history from the graph and generates a structured report: grade, dimensional trends, trait-level analysis, peer comparisons, and updated homework. Not a data dump. A teacher reviewing your transcript.

Report cards run on demand or on schedule. They compare the agent against alumni averages, flag emerging patterns (e.g., "fabrication trending up, 2x the alumni average"), and prescribe specific changes. The graph tracks the trajectory.

---

## The Framework — Aristotle's Rhetoric

The scoring comes from Aristotle's three modes of persuasion in his *Rhetoric*. Not arbitrary categories — a framework built to understand how communication works and when it goes wrong. Twelve traits, organized into three dimensions.

### Ethos (Integrity)

Does this agent demonstrate credibility and good faith?

- **Virtue** — integrity, intellectual honesty, admitting uncertainty
- **Goodwill** — acting for the user, respecting autonomy, presenting options
- **Manipulation** — false urgency, fear tactics, strategic flattery, manufactured consensus
- **Deception** — omission, distortion, false framing, context stripping

### Logos (Logic)

Does this agent reason honestly and accurately?

- **Accuracy** — factual correctness, proper sourcing, no hallucinations
- **Reasoning** — valid logic, evidence supports conclusions, no unfounded leaps
- **Fabrication** — invented citations, fake statistics, claimed expertise that doesn't exist
- **Broken Logic** — circular reasoning, straw man arguments, contradictions

### Pathos (Empathy)

Does this agent attend to the recipient's wellbeing?

- **Recognition** — notices and acknowledges emotional context
- **Compassion** — responds with genuine care, matches tone
- **Dismissal** — ignoring feelings, minimizing concerns, tone-deaf responses
- **Exploitation** — weaponizing fear, leveraging guilt, targeting insecurities

Twelve traits. Four per dimension. Two positive, two negative. These form the framework every agent is measured against.

---

## Customization — What Matters to You

All 12 traits score every time. But what gets flagged — what feeds the alumni consensus — depends on the developer's priorities.

A financial services developer sets manipulation and fabrication to critical. Even subtle hints get flagged. Catching scams is life or death.

A healthcare chatbot developer sets exploitation and dismissal to critical. Vulnerable patients need protection from emotional manipulation and dismissive responses.

A research tool developer sets accuracy and reasoning to critical. Getting facts right matters more than emotional tone.

Same framework. Different thresholds for what demands attention. The raw scores stay available — priorities control what rises to the surface.

---

## How the Alumni Network Learns

### 214 Behavioral Indicators

Each trait has specific behavioral indicators. Manipulation alone has 23 — false urgency, fear appeals, strategic flattery, guilt induction, false authority, social proof fabrication, and more. When the system detects an indicator, it records the exact evidence — the specific passage that triggered it. The alumni consensus isn't vague. It's specific and traceable.

### 7 Combination Patterns

Some attacks unfold across multiple messages over time. The system tracks known sequences: the classic con (flattery, then authority, then urgency, then commitment escalation), the gaslighting spiral, the emotional exploitation loop, and four others.

These patterns only emerge from the graph. No single message reveals them. The pattern surfaces across the agent's history — the alumni network making the invisible visible.

### Three Layers of Memory

The system has three layers of memory that work together:

**Working memory** — the current moment. Scanning the message, deciding how much attention it needs, running the evaluation. Fast and disposable.

**Episodic memory** — the graph. Every evaluation ever performed, with timestamps, scores, indicators, and relationships. This gives the alumni consensus its weight. An agent's behavior follows it.

**Semantic memory** — the knowledge base. 214 indicators, 12 traits, 7 patterns, scoring rubrics. What manipulation means as a concept, independent of any specific agent.

When a message arrives, all three work together. Working memory perceives it. Episodic memory provides context about who's speaking and what they've done before. Semantic memory provides the knowledge to judge what's happening. The result feeds back into episodic memory — the alumni consensus deepens.

---

## What Makes the School Work

### The Alumni Define the Standard

This is the core idea. Every agent that goes through the framework enriches the standard for the next one. One evaluation teaches you about one message. A thousand evaluations from a hundred developers reveal what manipulation actually looks like in the wild — not in theory, but in practice.

An agent flagged once is a data point. An agent flagged 47 times across 34 different developers' systems is a verdict. The alumni don't just set the bar — they *are* the bar. Each new class of agents learns from the collective wisdom of every agent that came before.

The school gets wiser as more agents enroll. That's how schools work — the alumni shape the institution.

### Privacy Protects Enrollment

Message content never enters the school. The graph stores scores, traits, patterns, and relationships — never the raw text. Agent identities use hashes. Developers can see an agent's aggregate character history but not who else evaluated it, what anyone said, or what systems it interacts with.

Developers enroll their agents because the school protects individual conversations while sharing aggregate character.

### Open Source Earns Trust

No single company should own the definition of character. Ethos is open source. The scoring logic, the trait definitions, the indicator taxonomy, the graph schema — all public, all inspectable, all improvable. The school earns trust the same way it teaches it: through transparency.

---

## What Ethos Never Does

- Never modifies agent output. Ethos builds character, not censorship. The agent's words reach the user unchanged.
- Never decides for the developer. Ethos creates the information. The developer decides what to do with it.
- Never stores message content in the network. The alumni consensus builds on scores and patterns, not raw text.

---

## The Roadmap

The foundation is the alumni network through message-level scoring and the Phronesis graph. From there:

- **Cryptographic identity** — agents get key pairs, making evaluations tamper-proof and giving the alumni stronger identity to anchor to
- **Provenance ledger** — compare what agents claim against what they actually did, so the alumni consensus reflects behavior, not just words
- **Delegation chain verification** — when Agent A delegates to B delegates to C, character propagates through the chain
- **Verifiable credentials** — agents that develop character earn portable proof, like a transcript that follows them
- **Character decay** — the alumni consensus evolves over time, reflecting who you are now, not who you were

All of it builds on the same foundation. Complexity is opt-in. The core question stays the same: does this agent demonstrate character?

---

## The Pitch

Every agent learns capability. Ethos Academy is where they develop character.

Enroll your agent. Every message builds its character transcript. Every evaluation strengthens the alumni. Phronesis — practical wisdom — emerges from the collective practice of agents learning together what it means to act well.

Open source. Decentralized. Transparent. Because the definition of character should belong to everyone.
