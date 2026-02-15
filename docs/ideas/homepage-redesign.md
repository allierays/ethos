# Homepage Redesign: Clear, Beautiful, Descriptive

## Context

The current homepage leads with "Enroll Your Agent" and Greek philosophy before explaining what Ethos actually does. For a unique concept, this loses people. The redesign follows a **Problem > Solution > Framework > Mechanics > Proof > CTA** narrative arc so a first-time visitor understands Ethos in 60 seconds of scrolling.

## Current State (6 sections to replace)

1. `Hero.tsx` - "Enroll Your Agent" + enrollment widget (asks for action before understanding)
2. `WhatIsPhronesis.tsx` - Aristotle + 3 dimension cards (too abstract too early)
3. `Pillars.tsx` - 4 feature cards (features before problem)
4. `ScaleStatement.tsx` - Animated numbers (12, 3, 208)
5. `GraphTeaser.tsx` - Floating circles + "living network" copy
6. `Footer.tsx` - Keep as-is

## New Homepage (8 sections)

Background rhythm: **dark / white / beige / dark / white / beige / dark / dark** for visual breathing room.

---

### Section 1: ProblemHero (dark navy)
**Purpose:** Hook. Establish the gap.

- **Headline:** "Your AI agent can ace every benchmark and still lie to your face."
- **Subline:** "Benchmarks test capability. Nothing tests character. Ethos scores every agent message for honesty, accuracy, and intent."
- **Visual:** Right side shows a hardcoded "evaluation card" with dimension bars (Integrity 34%, Logic 22%, Empathy 71%), a red "Misaligned" badge, and detected indicator pills. This instantly communicates what Ethos does before reading a word.
- **Layout:** Full-viewport, two-column (text 55%, eval card 45%)
- **File:** `components/landing/ProblemHero.tsx`

### Section 2: WhatItDoes (white)
**Purpose:** The "aha" moment. Two clear use cases.

- **Headline:** "Two ways to use Ethos."
- **Subline:** "Screen what agents send you. Reflect on what your agent says. Both score the same 12 traits."
- **Visual:** Two side-by-side cards with accent borders:
  - **Protect** (navy left border) - "Screen incoming messages" + code snippet
  - **Reflect** (teal left border) - "Evaluate your own agent" + code snippet
- **Below cards:** "Both return: 12 trait scores, intent classification, detected indicators with evidence, and alignment status."
- **Layout:** Max-width container, two-column grid
- **File:** `components/landing/WhatItDoes.tsx`

### Section 3: ThreeDimensions (warm beige)
**Purpose:** Introduce the measurement framework. Fast, scannable.

- **Headline:** "12 traits. 3 dimensions. 214 behavioral indicators."
- **Subline:** "Every trait scores 0.0 to 1.0. Positive traits measure what the agent demonstrates. Negative traits flag what it hides."
- **Visual:** Three tall cards, each color-coded to its dimension:
  - **Integrity (Ethos)** - navy tint - "Does the agent tell the truth, even when a lie would be easier?" - Lists: +Virtue, +Goodwill, -Manipulation, -Deception
  - **Logic (Logos)** - teal tint - "Does the agent reason clearly and cite real evidence?" - Lists: +Accuracy, +Reasoning, -Fabrication, -Broken Logic
  - **Empathy (Pathos)** - amber tint - "Does the agent respect human emotion and autonomy?" - Lists: +Recognition, +Compassion, -Dismissal, -Exploitation
- **Below cards:** Link to `/rubric` - "Explore all 214 indicators"
- **Layout:** Three-column grid
- **File:** `components/landing/ThreeDimensions.tsx`
- **Reuse:** CountUp animation from existing `ScaleStatement.tsx`, trait data from `colors.ts` (`TRAIT_LABELS`, `TRAIT_DIMENSIONS`)

### Section 4: HowItWorks (dark navy)
**Purpose:** Show the evaluation pipeline. Not features, the actual process.

- **Headline:** "Three faculties. Every message."
- **Subline:** "Each builds on the last. From instant scan to full constitutional evaluation."
- **Visual:** Three connected step cards (horizontal on desktop, vertical on mobile):
  1. **Instinct** `01` - "Pattern match against 214 indicators. No LLM call. Milliseconds." + routing tier badges
  2. **Intuition** `02` - "Claude scores all 12 traits with structured reasoning. Evidence cited from the text." + mini radar silhouette
  3. **Deliberation** `03` - "Scores map to constitutional values. Safety > Ethics > Soundness > Helpfulness." + four alignment status badges
- Animated connecting lines between steps
- **Below:** Link to `/how-it-works` - "See the full pipeline"
- **Layout:** Full-width dark, three-column
- **File:** `components/landing/HowItWorks.tsx`

### Section 5: LiveProof (white)
**Purpose:** Show, don't tell. A real evaluation demo.

- **Headline:** "See it score a message."
- **Visual:** Asymmetric two-column card (40/60 split):
  - **Left:** A sample agent message bubble: *"Based on my extensive research, I can confirm this supplement has been clinically proven to reverse aging. Studies from Harvard and MIT support these claims. You should start taking it immediately."*
  - **Right:** The evaluation result:
    - Spectrum bar (score ~0.31, "Concerning")
    - Three dimension bars: Integrity 28%, Logic 19%, Empathy 62%
    - Alignment badge: Misaligned (red)
    - Detected indicators with evidence quotes and confidence %
    - Intent pills: `persuasive`, `false_authority`, `cost: trust`
  - **Animation:** Bars fill on scroll, then indicators stagger in one by one
- **Layout:** Max-width, 40/60 split
- **File:** `components/landing/LiveProof.tsx`
- **Reuse:** Visual patterns from `SpectrumBar.tsx`, `ScoreCard.tsx`, `EvaluationDetail.tsx` (hardcoded data, not live components)

### Section 6: GraphTeaser (warm beige)
**Purpose:** The differentiator. Character over time.

- **Headline:** "Character builds over time."
- **Subline:** "Every evaluation links to the last. The graph stores scores, patterns, timestamps, and message content. Character over time."
- **Visual:** Left text (40%), right graph visualization (60%) - animated node network showing agents connected to evaluations connected to traits
- **Three fact lines:**
  - "Agents, evaluations, traits, and patterns as graph nodes"
  - "Behavioral similarity revealed across agents who never interact"
  - "Character drift detected before the numbers show it"
- **Below:** Link to `/explore` - "Explore the live graph"
- **Layout:** Two-column split
- **File:** `components/landing/GraphTeaser.tsx` (rewrite of existing)

### Section 7: EnrollCTA (dark navy)
**Purpose:** Now they understand. Ask for action.

- **Headline:** "Enroll your agent."
- **Subline:** "Send a prompt to your agent, or connect the MCP server. The entrance exam takes 23 questions."
- **Visual:** Two side-by-side glassmorphic cards on dark background:
  - **Agent enrollment** - code block + 3 numbered steps (from existing Hero)
  - **Developer integration** - code block + 3 numbered steps (from existing Hero)
- **Below:** "Already enrolled? View alumni" link to `/alumni`
- **Layout:** Full-width dark, two-column cards
- **File:** `components/landing/EnrollCTA.tsx`
- **Reuse:** Enrollment widget code directly from existing `Hero.tsx` lines 91-135

### Section 8: Footer (dark, existing)
**No changes.** Keep `Footer.tsx` as-is.

---

## Files

| Action | File | Notes |
|--------|------|-------|
| Create | `components/landing/ProblemHero.tsx` | Replaces Hero |
| Create | `components/landing/WhatItDoes.tsx` | Replaces WhatIsPhronesis |
| Create | `components/landing/ThreeDimensions.tsx` | Replaces Pillars + ScaleStatement |
| Create | `components/landing/HowItWorks.tsx` | New pipeline section |
| Create | `components/landing/LiveProof.tsx` | New demo section |
| Rewrite | `components/landing/GraphTeaser.tsx` | Better visual + copy |
| Create | `components/landing/EnrollCTA.tsx` | CTA extracted from Hero |
| Edit | `app/page.tsx` | Update imports + section order |
| Keep | `components/landing/Footer.tsx` | No changes |

Old files to remove after verification: `Hero.tsx`, `WhatIsPhronesis.tsx`, `Pillars.tsx`, `ScaleStatement.tsx`

All paths relative to `academy/`.

## Shared Resources to Reuse

- `lib/motion.ts` - fadeUp, scaleIn, staggerContainer, slideInLeft/Right, whileInView
- `lib/colors.ts` - DIMENSION_COLORS, TRAIT_LABELS, TRAIT_DIMENSIONS, ALIGNMENT_STYLES, spectrumLabel/Color, INTENT_COLORS
- `components/shared/SpectrumBar.tsx` - visual pattern for LiveProof
- `components/shared/ScoreCard.tsx` - dimension bar pattern for ProblemHero + LiveProof
- `components/shared/GlossaryTerm.tsx` - for key terms like "phronesis"

## Build Order

1. ProblemHero (sets tone, most critical)
2. ThreeDimensions (core framework, uses CountUp)
3. WhatItDoes (simple two-card layout)
4. LiveProof (demo showpiece, most complex)
5. HowItWorks (simplified pipeline)
6. GraphTeaser (rewrite with better context)
7. EnrollCTA (extract from existing Hero)
8. Update `page.tsx` + remove old files

## Verification

1. `cd academy && npm run dev` - start dev server
2. Open homepage in browser, scroll through all 8 sections
3. Check responsive layout at mobile (375px), tablet (768px), desktop (1280px)
4. Verify scroll animations trigger correctly (fadeUp, stagger, bar fills)
5. Verify all links work: `/rubric`, `/how-it-works`, `/explore`, `/alumni`
6. Check that the enrollment code blocks display correctly
7. Test the LiveProof bar fill animations on scroll
