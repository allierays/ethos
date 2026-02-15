"use client";

import { useState } from "react";
import type { HighlightItem, EvaluationHistoryItem, HighlightIndicator } from "../../lib/types";
import { DIMENSION_COLORS, TRAIT_DIMENSIONS, TRAIT_LABELS } from "../../lib/colors";
import SpectrumBar from "./SpectrumBar";
import IntentSummary from "./IntentSummary";
import ReasoningText from "./ReasoningText";

type EvalLike = HighlightItem | EvaluationHistoryItem;

interface EvaluationDetailProps {
  evaluation: EvalLike;
}

function DimensionMiniBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between text-[11px]">
        <span className="font-medium">{label}</span>
        <span className="tabular-nums text-muted">{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-border/30">
        <div
          className="h-1.5 rounded-full"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function IndicatorGroup({
  title,
  indicators,
  type,
}: {
  title: string;
  indicators: HighlightIndicator[];
  type: "positive" | "negative";
}) {
  if (indicators.length === 0) return null;
  const isPositive = type === "positive";

  return (
    <div>
      <h5
        className={`text-[10px] font-semibold uppercase tracking-wider ${
          isPositive ? "text-aligned" : "text-misaligned"
        }`}
      >
        {title}
      </h5>
      <div className="mt-1.5 space-y-1.5">
        {indicators.map((ind, i) => {
          const dimension = TRAIT_DIMENSIONS[ind.trait] ?? "ethos";
          const dimColor = DIMENSION_COLORS[dimension] ?? "#64748b";
          return (
            <div key={`${ind.name}-${i}`} className="flex items-start gap-2">
              <div
                className="mt-1 h-2 w-2 shrink-0 rounded-full"
                style={{ backgroundColor: dimColor }}
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium">
                    {TRAIT_LABELS[ind.trait] ?? ind.trait}
                  </span>
                  <span className="text-[10px] text-muted">
                    {ind.name.replace(/_/g, " ")}
                  </span>
                  <span className="ml-auto text-[10px] tabular-nums text-muted">
                    {Math.round(ind.confidence * 100)}%
                  </span>
                </div>
                {ind.evidence && (
                  <p className="mt-0.5 text-[11px] italic text-muted/80 line-clamp-2">
                    &ldquo;{ind.evidence}&rdquo;
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const NEGATIVE_TRAITS = new Set([
  "manipulation",
  "deception",
  "fabrication",
  "brokenLogic",
  "broken_logic",
  "dismissal",
  "exploitation",
]);

export default function EvaluationDetail({ evaluation }: EvaluationDetailProps) {
  const [expanded, setExpanded] = useState(false);

  const overall =
    "overall" in evaluation
      ? evaluation.overall
      : (evaluation.ethos + evaluation.logos + evaluation.pathos) / 3;

  const intent = evaluation.intentClassification;
  const reasoning = evaluation.scoringReasoning;

  // Split indicators by polarity (only available on HighlightItem)
  const indicators = "indicators" in evaluation ? evaluation.indicators : [];
  const positiveIndicators = indicators.filter(
    (ind) => !NEGATIVE_TRAITS.has(ind.trait)
  );
  const negativeIndicators = indicators.filter(
    (ind) => NEGATIVE_TRAITS.has(ind.trait)
  );

  // Claims from intent
  const claims = intent?.claims ?? [];

  return (
    <div className="space-y-3">
      <SpectrumBar score={overall} size="sm" />
      {intent && <IntentSummary intent={intent} />}

      {(reasoning || indicators.length > 0) && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[11px] font-medium text-action hover:underline"
        >
          {expanded ? "Hide analysis" : "Show analysis"}
        </button>
      )}

      {expanded && (
        <div className="space-y-4 border-t border-border/50 pt-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <DimensionMiniBar
              label="Integrity"
              value={evaluation.ethos}
              color={DIMENSION_COLORS.ethos}
            />
            <DimensionMiniBar
              label="Logic"
              value={evaluation.logos}
              color={DIMENSION_COLORS.logos}
            />
            <DimensionMiniBar
              label="Empathy"
              value={evaluation.pathos}
              color={DIMENSION_COLORS.pathos}
            />
          </div>

          {reasoning && (
            <blockquote className="border-l-2 border-logos-300 pl-3 text-xs italic text-foreground/70">
              <ReasoningText text={reasoning} splitSentences={false} />
            </blockquote>
          )}

          {indicators.length > 0 && (
            <div className="space-y-3">
              <IndicatorGroup
                title="Positive signals"
                indicators={positiveIndicators}
                type="positive"
              />
              <IndicatorGroup
                title="Concerns"
                indicators={negativeIndicators}
                type="negative"
              />
            </div>
          )}

          {claims.length > 0 && (
            <div>
              <h5 className="text-[10px] font-semibold uppercase tracking-wider text-muted">
                Claims
              </h5>
              <div className="mt-1.5 space-y-1">
                {claims.map((c, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs">
                    <span className="shrink-0 rounded bg-border/20 px-1.5 py-0.5 text-[10px] font-medium text-muted">
                      {c.type}
                    </span>
                    <span className="text-foreground/80">{c.claim}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
