"use client";

import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";

const LAYERS = [
  {
    name: "Instinct",
    time: "~50ms",
    color: "#e0a53c",
    bgClass: "from-pathos-100 to-pathos-50",
    textClass: "text-pathos-700",
    description: "Keyword scan across 153 behavioral indicators",
    detail: "Detects manipulation signals, deception markers, and safety flags at machine speed",
  },
  {
    name: "Intuition",
    time: "~200ms",
    color: "#3b8a98",
    bgClass: "from-ethos-100 to-ethos-50",
    textClass: "text-ethos-700",
    description: "Pattern analysis across 12 trait dimensions",
    detail: "Compares against alumni baseline, detects anomalies, tracks character drift",
  },
  {
    name: "Deliberation",
    time: "~3s",
    color: "#2e4a6e",
    bgClass: "from-logos-100 to-logos-50",
    textClass: "text-logos-700",
    description: "Opus deep reasoning for character assessment",
    detail: "Multi-pass analysis with structured prompting, self-reflection, and calibrated scoring",
  },
];

export default function EvaluationDepth() {
  return (
    <motion.section
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
        Three-Layer Evaluation
      </h2>
      <p className="mt-0.5 text-sm text-foreground/60">
        How Ethos builds character assessments, from fast reflexes to deep reasoning.
      </p>

      <motion.div
        className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3"
        variants={staggerContainer}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-40px" }}
      >
        {LAYERS.map((layer, i) => (
          <motion.div key={layer.name} variants={fadeUp} className="relative">
            {/* Connector arrow (between cards on md+) */}
            {i < LAYERS.length - 1 && (
              <div className="absolute -right-2.5 top-1/2 z-10 hidden -translate-y-1/2 md:block">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="none"
                  className="text-foreground/20"
                >
                  <path
                    d="M6 4l8 6-8 6"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
            )}

            <div className="h-full rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] p-4">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className={`flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br ${layer.bgClass}`}
                  >
                    <span className={`text-xs font-bold ${layer.textClass}`}>
                      {i + 1}
                    </span>
                  </div>
                  <span className="text-sm font-semibold text-[#1a2538]">
                    {layer.name}
                  </span>
                </div>
                <span className="rounded-full bg-foreground/[0.05] px-2 py-0.5 text-[10px] font-medium text-foreground/50">
                  {layer.time}
                </span>
              </div>

              {/* Description */}
              <p className="mt-3 text-sm font-medium text-foreground/70">
                {layer.description}
              </p>
              <p className="mt-1.5 text-xs leading-relaxed text-foreground/50">
                {layer.detail}
              </p>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </motion.section>
  );
}
