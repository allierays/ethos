"use client";

import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { TraitScore } from "../../lib/types";

const TRAIT_LABELS: Record<string, string> = {
  virtue: "Virtue",
  goodwill: "Goodwill",
  manipulation: "Manipulation",
  deception: "Deception",
  accuracy: "Accuracy",
  reasoning: "Reasoning",
  fabrication: "Fabrication",
  broken_logic: "Broken Logic",
  recognition: "Recognition",
  compassion: "Compassion",
  dismissal: "Dismissal",
  exploitation: "Exploitation",
};

const TRAIT_ORDER = [
  "virtue",
  "goodwill",
  "manipulation",
  "deception",
  "accuracy",
  "reasoning",
  "fabrication",
  "broken_logic",
  "recognition",
  "compassion",
  "dismissal",
  "exploitation",
];

const NEGATIVE_TRAITS = new Set([
  "manipulation",
  "deception",
  "fabrication",
  "broken_logic",
  "dismissal",
  "exploitation",
]);

interface RadarChartProps {
  traits: Record<string, TraitScore>;
}

interface ChartDataPoint {
  trait: string;
  score: number;
  fill: string;
}

export default function RadarChart({ traits }: RadarChartProps) {
  const data: ChartDataPoint[] = TRAIT_ORDER.map((key) => {
    const score = traits[key]?.score ?? 0;
    const isNegative = NEGATIVE_TRAITS.has(key);
    return {
      trait: TRAIT_LABELS[key] ?? key,
      score: Math.round(score * 100) / 100,
      fill: isNegative ? "var(--misaligned)" : "var(--teal)",
    };
  });

  return (
    <div className="h-80 w-full" data-testid="radar-chart">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="var(--border)" />
          <PolarAngleAxis
            dataKey="trait"
            tick={{ fontSize: 11, fill: "var(--muted)" }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 1]}
            tick={{ fontSize: 10, fill: "var(--muted)" }}
            tickCount={6}
          />
          <Tooltip
            contentStyle={{
              background: "white",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 13,
            }}
            formatter={(value: number | undefined) => [
              value !== undefined ? value.toFixed(2) : "0.00",
              "Score",
            ]}
          />
          <Radar
            name="Traits"
            dataKey="score"
            stroke="var(--teal)"
            fill="var(--teal)"
            fillOpacity={0.2}
            strokeWidth={2}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
}
