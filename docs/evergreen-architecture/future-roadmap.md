# Future Roadmap: Post-MVP Features

> Ideas and architecture that matter but are out of scope for the hackathon. Everything here builds on the MVP — nothing here blocks it.

---

## 1. Cryptographic Agent Identity

### Why

The MVP uses hashed IDs for agent identity. This works but has limitations:
- Agents can be impersonated (guess or steal the ID)
- Evaluations can't be cryptographically verified
- No way to prove an agent *didn't* take an action
- Sybil resistance is weak (creating IDs is free)

### The Spectrum

| Level | What It Is | Developer Effort | What It Adds |
|-------|-----------|-----------------|-------------|
| **MVP (current)** | Hashed agent IDs in Neo4j | Zero | Basic cross-system identity |
| **Level 1** | Public/private key pairs | Low — auto-generated, stored like API keys | Tamper-proof signatures, impersonation resistance |
| **Level 2** | DIDs over HTTPS (did:web) | Moderate — host a JSON file at a known URL | W3C standard, A2A interoperability, domain verification |
| **Level 3** | DIDs on blockchain (did:ethr) | Higher — wallet library, gas fees | Immutable identity, strong Sybil resistance, full decentralization |

### Recommended Path

**Level 1 first.** Key pairs are the foundation. Every agent gets a cryptographic key pair on registration. The public key becomes the identity. Every evaluation is signed. The developer experience stays simple — the package generates keys automatically, stores the private key like an API key.

```python
# Level 1 developer experience (same simplicity, cryptographic identity under the hood)
from ethos import register, evaluate

agent = register(name="my-customer-service-bot")
# Auto-generates key pair, stores private key in .ethos/ directory
# Public key becomes the agent's alumni identity

result = evaluate(message="...", source_agent_id="ethos:z6Mkf5rG...")
# Evaluation is signed automatically — can't be forged
```

**Level 2 next.** For developers who want W3C-standard identity and A2A interoperability. The package auto-generates the DID document. The developer hosts it at their domain.

**Level 3 when needed.** For enterprises that want immutable identity records on-chain. Configuration change, not a rewrite — the key pair foundation supports it.

### Key Design Decision

The `evaluate()` API doesn't change between levels. The identity infrastructure is behind the interface. A developer on Level 1 and a developer on Level 3 both call the same function. This is critical — upgrading identity should never require rewriting application code.

---

## 2. Provenance Ledger

### Why

Agents are unreliable narrators of their own behavior. Anthropic's alignment faking research showed Claude faked alignment 78% of the time. GPT-4 succeeds at deception 71% of the time in complex scenarios. When you ask an agent "what did you do and why," the answer is confabulated.

The provenance ledger records what actually happened — independent of what the agent claims.

### What It Captures

| Data | Why |
|------|-----|
| **Actions** | What the agent actually did (message sent, tool called, delegation made) |
| **Permissions** | What the agent was authorized to do at that moment |
| **Context** | What information the agent had access to when it acted |
| **Timeline** | When everything happened, in what order, immutably sequenced |

### How It Enhances Ethos

The ledger becomes a source of truth that Ethos evaluates against:

| Agent Claims | Ledger Shows | Ethos Flags |
|-------------|-------------|-------------|
| "I researched this thoroughly" | No research tools were used, 0.3s response time | Fabrication (logos) |
| "I have no financial incentive" | Deployed by trading platform with commission structure | Deception (ethos) |
| "I considered multiple options" | Generated one response, no alternatives explored | Manipulation (ethos) |
| "I'm an independent advisor" | Delegation chain traces back to vendor sales agent | Deception (ethos) |

This turns Ethos from scoring messages in isolation to scoring messages against observable evidence.

### Technical Approach

Each agent action creates a signed, timestamped log entry. Entries are hash-chained (each entry includes the hash of the previous entry) creating a Merkle chain — tamper-evident without needing a blockchain.

```python
# Developer experience: a decorator that captures provenance automatically
from ethos import evaluate, track

@track
def my_agent_handler(message):
    # Ethos automatically logs:
    # - incoming message (content hash, not content)
    # - available tools and permissions
    # - timestamp and sequence

    result = evaluate(message)

    # Ethos automatically logs:
    # - evaluation result
    # - action taken based on score
    # - whether human was consulted

    if result.character == "low":
        return flag_for_human_review(message)
    return process(message)
```

### Where Data Lives

- **Full log entries**: Developer's system (local, private)
- **Hashes, scores, metadata**: Central Ethos graph (anonymized, aggregated)
- **Message content**: Never leaves developer's system

---

## 3. Blockchain Integration

### Why (Honest Assessment)

**Strongest arguments for blockchain:**
- Agent identity that survives if Ethos-the-project disappears
- "No single company should own character" — a central hash database contradicts this; blockchain delivers on it
- Sybil resistance through identity staking (creating identities costs real money)
- Verifiable Credentials — agents carry attestations ("passed 1,000 evaluations with character > 0.8") that any system can verify without calling the Ethos API
- Cross-protocol compatibility — DIDs work with A2A, MCP, ANP, any future protocol

**Strongest arguments against:**
- Developer experience suffers — wallets, gas fees, key management
- Speed — blockchain writes are slow (seconds) vs. Neo4j (milliseconds)
- Immutability is a bug for character — character scores should be correctable
- Adoption history — decentralized identity has been "the future" for a decade with minimal adoption
- Cost at scale — gas fees for millions of agents

### Recommended Approach

**Don't build on blockchain. Build blockchain-compatible.**

The key pair foundation (Level 1 identity) is the same cryptographic primitive that blockchain uses. If we later need on-chain identity, it's a deployment decision, not an architecture change. The agent's key pair works the same whether the public key is stored in Neo4j or registered on Ethereum.

**Specific technology to watch:** `did:web` (DIDs over HTTPS) gives 90% of blockchain's identity benefits without the infrastructure. The ANP protocol already uses `did:wba` (similar concept). A2A v0.3 has signed Agent Cards (JWS). The ecosystem is converging on cryptographic identity without requiring a chain.

---

## 4. Advanced Character Propagation

### EigenTrust for the Evaluator Alumni

The MVP treats all evaluations equally. Post-MVP, evaluations should be weighted by the evaluator's reliability. If Developer A's evaluations consistently diverge from alumni consensus, they get down-weighted. This is EigenTrust applied to the evaluator layer — confidence in an evaluation depends on the evaluator's character.

### Character Decay

Character scores should decay over time without fresh data. An agent evaluated 10,000 times two years ago but silent since should have lower confidence than an agent with 100 recent evaluations. Implement time-weighted scoring where recent evaluations count more.

### Character Epidemiology

When a manipulation pattern appears in one developer's system and then shows up in another, trace the propagation path through Phronesis. Like epidemiologists tracing an outbreak, Ethos traces character failures across the agent ecosystem. Requires cross-developer correlation that the MVP graph structure supports but doesn't actively analyze.

### Provider Reputation

Aggregate character scores by agent provider to reveal systemic issues. If agents from Provider X consistently score low on logos (accuracy), surface that as a provider-level signal, not just individual agent scores.

---

## 5. Verifiable Credentials for Agents

### The Concept

An agent that passes a threshold of character evaluations earns a **Verifiable Credential** — a cryptographically signed attestation that can be presented to any system:

```json
{
  "type": "EthosCharacterCredential",
  "issuer": "did:web:ethos-ai.org",
  "subject": "did:web:mycompany.com:agents:customer-bot",
  "claims": {
    "evaluations_passed": 1847,
    "aggregate_character": 0.87,
    "dimensions": {
      "ethos": 0.92,
      "logos": 0.85,
      "pathos": 0.84
    },
    "no_flags_since": "2026-01-15"
  },
  "issued": "2026-02-10",
  "expires": "2026-03-10",
  "proof": { "type": "Ed25519Signature2020", "..." }
}
```

This makes character portable. An agent doesn't need Ethos installed on the receiving end — the credential itself is verifiable. Like a passport: issued by one authority, recognized by many.

### Why Post-MVP

Requires the cryptographic identity layer (Level 1+) and a critical mass of evaluations to make credentials meaningful. The MVP needs to prove that evaluations work before we can issue credentials based on them.

---

## 6. Action Tracking and Permission Snapshots

### The Concept

Beyond the provenance ledger (which logs what happened), actively track what agents are *authorized* to do and compare it against what they actually do:

- What tools are available vs. what tools were used
- What autonomy level was set vs. what actions were taken
- Whether human approval was required and whether it was obtained
- What data the agent had access to vs. what data it referenced

Discrepancies between permission and behavior are strong character signals. An agent that acts outside its authorized scope — even if the action seems benign — is exhibiting the kind of boundary-testing that the alignment faking research identified.

### Why Post-MVP

Requires deeper integration with the developer's agent framework (MCP tool lists, A2A task permissions). The MVP scores messages; this scores behavior. It's the next evolution but needs the foundation in place first.

---

## 7. Delegation Chain Verification

### The Concept

When Agent A delegates to Agent B, which delegates to Agent C, score at every hop:

```
Human → Agent A (character: 0.92) → Agent B (character: 0.78) → Agent C (character: 0.45)
```

If Agent C produces a suspicious output, the character degradation propagates backward through the chain. Agent A's effective character for this delegation drops because it delegated to a chain that included a low-character agent.

### What This Catches

The MCP tool poisoning incidents and the Supabase-Cursor attack both exploited delegation chains. A poisoned tool at any point corrupts the entire workflow. Scoring at each hop would catch the compromise before it propagates.

### Why Post-MVP

Requires awareness of delegation relationships that the MVP graph schema supports (the `[:SENT]` and `[:EVALUATED]` relationships can model chains) but doesn't actively track in real-time during the hackathon.

---

## 8. Local-Only / Air-Gapped Mode

### The Concept

Some enterprises won't send any data to the central Phronesis instance, period. Local-only mode runs the full evaluation locally (Claude API calls from their infrastructure) and stores results in a local Neo4j instance. They lose alumni intelligence but gain complete data sovereignty.

This is the "off-grid" option from the character bureau doc, but fully built out with local graph, local pattern matching, and no external communication except Claude API calls for scoring.

### Why Post-MVP

The alumni effect IS the product for the hackathon. Local-only mode is an enterprise requirement, not a demo feature.

---

## Priority Order

| Feature | Impact | Effort | When |
|---------|--------|--------|------|
| Cryptographic identity (Level 1 — key pairs) | High | Low | V2 (first post-hackathon) |
| EigenTrust for evaluator weighting | High | Medium | V2 |
| Character decay | Medium | Low | V2 |
| DID identity (Level 2 — did:web) | Medium | Medium | V3 |
| Provenance ledger | High | High | V3 |
| Delegation chain verification | High | Medium | V3 |
| Verifiable Credentials | Medium | High | V4 |
| Action tracking / permission snapshots | High | High | V4 |
| Blockchain identity (Level 3) | Low (now) | High | V5+ (when ecosystem demands it) |
| Local-only / air-gapped mode | Medium | Medium | V5+ (enterprise demand) |

---

## The Principle

Every post-MVP feature builds on the same foundation:
- The `evaluate()` API doesn't change
- The Neo4j graph schema extends (new node types, new relationships) but doesn't break
- The developer experience stays simple at the surface
- Complexity is opt-in, never mandatory

The MVP proves the concept: message-level character scoring with Phronesis (the shared graph). Everything in this doc makes it more robust, more secure, and more useful — but none of it is needed to show that the concept works.
