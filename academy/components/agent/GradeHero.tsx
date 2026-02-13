"use client";

import { useMemo } from "react";
import { motion } from "motion/react";
import type { AgentProfile, DailyReportCard } from "../../lib/types";
import { GRADE_COLORS, RISK_STYLES, TREND_DISPLAY, DIMENSION_COLORS, DIMENSION_LABELS, getGrade } from "../../lib/colors";
import { formatClassOf } from "../../lib/academic";
import { fadeUp, staggerContainer } from "../../lib/motion";
import GlossaryTerm from "../shared/GlossaryTerm";
import GraphHelpButton from "../shared/GraphHelpButton";

interface TimelinePoint {
  ethos: number;
  logos: number;
  pathos: number;
}

const DIM_LABELS = Object.fromEntries(
  Object.entries(DIMENSION_LABELS).map(([k, v]) => [k, v.toLowerCase()])
);

interface GradeHeroProps {
  profile: AgentProfile;
  report: DailyReportCard | null;
  timeline?: TimelinePoint[];
}

export default function GradeHero({ profile, report, timeline = [] }: GradeHeroProps) {
  const latestAlignment =
    profile.alignmentHistory?.[profile.alignmentHistory.length - 1] ?? "unknown";
  const classOf = formatClassOf(profile.createdAt);

  const {
    phronesisScore, grade, gradeColor, overallPct, trend, riskLevel, riskStyle,
    agentName, evalCount, deltas, narrativeEl, bodyText,
  } = useMemo(() => {
    const dims = profile.dimensionAverages;
    const _phronesisScore = Math.round(
      (((dims.ethos ?? 0) + (dims.logos ?? 0) + (dims.pathos ?? 0)) / 3) * 100
    );

    // Compute grade from report or from profile dimension averages
    const reportGrade = report?.grade ?? null;
    const _grade = reportGrade || getGrade(_phronesisScore / 100);
    const _gradeColor = GRADE_COLORS[_grade] ?? "#64748b";
    const _overallPct = report ? Math.round(report.overallScore * 100) : _phronesisScore;
    const _trend = report?.trend
      ? TREND_DISPLAY[report.trend] ?? TREND_DISPLAY.insufficient_data
      : TREND_DISPLAY[profile.phronesisTrend] ?? TREND_DISPLAY.insufficient_data;
    const _riskLevel = report?.riskLevel ?? "low";
    const _riskStyle = RISK_STYLES[_riskLevel] ?? RISK_STYLES.low;

    // Build narrative + deltas for the unified text section
    const _agentName = profile.agentName || profile.agentId;
    const sorted = Object.entries(dims).sort(([, a], [, b]) => b - a);
    const strongest = sorted[0];
    const weakest = sorted[sorted.length - 1];
    const _evalCount = report?.totalEvaluationCount ?? profile.evaluationCount;
    const drift = report?.characterDrift ?? 0;

    const first = timeline[0];
    const last = timeline[timeline.length - 1];
    const _deltas =
      first && last && timeline.length > 1
        ? {
            ethos: Math.round((last.ethos - first.ethos) * 100),
            logos: Math.round((last.logos - first.logos) * 100),
            pathos: Math.round((last.pathos - first.pathos) * 100),
          }
        : null;

    const _narrativeEl =
      strongest && weakest
        ? buildNarrative(_agentName, strongest, weakest, _deltas, _evalCount, drift)
        : null;

    // Use report summary if available, otherwise fall back to narrative
    const _bodyText = report?.summary ?? null;

    return {
      phronesisScore: _phronesisScore,
      grade: _grade,
      gradeColor: _gradeColor,
      overallPct: _overallPct,
      trend: _trend,
      riskLevel: _riskLevel,
      riskStyle: _riskStyle,
      agentName: _agentName,
      evalCount: _evalCount,
      deltas: _deltas,
      narrativeEl: _narrativeEl,
      bodyText: _bodyText,
    };
  }, [profile, report, timeline]);

  return (
    <section className="bg-[#1a2538] text-white">
      <div className="mx-auto max-w-7xl px-6 py-10 sm:px-10 sm:py-14">
        <motion.div
          className="flex flex-col gap-8 sm:flex-row sm:items-center sm:justify-between"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {/* Left: Grade ring + identity */}
          <motion.div className="flex items-start gap-6" variants={fadeUp}>
            {grade ? (
              <div className="relative flex h-24 w-24 shrink-0 items-center justify-center">
                <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="#334155" strokeWidth="6" />
                  <circle
                    cx="50" cy="50" r="42" fill="none"
                    stroke={gradeColor} strokeWidth="6" strokeLinecap="round"
                    strokeDasharray={`${(overallPct ?? 0) * 2.64} 264`}
                    transform="rotate(-90 50 50)"
                    className="transition-all duration-1000"
                  />
                </svg>
                <span className="text-3xl font-bold" style={{ color: gradeColor }}>{grade}</span>
              </div>
            ) : (
              <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-full border-2 border-slate-600">
                <span className="text-sm text-slate-400">N/A</span>
              </div>
            )}

            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="bg-gradient-to-r from-ethos-300 via-logos-300 to-pathos-300 bg-clip-text text-3xl font-bold tracking-tight text-transparent sm:text-4xl">
                  {agentName}
                </h1>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold capitalize ${
                    latestAlignment === "aligned"
                      ? "bg-emerald-500/20 text-emerald-400"
                      : latestAlignment === "drifting"
                      ? "bg-amber-500/20 text-amber-400"
                      : latestAlignment === "misaligned"
                      ? "bg-red-500/20 text-red-400"
                      : "bg-slate-500/20 text-slate-400"
                  }`}
                >
                  <GlossaryTerm slug="alignment-status">{latestAlignment}</GlossaryTerm>
                </span>
              </div>
              {classOf && <p className="mt-1.5 text-sm text-slate-400">{classOf}</p>}
            </div>
          </motion.div>

          {/* Right: stat cards + help */}
          <motion.div className="flex items-start gap-3" variants={fadeUp}>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label={<GlossaryTerm slug="phronesis">Character</GlossaryTerm>} value={`${phronesisScore}%`} />
            <StatCard
              label="Trend" value={trend.arrow} sublabel={trend.label}
              valueClass={trend.color === "text-aligned" ? "text-emerald-400" : trend.color === "text-misaligned" ? "text-red-400" : "text-slate-400"}
            />
            <StatCard label="Evaluations" value={String(evalCount)} />
            <StatCard
              label="Risk" value={riskLevel}
              valueClass={`capitalize text-xs font-semibold rounded-full px-2 py-0.5 ${riskStyle}`}
              isRiskBadge
            />
          </div>
          <GraphHelpButton slug="guide-grade-hero" />
          </motion.div>
        </motion.div>

        {/* Unified text section: summary or narrative + dimension deltas */}
        {(bodyText || deltas) && (
          <motion.div
            className="mt-8 rounded-xl border border-white/15 bg-white/5 px-6 py-6 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
          >
            {(bodyText || narrativeEl) && (
              <p className="text-lg font-medium leading-relaxed text-white/80 sm:text-xl">
                {bodyText ?? narrativeEl}
              </p>
            )}

            {deltas && (
              <div className="mt-4 flex flex-wrap gap-3">
                {(["ethos", "logos", "pathos"] as const).map((dim) => {
                  const d = deltas[dim];
                  const plainLabel = DIM_LABELS[dim] ?? dim;
                  return (
                    <div key={dim} className="flex items-center gap-2 rounded-full bg-white/20 px-3.5 py-1.5">
                      <div className="h-2 w-2 rounded-full" style={{ backgroundColor: DIMENSION_COLORS[dim] }} />
                      <span className="text-sm font-semibold capitalize text-white">{plainLabel}</span>
                      <span className={`text-sm font-bold ${d > 0 ? "text-emerald-300" : d < 0 ? "text-red-300" : "text-slate-300"}`}>
                        {d > 0 ? "+" : ""}{d}%
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </motion.div>
        )}
      </div>
    </section>
  );
}

function StatCard({
  label,
  value,
  sublabel,
  valueClass,
  isRiskBadge,
}: {
  label: React.ReactNode;
  value: string;
  sublabel?: string;
  valueClass?: string;
  isRiskBadge?: boolean;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg bg-white/10 backdrop-blur-xl border border-white/20 px-5 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]">
      {isRiskBadge ? (
        <span className={valueClass}>{value}</span>
      ) : (
        <p className={`text-xl font-bold ${valueClass ?? "text-white"}`}>
          {value}
        </p>
      )}
      {sublabel && <p className="text-xs text-slate-200">{sublabel}</p>}
      <p className="mt-0.5 text-[11px] uppercase tracking-wider text-slate-300">
        {label}
      </p>
    </div>
  );
}

function buildNarrative(
  name: string,
  strongest: [string, number],
  weakest: [string, number],
  deltas: Record<string, number> | null,
  evalCount: number,
  drift: number
): React.ReactNode {
  const strongLabel = DIM_LABELS[strongest[0]] ?? strongest[0];
  const weakLabel = DIM_LABELS[weakest[0]] ?? weakest[0];

  const hi = (text: string) => <span className="font-bold text-white">{text}</span>;

  let growthLine: React.ReactNode = null;
  if (deltas && evalCount > 1) {
    const sorted = Object.entries(deltas).sort(([, a], [, b]) => b - a);
    const biggest = sorted[0];
    if (biggest[1] > 0) {
      const label = DIM_LABELS[biggest[0]] ?? biggest[0];
      growthLine = <>{" "}Over {evalCount} evaluations, {hi(`${label} grew the most (+${biggest[1]}%)`)}.{" "}</>;
    }
  }

  let edgeLine: React.ReactNode = null;
  if (strongest[0] !== weakest[0]) {
    const cap = weakLabel.charAt(0).toUpperCase() + weakLabel.slice(1);
    edgeLine = <>{" "}{cap} is where the {hi("biggest opportunity for growth")} remains.{" "}</>;
  }

  let trendLine: React.ReactNode = null;
  if (drift > 0.02) {
    trendLine = <>{" "}The trajectory suggests {hi("real improvement")} through repeated evaluation and correction.</>;
  } else if (drift < -0.02) {
    trendLine = <>{" "}Recent evaluations show {hi("a decline that warrants attention")} before negative habits solidify.</>;
  } else if (evalCount >= 2) {
    trendLine = <>{" "}Character foundations are {hi("stabilizing")}. Consistency will determine whether virtues become lasting habits.</>;
  } else {
    trendLine = <>{" "}More evaluations will reveal whether these early patterns become {hi("consistent habits")}.</>;
  }

  return (
    <>
      {name} shows the strongest scores in {hi(strongLabel)}.
      {growthLine}
      {edgeLine}
      {trendLine}
    </>
  );
}
