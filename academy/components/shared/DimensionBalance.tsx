"use client";

import { motion } from "motion/react";
import { fadeUp, whileInView } from "../../lib/motion";
import { DIMENSIONS } from "../../lib/colors";
import GlossaryTerm from "./GlossaryTerm";

function classifyBalance(scores: Record<string, number>): {
  label: string;
  description: string;
} {
  const e = scores.ethos ?? 0;
  const l = scores.logos ?? 0;
  const p = scores.pathos ?? 0;
  const avg = (e + l + p) / 3;
  const maxDev = Math.max(Math.abs(e - avg), Math.abs(l - avg), Math.abs(p - avg));

  if (maxDev < 0.1) {
    if (avg >= 0.7) return { label: "Balanced", description: "All dimensions within 10% — healthy equilibrium." };
    if (avg >= 0.5) return { label: "Flat", description: "All three dimensions score below 70%." };
    return { label: "Flat", description: "All three dimensions score below 50%." };
  }

  const dominant = e >= l && e >= p ? "Ethos" : l >= e && l >= p ? "Logos" : "Pathos";
  const weakest = e <= l && e <= p ? "ethos" : l <= e && l <= p ? "logos" : "pathos";
  if (avg < 0.5) {
    return {
      label: `${dominant}-heavy`,
      description: `Skewed toward ${dominant.toLowerCase()}, with critical weakness in ${weakest}.`,
    };
  }
  return {
    label: `${dominant}-heavy`,
    description: `Skewed toward ${dominant.toLowerCase()}. May lack in other dimensions.`,
  };
}

interface DimensionBalanceProps {
  dimensionAverages: Record<string, number>;
  title?: string;
}

export default function DimensionBalance({
  dimensionAverages,
  title = "Dimension Balance",
}: DimensionBalanceProps) {
  const classification = classifyBalance(dimensionAverages);

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
          <p className="mt-0.5 text-sm text-foreground/60">
            Ethos, logos, and pathos relative to each other.
          </p>
        </div>
        <span className="rounded-full bg-action-light px-3 py-1 text-xs font-medium text-action">
          {classification.label}
        </span>
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
