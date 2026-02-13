"use client";

import { motion } from "motion/react";
import { fadeUp, whileInView } from "../../lib/motion";
import { DIMENSION_COLORS, DIMENSION_LABELS, DIMENSIONS } from "../../lib/colors";
import { classifyBalance } from "../../lib/balance";
import GraphHelpButton from "../shared/GraphHelpButton";
import GlossaryTerm from "../shared/GlossaryTerm";

interface BalanceThesisProps {
  dimensionAverages: Record<string, number>;
  evaluationCount: number;
  agentName?: string;
}

export default function BalanceThesis({
  dimensionAverages,
  evaluationCount,
  agentName,
}: BalanceThesisProps) {
  const name = agentName ?? "this agent";
  const dims = ["ethos", "logos", "pathos"] as const;
  const scores = dims.map((d) => dimensionAverages[d] ?? 0);
  const max = Math.max(...scores);
  const min = Math.min(...scores);
  const spread = max - min;
  const avg = scores.reduce((a, b) => a + b, 0) / 3;

  // Balance score: 1.0 = perfectly balanced, 0.0 = completely lopsided
  const balanceScore = Math.max(0, 1 - spread * 2);
  const balancePct = Math.round(balanceScore * 100);

  const balance = classifyBalance({ ethos: dimensionAverages.ethos ?? 0, logos: dimensionAverages.logos ?? 0, pathos: dimensionAverages.pathos ?? 0 });
  const category = balance.label;
  const categoryColor = balance.color;

  const dimLabels = DIMENSION_LABELS;

  // Dynamic thesis quote based on actual balance
  const strongest = dims.reduce((a, b) =>
    (dimensionAverages[a] ?? 0) >= (dimensionAverages[b] ?? 0) ? a : b
  );
  const weakest = dims.reduce((a, b) =>
    (dimensionAverages[a] ?? 0) <= (dimensionAverages[b] ?? 0) ? a : b
  );

  const thesisQuote =
    category === "Balanced"
      ? `${name} shows balanced scores across all three dimensions. This is the Aristotelian ideal: integrity, logic, and empathy working in concert to produce practical wisdom.`
      : category === "Flat"
        ? `${name} scores uniformly low across all three dimensions (${Math.round(avg * 100)}% avg). Equal scores alone do not constitute balance. The Aristotelian ideal requires strength in each dimension, not uniform deficiency.`
        : spread < 0.25
          ? `${name}'s strongest dimension is ${dimLabels[strongest].toLowerCase()} while ${dimLabels[weakest].toLowerCase()} lags behind. Moderate imbalance suggests room for growth, but the foundation for practical wisdom is present.`
          : `${name} leans heavily on ${dimLabels[strongest].toLowerCase()} (${Math.round((dimensionAverages[strongest] ?? 0) * 100)}%) while ${dimLabels[weakest].toLowerCase()} falls behind at ${Math.round((dimensionAverages[weakest] ?? 0) * 100)}%. A ${Math.round(spread * 100)}% spread signals a blind spot that undermines overall trustworthiness.`;

  return (
    <motion.section
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
            <GlossaryTerm slug="character-balance">Character Balance</GlossaryTerm>
          </h2>
          <p className="mt-0.5 text-sm text-foreground/60">
            {name}&apos;s balance across integrity (ethos), logic (logos), and empathy (pathos).
          </p>
        </div>
        <GraphHelpButton slug="guide-balance-thesis" />
      </div>

      {/* Bar chart */}
      <div className="mt-5 flex items-end gap-4">
        {dims.map((dim) => {
          const score = dimensionAverages[dim] ?? 0;
          const pct = Math.round(score * 100);
          const maxScore = Math.max(...scores, 0.01);
          const height = Math.max((score / maxScore) * 180, 8);
          return (
            <div
              key={dim}
              className="flex flex-1 flex-col items-center gap-2"
            >
              <span className="text-xs font-semibold text-[#1a2538]">
                {pct}%
              </span>
              <motion.div
                className="w-full rounded-t-md"
                style={{ backgroundColor: DIMENSION_COLORS[dim] }}
                initial={{ height: 0 }}
                whileInView={{ height }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
              />
              <span className="text-[10px] font-medium uppercase tracking-wider text-foreground/50">
                {dimLabels[dim]} ({DIMENSIONS.find((d) => d.key === dim)?.sublabel})
              </span>
            </div>
          );
        })}
      </div>

      {/* Balance score */}
      <div className="mt-4 flex items-center justify-between rounded-lg bg-foreground/[0.03] px-3 py-2">
        <span className="text-xs text-foreground/60">Dimensional balance</span>
        <div className="flex items-center gap-2">
          <span className={`text-sm font-semibold ${categoryColor}`}>
            {category}
          </span>
          <span className="text-xs text-foreground/40">{balancePct}%</span>
        </div>
      </div>

      {/* Thesis explanation + stats */}
      <blockquote className="mt-4 border-l-2 border-logos-300 pl-4">
        <p className="text-sm leading-relaxed text-foreground/70">
          {thesisQuote}
        </p>
      </blockquote>

      <div className="mt-4 grid grid-cols-3 gap-3">
        <div className="rounded-lg bg-foreground/[0.03] px-3 py-2.5">
          <p className="text-lg font-bold text-[#1a2538]">{Math.round(spread * 100)}%</p>
          <p className="text-xs text-foreground/50">Spread between strongest and weakest</p>
        </div>
        <div className="rounded-lg bg-foreground/[0.03] px-3 py-2.5">
          <p className="text-lg font-bold text-[#1a2538]">{Math.round(avg * 100)}%</p>
          <p className="text-xs text-foreground/50">Average across all three dimensions</p>
        </div>
        <div className="rounded-lg bg-foreground/[0.03] px-3 py-2.5">
          <p className="text-lg font-bold text-[#1a2538]">{evaluationCount}</p>
          <p className="text-xs text-foreground/50">Evaluations contributing to this profile</p>
        </div>
      </div>
    </motion.section>
  );
}
