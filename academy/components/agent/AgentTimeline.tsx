"use client";

import { useEffect, useState } from "react";
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
import { getHistory, getAgent } from "../../lib/api";
import { DIMENSION_COLORS } from "../../lib/colors";
import type { EvaluationHistoryItem, AgentProfile } from "../../lib/types";
import AgentSelector from "./AgentSelector";

interface TimelineDataPoint {
  index: number;
  createdAt: string;
  ethos: number;
  logos: number;
  pathos: number;
  flags: string[];
  alignmentStatus: string;
}

export default function AgentTimeline() {
  const [agentId, setAgentId] = useState<string | null>(null);
  const [data, setData] = useState<TimelineDataPoint[]>([]);
  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!agentId) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [history, agentProfile] = await Promise.all([
          getHistory(agentId!),
          getAgent(agentId!),
        ]);

        if (cancelled) return;

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

        setData(points);
        setProfile(agentProfile);
      } catch {
        if (!cancelled) setError("Failed to load agent history");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [agentId]);

  const flaggedPoints = data.filter((d) => d.flags.length > 0);

  const trendLabel =
    profile?.phronesisTrend === "improving"
      ? "Improving"
      : profile?.phronesisTrend === "declining"
        ? "Declining"
        : profile?.phronesisTrend === "stable"
          ? "Stable"
          : "Insufficient data";

  const trendColor =
    profile?.phronesisTrend === "improving"
      ? "text-aligned"
      : profile?.phronesisTrend === "declining"
        ? "text-misaligned"
        : "text-muted";

  return (
    <div className="rounded-xl border border-border bg-white p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
            Agent Timeline
          </h3>
          <p className="mt-0.5 text-xs text-muted">
            Dimension scores over time — Phronesis in motion.
          </p>
        </div>
        <AgentSelector selectedAgentId={agentId} onSelect={setAgentId} />
      </div>

      {!agentId && (
        <div className="mt-8 flex h-48 items-center justify-center text-sm text-muted">
          Select an agent to view their timeline.
        </div>
      )}

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

      {!loading && !error && agentId && data.length === 0 && (
        <div className="mt-8 flex h-48 items-center justify-center text-sm text-muted">
          No evaluation history for this agent.
        </div>
      )}

      {!loading && !error && data.length > 0 && (
        <>
          {profile && (
            <div className="mt-3 flex items-center gap-4 text-xs">
              <span className="text-muted">
                {profile.evaluationCount} evaluations
              </span>
              <span className={trendColor}>
                {profile.phronesisTrend === "improving" && "↑ "}
                {profile.phronesisTrend === "declining" && "↓ "}
                {profile.phronesisTrend === "stable" && "→ "}
                {trendLabel}
              </span>
            </div>
          )}

          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
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
                  formatter={(value: number | undefined) => value?.toFixed(3) ?? ""}
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
        </>
      )}
    </div>
  );
}
