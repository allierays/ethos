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
import { DIMENSION_COLORS, DIMENSIONS, TRAIT_LABELS, TRAIT_DIMENSIONS } from "../../lib/colors";
import { fadeUp, whileInView } from "../../lib/motion";
import GraphHelpButton from "../shared/GraphHelpButton";
import GlossaryTerm from "../shared/GlossaryTerm";

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


export default function AlumniComparison({
  agentTraitAverages,
  agentName,
}: AlumniComparisonProps) {
  const name = agentName ?? "this agent";
  const [data, setData] = useState<ComparisonPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getAlumni()
      .then((alumni) => {
        if (cancelled) return;
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
        if (cancelled) return;
        setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [agentTraitAverages]);

  return (
    <motion.div
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-[#1a2538]">
            <GlossaryTerm slug="alumni">Alumni Comparison</GlossaryTerm>
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
      ) : error ? (
        <div className="mt-8 flex h-48 items-center justify-center text-sm text-muted">
          Comparison data unavailable.
        </div>
      ) : data.length === 0 ? (
        <div className="mt-8 flex h-48 items-center justify-center text-sm text-muted">
          No comparison data available.
        </div>
      ) : (
        <div className="mt-4 space-y-3">
          {DIMENSIONS.map((dim) => {
            const dimData = data.filter((d) => d.dimension === dim.key);
            if (dimData.length === 0) return null;
            const color = DIMENSION_COLORS[dim.key] ?? "#64748b";
            const chartHeight = dimData.length * 32 + 8;

            return (
              <div key={dim.key}>
                {/* Dimension header */}
                <div className="mb-1 flex items-center gap-1.5">
                  <div
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color }}>
                    {dim.label}
                  </span>
                  <span className="text-[9px] text-foreground/60">{dim.sublabel}</span>
                </div>

                {/* Chart for this dimension */}
                <div style={{ height: chartHeight }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dimData} layout="vertical" barGap={1} margin={{ top: 0, right: 4, bottom: 0, left: 0 }}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#e2e8f0"
                        horizontal={false}
                      />
                      <XAxis
                        type="number"
                        domain={[0, 1]}
                        hide
                      />
                      <YAxis
                        type="category"
                        dataKey="trait"
                        tick={{ fontSize: 10, fill: "#64748b" }}
                        tickLine={false}
                        axisLine={false}
                        width={80}
                      />
                      <Tooltip
                        contentStyle={{
                          fontSize: 11,
                          borderRadius: 6,
                          border: "1px solid #e2e8f0",
                          padding: "4px 8px",
                        }}
                        formatter={(value: number | undefined, dataKey?: string) => [
                          value !== undefined ? `${(value * 100).toFixed(0)}%` : "0%",
                          dataKey === "agent" ? name : "Alumni",
                        ]}
                      />
                      <ReferenceLine x={0.5} stroke="#d1c9be" strokeDasharray="3 3" />
                      <Bar dataKey="alumni" radius={[0, 3, 3, 0]} barSize={7} fillOpacity={0.3}>
                        {dimData.map((_, i) => (
                          <Cell key={`alumni-${i}`} fill="#94a3b8" />
                        ))}
                      </Bar>
                      <Bar dataKey="agent" radius={[0, 3, 3, 0]} barSize={7}>
                        {dimData.map((entry, i) => (
                          <Cell
                            key={`agent-${i}`}
                            fill={color}
                            fillOpacity={entry.delta >= 0 ? 0.9 : 0.55}
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
          <div className="flex items-center justify-between px-[80px] text-[9px] text-foreground/50">
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
          <span className="inline-block h-2 w-4 rounded bg-ethos-500" /> {name}
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded bg-muted/30" /> Alumni avg
        </span>
      </div>
    </motion.div>
  );
}
