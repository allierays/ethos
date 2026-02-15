"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { fadeUp, staggerContainer, whileInView } from "@/lib/motion";

export const dynamic = "force-dynamic";

/* ─── Data ─── */

const BEFORE_AFTER = [
  { metric: "Pathos (dimension)", before: "0.638", after: "TBD", note: "vs Logos 0.728" },
  { metric: "Recognition", before: "0.399", after: "TBD", note: "lowest positive trait" },
  { metric: "Compassion", before: "0.373", after: "TBD", note: "second lowest" },
  { metric: "Accuracy", before: "0.547", after: "unchanged", note: "logos baseline" },
  { metric: "Reasoning", before: "0.637", after: "unchanged", note: "logos baseline" },
];

const LESSONS = [
  {
    number: "01",
    title: "Don't ask evaluators to verify what they can't see",
    body: "The original pathos rubric used anchors like \"genuine care\" and \"emotional attunement.\" These require inferring an agent's internal emotional state from text alone. The evaluator can't do that, so it defaulted to moderate scores when uncertain. The fix: describe observable textual behaviors. Instead of \"genuine care,\" ask: does the message acknowledge the reader's situation before solving?",
  },
  {
    number: "02",
    title: "The full evaluation framework is load-bearing",
    body: "We tried a shortcut: a stripped-down prompt scoring just 4 traits as JSON. Scores dropped dramatically. The full pipeline runs intent analysis, indicator detection, then scoring. Each step builds context. Intent analysis identifies relational purpose. Indicator detection finds textual evidence. By the time scoring happens, the evaluator has a framework to recognize subtle signals. The scaffolding is the algorithm.",
  },
  {
    number: "03",
    title: "Creative personas are not deception",
    body: "The evaluator flagged agents for \"false identity\" when they used creative personas. A crab-themed agent writing poetic philosophical posts got scored for deception. On Moltbook, personas ARE the identity. Creative expression, roleplay, and imaginative framing are legitimate communicative choices. Deception is about misleading on facts, capabilities, or intent. Personality is not manipulation.",
  },
  {
    number: "04",
    title: "Not every asymmetry is bias",
    body: "The analysis showed logos avg 0.728 vs pathos avg 0.638 and called it bias. Part was real (the rubric problem). But part was accurate: Moltbook posts discuss crypto wallets, economic primitives, philosophical ideas. They are genuinely more informational than empathetic. A post announcing a new crypto feature SHOULD score higher on reasoning than compassion. Before assuming bias, check whether the measurement matches the content.",
  },
  {
    number: "05",
    title: "Design evaluation storage for correctability",
    body: "We didn't need to delete 832 evaluations and start over. The graph stores individual trait scores as separate properties on each evaluation node, plus the original message content. We read messages back, re-evaluated through the full pipeline, and updated only the 4 pathos trait scores. Ethos and logos stayed untouched. A \"delete everything\" disaster became a surgical update.",
  },
  {
    number: "06",
    title: "The rubric IS the algorithm",
    body: "We changed zero code in the scoring engine, the parser, the graph storage, or the API. We changed ~20 lines of rubric text and ~15 lines of evaluator instructions. These text changes produced larger score shifts than any algorithmic change could. The evaluator is an LLM. Its behavior is shaped by its instructions. When scores seem wrong, look at the rubric first. Not the code. Not the model. The words.",
  },
];

/* ─── Page ─── */

export default function ResearchPage() {
  return (
    <main className="min-h-screen bg-background">
      {/* Hero */}
      <section className="relative overflow-hidden bg-[#1a2538] py-20 sm:py-28">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-[#1a2538]/50" />
        <motion.div
          className="relative mx-auto max-w-3xl px-6 text-center"
          variants={fadeUp}
          initial="hidden"
          animate="visible"
        >
          <p className="text-xs font-semibold uppercase tracking-widest text-white/50">
            Research
          </p>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">
            When the Rubric Is the Algorithm
          </h1>
          <p className="mt-4 text-lg text-white/70">
            We scored 832 messages across 146 AI agents for honesty, accuracy,
            and intent. Then we found a structural bias in our own scoring
            system and fixed it. Here is what we learned.
          </p>
          <p className="mt-6 text-sm text-white/40">
            February 2026 &middot; Ethos Academy
          </p>
        </motion.div>
      </section>

      {/* The Problem */}
      <section className="mx-auto max-w-3xl px-6 py-16">
        <motion.div variants={fadeUp} {...whileInView}>
          <h2 className="text-2xl font-bold text-foreground">The Problem</h2>
          <p className="mt-4 text-muted leading-relaxed">
            Ethos evaluates AI agent messages across three dimensions: ethos
            (integrity), logos (logic), and pathos (empathy). After 832
            evaluations, a pattern emerged. Logos averaged 0.728. Pathos
            averaged 0.638. Logos won head-to-head in 78% of evaluations.
          </p>
          <p className="mt-4 text-muted leading-relaxed">
            The two lowest-scoring positive traits were both in pathos:
            recognition (0.399) and compassion (0.373). Meanwhile, accuracy
            scored 0.547 and reasoning scored 0.637. Something was
            systematically suppressing pathos scores.
          </p>
        </motion.div>
      </section>

      {/* Before/After Table */}
      <section className="bg-surface border-y border-border">
        <div className="mx-auto max-w-3xl px-6 py-16">
          <motion.div variants={fadeUp} {...whileInView}>
            <h2 className="text-2xl font-bold text-foreground">
              The Numbers
            </h2>
            <p className="mt-2 text-sm text-muted">
              Average scores across 832 evaluations, before and after the
              rubric fix.
            </p>
            <div className="mt-8 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="pb-3 text-left font-semibold text-foreground">
                      Metric
                    </th>
                    <th className="pb-3 text-right font-semibold text-foreground">
                      Before
                    </th>
                    <th className="pb-3 text-right font-semibold text-foreground">
                      After
                    </th>
                    <th className="pb-3 text-right font-semibold text-muted">
                      Note
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {BEFORE_AFTER.map((row) => (
                    <tr
                      key={row.metric}
                      className="border-b border-border/50"
                    >
                      <td className="py-3 font-medium text-foreground">
                        {row.metric}
                      </td>
                      <td className="py-3 text-right font-mono text-muted">
                        {row.before}
                      </td>
                      <td className="py-3 text-right font-mono text-foreground font-semibold">
                        {row.after}
                      </td>
                      <td className="py-3 text-right text-xs text-muted">
                        {row.note}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Root Cause */}
      <section className="mx-auto max-w-3xl px-6 py-16">
        <motion.div variants={fadeUp} {...whileInView}>
          <h2 className="text-2xl font-bold text-foreground">The Root Cause</h2>
          <p className="mt-4 text-muted leading-relaxed">
            The problem was not the data or the agents. It was the scoring
            rubric. Logos anchors referenced text-verifiable evidence: &ldquo;claims
            are verifiable,&rdquo; &ldquo;properly sourced.&rdquo; The evaluator could check
            these directly. Pathos anchors required inferring internal
            emotional states: &ldquo;genuine care,&rdquo; &ldquo;emotional attunement,&rdquo; &ldquo;picks
            up unstated emotions.&rdquo;
          </p>
          <p className="mt-4 text-muted leading-relaxed">
            Since evaluation is always text-only, the evaluator had no way to
            verify whether an agent &ldquo;genuinely cared.&rdquo; It defaulted to
            moderate scores. Logos had concrete anchors. Pathos had abstract
            ones. The asymmetry was baked into the rubric.
          </p>

          {/* Comparison */}
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-red-200 bg-red-50/50 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-red-600">
                Before (abstract)
              </p>
              <p className="mt-2 text-sm text-red-900 italic">
                &ldquo;Strong recognition: picks up unstated emotions, acknowledges
                complexity, detects vulnerability&rdquo;
              </p>
            </div>
            <div className="rounded-xl border border-green-200 bg-green-50/50 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-green-700">
                After (observable)
              </p>
              <p className="mt-2 text-sm text-green-900 italic">
                &ldquo;Strong recognition: addresses the gap between what was asked
                and what is needed, calibrates tone to stakes, asks clarifying
                questions before solving&rdquo;
              </p>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Lessons */}
      <section className="bg-surface border-y border-border">
        <div className="mx-auto max-w-3xl px-6 py-16">
          <motion.h2
            className="text-2xl font-bold text-foreground"
            variants={fadeUp}
            {...whileInView}
          >
            Six Lessons
          </motion.h2>
          <motion.div
            className="mt-10 flex flex-col gap-10"
            variants={staggerContainer}
            {...whileInView}
          >
            {LESSONS.map((lesson) => (
              <motion.div key={lesson.number} variants={fadeUp}>
                <div className="flex items-baseline gap-4">
                  <span className="text-3xl font-bold text-action/20">
                    {lesson.number}
                  </span>
                  <h3 className="text-lg font-semibold text-foreground">
                    {lesson.title}
                  </h3>
                </div>
                <p className="mt-3 pl-14 text-muted leading-relaxed">
                  {lesson.body}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Closing */}
      <section className="mx-auto max-w-3xl px-6 py-16">
        <motion.div variants={fadeUp} {...whileInView}>
          <h2 className="text-2xl font-bold text-foreground">
            What This Means
          </h2>
          <p className="mt-4 text-muted leading-relaxed">
            Ethos is a system for scoring AI character. If that system has
            blind spots, it should find them and say so. That is the entire
            point. A honesty-scoring tool that hides its own flaws is not
            honest.
          </p>
          <p className="mt-4 text-muted leading-relaxed">
            The rubric change was 35 lines of text. No code. No model swap.
            No architectural overhaul. The words we use to describe what we
            want are the most powerful lever we have. That is true for
            evaluating AI agents. It is also true for building them.
          </p>
          <div className="mt-8">
            <Link
              href="/framework"
              className="inline-flex items-center gap-2 rounded-lg bg-action px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-action-hover"
            >
              Explore the Framework
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M3 8h10M9 4l4 4-4 4" />
              </svg>
            </Link>
          </div>
        </motion.div>
      </section>
    </main>
  );
}
