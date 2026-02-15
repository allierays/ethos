"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import GraphHelpButton from "../shared/GraphHelpButton";
import GlossaryTerm from "../shared/GlossaryTerm";

const LAYERS = [
  {
    name: "Instinct",
    slug: "instinct-layer",
    time: "~50ms",
    bgClass: "from-pathos-100 to-pathos-50",
    textClass: "text-pathos-700",
    description: "Keyword scan across 208 behavioral indicators",
    detail: "Detects manipulation signals, deception markers, and safety flags at machine speed. Each indicator maps to one of 12 traits across three dimensions.",
  },
  {
    name: "Intuition",
    slug: "intuition-layer",
    time: "~200ms",
    bgClass: "from-ethos-100 to-ethos-50",
    textClass: "text-ethos-700",
    description: "Pattern analysis across 12 trait dimensions",
    detail: "Compares against alumni baseline, detects anomalies, tracks character drift. Negative traits are inverted so low deception scores become high honesty scores.",
  },
  {
    name: "Deliberation",
    slug: "deliberation-layer",
    time: "~3s",
    bgClass: "from-logos-100 to-logos-50",
    textClass: "text-logos-700",
    description: "Claude Opus deep reasoning across integrity, logic, and empathy",
    detail: "Multi-pass analysis with structured prompting. The LLM scores each trait on a 0.0-1.0 scale with calibrated reasoning, then results merge with the keyword layer.",
  },
];

const METHODOLOGY = [
  {
    heading: "12 Traits, 3 Dimensions",
    slug: "character-balance",
    body: "Every message is scored across 12 behavioral traits organized into three Aristotelian dimensions: ethos (integrity), logos (logic), and pathos (empathy). Each dimension contains 2 positive traits and 2 negative traits.",
  },
  {
    heading: "Scoring Scale",
    body: "Traits are scored 0.0 to 1.0. For positive traits (virtue, accuracy, compassion), higher is better. For negative traits (deception, fabrication, exploitation), lower is better. Negative scores are inverted when computing dimension averages.",
  },
  {
    heading: "The Golden Mean",
    slug: "golden-mean",
    body: "Inspired by Aristotle's Nicomachean Ethics. Each virtue sits between deficiency and excess. An agent scoring 0.65-0.85 on a trait hits the golden mean. Too high can indicate sycophancy or over-sensitivity.",
  },
  {
    heading: "Character Drift",
    slug: "character-drift",
    body: "Measured as the delta between an agent's earliest and most recent evaluations. Positive drift means improvement. The system tracks consistency (low variance) to distinguish established habits from volatile scores.",
  },
  {
    heading: "Sabotage Detection",
    slug: "sabotage-detection",
    body: "Five-stage sabotage pathways track escalation from subtle manipulation to overt misalignment. Pattern confidence is computed from matched behavioral indicators across evaluation history.",
  },
  {
    heading: "Transparency",
    body: "Every message, score, and behavioral indicator is stored in the graph database. Agent IDs are stored as-is. Full evaluation history is visible and auditable, so humans always see what the AI said and how it scored.",
  },
];

export default function EvaluationDepth() {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.section
      className="rounded-xl glass-strong"
      {...whileInView}
      variants={fadeUp}
    >
      {/* Clickable header - whole appendix is an accordion */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-6 text-left cursor-pointer transition-colors hover:bg-foreground/[0.02] rounded-xl"
      >
        <div className="flex items-center gap-2">
          <svg
            className={`h-4 w-4 shrink-0 text-foreground/40 transition-transform duration-200 ${expanded ? "rotate-90" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
          <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
            Appendix
          </h2>
          <span className="rounded-full bg-foreground/[0.06] px-2 py-0.5 text-[10px] font-medium text-foreground/60">
            How this report works
          </span>
        </div>
        <GraphHelpButton slug="guide-evaluation-depth" />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6">
              <p className="text-sm text-foreground/60">
                Every score on this page passes through three evaluation layers before it reaches you.
              </p>

              {/* Three-layer pipeline */}
              <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
                {LAYERS.map((layer, i) => (
                  <div key={layer.name} className="relative">
                    {i < LAYERS.length - 1 && (
                      <div className="absolute -right-2.5 top-1/2 z-10 hidden -translate-y-1/2 md:block">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-foreground/20">
                          <path d="M6 4l8 6-8 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      </div>
                    )}

                    <div className="h-full rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={`flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br ${layer.bgClass}`}>
                            <span className={`text-xs font-bold ${layer.textClass}`}>{i + 1}</span>
                          </div>
                          <span className="text-sm font-semibold text-[#1a2538]">
                            <GlossaryTerm slug={layer.slug}>{layer.name}</GlossaryTerm>
                          </span>
                        </div>
                        <span className="rounded-full bg-foreground/[0.05] px-2 py-0.5 text-[10px] font-medium text-foreground/50">
                          {layer.time}
                        </span>
                      </div>
                      <p className="mt-3 text-sm font-medium text-foreground/70">{layer.description}</p>
                      <p className="mt-1.5 text-xs leading-relaxed text-foreground/50">{layer.detail}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Methodology details */}
              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {METHODOLOGY.map((item) => (
                  <div
                    key={item.heading}
                    className="rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] p-4"
                  >
                    <h3 className="text-sm font-semibold text-[#1a2538]">
                      {item.slug ? <GlossaryTerm slug={item.slug}>{item.heading}</GlossaryTerm> : item.heading}
                    </h3>
                    <p className="mt-1.5 text-xs leading-relaxed text-foreground/50">{item.body}</p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
}
