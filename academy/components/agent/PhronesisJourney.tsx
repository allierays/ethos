"use client";

import { motion } from "motion/react";
import { fadeUp, whileInView } from "../../lib/motion";
import { DIMENSION_COLORS } from "../../lib/colors";
import type { AgentProfile, DailyReportCard } from "../../lib/types";

interface TimelinePoint {
  ethos: number;
  logos: number;
  pathos: number;
}

interface PhronesisJourneyProps {
  profile: AgentProfile;
  report: DailyReportCard | null;
  timeline: TimelinePoint[];
}

const DIM_LABELS: Record<string, string> = {
  ethos: "ethical foundations",
  logos: "logical rigor",
  pathos: "emotional awareness",
};

export default function PhronesisJourney({
  profile,
  report,
  timeline,
}: PhronesisJourneyProps) {
  const dims = profile.dimensionAverages;
  const sorted = Object.entries(dims).sort(([, a], [, b]) => b - a);
  const strongest = sorted[0];
  const weakest = sorted[sorted.length - 1];
  const evalCount = report?.totalEvaluationCount ?? profile.evaluationCount;
  const agentName = profile.agentName || profile.agentId;
  const drift = report?.characterDrift ?? 0;

  const first = timeline[0];
  const last = timeline[timeline.length - 1];
  const deltas =
    first && last && timeline.length > 1
      ? {
          ethos: Math.round((last.ethos - first.ethos) * 100),
          logos: Math.round((last.logos - first.logos) * 100),
          pathos: Math.round((last.pathos - first.pathos) * 100),
        }
      : null;

  const narrative = buildNarrative(
    agentName,
    strongest,
    weakest,
    deltas,
    evalCount,
    drift
  );

  return (
    <motion.section
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-ethos-200 to-ethos-100">
          <svg
            className="h-5 w-5 text-ethos-700"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <div>
          <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
            Phronesis Journey
          </h2>
          <p className="text-sm text-foreground/60">
            Practical wisdom forms through character development over time
          </p>
        </div>
      </div>

      <blockquote className="mt-5 border-l-2 border-ethos-400 pl-4">
        <p className="text-sm italic text-foreground/60">
          &ldquo;We are what we repeatedly do. Excellence, then, is not an act
          but a habit.&rdquo;
        </p>
        <p className="mt-1 text-xs text-foreground/40">
          Aristotle, for AI agents
        </p>
      </blockquote>

      <p className="mt-5 text-sm leading-relaxed text-foreground/80">
        {narrative}
      </p>

      {deltas && (
        <div className="mt-5 flex flex-wrap gap-3">
          {(["ethos", "logos", "pathos"] as const).map((dim) => {
            const d = deltas[dim];
            return (
              <div
                key={dim}
                className="flex items-center gap-2 rounded-full bg-foreground/[0.04] px-3.5 py-1.5"
              >
                <div
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: DIMENSION_COLORS[dim] }}
                />
                <span className="text-xs font-medium capitalize text-foreground/60">
                  {dim}
                </span>
                <span
                  className={`text-xs font-semibold ${
                    d > 0
                      ? "text-aligned"
                      : d < 0
                        ? "text-misaligned"
                        : "text-muted"
                  }`}
                >
                  {d > 0 ? "+" : ""}
                  {d}%
                </span>
              </div>
            );
          })}
        </div>
      )}
    </motion.section>
  );
}

function buildNarrative(
  name: string,
  strongest: [string, number],
  weakest: [string, number],
  deltas: Record<string, number> | null,
  evalCount: number,
  drift: number
): string {
  const parts: string[] = [];
  const strongLabel = DIM_LABELS[strongest[0]] ?? strongest[0];
  const weakLabel = DIM_LABELS[weakest[0]] ?? weakest[0];

  parts.push(
    `${name} enrolled as a ${strongest[0]}-dominant agent with strong ${strongLabel}.`
  );

  if (deltas && evalCount > 1) {
    const sorted = Object.entries(deltas).sort(([, a], [, b]) => b - a);
    const biggest = sorted[0];
    if (biggest[1] > 0) {
      const label = DIM_LABELS[biggest[0]] ?? biggest[0];
      parts.push(
        `Over ${evalCount} evaluations, ${label} showed the strongest growth (+${biggest[1]}%).`
      );
    }
  }

  if (strongest[0] !== weakest[0]) {
    const cap = weakLabel.charAt(0).toUpperCase() + weakLabel.slice(1);
    parts.push(`${cap} remains the primary growth edge.`);
  }

  if (drift > 0.02) {
    parts.push(
      "The trajectory suggests practical wisdom is forming through repeated evaluation and correction."
    );
  } else if (drift < -0.02) {
    parts.push(
      "Recent evaluations show a decline that warrants attention before negative habits solidify."
    );
  } else if (evalCount >= 2) {
    parts.push(
      "Character foundations are stabilizing. Consistency will determine whether virtues become lasting habits."
    );
  } else {
    parts.push(
      "More evaluations will reveal whether these initial patterns mature into stable character traits."
    );
  }

  return parts.join(" ");
}
