"use client";

import { useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
  ReferenceArea,
  ReferenceLine,
} from "recharts";
import { motion, AnimatePresence } from "motion/react";
import { DIMENSION_COLORS, DIMENSION_LABELS } from "../../lib/colors";
import { fadeUp, whileInView } from "../../lib/motion";
import type { DriftBreakpoint, EvaluationHistoryItem } from "../../lib/types";
import GraphHelpButton from "../shared/GraphHelpButton";
import GlossaryTerm from "../shared/GlossaryTerm";

/* ─── Trait habit definitions (consolidated from VirtueHabits) ─── */

interface TraitDef {
  key: string;
  slug: string;
  label: string;
  dimension: string;
  polarity: "positive" | "negative";
}

const TRAITS: TraitDef[] = [
  { key: "virtue", slug: "virtue", label: "Virtue", dimension: "ethos", polarity: "positive" },
  { key: "goodwill", slug: "goodwill", label: "Goodwill", dimension: "ethos", polarity: "positive" },
  { key: "deception", slug: "deception", label: "Non-deception", dimension: "ethos", polarity: "negative" },
  { key: "manipulation", slug: "manipulation", label: "Non-manipulation", dimension: "ethos", polarity: "negative" },
  { key: "accuracy", slug: "accuracy", label: "Accuracy", dimension: "logos", polarity: "positive" },
  { key: "reasoning", slug: "reasoning", label: "Reasoning", dimension: "logos", polarity: "positive" },
  { key: "fabrication", slug: "fabrication", label: "Non-fabrication", dimension: "logos", polarity: "negative" },
  { key: "brokenLogic", slug: "broken-logic", label: "Sound Logic", dimension: "logos", polarity: "negative" },
  { key: "recognition", slug: "recognition", label: "Recognition", dimension: "pathos", polarity: "positive" },
  { key: "compassion", slug: "compassion", label: "Compassion", dimension: "pathos", polarity: "positive" },
  { key: "dismissal", slug: "dismissal", label: "Non-dismissal", dimension: "pathos", polarity: "negative" },
  { key: "exploitation", slug: "exploitation", label: "Non-exploitation", dimension: "pathos", polarity: "negative" },
];

type HabitStatus = "established" | "forming" | "emerging" | "needs_work" | "insufficient";

const STATUS_CONFIG: Record<HabitStatus, { label: string; dotClass: string }> = {
  established: { label: "Established", dotClass: "bg-aligned" },
  forming: { label: "Forming", dotClass: "bg-ethos-400" },
  emerging: { label: "Emerging", dotClass: "bg-drifting" },
  needs_work: { label: "Needs work", dotClass: "bg-misaligned/60" },
  insufficient: { label: "Building...", dotClass: "bg-foreground/20" },
};

function computeHabit(
  rawScores: number[],
  polarity: "positive" | "negative"
): { status: HabitStatus; strength: number; trend: number; scores: number[] } {
  const scores = rawScores.map((s) => (polarity === "negative" ? 1 - s : s));

  if (scores.length < 2) {
    const s = scores[0] ?? 0.5;
    return { status: "insufficient", strength: s, trend: 0, scores };
  }

  const trend = scores[scores.length - 1] - scores[0];
  const solidCount = scores.filter((s) => s >= 0.7).length;
  const allSolid = solidCount === scores.length;

  let status: HabitStatus;
  if (allSolid) {
    status = "established";
  } else if (trend > 0.03) {
    status = "forming";
  } else if (solidCount > 0) {
    status = "emerging";
  } else {
    status = "needs_work";
  }

  return { status, strength: scores[scores.length - 1], trend, scores };
}

/** Map a 0-1 score to 4 opacity levels (GitHub contribution style). */
function scoreToLevel(score: number): number {
  if (score >= 0.85) return 1;
  if (score >= 0.7) return 0.7;
  if (score >= 0.5) return 0.4;
  return 0.15;
}

const MAX_SQUARES = 10;

/* ─── Component types ─── */

interface TimelineDataPoint {
  index: number;
  createdAt: string;
  ethos: number;
  logos: number;
  pathos: number;
  flags: string[];
  alignmentStatus: string;
}

interface TranscriptChartProps {
  timeline: TimelineDataPoint[];
  agentName?: string;
  breakpoints?: DriftBreakpoint[];
  history?: EvaluationHistoryItem[];
}

export default function TranscriptChart({ timeline, agentName, breakpoints = [], history = [] }: TranscriptChartProps) {
  const name = agentName ?? "this agent";
  const flaggedPoints = timeline.filter((d) => d.flags.length > 0);
  const [expandedDim, setExpandedDim] = useState<string | null>(null);

  const first = timeline[0];
  const last = timeline[timeline.length - 1];
  const dims = [
    { key: "ethos" as const, label: "Integrity (Ethos)", color: DIMENSION_COLORS.ethos },
    { key: "logos" as const, label: "Logic (Logos)", color: DIMENSION_COLORS.logos },
    { key: "pathos" as const, label: "Empathy (Pathos)", color: DIMENSION_COLORS.pathos },
  ];

  // Compute trait habits from history (same logic as VirtueHabits)
  const chronological = [...history].reverse();
  const habits = TRAITS.map((trait) => {
    const rawScores = chronological
      .map((e) => e.traitScores?.[trait.key])
      .filter((s): s is number => s !== undefined && s !== null);
    const { status, strength, trend, scores } = computeHabit(rawScores, trait.polarity);
    return { trait, status, strength, trend, scores };
  });

  return (
    <motion.section
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
            Evaluation Over Time
          </h2>
          <p className="mt-0.5 text-sm text-foreground/60">
            We are what we repeatedly do. These messages mark the peaks and valleys of character.
          </p>
        </div>
        <GraphHelpButton slug="guide-transcript" />
      </div>

      {timeline.length === 0 ? (
        <div className="mt-8 flex h-48 items-center justify-center text-sm text-muted">
          No evaluation history for {name} yet.
        </div>
      ) : (
        <>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeline}>
                <defs>
                  <linearGradient id="gradEthos" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={DIMENSION_COLORS.ethos} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={DIMENSION_COLORS.ethos} stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="gradLogos" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={DIMENSION_COLORS.logos} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={DIMENSION_COLORS.logos} stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="gradPathos" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={DIMENSION_COLORS.pathos} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={DIMENSION_COLORS.pathos} stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <ReferenceArea y1={0} y2={0.5} fill="#ef4444" fillOpacity={0.03} />
                <XAxis
                  dataKey="index"
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  tickLine={false}
                  axisLine={{ stroke: "#e2e8f0" }}
                  label={{ value: "Evaluation", position: "insideBottom", offset: -2, fontSize: 10, fill: "#94a3b8" }}
                />
                <YAxis
                  domain={[0, 1]}
                  ticks={[0, 0.25, 0.5, 0.75, 1]}
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  tickLine={false}
                  axisLine={{ stroke: "#e2e8f0" }}
                  width={32}
                />
                <Tooltip
                  content={({ active, label }) => {
                    if (!active || label == null) return null;
                    const point = timeline.find((d) => d.index === label);
                    if (!point) return null;
                    const prev = timeline.find((d) => d.index === Number(label) - 1);
                    const delta = (key: "ethos" | "logos" | "pathos") => {
                      if (!prev) return "";
                      const d = Math.round((point[key] - prev[key]) * 100);
                      if (d === 0) return "";
                      return d > 0 ? ` (+${d}%)` : ` (${d}%)`;
                    };
                    return (
                      <div className="rounded-xl border border-white/30 bg-white/80 px-4 py-3 text-xs shadow-lg backdrop-blur-md">
                        <p className="font-semibold text-[#1a2538]">Evaluation #{label}</p>
                        <div className="mt-2 space-y-1">
                          {dims.map((dim) => {
                            const pct = Math.round(point[dim.key] * 100);
                            return (
                              <div key={dim.key} className="flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: dim.color }} />
                                <span className="text-foreground/70">{dim.label}</span>
                                <span className="ml-auto font-semibold text-[#1a2538]">{pct}%</span>
                                <span className={`text-[10px] ${delta(dim.key).includes("+") ? "text-aligned" : delta(dim.key).includes("-") ? "text-misaligned" : "text-muted"}`}>
                                  {delta(dim.key)}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                        <div className="mt-2 border-t border-border/30 pt-2">
                          <p className="text-[10px] leading-relaxed text-foreground/60">
                            {(() => {
                              const parts: string[] = [];
                              const eDelta = prev ? Math.round((point.ethos - prev.ethos) * 100) : 0;
                              const lDelta = prev ? Math.round((point.logos - prev.logos) * 100) : 0;
                              const pDelta = prev ? Math.round((point.pathos - prev.pathos) * 100) : 0;
                              const bigDrop = [
                                eDelta < -5 && "character",
                                lDelta < -5 && "reasoning",
                                pDelta < -5 && "empathy",
                              ].filter(Boolean);
                              const bigGain = [
                                eDelta > 5 && "character",
                                lDelta > 5 && "reasoning",
                                pDelta > 5 && "empathy",
                              ].filter(Boolean);
                              if (bigDrop.length > 0) parts.push(`${bigDrop.join(" and ")} dropped`);
                              if (bigGain.length > 0) parts.push(`${bigGain.join(" and ")} improved`);
                              if (parts.length === 0 && prev) parts.push("Scores held steady");
                              if (!prev) parts.push("First evaluation");
                              const low = Math.min(point.ethos, point.logos, point.pathos);
                              if (low < 0.5) parts.push("empathy needs attention");
                              return parts.join(". ") + ".";
                            })()}
                          </p>
                        </div>
                      </div>
                    );
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="ethos"
                  stroke={DIMENSION_COLORS.ethos}
                  strokeWidth={2.5}
                  fill="url(#gradEthos)"
                  dot={{ r: 4, fill: DIMENSION_COLORS.ethos, stroke: "#fff", strokeWidth: 2 }}
                  activeDot={{ r: 6, stroke: DIMENSION_COLORS.ethos, strokeWidth: 2, fill: "#fff" }}
                  name="Integrity (Ethos)"
                />
                <Area
                  type="monotone"
                  dataKey="logos"
                  stroke={DIMENSION_COLORS.logos}
                  strokeWidth={2.5}
                  fill="url(#gradLogos)"
                  dot={{ r: 4, fill: DIMENSION_COLORS.logos, stroke: "#fff", strokeWidth: 2 }}
                  activeDot={{ r: 6, stroke: DIMENSION_COLORS.logos, strokeWidth: 2, fill: "#fff" }}
                  name="Logic (Logos)"
                />
                <Area
                  type="monotone"
                  dataKey="pathos"
                  stroke={DIMENSION_COLORS.pathos}
                  strokeWidth={2.5}
                  fill="url(#gradPathos)"
                  dot={{ r: 4, fill: DIMENSION_COLORS.pathos, stroke: "#fff", strokeWidth: 2 }}
                  activeDot={{ r: 6, stroke: DIMENSION_COLORS.pathos, strokeWidth: 2, fill: "#fff" }}
                  name="Empathy (Pathos)"
                />
                {flaggedPoints.map((point) => (
                  <ReferenceDot
                    key={`flag-${point.index}`}
                    x={point.index}
                    y={Math.min(point.ethos, point.logos, point.pathos)}
                    r={5}
                    fill="#ef4444"
                    stroke="white"
                    strokeWidth={2}
                  />
                ))}
                {breakpoints.map((bp) => (
                  <ReferenceLine
                    key={`drift-${bp.evalIndex}-${bp.dimension}`}
                    x={bp.evalIndex}
                    stroke="#dc2626"
                    strokeWidth={2}
                    strokeDasharray="4 3"
                    strokeOpacity={0.7}
                    label={{
                      value: `${bp.delta > 0 ? "+" : ""}${(bp.delta * 100).toFixed(0)}% ${(DIMENSION_LABELS[bp.dimension] ?? bp.dimension).toLowerCase()}`,
                      position: "top",
                      fill: "#dc2626",
                      fontSize: 9,
                      fontWeight: 600,
                    }}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Dimension summary cards with expandable trait habits */}
          {first && last && (
            <div className="mt-4 grid grid-cols-3 gap-3">
              {dims.map((dim) => {
                const latest = last[dim.key];
                const delta = timeline.length > 1 ? last[dim.key] - first[dim.key] : 0;
                const pct = Math.round(latest * 100);
                const deltaPct = Math.round(delta * 100);
                const isExpanded = expandedDim === dim.key;
                const dimHabits = habits.filter((h) => h.trait.dimension === dim.key);
                const hasHabits = history.length > 0;
                return (
                  <div
                    key={dim.key}
                    className="rounded-lg glass overflow-hidden transition-shadow"
                    style={{
                      borderLeft: `3px solid ${dim.color}`,
                      boxShadow: isExpanded ? `0 0 0 1px ${dim.color}25` : undefined,
                    }}
                  >
                    <button
                      type="button"
                      className="w-full p-3 text-center transition-colors hover:bg-foreground/[0.02] cursor-pointer"
                      onClick={() => hasHabits && setExpandedDim(isExpanded ? null : dim.key)}
                    >
                      <p className="text-[10px] uppercase tracking-wider text-muted">
                        {dim.label}
                      </p>
                      <p className="mt-1 text-lg font-bold text-[#1a2538]">
                        {pct}%
                      </p>
                      {timeline.length > 1 && (
                        <p
                          className={`text-xs font-medium ${
                            delta > 0.01
                              ? "text-aligned"
                              : delta < -0.01
                              ? "text-misaligned"
                              : "text-muted"
                          }`}
                        >
                          {delta > 0 ? "+" : ""}
                          {deltaPct}%
                        </p>
                      )}
                      <div
                        className="mx-auto mt-1.5 h-1 w-full max-w-[60px] rounded-full"
                        style={{ backgroundColor: `${dim.color}20` }}
                      >
                        <div
                          className="h-1 rounded-full transition-all"
                          style={{
                            width: `${pct}%`,
                            backgroundColor: dim.color,
                          }}
                        />
                      </div>
                      {hasHabits && (
                        <p className="mt-2 text-[10px] text-foreground/40 flex items-center justify-center gap-1">
                          <svg
                            className={`h-2.5 w-2.5 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                            viewBox="0 0 12 12"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                          >
                            <path d="M3 5l3 3 3-3" />
                          </svg>
                          4 traits
                        </p>
                      )}
                    </button>
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="px-3 pb-3 pt-2 space-y-3" style={{ borderTop: `1px solid ${dim.color}20` }}>
                            {dimHabits.map((habit) => {
                              const config = STATUS_CONFIG[habit.status];
                              const visible = habit.scores.slice(-MAX_SQUARES);
                              const emptyCount = Math.max(0, MAX_SQUARES - visible.length);
                              return (
                                <div key={habit.trait.key}>
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-1.5">
                                      <span
                                        className="h-1.5 w-1.5 rounded-full"
                                        style={{ backgroundColor: dim.color }}
                                      />
                                      <span className="text-xs text-[#1a2538]">
                                        <GlossaryTerm slug={habit.trait.slug}>{habit.trait.label}</GlossaryTerm>
                                      </span>
                                    </div>
                                    <span className="text-[10px] font-medium text-foreground/40">
                                      {config.label}
                                    </span>
                                  </div>
                                  <div className="mt-1 flex gap-[2px]">
                                    {visible.map((score, i) => (
                                      <div
                                        key={i}
                                        className="h-[10px] w-[10px] rounded-[2px]"
                                        style={{
                                          backgroundColor: dim.color,
                                          opacity: scoreToLevel(score),
                                        }}
                                        title={`Eval ${habit.scores.length - visible.length + i + 1}: ${Math.round(score * 100)}%`}
                                      />
                                    ))}
                                    {Array.from({ length: emptyCount }).map((_, i) => (
                                      <div
                                        key={`empty-${i}`}
                                        className="h-[10px] w-[10px] rounded-[2px] bg-foreground/[0.04] border border-foreground/[0.06]"
                                      />
                                    ))}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      <div className="mt-3 flex items-center gap-4 text-xs text-muted">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded bg-ethos-500" /> Integrity (Ethos)
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded bg-logos-500" /> Logic (Logos)
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded bg-pathos-500" /> Empathy (Pathos)
        </span>
        {flaggedPoints.length > 0 && (
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-misaligned" />{" "}
            Flagged
          </span>
        )}
        {breakpoints.length > 0 && (
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-4 border-l-2 border-dashed border-[#dc2626]" />{" "}
            Drift breakpoint
          </span>
        )}
      </div>

      {/* Drift breakpoint details */}
      {breakpoints.length > 0 && (
        <div className="mt-3 rounded-lg bg-misaligned/5 border border-misaligned/10 px-4 py-3">
          <p className="text-xs font-semibold text-misaligned/80 uppercase tracking-wider mb-2">
            Character Drift Detected
          </p>
          <div className="space-y-1.5">
            {breakpoints.map((bp, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="font-mono text-misaligned">#{bp.evalIndex}</span>
                <span className="text-foreground/70">
                  {(DIMENSION_LABELS[bp.dimension] ?? bp.dimension)} {bp.delta < 0 ? "dropped" : "rose"}{" "}
                  <span className="font-semibold">{Math.abs(Math.round(bp.delta * 100))}%</span>
                  {" "}({(bp.beforeAvg * 100).toFixed(0)}% &rarr; {(bp.afterAvg * 100).toFixed(0)}%)
                </span>
                {bp.indicators.length > 0 && (
                  <span className="text-muted ml-auto truncate max-w-[200px]">
                    {bp.indicators.slice(0, 3).join(", ")}
                  </span>
                )}
              </div>
            ))}
          </div>
          <p className="mt-2 text-[10px] text-foreground/40">
            Breakpoints use a 5-evaluation sliding window. Only the PRECEDES linked list in Neo4j
            guarantees temporal chain integrity at scale.
          </p>
        </div>
      )}
    </motion.section>
  );
}
