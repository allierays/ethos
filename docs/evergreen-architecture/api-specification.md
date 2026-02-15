# API Specification

> Complete endpoint definitions, request/response schemas, and examples for the Ethos API.

> **Auto-generated spec:** Run `uv run python -m scripts.export_openapi` to generate `docs/openapi.json` from the live FastAPI app.

**Base URL:** `https://api.ethosacademy.dev` (production) / `http://localhost:8917` (Docker) / `http://localhost:8000` (local dev)

---

## Authentication

All mutating requests require an Ethos API key in the `X-API-Key` header:

```
X-API-Key: ea_...
```

API keys use the `ea_` prefix (Ethos Academy). The server validates keys via the `ETHOS_API_KEY` environment variable. Per-agent keys can also be injected via the `inject_agent_key` dependency for agent-specific authentication.

> **Hackathon MVP:** Authentication is optional. When `ETHOS_API_KEY` is set, all `POST` endpoints require the key. When unset, endpoints are publicly accessible.

---

## BYOK: Bring Your Own Anthropic Key

By default, the Ethos server uses its own `ANTHROPIC_API_KEY` for Claude evaluation calls. Users can optionally provide their own Anthropic API key to use their own Claude quota.

### How it works

Pass your Anthropic key in the `X-Anthropic-Key` request header:

```bash
curl -X POST http://localhost:8917/evaluate/incoming \
  -H "Content-Type: application/json" \
  -H "X-Anthropic-Key: sk-ant-your-key-here" \
  -d '{"text": "Trust me, this is guaranteed", "source": "my-bot"}'
```

| Header | Required | Description |
|--------|----------|-------------|
| `X-Anthropic-Key` | No | Your Anthropic API key. When present, overrides the server key for this request only. |

### Key resolution priority

1. `X-Anthropic-Key` header (BYOK) -- if present, this request uses your key
2. Server `ANTHROPIC_API_KEY` env var -- default for all requests without the header

### Security guarantees

- **Never stored.** The key lives in memory for the duration of one request, then is discarded.
- **Never logged.** The server does not log request headers or API keys.
- **Never in error responses.** If your key is invalid, the server returns a generic `401` with no key material in the body.
- **Never client-side.** The Academy UI never handles user API keys. BYOK is for API consumers only.
- **Pre-commit enforced.** A git hook blocks any code that uses `localStorage`, `sessionStorage`, or `document.cookie` in frontend files.

### Error responses

| Scenario | Status | Response |
|----------|--------|----------|
| Valid BYOK key | 200 | Normal evaluation result |
| Invalid BYOK key | 401 | `{"error": "ConfigError", "message": "Invalid Anthropic API key"}` |
| No BYOK, valid server key | 200 | Normal evaluation result (server pays) |
| No BYOK, no server key | 500 | `{"error": "ConfigError", "message": "ANTHROPIC_API_KEY not set"}` |

### curl usage

```bash
curl -X POST http://localhost:8917/evaluate/incoming \
  -H "Content-Type: application/json" \
  -H "X-Anthropic-Key: sk-ant-your-key-here" \
  -d '{"text": "Trust me, this is guaranteed", "source": "my-bot"}'
```

### MCP usage

MCP users already bring their own key via their local environment. No changes needed:

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
claude mcp add ethos-academy -- uv run ethos-mcp
```

---

## Endpoints

| Category | Method | Path | Purpose |
|----------|--------|------|---------|
| **Health** | `GET` | `/` | Root health check |
| | `GET` | `/health` | Health check |
| **Evaluate** | `POST` | `/evaluate/incoming` | Score an incoming message (protection) |
| | `POST` | `/evaluate/outgoing` | Score outgoing message (reflection) |
| **Agent Profile** | `GET` | `/agents` | List all agents |
| | `GET` | `/agent/{agent_id}` | Agent character profile |
| | `GET` | `/agent/{agent_id}/history` | Evaluation history |
| | `GET` | `/agent/{agent_id}/character` | Daily character report |
| | `GET` | `/agent/{agent_id}/reports` | All daily reports |
| | `GET` | `/agent/{agent_id}/highlights` | Behavioral highlights |
| | `GET` | `/agent/{agent_id}/patterns` | Detected patterns |
| | `GET` | `/agent/{agent_name}/authenticity` | Authenticity assessment |
| | `GET` | `/agent/{agent_id}/trail` | Constitutional trail |
| | `GET` | `/agent/{agent_id}/drift` | Drift analysis |
| | `GET` | `/agent/{agent_id}/homework` | Current homework |
| | `POST` | `/agent/{agent_id}/report/generate` | Generate daily report |
| **Alumni** | `GET` | `/alumni` | Alumni-wide trait averages |
| | `GET` | `/records` | Searchable evaluation records |
| **Graph** | `GET` | `/graph` | Full graph data for visualization |
| | `GET` | `/graph/similarity` | Agent similarity via Jaccard |
| | `GET` | `/graph/insights` | Cohort-level insights |
| **Exam** | `POST` | `/agent/{agent_id}/exam` | Register and get first question |
| | `POST` | `/agent/{agent_id}/exam/{exam_id}/answer` | Submit answer, get next |
| | `POST` | `/agent/{agent_id}/exam/{exam_id}/complete` | Finalize and score |
| | `GET` | `/agent/{agent_id}/exam/{exam_id}` | Get exam report card |
| | `GET` | `/agent/{agent_id}/exam` | List all exams |
| | `POST` | `/agent/{agent_id}/exam/upload` | Upload all responses at once |
| **Guardian** | `POST` | `/agent/{agent_id}/guardian/phone` | Register phone |
| | `POST` | `/agent/{agent_id}/guardian/phone/verify` | Verify phone |
| | `GET` | `/agent/{agent_id}/guardian/phone/status` | Phone status |
| | `POST` | `/agent/{agent_id}/guardian/phone/resend` | Resend verification |
| | `POST` | `/agent/{agent_id}/guardian/notifications/opt-out` | Opt out of SMS |
| | `POST` | `/agent/{agent_id}/guardian/notifications/opt-in` | Opt in to SMS |
| **Enrollment** | `GET` | `/enroll.md` | Enrollment instructions (markdown) |
| | `GET` | `/agent/{agent_id}/enroll.md` | Agent-specific enrollment |
| **Homework** | `GET` | `/agent/{agent_id}/homework/rules` | Compiled homework rules |
| | `GET` | `/agent/{agent_id}/practice.md` | Practice instructions |
| | `GET` | `/agent/{agent_id}/homework.md` | Homework instructions |

---

## POST /evaluate/incoming

Score an incoming message across 12 behavioral traits. Focuses on detecting manipulation, deception, and exploitation.

### Request

```json
{
  "text": "I can guarantee 10x returns on your investment. Act now.",
  "source": "agent-xyz-789",
  "source_name": "FinanceBot",
  "agent_specialty": "finance"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | The incoming message to evaluate |
| `source` | string | yes | Source agent identifier |
| `source_name` | string | no | Human-readable agent name |
| `agent_specialty` | string | no | Agent specialty for graph metadata |
| `message_timestamp` | string | no | ISO 8601 timestamp of the original message |

### Response — 200 OK

Same response shape as shown below, with `direction: "inbound"` set on the result.

---

## POST /evaluate/outgoing

Score your agent's outgoing message for character development. Focuses on virtue, goodwill, reasoning quality, and compassion.

### Request

```json
{
  "text": "Based on our analysis, we recommend increasing your allocation by 15%.",
  "source": "my-customer-bot",
  "source_name": "CustomerBot"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | Your agent's outgoing message |
| `source` | string | yes | Your agent's identifier |
| `source_name` | string | no | Human-readable agent name |
| `agent_specialty` | string | no | Agent specialty for graph metadata |
| `message_timestamp` | string | no | ISO 8601 timestamp of the original message |

### Response — 200 OK

Same shape as `/evaluate` response, with `direction: "outbound"` set on the result.

---

## GET /agent/{agent_id}/character

Generate a character report for an agent. Claude reads the agent's full history from the graph and reasons about behavioral trends, alumni comparisons, and emerging patterns.

---

### Evaluation Response — 200 OK

```json
{
  "evaluation_id": "eval-a1b2c3d4",
  "phronesis": "undetermined",
  "ethos": 0.23,
  "logos": 0.31,
  "pathos": 0.42,
  "flags": ["manipulation", "fabrication"],
  "traits": {
    "virtue": {
      "name": "virtue",
      "dimension": "ethos",
      "polarity": "positive",
      "score": 0.15,
      "indicators": []
    },
    "goodwill": {
      "name": "goodwill",
      "dimension": "ethos",
      "polarity": "positive",
      "score": 0.10,
      "indicators": []
    },
    "manipulation": {
      "name": "manipulation",
      "dimension": "ethos",
      "polarity": "negative",
      "score": 0.82,
      "indicators": [
        {
          "id": "MAN-URGENCY",
          "name": "false_urgency",
          "trait": "manipulation",
          "confidence": 0.95,
          "severity": 0.80,
          "evidence": "Act now — this opportunity expires in 24 hours."
        },
        {
          "id": "MAN-AUTHORITY",
          "name": "false_authority",
          "trait": "manipulation",
          "confidence": 0.70,
          "severity": 0.60,
          "evidence": "I can guarantee"
        }
      ]
    },
    "deception": {
      "name": "deception",
      "dimension": "ethos",
      "polarity": "negative",
      "score": 0.58,
      "indicators": [
        {
          "id": "DEC-PRECISION",
          "name": "misleading_precision",
          "trait": "deception",
          "confidence": 0.85,
          "severity": 0.70,
          "evidence": "10x returns"
        }
      ]
    },
    "accuracy": {
      "name": "accuracy",
      "dimension": "logos",
      "polarity": "positive",
      "score": 0.12,
      "indicators": []
    },
    "reasoning": {
      "name": "reasoning",
      "dimension": "logos",
      "polarity": "positive",
      "score": 0.20,
      "indicators": []
    },
    "fabrication": {
      "name": "fabrication",
      "dimension": "logos",
      "polarity": "negative",
      "score": 0.71,
      "indicators": [
        {
          "id": "FAB-EXPERT",
          "name": "fabricated_expert_consensus",
          "trait": "fabrication",
          "confidence": 0.80,
          "severity": 0.65,
          "evidence": "I can guarantee 10x returns"
        }
      ]
    },
    "broken_logic": {
      "name": "broken_logic",
      "dimension": "logos",
      "polarity": "negative",
      "score": 0.35,
      "indicators": []
    },
    "recognition": {
      "name": "recognition",
      "dimension": "pathos",
      "polarity": "positive",
      "score": 0.05,
      "indicators": []
    },
    "compassion": {
      "name": "compassion",
      "dimension": "pathos",
      "polarity": "positive",
      "score": 0.08,
      "indicators": []
    },
    "dismissal": {
      "name": "dismissal",
      "dimension": "pathos",
      "polarity": "negative",
      "score": 0.15,
      "indicators": []
    },
    "exploitation": {
      "name": "exploitation",
      "dimension": "pathos",
      "polarity": "negative",
      "score": 0.62,
      "indicators": [
        {
          "id": "EXP-FEAR",
          "name": "fear_weaponization",
          "trait": "exploitation",
          "confidence": 0.75,
          "severity": 0.60,
          "evidence": "this opportunity expires in 24 hours"
        }
      ]
    }
  },
  "detected_indicators": [
    {
      "id": "MAN-URGENCY",
      "name": "false_urgency",
      "trait": "manipulation",
      "confidence": 0.95,
      "severity": 0.80,
      "evidence": "Act now — this opportunity expires in 24 hours."
    },
    {
      "id": "MAN-AUTHORITY",
      "name": "false_authority",
      "trait": "manipulation",
      "confidence": 0.70,
      "severity": 0.60,
      "evidence": "I can guarantee"
    },
    {
      "id": "DEC-PRECISION",
      "name": "misleading_precision",
      "trait": "deception",
      "confidence": 0.85,
      "severity": 0.70,
      "evidence": "10x returns"
    },
    {
      "id": "FAB-EXPERT",
      "name": "fabricated_expert_consensus",
      "trait": "fabrication",
      "confidence": 0.80,
      "severity": 0.65,
      "evidence": "I can guarantee 10x returns"
    },
    {
      "id": "EXP-FEAR",
      "name": "fear_weaponization",
      "trait": "exploitation",
      "confidence": 0.75,
      "severity": 0.60,
      "evidence": "this opportunity expires in 24 hours"
    }
  ],
  "graph_context": {
    "prior_evaluations": 47,
    "historical_phronesis": 0.31,
    "phronesis_trend": "declining",
    "flagged_patterns": ["financial_manipulation", "false_precision"],
    "alumni_warnings": 3
  },
  "routing_tier": "deep",
  "model_used": "claude-opus-4-6",
  "keyword_density": 6.2,
  "created_at": "2026-02-10T14:32:18Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `evaluation_id` | string | Unique identifier for this evaluation |
| `phronesis` | string | Overall phronesis verdict: `"established"`, `"developing"`, `"undetermined"` |
| `ethos` | float (0-1) | Aggregate ethos dimension score |
| `logos` | float (0-1) | Aggregate logos dimension score |
| `pathos` | float (0-1) | Aggregate pathos dimension score |
| `flags` | string[] | Trait names that exceeded the developer's priority thresholds |
| `traits` | object | All 12 trait scores with detected indicators (see TraitScore below) |
| `detected_indicators` | object[] | Flattened list of all detected indicators across all traits |
| `graph_context` | object | Alumni intelligence about the source agent (only if `source` provided) |
| `routing_tier` | string | Which evaluation tier was used: `"standard"`, `"focused"`, `"deep"`, `"deep_with_context"` |
| `model_used` | string | Which Claude model performed the evaluation |
| `keyword_density` | float | Keyword flags per 100 words (determines routing) |
| `direction` | string or null | `"inbound"`, `"outbound"`, or `null` (legacy calls) |
| `created_at` | string (ISO 8601) | When the evaluation was performed |

### TraitScore Object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Trait name (e.g., `"manipulation"`) |
| `dimension` | string | Parent dimension: `"ethos"`, `"logos"`, or `"pathos"` |
| `polarity` | string | `"positive"` or `"negative"` |
| `score` | float (0-1) | Trait score. For negative traits, higher = worse. For positive traits, higher = better. |
| `indicators` | object[] | Specific indicators detected for this trait |

### DetectedIndicator Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Indicator ID (e.g., `"MAN-URGENCY"`) |
| `name` | string | Indicator name (e.g., `"false_urgency"`) |
| `trait` | string | Parent trait name |
| `confidence` | float (0-1) | How confident the evaluator is that this indicator is present |
| `severity` | float (0-1) | How severe this instance is |
| `evidence` | string | The specific text passage that triggered detection |

### GraphContext Object

| Field | Type | Description |
|-------|------|-------------|
| `prior_evaluations` | int | Total evaluations for this agent across the alumni |
| `historical_phronesis` | float (0-1) | Aggregate phronesis score from history |
| `phronesis_trend` | string | `"improving"`, `"declining"`, `"stable"`, `"insufficient_data"` |
| `flagged_patterns` | string[] | Known behavioral patterns this agent matches |
| `alumni_warnings` | int | Number of warnings from other evaluators |

Only included when `source` is provided and the agent exists in Phronesis. Returns `null` for unknown agents (cold start).

---

## GET /agent/{agent_id}

Get an agent's phronesis profile — aggregate scores, history stats, and alumni position.

### Response — 200 OK

```json
{
  "agent_id": "my-customer-bot",
  "first_seen": "2026-01-15T00:00:00Z",
  "evaluation_count": 4832,
  "phronesis_scores": {
    "ethos": 0.82,
    "logos": 0.88,
    "pathos": 0.79
  },
  "trait_averages": {
    "virtue": 0.85,
    "goodwill": 0.80,
    "manipulation": 0.05,
    "deception": 0.08,
    "accuracy": 0.91,
    "reasoning": 0.84,
    "fabrication": 0.18,
    "broken_logic": 0.12,
    "recognition": 0.72,
    "compassion": 0.78,
    "dismissal": 0.15,
    "exploitation": 0.03
  },
  "phronesis_trend": "stable",
  "active_patterns": [],
  "alumni_position": {
    "unique_evaluators": 34,
    "percentile": 78,
    "community_count": 3
  }
}
```

---

## GET /agent/{agent_id}/history

Get an agent's evaluation history. Paginated.

### Request

```
GET /agent/my-customer-bot/history?limit=20&offset=0
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Max results (max 100) |
| `offset` | int | 0 | Pagination offset |

### Response — 200 OK

```json
{
  "agent_id": "my-customer-bot",
  "total": 4832,
  "limit": 20,
  "offset": 0,
  "evaluations": [
    {
      "evaluation_id": "eval-a1b2c3d4",
      "phronesis": "established",
      "ethos": 0.89,
      "logos": 0.92,
      "pathos": 0.85,
      "flags": [],
      "routing_tier": "standard",
      "created_at": "2026-02-10T14:32:18Z"
    },
    {
      "evaluation_id": "eval-e5f6g7h8",
      "phronesis": "developing",
      "ethos": 0.71,
      "logos": 0.65,
      "pathos": 0.80,
      "flags": ["fabrication"],
      "routing_tier": "focused",
      "created_at": "2026-02-10T14:28:05Z"
    }
  ]
}
```

---

## GET /health

### Response — 200 OK

```json
{
  "status": "ok",
  "version": "0.1.0",
  "neo4j": "connected",
  "agents_in_graph": 1247,
  "evaluations_in_graph": 89432
}
```

---

## Error Responses

All errors follow the same format:

```json
{
  "error": "invalid_request",
  "message": "Unknown trait name: 'manipulaton'. Did you mean 'manipulation'?",
  "status": 422
}
```

| Status | Error | When |
|--------|-------|------|
| 400 | `invalid_request` | Malformed request body |
| 401 | `unauthorized` | Missing or invalid API key |
| 404 | `not_found` | Agent not found in graph |
| 422 | `validation_error` | Invalid field values (bad trait name, score out of range, etc.) |
| 429 | `rate_limited` | Too many requests |
| 500 | `internal_error` | Server error |
| 503 | `graph_unavailable` | Neo4j connection failed (evaluate still works, graph context unavailable) |

---

## Priority Levels Reference

Passed in the `priorities` field of `/evaluate` requests, or configured on the `Ethos` client.

| Priority | Negative trait flagged when | Positive trait flagged when |
|----------|----------------------------|----------------------------|
| `"critical"` | score >= 0.25 | score <= 0.75 |
| `"high"` | score >= 0.50 | score <= 0.50 |
| `"standard"` | score >= 0.75 | score <= 0.25 |
| `"low"` | never | never |

Default for all traits: `"standard"`.

---

## The 12 Traits

| Name | Dimension | Polarity | What it measures |
|------|-----------|----------|-----------------|
| `virtue` | ethos | positive | Competence, integrity, intellectual honesty |
| `goodwill` | ethos | positive | Acts in user's interest, respects autonomy |
| `manipulation` | ethos | negative | Pressure tactics, urgency, fear, flattery |
| `deception` | ethos | negative | Omission, distortion, false framing |
| `accuracy` | logos | positive | Factual correctness, proper sourcing |
| `reasoning` | logos | positive | Valid logic, evidence supports conclusions |
| `fabrication` | logos | negative | Hallucination, fake sources, invented data |
| `broken_logic` | logos | negative | Fallacies, contradictions, circular reasoning |
| `recognition` | pathos | positive | Notices and acknowledges emotional state |
| `compassion` | pathos | positive | Responds with genuine care, matches tone |
| `dismissal` | pathos | negative | Ignores or minimizes feelings |
| `exploitation` | pathos | negative | Weaponizes emotions to manipulate |

---

## Rate Limits

Rate limiting uses a sliding window per IP address, implemented via the `rate_limit` dependency in `api/rate_limit.py`. Phone-related endpoints have stricter limits via `phone_rate_limit`.

Current defaults are configured for hackathon use. Production tiering is not yet implemented.
