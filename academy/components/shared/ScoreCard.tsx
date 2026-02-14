"use client";

import type { EvaluationResult } from "../../lib/types";
import { ALIGNMENT_STYLES } from "../../lib/colors";
import GraphHelpButton from "./GraphHelpButton";
import SpectrumBar from "./SpectrumBar";
import IntentSummary from "./IntentSummary";

interface ScoreCardProps {
  result: EvaluationResult;
}

function DimensionBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium capitalize">{label}</span>
        <span className="tabular-nums text-muted">{pct}%</span>
      </div>
      <div className="h-2 rounded-full bg-border/50">
        <div
          className="h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export default function ScoreCard({ result }: ScoreCardProps) {
  const alignmentClass =
    ALIGNMENT_STYLES[result.alignmentStatus] ?? "bg-border/10 text-muted";

  return (
    <div
      className="space-y-5 rounded-xl border border-border bg-white p-5"
      data-testid="score-card"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[#1a2538]">
          Dimensions
        </h3>
        <div className="flex items-center gap-2">
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${alignmentClass}`}
            data-testid="alignment-badge"
          >
            {result.alignmentStatus}
          </span>
          <GraphHelpButton slug="guide-score-card" />
        </div>
      </div>

      <SpectrumBar
        score={(result.ethos + result.logos + result.pathos) / 3}
      />

      <div className="space-y-3">
        <DimensionBar label="Integrity (Ethos)" value={result.ethos} color="var(--ethos-500)" />
        <DimensionBar label="Logic (Logos)" value={result.logos} color="var(--logos-500)" />
        <DimensionBar label="Empathy (Pathos)" value={result.pathos} color="var(--pathos-500)" />
      </div>

      {result.intentClassification && (
        <div className="border-t border-border pt-3">
          <span className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-muted">
            Intent
          </span>
          <IntentSummary intent={result.intentClassification} />
        </div>
      )}

      <div className="flex items-center justify-between border-t border-border pt-4">
        <span className="text-sm text-muted">Integrity</span>
        <span className="text-sm font-semibold capitalize">{result.phronesis}</span>
      </div>

      {result.flags.length > 0 && (
        <div className="space-y-2 border-t border-border pt-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-misaligned">
            Flags
          </span>
          <div className="flex flex-wrap gap-1.5">
            {result.flags.map((flag) => (
              <span
                key={flag}
                className="rounded-md bg-misaligned/10 px-2 py-0.5 text-xs font-medium text-misaligned"
              >
                {flag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
