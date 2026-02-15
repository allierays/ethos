"use client";

import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { motion } from "motion/react";
import type { IndicatorLike } from "../../lib/annotate";
import type { IntentClassification } from "../../lib/types";
import { DIMENSION_COLORS, DIMENSION_LABELS, TRAIT_DIMENSIONS, TRAIT_LABELS, INTENT_COLORS } from "../../lib/colors";
import ReasoningText from "./ReasoningText";

/* ─── Score bar (local, matches RecordsClient pattern) ─── */

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="relative flex-1 h-2 rounded-full bg-muted/10">
      <div
        className="absolute inset-y-0 left-0 rounded-full h-2"
        style={{ width: `${Math.round(value * 100)}%`, backgroundColor: color, opacity: 0.7 }}
      />
    </div>
  );
}

/* ─── Severity pill ─── */

function SeverityPill({ severity }: { severity: number }) {
  const pct = Math.round(severity * 100);
  let cls = "bg-aligned/10 text-aligned";
  if (pct >= 70) cls = "bg-misaligned/10 text-misaligned";
  else if (pct >= 40) cls = "bg-drifting/10 text-drifting";
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${cls}`}>
      sev {pct}
    </span>
  );
}

/* ─── Props ─── */

interface IndicatorSidebarProps {
  indicator: IndicatorLike;
  scoringReasoning?: string;
  intentClassification?: IntentClassification | null;
  onClose: () => void;
}

/* ─── Sidebar ─── */

export default function IndicatorSidebar({
  indicator,
  scoringReasoning,
  intentClassification,
  onClose,
}: IndicatorSidebarProps) {
  const closeRef = useRef<HTMLButtonElement>(null);

  // Auto-focus close button on mount
  useEffect(() => {
    closeRef.current?.focus();
  }, []);

  // Close on Escape
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const dimension = TRAIT_DIMENSIONS[indicator.trait] ?? "ethos";
  const dimColor = DIMENSION_COLORS[dimension] ?? DIMENSION_COLORS.ethos;
  const dimLabel = DIMENSION_LABELS[dimension] ?? dimension;
  const traitLabel = TRAIT_LABELS[indicator.trait] ?? indicator.trait?.replace(/_/g, " ") ?? "Unknown";
  const displayName = indicator.name?.replace(/_/g, " ") ?? "Indicator";

  const sidebar = (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.15 }}
        className="fixed inset-0 z-50 bg-black/20"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <motion.aside
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="fixed right-0 top-0 z-50 flex h-dvh w-full sm:w-[28rem] max-w-[90vw] flex-col bg-white/90 backdrop-blur-xl shadow-xl border-l border-border"
        role="dialog"
        aria-modal="true"
        aria-label="Indicator details"
      >
        {/* Header */}
        <div className="flex items-start gap-3 border-b border-border/30 px-5 py-4">
          <span
            className="mt-1 inline-block h-3 w-3 shrink-0 rounded-full"
            style={{ backgroundColor: dimColor }}
          />
          <div className="flex-1 min-w-0">
            <h2 className="text-base font-bold text-foreground capitalize leading-tight">
              {displayName}
            </h2>
            <p className="text-xs text-muted mt-0.5">
              {traitLabel} &middot; {dimLabel}
            </p>
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            className="shrink-0 rounded-lg p-1.5 text-muted hover:text-foreground hover:bg-muted/10 transition-colors"
            aria-label="Close indicator details"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {/* Evidence quote */}
          {indicator.evidence && (
            <div>
              <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted/70 mb-2">Evidence</h3>
              <blockquote
                className="text-sm text-foreground/80 leading-relaxed border-l-3 pl-3 py-1 italic"
                style={{ borderColor: dimColor }}
              >
                &ldquo;{indicator.evidence}&rdquo;
              </blockquote>
            </div>
          )}

          {/* Confidence */}
          <div>
            <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted/70 mb-2">Confidence</h3>
            <div className="flex items-center gap-3">
              <ScoreBar value={indicator.confidence} color={dimColor} />
              <span className="text-sm font-bold tabular-nums shrink-0" style={{ color: dimColor }}>
                {Math.round(indicator.confidence * 100)}%
              </span>
            </div>
          </div>

          {/* Severity (if present) */}
          {indicator.severity !== undefined && (
            <div>
              <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted/70 mb-2">Severity</h3>
              <SeverityPill severity={indicator.severity} />
            </div>
          )}

          {/* Description (if present) */}
          {indicator.description && (
            <div>
              <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted/70 mb-2">Description</h3>
              <p className="text-sm text-foreground/70 leading-relaxed">{indicator.description}</p>
            </div>
          )}

          {/* Dimension + trait pill */}
          <div>
            <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted/70 mb-2">Trait &amp; Dimension</h3>
            <div className="flex items-center gap-2">
              <span
                className="rounded-full px-2.5 py-0.5 text-xs font-semibold text-white"
                style={{ backgroundColor: dimColor }}
              >
                {dimLabel}
              </span>
              <span className="rounded-full bg-muted/10 px-2.5 py-0.5 text-xs font-medium text-muted">
                {traitLabel}
              </span>
            </div>
          </div>

          {/* Scoring reasoning */}
          {scoringReasoning && (
            <div>
              <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted/70 mb-2">Scoring Reasoning</h3>
              <ReasoningText text={scoringReasoning} className="text-sm text-foreground/80 leading-relaxed" />
            </div>
          )}

          {/* Intent summary */}
          {intentClassification && (
            <div>
              <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted/70 mb-2">Intent</h3>
              <div className="flex flex-wrap gap-1.5">
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${INTENT_COLORS[intentClassification.rhetoricalMode] ?? "bg-muted/10 text-muted"}`}>
                  {intentClassification.rhetoricalMode?.replace(/_/g, " ")}
                </span>
                <span className="rounded-full bg-muted/10 px-2 py-0.5 text-[10px] font-medium text-muted capitalize">
                  {intentClassification.primaryIntent?.replace(/_/g, " ")}
                </span>
              </div>
            </div>
          )}
        </div>
      </motion.aside>
    </>
  );

  return createPortal(sidebar, document.body);
}
