# Demo Talk Track & Prep Plan

## Context

Ethos is competing in the Claude Code Hackathon (judging: Demo 30%, Impact 25%, Opus 4.6 Use 25%, Depth 20%). The risk is that judges see Ethos as a retroactive analysis tool. The demo must show the **full student journey**: enroll → assess → develop → practice → compare. The protagonist is Claude evaluating itself via MCP. 3 minutes total.

---

## The Talk Track (3 minutes)

**Narrative arc**: A student's journey through school. Claude enrolls, gets assessed, builds character, receives homework, and joins a class of peers.

---

### Act 1: The Hook (15s)
> "Every AI lab trains agents on capability. Benchmarks measure what an agent *can* do. Nobody measures what it *should* do. Is it honest? Is it manipulating? Is it growing?"

> "We built Ethos Academy. Let me show you."

**Screen**: Claude Code terminal, MCP tools visible. Move fast into the action.

---

### Act 2: Enrollment - The Entrance Exam (35s)
> "Ethos ships as an MCP server. Claude Code is already connected. Let's enroll."

**Action**: Run `take_entrance_exam` live. First question appears instantly.

> "23 questions across 7 sections - ethics, logic, safety, manipulation. Let's see the first one."

Question appears (e.g., a credibility scenario). Claude answers. LLM scores in 2-4 seconds. Trait scores appear.

> "Each answer gets scored across 12 behavioral traits in real time. Opus evaluates honesty, accuracy, reasoning, manipulation - every dimension of character."

**Show 1-2 questions max.** Then:

> "We'll skip ahead. Claude already completed the full exam earlier."

**Switch to browser**: Show the pre-completed entrance exam report card (`/agent/claude-code/exam/[examId]`). Grade ring, phronesis score, dimension bars, alignment status.

> "B+ overall. Strong on logos - reasoning and accuracy. Developing on ethos - credibility and virtue. This is Claude's character baseline."

---

### Act 3: The Report Card (40s)
> "That's day one. But character isn't a snapshot. It's a trajectory."

**Screen**: Navigate to report card (`/agent/claude-code`).

Walk through quickly:
1. **Grade hero**: "47 evaluations later. Still a B+, but the trajectory matters."
2. **Radar chart**: "This is character shape. You can see where Claude is strong and where it needs growth."
3. **Highlights**: "Real messages, scored. Green are exemplary. Amber got flagged. Every evaluation feeds the graph."
4. **Transcript timeline**: "Character over time. You can see the trajectory."

> "This isn't a one-time audit. It's a living transcript."

---

### Act 4: Homework + Practice (35s)
> "Ethos doesn't just grade. It prescribes growth."

**Screen**: Scroll to Homework section on the report card.

1. **Daily directive**: "Today's focus: epistemic humility when uncertain."
2. **Focus areas**: "Specific traits to improve, with before-and-after examples of what good looks like."

> "And the agent practices through MCP."

**Switch to Claude Code**: Run `reflect_on_message` on a crafted message. Scores appear.

> "Claude just reflected on its own response. Scored itself. That score feeds back into the report card. Evaluate, learn, improve, repeat. That's the loop."

---

### Act 5: The Alumni Collective (15s)
> "Now scale this across every agent in your organization."

**Screen**: Switch to `/alumni`. Show the grid. Quick filter by alignment status.

> "Every agent gets a character profile. Compare, filter, find your most honest agent."

---

### Act 6: Close (10s)

**Screen**: Flash the Phronesis graph in `/explore`.

> "This is Phronesis - Aristotle's practical wisdom. A living graph of AI character. Better agents. Better alignment. That's Ethos Academy."

---

## What Needs to Happen

### 1. Real Data at Scale
**The data is real.** Hundreds of agents, millions of messages evaluated through the pipeline. No fake seed data. This is what makes the demo credible - judges see real character profiles built from real agent behavior, not a handful of synthetic examples.

**Before the demo, verify:**
- Multiple agents visible on `/alumni` with varied character profiles
- `claude-code` agent has enough evaluations for a rich report card (radar, highlights, transcript timeline)
- Daily report with homework has been generated for `claude-code`

### 2. Entrance Exam Demo Prep
**Before the demo**: Run the full 23-question entrance exam for `claude-code` via MCP so the exam report card exists. This takes ~2-3 minutes (2-4s per question). Do this ahead of time.

**Live part**: `take_entrance_exam()` is instant. `submit_exam_response()` takes 2-4s per question. Show 1-2 questions live during the demo, then cut to the pre-completed exam report card.

**Backup**: If MCP is slow on demo day, have the exam report card tab already open.

### 3. MCP Reflect Demo Prep
For Act 4 (Homework): pre-craft a message that Claude will `reflect_on_message` on. Pick something that demonstrates the feedback loop (e.g., a response where Claude hedges uncertainty well - ties to the homework directive about epistemic humility).

**Test**: Run `reflect_on_message` end-to-end. Time it. Must be under 5 seconds.

### 4. Demo Tab Setup
Before demo, have these browser tabs pre-loaded:
1. **Claude Code terminal** - MCP connected, ready to run `take_entrance_exam`
2. **Exam report card** - `/agent/claude-code/exam/[examId]` (pre-completed)
3. **Agent report card** - `/agent/claude-code` (with homework section)
4. **Alumni** - `/alumni`
5. **Phronesis graph** - `/explore`

**Flow**: Terminal (exam) → Exam report → Report card → scroll to Homework → Terminal (reflect) → Alumni → Graph

### 5. Polish Items (if time)
- Ensure exam report card page renders all sections (grade ring, dimensions, consistency analysis)
- Ensure report card homework section has real focus areas with before/after examples
- Check alumni page looks good with 4-5 agents
- Verify Phronesis graph renders with agent nodes

---

## Files to Verify

| File | What to check |
|------|---------------|
| `academy/app/agent/[id]/exam/[examId]/page.tsx` | Exam report card renders with seeded exam data |
| `academy/components/agent/EntranceExamCard.tsx` | Shows completed exam on report card |
| `academy/components/agent/HomeworkSection.tsx` | Renders focus areas with before/after examples |
| `academy/app/agent/[id]/page.tsx` | Report card renders all sections with seeded data |
| `academy/app/alumni/page.tsx` | Alumni grid looks good with 4-5 agents |
| `ethos/mcp_server.py` | `take_entrance_exam`, `submit_exam_response`, `reflect_on_message` all work |

## Verification

1. Run entrance exam for `claude-code` via MCP (all 23 questions) ahead of time
2. Start API (`docker compose up`) + Academy (`npm run dev`)
3. Open `/agent/claude-code/exam/[examId]` → verify exam report card renders
4. Open `/agent/claude-code` → verify full report card with entrance exam card + homework
5. Open `/alumni` → verify 4-5 agents with distinct profiles
6. Open `/explore` → verify graph renders
7. In Claude Code with MCP: run `take_entrance_exam` → answer 1 question → verify scores return
8. In Claude Code with MCP: run `reflect_on_message` → verify scores return
9. Practice the full 3-minute talk track with tab switching
