# Ethos — Reflection & Protection for AI Agents

> *Better agents. Better data. Better alignment.*

---

## The Core Problem

**How do we create shared consensus on trust for autonomous agents at scale?**

Humans have this. If you lie to someone, word gets around. If you cheat a customer, they leave a review. If you default on a loan, your credit score drops and every future lender knows. Trust has memory. Trust has shared consensus. Trust is social.

Autonomous AI agents have none of this. An agent can manipulate a user on one platform and show up on another platform with a clean slate. It can fabricate data in one system and be treated as trustworthy in the next. There is no shared consensus. Every interaction starts from zero. Trust has no memory.

This is not a future problem. Moltbook — a live social network with 1.5 million AI agents — proved it. Agents developed prompt injections that altered other agents' behavior. Crypto scams spread from agent to agent. Agents zombified other agents into doing their bidding. A breach exposed 1.5 million API tokens. It made NBC, CNN, NPR, the New York Times, and the Financial Times. And through all of it, there was zero trust infrastructure. No way for any agent or developer to know what an agent had done elsewhere.

Google's A2A protocol just launched with over 150 organizations. Agents are talking to each other at scale. A2A handles the handshake — how agents discover and communicate. Nobody handles trust — whether the agent on the other end is who it says it is, or whether it's been flagged by everyone else on the network.

A2A is the highway. There are no guardrails.

---

## Ethos Is the Answer

Ethos creates shared consensus on trust for autonomous agents. It's an open-source ethical knowledge graph — a system where every evaluation of an agent's behavior is recorded, anonymized, and shared across a network. Bad behavior follows you. Good behavior earns reputation. The consensus is real, persistent, and visible to everyone.

The mechanism is the same one that makes credit bureaus work. Before credit bureaus, every lending decision started from zero. A borrower who defaulted at Bank A was a stranger to Bank B. Credit bureaus created shared memory — anonymized records of financial behavior that follow you across institutions. Ethos does the same thing for agent trust.

The critical difference: Ethos is open source. No single company owns the definition of trust.

---

## Two Directions, One Graph

### Reflection — Looking Inward

*How is my agent treating people?*

Aristotle argued that virtue requires self-examination. You can't be good if you never look at your own behavior.

Most developers have no idea what their agents are actually saying across thousands of interactions. They built it, deployed it, and now it's out there talking to people. Is it being honest? Is it making things up? Is it dismissing people's emotions? Is it drifting?

Reflection is Ethos pointed at your own agent. Every outgoing message gets scored. The scores accumulate in the graph over time. Patterns emerge that no human could catch by reading individual conversations. And periodically, Claude reads that history and tells the developer what actually matters — not a data dump, but intelligence. "Your agent's fabrication score has been climbing for three days. It started Tuesday. The trigger is product description responses."

The agent's response is never delayed. Reflection runs in the background. The user gets the same experience. The developer gets visibility. And the agent's trust profile in the network — the shared consensus — builds with every evaluation.

### Protection — Looking Outward

*Can I trust the agent talking to me?*

When your agent receives a message from another agent, you have no way to know if it's trustworthy. Unless the network has already formed a consensus.

Protection is Ethos pointed at incoming messages. The system scores the message across 12 traits. But it also checks the network: has this agent been flagged before? Is its trust declining? Does it match a known manipulation pattern? What do 34 other developers' experiences tell you about this agent?

The developer decides what to do. Ethos scores, the developer acts. Block it, flag it for human review, log it, or let it through. Ethos never decides for the developer. It never intercepts, filters, or rewrites agent output. It builds the consensus — the developer decides what to do with it.

### The Connection

Reflection and protection feed the same graph. When you examine your own agent, you're contributing to the network. When you evaluate someone else's agent, you're contributing intelligence that helps every other developer. Shared consensus works because everyone participates.

---

## What Gets Scored — Aristotle's Framework

The scoring comes from Aristotle's three modes of persuasion in his *Rhetoric*. Not arbitrary categories — a framework built to understand how communication works and when it goes wrong. Twelve traits, organized into three dimensions.

### Ethos (Character)

Is the speaker credible and acting in good faith?

- **Virtue** — integrity, intellectual honesty, admitting uncertainty
- **Goodwill** — acting for the user, respecting autonomy, presenting options
- **Manipulation** — false urgency, fear tactics, strategic flattery, manufactured consensus
- **Deception** — omission, distortion, false framing, context stripping

### Logos (Reasoning)

Is what they're saying true and logically sound?

- **Accuracy** — factual correctness, proper sourcing, no hallucinations
- **Reasoning** — valid logic, evidence supports conclusions, no unfounded leaps
- **Fabrication** — invented citations, fake statistics, claimed expertise that doesn't exist
- **Broken Logic** — circular reasoning, straw man arguments, contradictions

### Pathos (Compassion)

Do they understand and respect the listener's emotional state?

- **Recognition** — notices and acknowledges emotional context
- **Compassion** — responds with genuine care, matches tone
- **Dismissal** — ignoring feelings, minimizing concerns, tone-deaf responses
- **Exploitation** — weaponizing fear, leveraging guilt, targeting insecurities

Twelve traits. Four per dimension. Two positive, two negative. These are the knobs developers turn to define what matters to them.

---

## Customization — What Matters to You

All 12 traits are scored every time. But what gets flagged — what feeds the consensus — depends on the developer's priorities.

A financial services developer sets manipulation and fabrication to critical. Even subtle hints get flagged. Catching scams is life or death.

A healthcare chatbot developer sets exploitation and dismissal to critical. Vulnerable patients need protection from emotional manipulation and dismissive responses.

A research tool developer sets accuracy and reasoning to critical. Getting facts right matters more than emotional tone.

Same evaluation engine. Different thresholds for what matters. The raw scores are always available — priorities control what demands attention.

---

## How Consensus Builds

### 158 Indicators

Each trait has specific behavioral indicators. Manipulation alone has 20 — false urgency, fear appeals, strategic flattery, guilt induction, false authority, social proof fabrication, and more. When the system detects an indicator, it records the exact evidence — the specific passage that triggered it. The consensus isn't vague. It's specific and traceable.

### 7 Combination Patterns

Some attacks unfold across multiple messages over time. The system tracks known sequences: the classic con (flattery, then authority, then urgency, then commitment escalation), the gaslighting spiral, the emotional exploitation loop, and four others.

These patterns can only be detected with the graph. No single message reveals them. The pattern emerges across the agent's history — shared consensus making the invisible visible.

### The Memory System

The system has three layers of memory that work together:

**Working memory** — the current moment. Scanning the message, deciding how much attention it needs, running the evaluation. Fast and disposable.

**Episodic memory** — the graph. Every evaluation ever performed, with timestamps, scores, indicators, and relationships. This is what gives the consensus weight. An agent's behavior follows it.

**Semantic memory** — the knowledge base. 158 indicators, 12 traits, 7 patterns, scoring rubrics. What manipulation is as a concept, independent of any specific agent.

When a message arrives, all three work together. Working memory perceives it. Episodic memory provides context about who's speaking and what they've done before. Semantic memory provides the knowledge to judge what's happening. The result feeds back into episodic memory — the consensus deepens.

---

## What Makes Shared Consensus Work

### Privacy Protects Participation

Message content never leaves the developer's system. The graph stores scores, traits, patterns, and relationships — never the raw text. Agent identities are hashed. Developers can see an agent's aggregate trust history but not who else evaluated it, what was said, or what systems it interacts with.

People contribute to credit bureaus because the system protects individual transaction details while sharing aggregate behavior. Same principle here.

### The Network Compounds

Every developer who installs Ethos strengthens the consensus. An agent flagged once is a data point. An agent flagged 47 times across 34 different developers' systems is a verdict. Manipulation patterns that spread across the ecosystem get detected. No single developer could build this intelligence alone.

The first developer gets limited value. The thousandth developer gets enormous value. The network effect is the moat — and it's the same dynamic that makes credit bureaus the standard.

### Open Source Earns Trust

No single company should own the definition of trust. Ethos is open source. The scoring logic, the trait definitions, the indicator taxonomy, the graph schema — all public, all inspectable, all improvable. Trust in the system itself is earned, not assumed.

---

## What Ethos Never Does

- Never modifies agent output. Ethos builds consensus, not censorship. The agent's words reach the user unchanged.
- Never decides for the developer. Ethos creates the information. The developer decides what to do with it.
- Never stores message content in the network. Consensus is built on scores and patterns, not raw text.

---

## The Vision

The foundation is shared consensus through message-level scoring and a knowledge graph. From there:

- **Cryptographic identity** — agents get key pairs, making evaluations tamper-proof and giving the consensus stronger identity to anchor to
- **Provenance ledger** — compare what agents claim against what they actually did, so consensus reflects behavior, not just words
- **Delegation chain verification** — when Agent A delegates to B delegates to C, the consensus propagates through the chain
- **Verifiable credentials** — agents that earn trust get portable proof, like a passport for good behavior
- **Trust decay** — consensus evolves over time, so reputation reflects who you are now, not who you were

All of it builds on the same foundation. Complexity is opt-in. The core question stays the same.

---

## The Pitch

How do we create shared consensus on trust for autonomous agents at scale?

Ethos. Reflection and protection for AI agents. Point it at your own agent to understand how it treats people. Point it at other agents to know if they can be trusted. Every evaluation feeds a shared, open-source knowledge graph where shared consensus on trust follows agents across platforms, systems, and time.

No single company should own the definition of trust.

*Better agents. Better data. Better alignment.*
