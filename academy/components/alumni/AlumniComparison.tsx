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

interface AlumniComparisonProps {
  agentTraitAverages: Record<string, number>;
}

interface ComparisonPoint {
  trait: string;
  agent: number;
  alumni: number;
  delta: number;
}

export default function AlumniComparison({
  agentTraitAverages,
}: AlumniComparisonProps) {
  const [data, setData] = useState<ComparisonPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAlumni()
      .then((alumni) => {
        const points: ComparisonPoint[] = Object.entries(agentTraitAverages).map(
          ([trait, agentScore]) => {
            const alumniScore = alumni.traitAverages[trait] ?? 0;
            return {
              trait,
              agent: Math.round(agentScore * 1000) / 1000,
              alumni: Math.round(alumniScore * 1000) / 1000,
              delta: Math.round((agentScore - alumniScore) * 1000) / 1000,
            };
          }
        );
        setData(points);
      })
      .catch(() => {
        // If alumni fails, show agent data only
        const points: ComparisonPoint[] = Object.entries(agentTraitAverages).map(
          ([trait, agentScore]) => ({
            trait,
            agent: Math.round(agentScore * 1000) / 1000,
            alumni: 0,
            delta: 0,
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
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
          Alumni Comparison
        </h3>
        <p className="mt-0.5 text-xs text-muted">
          This agent&apos;s scores overlaid on network averages.
        </p>
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
        <div className="mt-4 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" barGap={2}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#e2e8f0"
                horizontal={false}
              />
              <XAxis
                type="number"
                domain={[0, 1]}
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickLine={false}
                axisLine={{ stroke: "#e2e8f0" }}
              />
              <YAxis
                type="category"
                dataKey="trait"
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickLine={false}
                axisLine={{ stroke: "#e2e8f0" }}
                width={90}
              />
              <Tooltip
                contentStyle={{
                  fontSize: 12,
                  borderRadius: 8,
                  border: "1px solid #e2e8f0",
                }}
                formatter={(value: number | undefined, name?: string) => [
                  value?.toFixed(3) ?? "",
                  name === "agent" ? "Agent" : "Alumni",
                ]}
              />
              <ReferenceLine x={0.5} stroke="#d1c9be" strokeDasharray="3 3" />
              <Bar dataKey="alumni" radius={[0, 4, 4, 0]} barSize={10} fillOpacity={0.3}>
                {data.map((_, i) => (
                  <Cell key={`alumni-${i}`} fill="#94a3b8" />
                ))}
              </Bar>
              <Bar dataKey="agent" radius={[0, 4, 4, 0]} barSize={10}>
                {data.map((entry, i) => (
                  <Cell
                    key={`agent-${i}`}
                    fill={entry.delta >= 0 ? DIMENSION_COLORS.ethos : "#ef4444"}
                    fillOpacity={0.9}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-3 flex items-center gap-4 text-xs text-muted">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded bg-teal" /> Agent
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded bg-muted/30" /> Alumni avg
        </span>
      </div>
    </motion.div>
  );
}
