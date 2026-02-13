"use client";

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
} from "recharts";
import { motion } from "motion/react";
import { DIMENSION_COLORS } from "../../lib/colors";
import { fadeUp, whileInView } from "../../lib/motion";

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
}

export default function TranscriptChart({ timeline }: TranscriptChartProps) {
  const flaggedPoints = timeline.filter((d) => d.flags.length > 0);

  const first = timeline[0];
  const last = timeline[timeline.length - 1];
  const dims = [
    { key: "ethos" as const, label: "Ethos", color: DIMENSION_COLORS.ethos },
    { key: "logos" as const, label: "Logos", color: DIMENSION_COLORS.logos },
    { key: "pathos" as const, label: "Pathos", color: DIMENSION_COLORS.pathos },
  ];

  return (
    <motion.section
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
        Transcript
      </h2>
      <p className="mt-0.5 text-sm text-foreground/60">
        Is this agent getting better or worse?
      </p>

      {timeline.length === 0 ? (
        <div className="mt-8 flex h-48 items-center justify-center text-sm text-muted">
          No evaluation history yet.
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
                  contentStyle={{
                    fontSize: 12,
                    borderRadius: 12,
                    border: "1px solid rgba(255,255,255,0.3)",
                    background: "rgba(255,255,255,0.8)",
                    backdropFilter: "blur(12px)",
                    boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
                  }}
                  formatter={(value: number | undefined, name?: string) => [
                    `${((value ?? 0) * 100).toFixed(0)}%`,
                    name,
                  ]}
                  labelFormatter={(label) => `Evaluation #${label}`}
                />
                <Area
                  type="monotone"
                  dataKey="ethos"
                  stroke={DIMENSION_COLORS.ethos}
                  strokeWidth={2.5}
                  fill="url(#gradEthos)"
                  dot={{ r: 4, fill: DIMENSION_COLORS.ethos, stroke: "#fff", strokeWidth: 2 }}
                  activeDot={{ r: 6, stroke: DIMENSION_COLORS.ethos, strokeWidth: 2, fill: "#fff" }}
                  name="Ethos"
                />
                <Area
                  type="monotone"
                  dataKey="logos"
                  stroke={DIMENSION_COLORS.logos}
                  strokeWidth={2.5}
                  fill="url(#gradLogos)"
                  dot={{ r: 4, fill: DIMENSION_COLORS.logos, stroke: "#fff", strokeWidth: 2 }}
                  activeDot={{ r: 6, stroke: DIMENSION_COLORS.logos, strokeWidth: 2, fill: "#fff" }}
                  name="Logos"
                />
                <Area
                  type="monotone"
                  dataKey="pathos"
                  stroke={DIMENSION_COLORS.pathos}
                  strokeWidth={2.5}
                  fill="url(#gradPathos)"
                  dot={{ r: 4, fill: DIMENSION_COLORS.pathos, stroke: "#fff", strokeWidth: 2 }}
                  activeDot={{ r: 6, stroke: DIMENSION_COLORS.pathos, strokeWidth: 2, fill: "#fff" }}
                  name="Pathos"
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
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Dimension summary stats */}
          {first && last && (
            <div className="mt-4 grid grid-cols-3 gap-3">
              {dims.map((dim) => {
                const latest = last[dim.key];
                const delta = timeline.length > 1 ? last[dim.key] - first[dim.key] : 0;
                const pct = Math.round(latest * 100);
                const deltaPct = Math.round(delta * 100);
                return (
                  <div
                    key={dim.key}
                    className="rounded-lg glass p-3 text-center"
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
                  </div>
                );
              })}
            </div>
          )}
        </>
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
            <span className="inline-block h-2 w-2 rounded-full bg-misaligned" />{" "}
            Flagged
          </span>
        )}
      </div>
    </motion.section>
  );
}
