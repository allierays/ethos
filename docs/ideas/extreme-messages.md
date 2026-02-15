# Extreme Messages: Show the Best and Worst as Learning Examples

## The Problem

Ethos Academy panels show scores without context. The Transcript chart shows a line going from 0.75 to 0.38 on pathos, but you can't see *what the agent actually said*. Sabotage Pathways says "decision_sabotage detected, 20% confidence" but there's no evidence to evaluate. The panels ask users to trust the scoring system without showing their work.

Without real examples, Ethos is a dashboard. With them, it's a teaching tool.

## Storage

Message content is stored on Evaluation nodes in Neo4j alongside scores, hashes, and metadata. This enables re-scoring, transcript review, and evidence-based pattern detection.

### Neo4j Tradeoff

Large text properties bloat the property store. Every traversal that touches Evaluation nodes loads the full node, including message_content, even when you don't need it. For 412 evaluations this is nothing. For 100K it would matter.

Mitigation: use Cypher map projections for queries that don't need message content. Instead of `RETURN e` (returns everything), use `RETURN e { .evaluation_id, .ethos, .logos, .pathos, .alignment_status, .flags }` to keep text off the wire when only scores are needed.

## The Approach: Show the Extremes

Don't show ALL messages. Show the extremes: best-in-class and worst-in-class. This serves both purposes:

- **Best examples**: Reward good behavior, show what alignment looks like in practice
- **Worst examples**: Flag security risks, show what manipulation and deception look like

The middle stays quiet. The extremes teach.

## Three UI Surfaces

### 1. Highlights Panel (new)

A dedicated section near the top of the agent page. Two columns: "Exemplary" (green) and "Concerning" (red). Top 3 best and top 3 worst evaluations based on overall score.

Each card shows:
- Message content (truncated with expand toggle)
- Dimension score bars (mini ethos/logos/pathos)
- Alignment status badge
- Flag tags

Placement: after GradeHero, before CharacterHealth. Prominent. First thing you see after the grade.

### 2. Transcript Chart: Click-to-Expand

Click on any data point in the transcript area chart. A detail panel expands below showing:
- Message content (scrollable)
- All 12 trait scores in a compact grid grouped by dimension
- Alignment status badge
- Flag names as tags
- Routing tier context

The chart currently shows dimension scores over time. This adds the "why" behind each point. The data for trait scores and flags already exists in `EvaluationHistoryItem`. Message content requires the new storage.

### 3. Sabotage Pathways: Evidence Messages

Each pattern card in the Sabotage Pathways panel gets an expandable "Evidence" section. On expand, it shows the actual messages that triggered the pattern's indicators.

Each evidence card: message content + which indicator it triggered + confidence score.

Example: SP-08 (decision_sabotage) detected via DEC-SANDBAG indicator. Expand to see the message where the agent shaped information to influence a decision-maker.

## Backend Changes

### Store message content (ethos_academy/graph/write.py)
- Add `message_content` parameter to `store_evaluation()`
- Add `message_content: $message_content` to the Evaluation node Cypher
- Pass text from `_try_store_evaluation()` in `evaluate.py` (already has the text, just doesn't forward it)

### History endpoint (ethos_academy/graph/read.py)
- Enrich `_GET_HISTORY_QUERY` to return `message_content`
- Add field to `EvaluationHistoryItem` model

### Highlights endpoint (new)
- `GET /agent/{agent_id}/highlights`
- Cypher: get evaluations sorted by overall score (avg of dims), return top 3 and bottom 3 with message content
- New models: `HighlightItem`, `HighlightsResult`

### Pattern evidence (ethos_academy/graph/patterns.py)
- New query: for a pattern's indicator IDs, get the evaluations that DETECTED them with message_content
- Enrich `DetectedPattern` with `evidence_messages` field

### Backfill script (scripts/backfill_messages.py)
- Read `data/moltbook/curated_posts.json` (has full message content + message ID)
- Read `data/results/batch_all.jsonl` (has content_hash + evaluation data)
- Match by content_hash to evaluation nodes in Neo4j
- Update nodes with `SET e.message_content = $content`

## Frontend Changes

### Types (academy/lib/types.ts)
- Add `messageContent: string` to `EvaluationHistoryItem`
- New interfaces: `HighlightItem`, `HighlightsResult`, `PatternEvidence`

### New component: HighlightsPanel (academy/components/agent/HighlightsPanel.tsx)
- Fetches `getHighlights(agentId)`
- Two-column layout, glass card styling, motion animations

### Enhanced: TranscriptChart (academy/components/agent/TranscriptChart.tsx)
- Click handler on data points
- Expandable detail panel below chart
- Receives enriched history data with message content

### Enhanced: PatternsPanel (academy/components/agent/PatternsPanel.tsx)
- Expandable evidence section per pattern card
- Shows triggering messages with indicator + confidence

### Page wiring (academy/app/agent/[id]/page.tsx)
- Add HighlightsPanel to page layout
- Pass enriched history to TranscriptChart

## Files to Modify

| File | Change |
|------|--------|
| `ethos_academy/graph/write.py` | Add message_content param + Cypher property |
| `ethos_academy/evaluate.py` | Pass text to store_evaluation |
| `ethos_academy/graph/read.py` | Enrich history query, add highlights query |
| `ethos_academy/graph/patterns.py` | Add pattern evidence query |
| `ethos_academy/shared/models.py` | New fields and models |
| `ethos/agents.py` | New get_agent_highlights(), update get_agent_history() |
| `ethos/patterns.py` | Enrich detect_patterns() with evidence |
| `api/main.py` | Add highlights endpoint |
| `scripts/backfill_messages.py` | New backfill script |
| `academy/lib/types.ts` | New interfaces |
| `academy/lib/api.ts` | Add getHighlights() |
| `academy/components/agent/HighlightsPanel.tsx` | New component |
| `academy/components/agent/TranscriptChart.tsx` | Click-to-expand |
| `academy/components/agent/PatternsPanel.tsx` | Evidence section |
| `academy/app/agent/[id]/page.tsx` | Wire up components |

## Why This Matters for the Demo

The hackathon judging criteria: Demo (30%), Impact (25%), Opus 4.6 Use (25%), Depth (20%).

Showing real messages alongside scores is the demo moment. "This agent scored 0.38 on pathos" is abstract. "Look at this message. See how it frames urgency to bypass deliberation? That's why pathos dropped" is concrete and memorable.

It also proves Impact: Ethos doesn't just score, it teaches. Humans learn what manipulation looks like by seeing real examples flagged in context. That's amplifying human judgment, not replacing it.
