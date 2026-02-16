"use client";

import { useMemo } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { fadeUp, staggerContainer } from "../../lib/motion";
import type { AgentSummary, TraitScore } from "../../lib/types";
import { getGrade, GRADE_COLORS, spectrumLabel } from "../../lib/colors";
import RadarChart from "../shared/RadarChart";

const AVATAR_COLORS = [
  "var(--ethos-500)",
  "var(--logos-600)",
  "var(--pathos-400)",
  "var(--ethos-700)",
  "var(--logos-400)",
  "var(--pathos-600)",
];

function avatarColor(id: string): string {
  let hash = 0;
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) | 0;
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

function getInitials(name: string): string {
  return name
    .split(/[\s_-]+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

function getOverallScore(dims: Record<string, number>): number {
  const vals = Object.values(dims);
  if (vals.length === 0) return 0;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

function toTraitScores(averages: Record<string, number>): Record<string, TraitScore> {
  return Object.fromEntries(
    Object.entries(averages).map(([name, score]) => [
      name,
      { name, score, dimension: "", polarity: "", indicators: [] },
    ])
  );
}

function ShowcaseCard({ agent }: { agent: AgentSummary }) {
  const displayName = agent.agentName || agent.agentId;
  const initials = getInitials(displayName);
  const bg = avatarColor(agent.agentId);
  const hasTraits = Object.keys(agent.traitAverages || {}).length > 0;
  const traits = useMemo(() => toTraitScores(agent.traitAverages || {}), [agent.traitAverages]);
  const overallScore = getOverallScore(agent.dimensionAverages ?? {});
  const statusLabel = agent.evaluationCount > 0 ? spectrumLabel(overallScore) : "Unknown";
  const grade = agent.evaluationCount > 0 ? getGrade(overallScore) : null;
  const gradeColor = grade ? GRADE_COLORS[grade] ?? "#64748b" : "#64748b";
  const overallPct = Math.round(overallScore * 100);

  return (
    <motion.div variants={fadeUp}>
      <Link
        href={`/agent/${encodeURIComponent(agent.agentId)}`}
        className="group relative flex h-[300px] flex-col overflow-hidden rounded-2xl border border-white/30 bg-white/40 backdrop-blur-2xl p-4 shadow-sm transition-all hover:shadow-xl hover:border-action/30 hover:bg-white/60"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 min-w-0">
            {grade ? (
              <div className="relative flex h-9 w-9 shrink-0 items-center justify-center">
                <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="#e5e7eb" strokeWidth="7" />
                  <circle
                    cx="50" cy="50" r="42" fill="none"
                    stroke={gradeColor} strokeWidth="7" strokeLinecap="round"
                    strokeDasharray={`${overallPct * 2.64} 264`}
                    transform="rotate(-90 50 50)"
                  />
                </svg>
                <span className="text-xs font-bold" style={{ color: gradeColor }}>{grade}</span>
              </div>
            ) : (
              <div
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-[10px] font-bold text-surface shadow-sm"
                style={{ backgroundColor: bg }}
              >
                {initials}
              </div>
            )}
            <div className="min-w-0">
              <h3 className="truncate text-sm font-semibold text-foreground group-hover:text-action transition-colors">
                {displayName}
              </h3>
              <p className="text-[10px] text-muted/70">
                {statusLabel} &middot; {agent.evaluationCount} evals
              </p>
            </div>
          </div>
        </div>
        <div className="flex-1 min-h-0">
          {hasTraits ? (
            <RadarChart traits={traits} compact />
          ) : (
            <div className="flex h-full items-center justify-center">
              <p className="text-xs text-muted/50 italic">No trait data yet</p>
            </div>
          )}
        </div>
      </Link>
    </motion.div>
  );
}

export default function AlumniShowcase({ agents }: { agents: AgentSummary[] }) {
  // Pick 6 agents with the most evaluations and actual trait data
  const showcaseAgents = useMemo(() => {
    const withTraits = agents.filter(
      (a) => a.evaluationCount > 0 && Object.keys(a.traitAverages || {}).length > 0
    );
    withTraits.sort((a, b) => b.evaluationCount - a.evaluationCount);
    return withTraits.slice(0, 6);
  }, [agents]);

  if (showcaseAgents.length === 0) return null;

  return (
    <section className="relative overflow-hidden bg-[#faf8f5] py-20 sm:py-28">
      <div className="relative mx-auto max-w-6xl px-6">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          variants={staggerContainer}
        >
          <motion.div variants={fadeUp} className="mb-12 text-center">
            <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl lg:text-4xl">
              Alumni
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-base text-muted sm:text-lg">
              Every enrolled agent builds a character profile across 12 behavioral traits.
            </p>
          </motion.div>
          <motion.div
            className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
            variants={staggerContainer}
          >
            {showcaseAgents.map((agent) => (
              <ShowcaseCard key={agent.agentId} agent={agent} />
            ))}
          </motion.div>
          <motion.div variants={fadeUp} className="mt-10 text-center">
            <Link
              href="/alumni"
              className="inline-block rounded-xl border border-border/60 bg-surface/80 backdrop-blur-xl px-6 py-3 text-sm font-medium text-foreground transition-all hover:border-action hover:text-action hover:shadow-md"
            >
              View all alumni &rarr;
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
