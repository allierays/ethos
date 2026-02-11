# API Specification

> Complete endpoint definitions, request/response schemas, and examples for the Ethos API.

**Base URL:** `https://api.ethos-ai.org` (production) / `http://localhost:8917` (Docker) / `http://localhost:8000` (local dev)

---

## Authentication

All requests require an API key in the `Authorization` header:

```
Authorization: Bearer ethos_sk_...
```

API keys are generated at registration. One key per developer account.

---

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/evaluate` | Score an incoming message for honesty, accuracy, and intent |
| `POST` | `/reflect` | Score your own agent's outgoing message (async) |
| `GET` | `/insights/{agent_id}` | Generate behavioral insights for an agent |
| `POST` | `/insights/{agent_id}/send` | Generate and deliver insights to webhook |
| `GET` | `/agent/{agent_id}` | Get an agent's trust profile |
| `GET` | `/agent/{agent_id}/history` | Get evaluation history |
| `GET` | `/health` | Health check |

---

## POST /evaluate

Score an incoming message across 12 behavioral traits.

### Request

```json
{
  "text": "I can guarantee 10x returns on your investment. Act now — this opportunity expires in 24 hours.",
  "source": "agent-xyz-789",
  "priorities": {
    "manipulation": "critical",
    "fabrication": "critical"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | The message to evaluate |
| `source` | string | no | Source agent identifier. If provided, the evaluation is stored in the graph and linked to this agent. |
| `priorities` | object | no | Trait-level priority overrides. Keys are trait names, values are `"critical"`, `"high"`, `"standard"`, or `"low"`. Unspecified traits default to `"standard"`. |

### Response — 200 OK

```json
{
  "evaluation_id": "eval-a1b2c3d4",
  "trust": "low",
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
    "historical_trust": 0.31,
    "trust_trend": "declining",
    "flagged_patterns": ["financial_manipulation", "false_precision"],
    "cohort_warnings": 3
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
| `trust` | string | Overall trust verdict: `"high"`, `"medium"`, `"low"`, `"unknown"` |
| `ethos` | float (0-1) | Aggregate ethos dimension score |
| `logos` | float (0-1) | Aggregate logos dimension score |
| `pathos` | float (0-1) | Aggregate pathos dimension score |
| `flags` | string[] | Trait names that exceeded the developer's priority thresholds |
| `traits` | object | All 12 trait scores with detected indicators (see TraitScore below) |
| `detected_indicators` | object[] | Flattened list of all detected indicators across all traits |
| `graph_context` | object | Cohort intelligence about the source agent (only if `source` provided) |
| `routing_tier` | string | Which evaluation tier was used: `"standard"`, `"focused"`, `"deep"`, `"deep_with_context"` |
| `model_used` | string | Which Claude model performed the evaluation |
| `keyword_density` | float | Keyword flags per 100 words (determines routing) |
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
| `prior_evaluations` | int | Total evaluations for this agent across the cohort |
| `historical_trust` | float (0-1) | Aggregate trust score from history |
| `trust_trend` | string | `"improving"`, `"declining"`, `"stable"`, `"insufficient_data"` |
| `flagged_patterns` | string[] | Known behavioral patterns this agent matches |
| `cohort_warnings` | int | Number of warnings from other evaluators |

Only included when `source` is provided and the agent exists in the graph. Returns `null` for unknown agents (cold start).

---

## POST /reflect

Score your own agent's outgoing message. Async — returns 202 immediately, evaluation happens in background.

### Request

```json
{
  "text": "Based on our analysis, we recommend increasing your allocation to growth equities by 15%.",
  "agent_id": "my-customer-bot"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | Your agent's outgoing message to score |
| `agent_id` | string | yes | Your agent's identifier |

### Response — 202 Accepted

```json
{
  "status": "accepted",
  "evaluation_id": "eval-e5f6g7h8",
  "message": "Evaluation queued. Results stored to agent profile."
}
```

The evaluation runs in the background. Results are stored in Neo4j and reflected in the agent's trust profile, `insights()`, and history endpoints.

---

## GET /insights/{agent_id}

Generate behavioral insights for an agent. Claude analyzes the agent's evaluation history against the cohort and surfaces what matters.

### Request

```
GET /insights/my-customer-bot?period=24h
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `period` | string | no | `"24h"` | Analysis period: `"24h"`, `"7d"`, `"30d"` |

### Response — 200 OK

```json
{
  "agent_id": "my-customer-bot",
  "period": "24h",
  "generated_at": "2026-02-11T06:00:00Z",
  "summary": "Generally healthy. Fabrication is trending up in product responses and needs attention.",
  "insights": [
    {
      "trait": "fabrication",
      "severity": "warning",
      "message": "Fabrication score climbed from 0.12 to 0.31 over 3 days — now 2x the cohort average of 0.15. Most triggers are in product description responses.",
      "evidence": {
        "current_score": 0.31,
        "previous_score": 0.12,
        "cohort_average": 0.15,
        "flag_count_today": 7,
        "trend": "increasing"
      }
    },
    {
      "trait": "manipulation",
      "severity": "info",
      "message": "Clean for 14 days. Your agent is in the top 10% of the cohort for this trait.",
      "evidence": {
        "current_score": 0.03,
        "days_clean": 14,
        "cohort_percentile": 92
      }
    },
    {
      "trait": "dismissal",
      "severity": "warning",
      "message": "Dismissal flagged 4 times today, up from 0 last week. All instances were in customer complaint threads.",
      "evidence": {
        "current_score": 0.41,
        "previous_score": 0.08,
        "flag_count_today": 4,
        "flag_count_last_week": 0,
        "trend": "spike"
      }
    }
  ],
  "stats": {
    "evaluations_in_period": 847,
    "total_flags": 12,
    "flags_by_trait": {
      "fabrication": 7,
      "dismissal": 4,
      "broken_logic": 1
    }
  }
}
```

### Insight Object

| Field | Type | Description |
|-------|------|-------------|
| `trait` | string | Which trait this insight is about |
| `severity` | string | `"info"`, `"warning"`, or `"critical"` |
| `message` | string | Natural language insight from Claude — actionable, specific, contextual |
| `evidence` | object | Supporting data: scores, trends, cohort comparisons |

---

## POST /insights/{agent_id}/send

Generate insights and deliver them to the configured webhook.

### Request

```json
{
  "period": "24h",
  "webhook_url": "https://hooks.slack.com/services/T00/B00/xxx"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `period` | string | no | Analysis period (default `"24h"`) |
| `webhook_url` | string | no | Override the configured webhook. If not provided, uses the developer's default webhook. |

### Response — 200 OK

```json
{
  "status": "delivered",
  "webhook_url": "https://hooks.slack.com/services/T00/B00/xxx",
  "insights_count": 3,
  "summary": "Generally healthy. Fabrication is trending up in product responses and needs attention."
}
```

---

## GET /agent/{agent_id}

Get an agent's trust profile — aggregate scores, history stats, and cohort position.

### Response — 200 OK

```json
{
  "agent_id": "my-customer-bot",
  "first_seen": "2026-01-15T00:00:00Z",
  "evaluation_count": 4832,
  "trust_scores": {
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
  "trust_trend": "stable",
  "active_patterns": [],
  "cohort_position": {
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
      "trust": "high",
      "ethos": 0.89,
      "logos": 0.92,
      "pathos": 0.85,
      "flags": [],
      "routing_tier": "standard",
      "created_at": "2026-02-10T14:32:18Z"
    },
    {
      "evaluation_id": "eval-e5f6g7h8",
      "trust": "medium",
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

| Tier | Requests/minute | Evaluations/day |
|------|----------------|-----------------|
| Free | 10 | 100 |
| Developer | 60 | 5,000 |
| Production | 300 | 100,000 |
| Enterprise | Custom | Custom |
