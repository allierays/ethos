"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { getAlumni } from "../../lib/api";
import { DIMENSION_COLORS } from "../../lib/colors";

const TRAIT_META: Record<string, { polarity: "positive" | "negative" }> = {
  virtue: { polarity: "positive" },
  goodwill: { polarity: "positive" },
  manipulation: { polarity: "negative" },
  deception: { polarity: "negative" },
  accuracy: { polarity: "positive" },
  reasoning: { polarity: "positive" },
  fabrication: { polarity: "negative" },
  brokenLogic: { polarity: "negative" },
  recognition: { polarity: "positive" },
  compassion: { polarity: "positive" },
  dismissal: { polarity: "negative" },
  exploitation: { polarity: "negative" },
};

interface ChartDataPoint {
  trait: string;
  score: number;
  polarity: "positive" | "negative";
}

export default function AlumniPanel() {
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [totalEvaluations, setTotalEvaluations] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const alumni = await getAlumni();
        if (cancelled) return;

        const points: ChartDataPoint[] = Object.entries(
          alumni.traitAverages
        ).map(([trait, score]) => ({
          trait,
          score: Math.round(score * 1000) / 1000,
          polarity: TRAIT_META[trait]?.polarity ?? "positive",
        }));

        setData(points);
        setTotalEvaluations(alumni.totalEvaluations);
        setLoading(false);
      } catch {
        if (!cancelled) {
          setError("Failed to load alumni data");
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="rounded-xl border border-border bg-white p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
            Alumni Averages
          </h3>
          <p className="mt-0.5 text-xs text-muted">
            Network-wide trait baselines across all agents.
          </p>
        </div>
        {totalEvaluations > 0 && (
          <span className="text-xs text-muted">
            {totalEvaluations} total evaluations
          </span>
        )}
      </div>

      {loading && (
        <div className="mt-8 flex h-48 items-center justify-center">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted border-t-teal" />
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg bg-misaligned/10 px-4 py-2 text-sm text-misaligned">
          {error}
        </div>
      )}

      {!loading && !error && data.length === 0 && (
        <div className="mt-8 flex h-48 items-center justify-center text-sm text-muted">
          No evaluation data yet.
        </div>
      )}

      {!loading && !error && data.length > 0 && (
        <div className="mt-4 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical">
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
                formatter={(value: number | undefined) => value?.toFixed(3) ?? ""}
              />
              <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={16}>
                {data.map((entry, i) => (
                  <Cell
                    key={`cell-${i}`}
                    fill={
                      entry.polarity === "positive" ? DIMENSION_COLORS.ethos : "#ef4444"
                    }
                    fillOpacity={0.8}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-3 flex items-center gap-4 text-xs text-muted">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded bg-teal" /> Positive
          trait
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded bg-misaligned" />{" "}
          Negative trait
        </span>
      </div>
    </div>
  );
}
