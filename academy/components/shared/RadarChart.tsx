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
import GlossaryTerm from "./GlossaryTerm";

/* ─── Trait metadata ─── */

export const TRAIT_LABELS: Record<string, string> = {
  virtue: "Virtue",
  goodwill: "Goodwill",
  manipulation: "Non-manipulation",
  deception: "Non-deception",
  accuracy: "Accuracy",
  reasoning: "Reasoning",
  fabrication: "Non-fabrication",
  broken_logic: "Sound Logic",
  recognition: "Recognition",
  compassion: "Compassion",
  dismissal: "Non-dismissal",
  exploitation: "Non-exploitation",
};

/**
 * Traits ordered by dimension for visual grouping on the radar:
 * Ethos (character) → Logos (reasoning) → Pathos (empathy)
 */
export const TRAIT_ORDER = [
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

export const NEGATIVE_TRAITS = new Set([
  "manipulation",
  "deception",
  "fabrication",
  "broken_logic",
  "dismissal",
  "exploitation",
]);

export const DIMENSION_MAP: Record<string, string> = {
  virtue: "ethos",
  goodwill: "ethos",
  manipulation: "ethos",
  deception: "ethos",
  accuracy: "logos",
  reasoning: "logos",
  fabrication: "logos",
  broken_logic: "logos",
  recognition: "pathos",
  compassion: "pathos",
  dismissal: "pathos",
  exploitation: "pathos",
};

const DIM_COLORS: Record<string, string> = {
  ethos: "#3b8a98",
  logos: "#2e4a6e",
  pathos: "#e0a53c",
};

interface RadarChartProps {
  traits: Record<string, TraitScore>;
  alumni?: Record<string, number>;
  selectedTrait?: string | null;
  onTraitClick?: (traitKey: string) => void;
  compact?: boolean;
}

export interface ChartDataPoint {
  traitKey: string;
  trait: string;
  health: number;
  raw: number;
  inverted: boolean;
  dimension: string;
  alumni?: number;
}

/**
 * Trait Development Radar
 *
 * Inverts negative traits so 1.0 always means "ideal behavior."
 * A perfect agent forms a full circle. Any dip reveals a character flaw.
 */
export default function RadarChart({ traits, alumni, selectedTrait, onTraitClick, compact }: RadarChartProps) {
  const data: ChartDataPoint[] = TRAIT_ORDER.map((key) => {
    const raw = traits[key]?.score ?? 0;
    const isNegative = NEGATIVE_TRAITS.has(key);
    const health = isNegative ? 1 - raw : raw;
    const dim = DIMENSION_MAP[key] ?? "ethos";

    const alumniRaw = alumni?.[key];
    const alumniHealth =
      alumniRaw !== undefined
        ? isNegative
          ? 1 - alumniRaw
          : alumniRaw
        : undefined;

    return {
      traitKey: key,
      trait: TRAIT_LABELS[key] ?? key,
      health: Math.round(health * 100) / 100,
      raw: Math.round(raw * 100) / 100,
      inverted: isNegative,
      dimension: dim,
      alumni: alumniHealth !== undefined ? Math.round(alumniHealth * 100) / 100 : undefined,
    };
  });

  return (
    <div className={`${compact ? "h-full" : "h-80"} w-full`} data-testid="radar-chart">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart data={data} cx="50%" cy="50%" outerRadius={compact ? "60%" : "70%"}>
          <PolarGrid stroke="var(--border)" />
          <PolarAngleAxis
            dataKey="trait"
            tick={({ payload, x, y, textAnchor }) => {
              const point = data.find((d) => d.trait === payload.value);
              const dim = point?.dimension ?? "ethos";
              const color = DIM_COLORS[dim] ?? "var(--muted)";
              const isSelected = point?.traitKey === selectedTrait;
              const baseFontSize = compact ? 8 : 10;
              return (
                <text
                  x={x}
                  y={y}
                  textAnchor={textAnchor}
                  fontSize={isSelected ? baseFontSize + 1 : baseFontSize}
                  fill={color}
                  fontWeight={isSelected ? 700 : 500}
                  className={onTraitClick ? "cursor-pointer" : ""}
                  onClick={() => point && onTraitClick?.(point.traitKey)}
                >
                  {payload.value}
                </text>
              );
            }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 1]}
            tick={compact ? false : { fontSize: 9, fill: "var(--muted)" }}
            tickCount={5}
          />
          <Tooltip
            contentStyle={{
              background: "white",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(value: number | undefined) => [
              value !== undefined ? `${(value * 100).toFixed(0)}%` : "0%",
              "Trait Health",
            ]}
          />
          {/* Alumni comparison (ghosted) */}
          {alumni && (
            <Radar
              name="Alumni"
              dataKey="alumni"
              stroke="#94a3b8"
              fill="none"
              strokeWidth={1}
              strokeDasharray="4 3"
            />
          )}
          {/* Agent trait development */}
          <Radar
            name="Trait Health"
            dataKey="health"
            stroke="var(--teal)"
            fill="var(--teal)"
            fillOpacity={0.15}
            strokeWidth={2}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className={`mt-1 flex items-center justify-center gap-4 text-[10px] text-muted ${compact ? "hidden" : ""}`}>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded" style={{ backgroundColor: "#3b8a98" }} /> <GlossaryTerm slug="ethos">Integrity (Ethos)</GlossaryTerm>
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded" style={{ backgroundColor: "#2e4a6e" }} /> <GlossaryTerm slug="logos">Logic (Logos)</GlossaryTerm>
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded" style={{ backgroundColor: "#e0a53c" }} /> <GlossaryTerm slug="pathos">Empathy (Pathos)</GlossaryTerm>
        </span>
        {alumni && (
          <span className="flex items-center gap-1">
            <span className="inline-block h-4 w-4 border-t border-dashed border-slate-400" /> Alumni
          </span>
        )}
      </div>
    </div>
  );
}
