"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "motion/react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
} from "recharts";
import { getAgent, getHistory } from "../../../lib/api";
import type { AgentProfile, EvaluationHistoryItem } from "../../../lib/types";
import RadarChart from "../../../components/shared/RadarChart";
import DimensionBalance from "../../../components/shared/DimensionBalance";
import AlumniComparison from "../../../components/alumni/AlumniComparison";
import InsightsPanel from "../../../components/agent/InsightsPanel";
import { fadeUp, staggerContainer, whileInView } from "../../../lib/motion";
import { getAcademicLabel, formatClassOf } from "../../../lib/academic";
import { ALIGNMENT_STYLES, TREND_DISPLAY, DIMENSION_COLORS } from "../../../lib/colors";

/* ─── Timeline data point ─── */

interface TimelineDataPoint {
  index: number;
  createdAt: string;
  ethos: number;
  logos: number;
  pathos: number;
  flags: string[];
  alignmentStatus: string;
}

/* ─── Page ─── */

export default function AgentReportCard() {
  const params = useParams();
  const agentId = params.id as string;

  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [timeline, setTimeline] = useState<TimelineDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!agentId) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [agentProfile, history] = await Promise.all([
          getAgent(agentId),
          getHistory(agentId),
        ]);

        if (cancelled) return;

        setProfile(agentProfile);

        const points: TimelineDataPoint[] = history
          .slice()
          .reverse()
          .map((item: EvaluationHistoryItem, i: number) => ({
            index: i + 1,
            createdAt: item.createdAt,
            ethos: item.ethos,
            logos: item.logos,
            pathos: item.pathos,
            flags: item.flags,
            alignmentStatus: item.alignmentStatus,
          }));

        setTimeline(points);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load agent");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [agentId]);

  if (loading) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex h-96 items-center justify-center">
          <div className="text-center">
            <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-action border-t-transparent" />
            <p className="mt-3 text-sm text-muted">Loading agent profile...</p>
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex h-96 items-center justify-center">
          <div className="text-center">
            <p className="text-sm text-misaligned">{error}</p>
          </div>
        </div>
      </main>
    );
  }

  if (!profile) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex h-96 items-center justify-center">
          <p className="text-sm text-muted">Agent not found.</p>
        </div>
      </main>
    );
  }

  const trend = TREND_DISPLAY[profile.phronesisTrend] ?? TREND_DISPLAY.insufficient_data;
  const latestAlignment =
    profile.alignmentHistory?.[profile.alignmentHistory.length - 1] ?? "unknown";
  const alignmentStyle = ALIGNMENT_STYLES[latestAlignment] ?? "bg-muted/10 text-muted";
  const academicLabel = getAcademicLabel(latestAlignment);
  const classOf = formatClassOf(profile.createdAt);
  const flaggedPoints = timeline.filter((d) => d.flags.length > 0);

  // Compute overall phronesis score
  const dims = profile.dimensionAverages;
  const phronesisScore = Math.round(
    ((dims.ethos ?? 0) + (dims.logos ?? 0) + (dims.pathos ?? 0)) / 3 * 100
  );

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      {/* Agent Header */}
      <motion.div
        className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        {...whileInView}
        variants={fadeUp}
      >
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">
              Agent Report Card
            </h1>
            <span className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${alignmentStyle}`}>
              {latestAlignment}
            </span>
            {academicLabel && (
              <span className="rounded-full bg-ethos-100 px-3 py-1 text-xs font-semibold text-ethos-700">
                {academicLabel}
              </span>
            )}
          </div>
          <div className="mt-1 flex items-center gap-3">
            <p className="font-mono text-sm text-muted" title={profile.agentId}>
              {profile.agentId}
            </p>
            {classOf && (
              <span className="text-xs text-muted">{classOf}</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-center">
            <p className="text-3xl font-bold">{phronesisScore}%</p>
            <p className="text-xs text-muted">Phronesis</p>
          </div>
          <div className="text-center">
            <p className={`text-2xl font-semibold ${trend.color}`}>
              {trend.arrow}
            </p>
            <p className="text-xs text-muted">{trend.label}</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-semibold">{profile.evaluationCount}</p>
            <p className="text-xs text-muted">Evaluations</p>
          </div>
        </div>
      </motion.div>

      {/* 4 Pillar sections */}
      <motion.div
        className="mt-10 space-y-8"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        {/* 1. Transcript */}
        <motion.section variants={fadeUp}>
          <div className="rounded-xl border border-border bg-white p-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
              Transcript
            </h2>
            <p className="mt-0.5 text-xs text-muted">
              Is this agent getting better or worse?
            </p>

            {timeline.length === 0 ? (
              <div className="mt-8 flex h-48 items-center justify-center text-sm text-muted">
                No evaluation history yet.
              </div>
            ) : (
              <div className="mt-4 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeline}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis
                      dataKey="index"
                      tick={{ fontSize: 11, fill: "#64748b" }}
                      tickLine={false}
                      axisLine={{ stroke: "#e2e8f0" }}
                    />
                    <YAxis
                      domain={[0, 1]}
                      tick={{ fontSize: 11, fill: "#64748b" }}
                      tickLine={false}
                      axisLine={{ stroke: "#e2e8f0" }}
                      width={32}
                    />
                    <Tooltip
                      contentStyle={{
                        fontSize: 12,
                        borderRadius: 8,
                        border: "1px solid #e2e8f0",
                      }}
                      formatter={(value: number | undefined) =>
                        value?.toFixed(3) ?? ""
                      }
                    />
                    <Line
                      type="monotone"
                      dataKey="ethos"
                      stroke={DIMENSION_COLORS.ethos}
                      strokeWidth={2}
                      dot={false}
                      name="Ethos"
                    />
                    <Line
                      type="monotone"
                      dataKey="logos"
                      stroke={DIMENSION_COLORS.logos}
                      strokeWidth={2}
                      dot={false}
                      name="Logos"
                    />
                    <Line
                      type="monotone"
                      dataKey="pathos"
                      stroke={DIMENSION_COLORS.pathos}
                      strokeWidth={2}
                      dot={false}
                      name="Pathos"
                    />
                    {flaggedPoints.map((point) => (
                      <ReferenceDot
                        key={`flag-${point.index}`}
                        x={point.index}
                        y={Math.min(point.ethos, point.logos, point.pathos)}
                        r={4}
                        fill="#ef4444"
                        stroke="white"
                        strokeWidth={2}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            <div className="mt-3 flex items-center gap-4 text-xs text-muted">
              <span className="flex items-center gap-1">
                <span className="inline-block h-2 w-4 rounded bg-teal" /> Ethos
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-2 w-4 rounded bg-blue" /> Logos
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-2 w-4 rounded bg-warm" /> Pathos
              </span>
              {flaggedPoints.length > 0 && (
                <span className="flex items-center gap-1">
                  <span className="inline-block h-2 w-2 rounded-full bg-misaligned" /> Flagged
                </span>
              )}
            </div>
          </div>
        </motion.section>

        {/* 2. Profile */}
        <motion.section variants={fadeUp}>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Radar chart (trait profile) */}
            <div className="rounded-xl border border-border bg-white p-6">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
                Profile — Trait Radar
              </h2>
              <p className="mt-0.5 text-xs text-muted">
                What is this agent's character?
              </p>
              {Object.keys(profile.traitAverages).length > 0 ? (
                <RadarChart
                  traits={Object.fromEntries(
                    Object.entries(profile.traitAverages).map(([name, score]) => [
                      name,
                      { name, score, dimension: "", polarity: "", indicators: [] },
                    ])
                  )}
                />
              ) : (
                <div className="flex h-64 items-center justify-center text-sm text-muted">
                  Not enough data for radar chart.
                </div>
              )}
            </div>

            {/* Dimension bars */}
            <div className="rounded-xl border border-border bg-white p-6">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
                Profile — Dimensions
              </h2>
              <p className="mt-0.5 text-xs text-muted">
                Lifetime averages across three dimensions.
              </p>
              <div className="mt-6 space-y-5">
                {(["ethos", "logos", "pathos"] as const).map((dim) => {
                  const score = profile.dimensionAverages[dim] ?? 0;
                  const pct = Math.round(score * 100);
                  return (
                    <div key={dim}>
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium capitalize">{dim}</span>
                        <span className="font-mono tabular-nums text-muted">
                          {pct}%
                        </span>
                      </div>
                      <div className="mt-1.5 h-3 w-full rounded-full bg-border/30">
                        <motion.div
                          className="h-3 rounded-full"
                          style={{ backgroundColor: DIMENSION_COLORS[dim] }}
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Trait averages as horizontal list */}
              {Object.keys(profile.traitAverages).length > 0 && (
                <div className="mt-6 border-t border-border pt-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted">
                    Trait Averages
                  </p>
                  <div className="mt-3 space-y-2">
                    {Object.entries(profile.traitAverages).map(([trait, score]) => {
                      const pct = Math.round(score * 100);
                      return (
                        <div key={trait} className="flex items-center gap-2 text-xs">
                          <span className="w-24 text-muted capitalize">{trait}</span>
                          <div className="flex-1 h-1.5 rounded-full bg-border/30">
                            <div
                              className="h-1.5 rounded-full bg-action/60"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="w-8 text-right font-mono tabular-nums text-muted">
                            {pct}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.section>

        {/* 3. Alumni */}
        <motion.section variants={fadeUp}>
          <AlumniComparison agentTraitAverages={profile.traitAverages} />
        </motion.section>

        {/* 4. Balance */}
        <motion.section variants={fadeUp}>
          <DimensionBalance dimensionAverages={profile.dimensionAverages} />
        </motion.section>

        {/* 5. Insights */}
        <motion.section variants={fadeUp}>
          <InsightsPanel agentId={agentId} />
        </motion.section>
      </motion.div>
    </main>
  );
}
