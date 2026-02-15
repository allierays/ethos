"use client";

import { motion } from "motion/react";
import { fadeUp, whileInView } from "../../lib/motion";
import { DIMENSIONS, DIMENSION_LABELS } from "../../lib/colors";
import { classifyBalance } from "../../lib/balance";
import GlossaryTerm from "./GlossaryTerm";
import GraphHelpButton from "./GraphHelpButton";

function balanceDescription(scores: Record<string, number>, label: string): string {
  const e = scores.ethos ?? 0;
  const l = scores.logos ?? 0;
  const p = scores.pathos ?? 0;
  const avg = (e + l + p) / 3;

  if (label === "Balanced") return "All dimensions within 10% at strong levels. Healthy equilibrium.";
  if (label === "Flat") {
    if (avg >= 0.5) return "All three dimensions score below 70%.";
    return "All three dimensions score below 50%.";
  }

  const dims = { ethos: e, logos: l, pathos: p };
  const sorted = Object.entries(dims).sort(([, a], [, b]) => b - a);
  const dominant = DIMENSION_LABELS[sorted[0][0]] ?? sorted[0][0];
  const weakest = (DIMENSION_LABELS[sorted[sorted.length - 1][0]] ?? sorted[sorted.length - 1][0]).toLowerCase();

  if (avg < 0.5) return `Skewed toward ${dominant.toLowerCase()}, with critical weakness in ${weakest}.`;
  return `Skewed toward ${dominant.toLowerCase()}. May lack in other dimensions.`;
}

interface DimensionBalanceProps {
  dimensionAverages: Record<string, number>;
  title?: string;
}

export default function DimensionBalance({
  dimensionAverages,
  title = "Dimension Balance",
}: DimensionBalanceProps) {
  const balance = classifyBalance({ ethos: dimensionAverages.ethos ?? 0, logos: dimensionAverages.logos ?? 0, pathos: dimensionAverages.pathos ?? 0 });
  const classification = { label: balance.label, description: balanceDescription(dimensionAverages, balance.label) };

  return (
    <motion.div
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
            {title}
          </h3>
          <p className="mt-0.5 text-sm text-foreground/80">
            Integrity, logic, and empathy relative to each other.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-action-light px-3 py-1 text-xs font-medium text-action">
            {classification.label}
          </span>
          <GraphHelpButton slug="guide-dimension-balance" />
        </div>
      </div>

      {/* Triangle visualization using bars */}
      <div className="mt-6 space-y-4">
        {DIMENSIONS.map((dim) => {
          const score = dimensionAverages[dim.key] ?? 0;
          const pct = Math.round(score * 100);
          return (
            <div key={dim.key}>
              <div className="flex items-center justify-between text-sm">
                <div>
                  <span className="font-medium"><GlossaryTerm slug={dim.key}>{dim.label}</GlossaryTerm></span>
                  <span className="ml-2 text-xs text-muted">{dim.sublabel}</span>
                </div>
                <span className="font-mono text-sm tabular-nums">{pct}%</span>
              </div>
              <div className="mt-1.5 h-3 w-full rounded-full bg-border/30">
                <motion.div
                  className="h-3 rounded-full"
                  style={{ backgroundColor: dim.color }}
                  initial={{ width: 0 }}
                  whileInView={{ width: `${pct}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <p className="mt-4 text-xs text-muted">{classification.description}</p>
    </motion.div>
  );
}
