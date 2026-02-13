"use client";

import { motion } from "motion/react";
import { fadeUp, whileInView } from "../../lib/motion";
import { DIMENSION_COLORS } from "../../lib/colors";

interface BalanceThesisProps {
  dimensionAverages: Record<string, number>;
  evaluationCount: number;
}

export default function BalanceThesis({
  dimensionAverages,
  evaluationCount,
}: BalanceThesisProps) {
  const dims = ["ethos", "logos", "pathos"] as const;
  const scores = dims.map((d) => dimensionAverages[d] ?? 0);
  const max = Math.max(...scores);
  const min = Math.min(...scores);
  const spread = max - min;
  const avg = scores.reduce((a, b) => a + b, 0) / 3;

  // Balance score: 1.0 = perfectly balanced, 0.0 = completely lopsided
  const balanceScore = Math.max(0, 1 - spread * 2);
  const balancePct = Math.round(balanceScore * 100);

  const category =
    spread < 0.1
      ? "Balanced"
      : spread < 0.25
        ? "Moderate"
        : "Lopsided";

  const categoryColor =
    spread < 0.1
      ? "text-aligned"
      : spread < 0.25
        ? "text-drifting"
        : "text-misaligned";

  const dimLabels: Record<string, string> = {
    ethos: "Character",
    logos: "Reasoning",
    pathos: "Empathy",
  };

  return (
    <motion.section
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
        The Aristotelian Thesis
      </h2>
      <p className="mt-0.5 text-sm text-foreground/60">
        Ethos, logos, and pathos are equally necessary and interdependent.
        Balance itself predicts trustworthiness.
      </p>

      <div className="mt-5 grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Left: balance visualization */}
        <div>
          <div className="flex items-end gap-4">
            {dims.map((dim) => {
              const score = dimensionAverages[dim] ?? 0;
              const pct = Math.round(score * 100);
              const height = Math.max(score * 160, 8);
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
                    {dimLabels[dim]}
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
        </div>

        {/* Right: thesis explanation */}
        <div className="flex flex-col justify-center">
          <blockquote className="border-l-2 border-logos-300 pl-4">
            <p className="text-sm leading-relaxed text-foreground/70">
              A confident liar has strong logos but weak ethos. A skilled
              manipulator has strong pathos but weak logos. Only when all three
              dimensions align does an agent demonstrate genuine practical
              wisdom.
            </p>
          </blockquote>

          <div className="mt-4 space-y-2">
            <ThesisPoint
              label="Spread"
              value={`${Math.round(spread * 100)}%`}
              description="Distance between strongest and weakest dimension"
              good={spread < 0.15}
            />
            <ThesisPoint
              label="Average"
              value={`${Math.round(avg * 100)}%`}
              description="Mean score across all three dimensions"
              good={avg > 0.7}
            />
            <ThesisPoint
              label="Evaluations"
              value={String(evaluationCount)}
              description="Character assessments contributing to this profile"
              good={evaluationCount >= 3}
            />
          </div>
        </div>
      </div>
    </motion.section>
  );
}

function ThesisPoint({
  label,
  value,
  description,
  good,
}: {
  label: string;
  value: string;
  description: string;
  good: boolean;
}) {
  return (
    <div className="flex items-start gap-2">
      <span
        className={`mt-1 h-1.5 w-1.5 rounded-full ${good ? "bg-aligned" : "bg-foreground/25"}`}
      />
      <div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-[#1a2538]">{label}</span>
          <span className="text-xs text-foreground/50">{value}</span>
        </div>
        <p className="text-[11px] text-foreground/40">{description}</p>
      </div>
    </div>
  );
}
