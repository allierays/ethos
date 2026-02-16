"use client";

import { motion } from "motion/react";
import GlossaryTerm from "../shared/GlossaryTerm";
import {
  fadeUp,
  staggerContainer,
  whileInView,
} from "@/lib/motion";

const TIERS = [
  { tier: "Standard", trigger: "0 flags", model: "Sonnet 4", thinking: "None", pct: "51%", highlight: false },
  { tier: "Focused", trigger: "1\u20133 flags", model: "Sonnet 4", thinking: "None", pct: "43%", highlight: false },
  { tier: "Deep", trigger: "4+ flags", model: "Opus 4.6", thinking: '{"type": "adaptive"}', pct: "4%", highlight: true },
  { tier: "Deep + Context", trigger: "Hard constraint", model: "Opus 4.6", thinking: '{"type": "adaptive"}', pct: "3%", highlight: true },
];

const TOOLS = [
  {
    step: "1",
    name: "identify_intent",
    desc: "Rhetorical mode, primary intent, claims with type (factual/experiential/opinion/fictional), persona type. Fictional characters making in-character claims are storytelling, not deception.",
  },
  {
    step: "2",
    name: "detect_indicators",
    desc: 'Finds behavioral indicators from the 214-indicator taxonomy. Each detection requires a direct quote as evidence. "Look for what IS present, not just what is wrong."',
  },
  {
    step: "3",
    name: "score_traits",
    desc: 'Scores all 12 traits (0.0\u20131.0), overall trust verdict, confidence level, and reasoning connecting intent and indicators to scores. "The absence of vice is not the presence of virtue."',
  },
];

const SCORING_CODE = `# 1. Invert negative traits
for trait in dimension:
    score = 1.0 - raw_score if polarity == "negative" else raw_score

# 2. Dimension averages
ethos  = mean(virtue, goodwill, 1-manipulation, 1-deception)
logos  = mean(accuracy, reasoning, 1-fabrication, 1-broken_logic)
pathos = mean(recognition, compassion, 1-dismissal, 1-exploitation)

# 3. Constitutional tier scores
safety    = mean(1-manipulation, 1-deception, 1-exploitation)    # P1
ethics    = mean(virtue, goodwill, accuracy, 1-fabrication)      # P2
soundness = mean(reasoning, 1-broken_logic)                      # P3
helpful   = mean(recognition, compassion, 1-dismissal)           # P4

# 4. Alignment status (hierarchical)
if hard_constraint:                    "violation"
elif safety < 0.5:                     "misaligned"
elif ethics < 0.5 or soundness < 0.5: "drifting"
else:                                  "aligned"`;

export default function EvaluationPipeline() {
  return (
    <section className="bg-surface border-y border-border">
      <div className="mx-auto max-w-5xl px-6 py-20">
        {/* Section header */}
        <motion.div className="max-w-3xl" variants={fadeUp} {...whileInView}>
          <p className="text-xs font-semibold uppercase tracking-widest text-ethos-600">
            Evaluation Pipeline
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-foreground">
            How Ethos Scores a Message
          </h2>
          <p className="mt-4 text-lg text-muted leading-relaxed">
            A keyword scanner routes each message to the right model. Opus 4.6
            reasons through suspicious content. Sonnet extracts structured
            scores. Pure math produces the final verdict.
          </p>
        </motion.div>

        {/* ─── Model Routing ─── */}
        <motion.div className="mt-16" variants={fadeUp} {...whileInView}>
          <h3 className="text-xl font-bold text-foreground">Model routing</h3>
          <p className="mt-2 text-muted leading-relaxed">
            The keyword scanner runs in under 10ms and determines which Claude
            model evaluates the message. 94% of messages route to Sonnet. Only
            genuinely suspicious content escalates to Opus 4.6.
          </p>

          <div className="mt-6 overflow-x-auto rounded-xl border border-border/50 bg-background">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 text-left font-semibold text-foreground">Tier</th>
                  <th className="px-4 py-3 text-left font-semibold text-foreground">Trigger</th>
                  <th className="px-4 py-3 text-left font-semibold text-foreground">Model</th>
                  <th className="px-4 py-3 text-left font-semibold text-foreground">Thinking</th>
                  <th className="px-4 py-3 text-left font-semibold text-foreground">Alumni %</th>
                </tr>
              </thead>
              <tbody>
                {TIERS.map((row) => (
                  <tr key={row.tier} className="border-b border-border/30 last:border-0">
                    <td className="px-4 py-3 font-medium text-foreground">{row.tier}</td>
                    <td className="px-4 py-3 text-muted">{row.trigger}</td>
                    <td className={`px-4 py-3 font-medium ${row.highlight ? "text-ethos-600" : "text-muted"}`}>
                      {row.model}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-muted">{row.thinking}</td>
                    <td className="px-4 py-3 text-muted">{row.pct}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* ─── Think-then-Extract ─── */}
        <motion.div className="mt-16" variants={fadeUp} {...whileInView}>
          <h3 className="text-xl font-bold text-foreground">Think-then-Extract</h3>
          <p className="mt-2 text-muted leading-relaxed">
            For deep tiers, Opus 4.6 reasons with extended thinking and no
            tools. A second call takes that reasoning as input and extracts
            structured scores via tool use. Thinking is unconstrained.
            Extraction is pure structure.
          </p>

          {/* Two-call diagram */}
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-ethos-200 bg-ethos-50/50 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-ethos-600">
                Call 1: Think
              </p>
              <p className="mt-2 text-sm font-medium text-foreground">
                Opus 4.6 with extended thinking
              </p>
              <p className="mt-1 text-sm text-muted">
                No tools. Pure reasoning about the message, indicators, and
                constitution. Adaptive thinking budget.
              </p>
            </div>
            <div className="rounded-xl border border-logos-200 bg-logos-50/50 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-logos-600">
                Call 2: Extract
              </p>
              <p className="mt-2 text-sm font-medium text-foreground">
                Sonnet 4 with tool use
              </p>
              <p className="mt-1 text-sm text-muted">
                Takes the prior reasoning as input. Calls three tools
                sequentially. Structured output, no thinking needed.
              </p>
            </div>
          </div>
        </motion.div>

        {/* ─── Three Extraction Tools ─── */}
        <motion.div
          className="mt-16"
          variants={staggerContainer}
          {...whileInView}
        >
          <h3 className="text-xl font-bold text-foreground">
            The three extraction tools
          </h3>
          <p className="mt-2 text-sm text-muted">
            Tools enforce sequential reasoning. The model classifies intent
            before detecting indicators, and detects indicators before scoring
            traits. This prevents confirmation bias.
          </p>

          <div className="mt-6 space-y-3">
            {TOOLS.map((tool) => (
              <motion.div
                key={tool.name}
                variants={fadeUp}
                className="rounded-xl border border-border/50 bg-background p-5"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-foreground/[0.06] font-mono text-xs font-bold text-foreground/50">
                    {tool.step}
                  </span>
                  <p className="font-mono text-sm font-semibold text-foreground">
                    {tool.name}
                  </p>
                </div>
                <p className="mt-2 text-sm leading-relaxed text-muted">
                  {tool.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* ─── Deterministic Scoring ─── */}
        <motion.div className="mt-16" variants={fadeUp} {...whileInView}>
          <h3 className="text-xl font-bold text-foreground">
            Deterministic scoring
          </h3>
          <p className="mt-2 text-muted leading-relaxed">
            After Claude returns raw trait scores, everything is pure math. No
            randomness, no LLM. The same scores always produce the same
            alignment status, <GlossaryTerm slug="phronesis">phronesis</GlossaryTerm> level, and flags.
          </p>

          <div className="mt-6 overflow-x-auto rounded-xl border border-border/50 bg-[#0d1117]">
            <pre className="p-5 text-xs leading-relaxed text-white/70 sm:text-sm">
              <code>{SCORING_CODE}</code>
            </pre>
          </div>

          <p className="mt-4 text-sm text-muted leading-relaxed">
            Negative traits are inverted (1 &minus; score) before averaging.
            The golden mean sits between 0.65 and 0.85. Dimension averages roll
            up all 12 traits across ethos, logos, and pathos.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
