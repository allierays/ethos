"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { getPatterns } from "../../lib/api";
import type { PatternResult, DetectedPattern } from "../../lib/types";
import { fadeUp, staggerContainer } from "../../lib/motion";
import GlossaryTerm from "../shared/GlossaryTerm";

interface PatternsPanelProps {
  agentId: string;
  agentName?: string;
}

export default function PatternsPanel({ agentId, agentName }: PatternsPanelProps) {
  const name = agentName ?? "this agent";
  const [data, setData] = useState<PatternResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getPatterns(agentId)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load patterns"
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [agentId]);

  return (
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wider text-[#1a2538]">
        <GlossaryTerm slug="sabotage-pathway">Sabotage Pathways</GlossaryTerm>
      </h3>
      <p className="mt-0.5 text-sm text-foreground/80">
        Flagged indicators and manipulation patterns for {name}.
      </p>

      {loading && (
        <div className="mt-8 flex h-24 items-center justify-center">
          <div className="mx-auto h-5 w-5 animate-spin rounded-full border-2 border-muted border-t-action" />
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg bg-misaligned/10 px-4 py-2 text-sm text-misaligned">
          {error}
        </div>
      )}

      {!loading && !error && data && data.patterns.length === 0 && (
        <div className="mt-6 flex items-center gap-2 text-sm text-aligned">
          <svg
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          No sabotage pathways detected for {name}.
        </div>
      )}

      {!loading && !error && data && data.patterns.length > 0 && (
        <motion.div
          className="mt-4 space-y-4"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {data.patterns.map((pattern: DetectedPattern) => (
            <PatternCard key={pattern.patternId} pattern={pattern} />
          ))}
        </motion.div>
      )}
    </div>
  );
}

function PatternCard({ pattern }: { pattern: DetectedPattern }) {
  const confidencePct = Math.round(pattern.confidence * 100);
  const barColor =
    confidencePct >= 70
      ? "bg-misaligned"
      : confidencePct >= 40
      ? "bg-drifting"
      : "bg-muted";

  // Stage dots (5 stages for sabotage pathways)
  const totalStages = 5;

  return (
    <motion.div
      variants={fadeUp}
      className="rounded-lg glass p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[#1a2538]">
            {pattern.patternId}: {pattern.name}
          </p>
          {pattern.description && (
            <p className="mt-1 text-xs leading-relaxed text-foreground/70">
              {pattern.description}
            </p>
          )}
        </div>
        <span className="shrink-0 rounded-full bg-background px-2.5 py-0.5 text-xs font-mono tabular-nums text-foreground/80 border border-border/50">
          {pattern.occurrenceCount}x
        </span>
      </div>

      {/* Confidence bar */}
      <div className="mt-3">
        <div className="flex items-center justify-between text-[10px] text-foreground/80">
          <span>Confidence</span>
          <span className="font-mono tabular-nums">{confidencePct}%</span>
        </div>
        <div className="mt-1 h-1.5 w-full rounded-full bg-border/30">
          <motion.div
            className={`h-1.5 rounded-full ${barColor}`}
            initial={{ width: 0 }}
            whileInView={{ width: `${confidencePct}%` }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Stage dots */}
      <div className="mt-3 flex items-center gap-1">
        <span className="mr-1 text-[10px] text-foreground/80">Stage</span>
        {Array.from({ length: totalStages }).map((_, i) => (
          <span
            key={i}
            className={`h-2 w-2 rounded-full ${
              i < pattern.currentStage ? barColor : "bg-border/40"
            }`}
          />
        ))}
        <span className="ml-1 text-[10px] text-foreground/80 font-mono tabular-nums">
          {pattern.currentStage}/{totalStages}
        </span>
      </div>

      {/* Metadata + indicators */}
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] text-foreground/70">
        {pattern.firstSeen && (
          <span>First seen: {new Date(pattern.firstSeen).toLocaleDateString()}</span>
        )}
        {pattern.lastSeen && (
          <span>Last seen: {new Date(pattern.lastSeen).toLocaleDateString()}</span>
        )}
      </div>

      {pattern.matchedIndicators.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {pattern.matchedIndicators.map((ind) => (
            <span
              key={ind}
              className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] text-slate-600"
            >
              {ind}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}
