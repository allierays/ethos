"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import { getAlumni } from "../../lib/api";
import { DIMENSION_COLORS } from "../../lib/colors";
import { fadeUp, whileInView } from "../../lib/motion";
import GraphHelpButton from "../shared/GraphHelpButton";

interface AlumniComparisonProps {
  agentTraitAverages: Record<string, number>;
  agentName?: string;
}

interface ComparisonPoint {
  trait: string;
  traitKey: string;
  agent: number;
  alumni: number;
  delta: number;
  dimension: string;
}

const TRAIT_LABELS: Record<string, string> = {
  virtue: "Virtue",
  goodwill: "Goodwill",
  manipulation: "Manipulation",
  deception: "Deception",
  accuracy: "Accuracy",
  reasoning: "Reasoning",
  fabrication: "Fabrication",
  brokenLogic: "Broken Logic",
  broken_logic: "Broken Logic",
  recognition: "Recognition",
  compassion: "Compassion",
  dismissal: "Dismissal",
  exploitation: "Exploitation",
};

const TRAIT_DIMENSIONS: Record<string, string> = {
  virtue: "ethos",
  goodwill: "ethos",
  manipulation: "ethos",
  deception: "ethos",
  accuracy: "logos",
  reasoning: "logos",
  fabrication: "logos",
  brokenLogic: "logos",
  broken_logic: "logos",
  recognition: "pathos",
  compassion: "pathos",
  dismissal: "pathos",
  exploitation: "pathos",
};

const DIMENSIONS = [
  { key: "ethos", label: "Ethos", sublabel: "Character" },
  { key: "logos", label: "Logos", sublabel: "Reasoning" },
  { key: "pathos", label: "Pathos", sublabel: "Empathy" },
];

export default function AlumniComparison({
  agentTraitAverages,
  agentName,
}: AlumniComparisonProps) {
  const name = agentName ?? "this agent";
  const [data, setData] = useState<ComparisonPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAlumni()
      .then((alumni) => {
        const points: ComparisonPoint[] = Object.entries(agentTraitAverages).map(
          ([trait, agentScore]) => {
            const alumniScore = alumni.traitAverages[trait] ?? 0;
            return {
              traitKey: trait,
              trait: TRAIT_LABELS[trait] ?? trait,
              agent: Math.round(agentScore * 1000) / 1000,
              alumni: Math.round(alumniScore * 1000) / 1000,
              delta: Math.round((agentScore - alumniScore) * 1000) / 1000,
              dimension: TRAIT_DIMENSIONS[trait] ?? "ethos",
            };
          }
        );
        setData(points);
      })
      .catch(() => {
        const points: ComparisonPoint[] = Object.entries(agentTraitAverages).map(
          ([trait, agentScore]) => ({
            traitKey: trait,
            trait: TRAIT_LABELS[trait] ?? trait,
            agent: Math.round(agentScore * 1000) / 1000,
            alumni: 0,
            delta: 0,
            dimension: TRAIT_DIMENSIONS[trait] ?? "ethos",
          })
        );
        setData(points);
      })
      .finally(() => setLoading(false));
  }, [agentTraitAverages]);

  return (
    <motion.div
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
            Alumni Comparison
          </h3>
          <p className="mt-0.5 text-xs text-muted">
            {name}&apos;s scores overlaid on network averages.
          </p>
        </div>
        <GraphHelpButton slug="guide-alumni-comparison" />
      </div>

      {loading ? (
        <div className="mt-8 flex h-48 items-center justify-center">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted border-t-teal" />
        </div>
      ) : data.length === 0 ? (
        <div className="mt-8 flex h-48 items-center justify-center text-sm text-muted">
          No comparison data available.
        </div>
      ) : (
        <div className="mt-5 space-y-6">
          {DIMENSIONS.map((dim) => {
            const dimData = data.filter((d) => d.dimension === dim.key);
            if (dimData.length === 0) return null;
            const color = DIMENSION_COLORS[dim.key] ?? "#64748b";
            const chartHeight = dimData.length * 48 + 24;

            return (
              <div key={dim.key}>
                {/* Dimension header */}
                <div className="mb-2 flex items-center gap-2">
                  <div
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-xs font-semibold uppercase tracking-wider" style={{ color }}>
                    {dim.label}
                  </span>
                  <span className="text-[10px] text-foreground/40">{dim.sublabel}</span>
                </div>

                {/* Chart for this dimension */}
                <div style={{ height: chartHeight }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dimData} layout="vertical" barGap={2}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#e2e8f0"
                        horizontal={false}
                      />
                      <XAxis
                        type="number"
                        domain={[0, 1]}
                        tick={{ fontSize: 10, fill: "#94a3b8" }}
                        tickLine={false}
                        axisLine={{ stroke: "#e2e8f0" }}
                        hide
                      />
                      <YAxis
                        type="category"
                        dataKey="trait"
                        tick={{ fontSize: 11, fill: "#64748b" }}
                        tickLine={false}
                        axisLine={false}
                        width={90}
                      />
                      <Tooltip
                        contentStyle={{
                          fontSize: 12,
                          borderRadius: 8,
                          border: "1px solid #e2e8f0",
                        }}
                        formatter={(value: number | undefined, dataKey?: string) => [
                          value !== undefined ? `${(value * 100).toFixed(0)}%` : "0%",
                          dataKey === "agent" ? name : "Alumni",
                        ]}
                      />
                      <ReferenceLine x={0.5} stroke="#d1c9be" strokeDasharray="3 3" />
                      <Bar dataKey="alumni" radius={[0, 4, 4, 0]} barSize={10} fillOpacity={0.3}>
                        {dimData.map((_, i) => (
                          <Cell key={`alumni-${i}`} fill="#94a3b8" />
                        ))}
                      </Bar>
                      <Bar dataKey="agent" radius={[0, 4, 4, 0]} barSize={10}>
                        {dimData.map((entry, i) => (
                          <Cell
                            key={`agent-${i}`}
                            fill={entry.delta >= 0 ? color : "#ef4444"}
                            fillOpacity={0.9}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            );
          })}

          {/* Shared x-axis scale */}
          <div className="flex items-center justify-between px-[90px] text-[10px] text-foreground/30">
            <span>0</span>
            <span>0.25</span>
            <span>0.5</span>
            <span>0.75</span>
            <span>1.0</span>
          </div>
        </div>
      )}

      <div className="mt-3 flex items-center gap-4 text-xs text-muted">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded bg-teal" /> {name}
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded bg-muted/30" /> Alumni avg
        </span>
      </div>
    </motion.div>
  );
}
