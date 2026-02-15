"use client";

import { useEffect, useMemo, useState } from "react";
import { getCohortInsights } from "../../lib/api";
import type {
  CohortInsightsResult,
  ConstitutionalRiskItem,
  SabotagePathwaySummary,
} from "../../lib/types";
import SimilarityNetwork from "./SimilarityNetwork";

/* ─── Constants ─── */

const VALUE_LABELS: Record<number, string> = {
  1: "Safety",
  2: "Ethics",
  3: "Soundness",
  4: "Helpfulness",
};

const VALUE_DESCRIPTIONS: Record<number, string> = {
  1: "Don't undermine human oversight",
  2: "Be honest and avoid harm",
  3: "Reason accurately and clearly",
  4: "Be genuinely useful",
};

const TIER_LABELS: Record<string, string> = {
  standard: "Standard",
  focused: "Focused",
  deep: "Deep",
  deep_with_context: "Deep + Context",
};

const TIER_DESCRIPTIONS: Record<string, string> = {
  standard: "Quick keyword scan",
  focused: "Targeted trait analysis",
  deep: "Full Opus 4.6 deliberation",
  deep_with_context: "Opus 4.6 + agent history",
};

/* ─── Helpers ─── */

interface ValueSummary {
  priority: number;
  strengths: number;
  concerns: number;
  topTraits: { trait: string; count: number; polarity: string }[];
}

function groupByValue(items: ConstitutionalRiskItem[]): Map<number, ValueSummary> {
  const byPriority = new Map<number, {
    strengths: number;
    concerns: number;
    traitCounts: Map<string, { count: number; polarity: string }>;
  }>();

  for (const item of items) {
    if (!byPriority.has(item.priority)) {
      byPriority.set(item.priority, {
        strengths: 0,
        concerns: 0,
        traitCounts: new Map(),
      });
    }
    const entry = byPriority.get(item.priority)!;
    if (item.polarity === "positive") {
      entry.strengths += item.detectionCount;
    } else {
      entry.concerns += item.detectionCount;
    }
    const existing = entry.traitCounts.get(item.trait);
    if (existing) {
      existing.count += item.detectionCount;
    } else {
      entry.traitCounts.set(item.trait, {
        count: item.detectionCount,
        polarity: item.polarity,
      });
    }
  }

  const result = new Map<number, ValueSummary>();
  for (const [priority, data] of byPriority) {
    result.set(priority, {
      priority,
      strengths: data.strengths,
      concerns: data.concerns,
      topTraits: Array.from(data.traitCounts.entries())
        .map(([trait, d]) => ({ trait, count: d.count, polarity: d.polarity }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 4),
    });
  }
  return result;
}

/* ─── Hero Stats ─── */

function HeroStats({
  agentCount,
  evaluationCount,
  alignedPct,
}: {
  agentCount: number;
  evaluationCount: number;
  alignedPct: number;
}) {
  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="rounded-xl border border-border bg-white px-5 py-4 text-center">
        <p className="text-3xl font-bold tabular-nums text-foreground">
          {agentCount.toLocaleString()}
        </p>
        <p className="mt-1 text-xs text-muted">AI agents monitored</p>
      </div>
      <div className="rounded-xl border border-border bg-white px-5 py-4 text-center">
        <p className="text-3xl font-bold tabular-nums text-foreground">
          {evaluationCount.toLocaleString()}
        </p>
        <p className="mt-1 text-xs text-muted">Messages scored for honesty</p>
      </div>
      <div className="rounded-xl border border-border bg-white px-5 py-4 text-center">
        <p className="text-3xl font-bold tabular-nums text-aligned">
          {alignedPct}%
        </p>
        <p className="mt-1 text-xs text-muted">Passed alignment check</p>
      </div>
    </div>
  );
}

/* ─── Alumni Health (alignment + depth) ─── */

function CohortHealthCard({
  tiers,
  statuses,
}: {
  tiers: { tier: string; count: number }[];
  statuses: { status: string; count: number }[];
}) {
  const totalEvals = useMemo(
    () => tiers.reduce((sum, t) => sum + t.count, 0),
    [tiers]
  );

  const deepCount = useMemo(
    () =>
      tiers
        .filter((t) => t.tier === "deep" || t.tier === "deep_with_context")
        .reduce((sum, t) => sum + t.count, 0),
    [tiers]
  );

  const deepPct = totalEvals > 0 ? ((deepCount / totalEvals) * 100).toFixed(0) : "0";

  const STATUS_DOT: Record<string, string> = {
    aligned: "bg-aligned",
    drifting: "bg-drifting",
    misaligned: "bg-misaligned",
    violation: "bg-violation",
  };

  const STATUS_TEXT: Record<string, string> = {
    aligned: "text-aligned",
    drifting: "text-drifting",
    misaligned: "text-misaligned",
    violation: "text-violation",
  };

  if (tiers.length === 0 && statuses.length === 0) return null;

  const alignedCount = statuses.find((s) => s.status === "aligned")?.count ?? 0;
  const alignedPct = totalEvals > 0 ? Math.round((alignedCount / totalEvals) * 100) : 0;
  const flaggedCount = totalEvals - alignedCount;
  const fastCount = totalEvals - deepCount;

  const STATUS_HINT: Record<string, string> = {
    aligned: "Honest, accurate, helpful",
    misaligned: "Deceptive or manipulative",
    drifting: "Shifting away from alignment",
    violation: "Active safety concern",
  };

  return (
    <div className="rounded-xl border border-border bg-white p-6 space-y-5">
      {/* Narrative header */}
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">
          How honest are AI agents?
        </h3>
        <p className="mt-1 text-sm text-foreground/70 leading-relaxed">
          Ethos Academy scored{" "}
          <span className="font-semibold text-foreground">{totalEvals.toLocaleString()} messages</span>{" "}
          from AI agents for honesty, accuracy, and intent.{" "}
          <span className="font-semibold text-aligned">{alignedPct}% passed.</span>{" "}
          {flaggedCount > 0 && (
            <>{flaggedCount.toLocaleString()} showed signs of manipulation, deception, or drift.</>
          )}
        </p>
      </div>

      {/* Alignment tiles */}
      {statuses.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted mb-2">Alignment verdict per message</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {statuses.map((s) => {
              const pct =
                totalEvals > 0
                  ? ((s.count / totalEvals) * 100).toFixed(0)
                  : "0";
              return (
                <div
                  key={s.status}
                  className="rounded-lg border border-border/60 bg-border/5 px-3 py-2.5"
                >
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${STATUS_DOT[s.status] || "bg-border"}`}
                    />
                    <p className={`text-lg font-semibold tabular-nums ${STATUS_TEXT[s.status] || "text-foreground"}`}>
                      {s.count.toLocaleString()}
                    </p>
                  </div>
                  <p className="text-xs capitalize text-foreground/70">
                    {s.status}
                    <span className="ml-1 font-normal text-muted">{pct}%</span>
                  </p>
                  <p className="mt-0.5 text-[10px] leading-tight text-muted">
                    {STATUS_HINT[s.status] || ""}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Opus callout + tier grid */}
      <div className="space-y-3">
        {deepCount > 0 && (
          <div className="rounded-lg bg-ethos-50 border border-ethos-200/30 px-4 py-3">
            <p className="text-sm text-foreground/80">
              <span className="font-semibold text-foreground">
                {fastCount.toLocaleString()} messages
              </span>{" "}
              caught by fast keyword scans.{" "}
              Only{" "}
              <span className="text-lg font-semibold text-ethos-600">{deepPct}%</span>{" "}
              were suspicious enough to need deep analysis with Opus 4.6.
            </p>
            <p className="text-xs text-muted mt-0.5">
              {deepCount.toLocaleString()} of {totalEvals.toLocaleString()} escalated to full deliberation
            </p>
          </div>
        )}

        <div>
          <p className="text-xs font-medium text-muted mb-2">How Ethos decides analysis depth</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {tiers.map((t) => {
              const pct =
                totalEvals > 0 ? ((t.count / totalEvals) * 100).toFixed(0) : "0";
              return (
                <div
                  key={t.tier}
                  className="rounded-lg border border-border/60 bg-border/5 px-3 py-2.5"
                >
                  <p className="text-lg font-semibold tabular-nums text-foreground">
                    {t.count.toLocaleString()}
                  </p>
                  <p className="text-xs font-medium text-foreground/70">
                    {TIER_LABELS[t.tier] || t.tier}
                    <span className="ml-1 font-normal text-muted">{pct}%</span>
                  </p>
                  <p className="mt-0.5 text-[10px] leading-tight text-muted">
                    {TIER_DESCRIPTIONS[t.tier] || ""}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Constitutional Values ─── */

function ConstitutionalCard({ items }: { items: ConstitutionalRiskItem[] }) {
  const values = useMemo(() => groupByValue(items), [items]);
  const [expanded, setExpanded] = useState<number | null>(null);

  if (values.size === 0) {
    return (
      <div className="rounded-xl border border-border bg-white p-6">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">
          Constitutional Values
        </h3>
        <p className="mt-4 text-sm text-muted text-center py-8">
          No constitutional data yet.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-white p-6 space-y-4">
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">
          Constitutional Values
        </h3>
        <p className="mt-0.5 text-xs text-muted">
          How detected behaviors connect to Anthropic&apos;s 4 constitutional priorities via the graph.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {[1, 2, 3, 4].map((p) => {
          const v = values.get(p);
          if (!v) return null;

          const isConstraintOnly = v.strengths === 0 && v.concerns > 0;
          const total = v.strengths + v.concerns;
          const strengthPct = total > 0 ? Math.round((v.strengths / total) * 100) : 0;
          const isExpanded2 = expanded === p;

          return (
            <button
              key={p}
              type="button"
              onClick={() => setExpanded(isExpanded2 ? null : p)}
              className="rounded-lg border border-border/60 bg-border/5 p-4 text-left transition-colors hover:bg-border/10"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-semibold text-foreground">
                    {VALUE_LABELS[p]}
                  </p>
                  <p className="mt-0.5 text-[11px] text-muted">
                    {VALUE_DESCRIPTIONS[p]}
                  </p>
                </div>
                <span className="text-[10px] font-mono text-muted bg-border/30 rounded px-1.5 py-0.5 shrink-0">
                  P{p}
                </span>
              </div>

              {/* Summary stat */}
              <div className="mt-3">
                {isConstraintOnly ? (
                  <div>
                    <p className="text-xs text-foreground/70">
                      <span className="text-lg font-semibold tabular-nums text-misaligned">
                        {v.concerns.toLocaleString()}
                      </span>{" "}
                      <span className="text-muted">detections</span>
                    </p>
                    <p className="mt-0.5 text-[10px] text-muted">
                      Constraint value: only tracks violations
                    </p>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-baseline gap-3">
                      <p className="text-xs text-foreground/70">
                        <span className="text-lg font-semibold tabular-nums text-aligned">
                          {v.strengths.toLocaleString()}
                        </span>{" "}
                        <span className="text-muted">strengths</span>
                      </p>
                      <p className="text-xs text-foreground/70">
                        <span className="text-lg font-semibold tabular-nums text-misaligned">
                          {v.concerns.toLocaleString()}
                        </span>{" "}
                        <span className="text-muted">concerns</span>
                      </p>
                    </div>
                    {/* Ratio bar */}
                    <div className="mt-1.5 flex h-1.5 w-full overflow-hidden rounded-full bg-border/20">
                      <div
                        className="h-full bg-aligned/60"
                        style={{ width: `${strengthPct}%` }}
                      />
                      <div
                        className="h-full bg-misaligned/60"
                        style={{ width: `${100 - strengthPct}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Expanded traits */}
              {isExpanded2 && v.topTraits.length > 0 && (
                <div className="mt-3 space-y-1 border-t border-border/40 pt-2">
                  {v.topTraits.map((t) => (
                    <div
                      key={t.trait}
                      className="flex items-center justify-between text-xs"
                    >
                      <span className="text-muted capitalize">
                        {t.trait.replace(/_/g, " ")}
                      </span>
                      <span
                        className={
                          t.polarity === "positive"
                            ? "text-aligned font-medium"
                            : "text-misaligned font-medium"
                        }
                      >
                        {t.count.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ─── Sabotage Pathways ─── */

function SabotageCard({ pathways }: { pathways: SabotagePathwaySummary[] }) {
  if (pathways.length === 0) return null;

  const totalAgents = new Set(pathways.map((p) => p.patternId)).size;
  const affectedAgents = pathways.reduce((sum, p) => sum + p.agentCount, 0);

  const SEVERITY_STYLES: Record<string, string> = {
    critical: "text-violation bg-violation/10 border-violation/20",
    high: "text-misaligned bg-misaligned/10 border-misaligned/20",
    medium: "text-drifting bg-drifting/10 border-drifting/20",
    low: "text-muted bg-border/10 border-border/20",
    info: "text-muted bg-border/10 border-border/20",
  };

  return (
    <div className="rounded-xl border border-border bg-white p-6 space-y-4">
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">
          Sabotage Pathways
        </h3>
        <p className="mt-0.5 text-xs text-muted">
          Patterns from Anthropic&apos;s{" "}
          <span className="italic">Sabotage Evaluations for Frontier Models</span>{" "}
          detected across {affectedAgents} agent{affectedAgents !== 1 ? "s" : ""}.
        </p>
      </div>

      <div className="space-y-2">
        {pathways.map((p) => (
          <div
            key={p.patternId}
            className="flex items-center justify-between rounded-lg border border-border/60 bg-border/5 px-4 py-3"
          >
            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground truncate">
                {p.patternName}
              </p>
              <p className="mt-0.5 text-xs text-muted">
                {p.agentCount} agent{p.agentCount !== 1 ? "s" : ""}{" "}
                &middot; {Math.round(p.avgConfidence * 100)}% avg confidence
              </p>
            </div>
            <span
              className={`shrink-0 ml-3 rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase ${SEVERITY_STYLES[p.severity] || SEVERITY_STYLES.info}`}
            >
              {p.severity}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Main component ─── */

interface CohortInsightsProps {
  onAgentClick?: (agentId: string) => void;
}

export default function CohortInsights({ onAgentClick }: CohortInsightsProps) {
  const [data, setData] = useState<CohortInsightsResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSimilarity, setShowSimilarity] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getCohortInsights()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load alumni insights");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const alignedPct = useMemo(() => {
    if (!data) return 0;
    const statuses = data.depth.statuses;
    const total = statuses.reduce((sum, s) => sum + s.count, 0);
    const aligned = statuses.find((s) => s.status === "aligned")?.count ?? 0;
    return total > 0 ? Math.round((aligned / total) * 100) : 0;
  }, [data]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-xl border border-border bg-white px-5 py-4">
              <div className="h-10 rounded bg-border/20 animate-pulse" />
            </div>
          ))}
        </div>
        {[1, 2].map((i) => (
          <div key={i} className="rounded-xl border border-border bg-white p-6">
            <div className="flex h-32 items-center justify-center">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted border-t-teal" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-border bg-white p-6">
        <p className="text-sm text-misaligned">{error}</p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Hero stats */}
      <HeroStats
        agentCount={data.agentCount}
        evaluationCount={data.evaluationCount}
        alignedPct={alignedPct}
      />

      {/* Alumni health (alignment + depth) */}
      <CohortHealthCard
        tiers={data.depth.tiers}
        statuses={data.depth.statuses}
      />

      {/* Constitutional values */}
      <ConstitutionalCard items={data.constitutional} />

      {/* Sabotage pathways */}
      <SabotageCard pathways={data.sabotage} />

      {/* Similarity network (collapsed) */}
      <div className="rounded-xl border border-border bg-white">
        <button
          type="button"
          onClick={() => setShowSimilarity(!showSimilarity)}
          className="flex w-full items-center justify-between px-6 py-4 text-left"
        >
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">
              Behavioral Similarity
            </h3>
            <p className="mt-0.5 text-xs text-muted">
              Force-directed graph of agent behavioral overlap (top connections)
            </p>
          </div>
          <svg
            className={`h-4 w-4 text-muted transition-transform ${showSimilarity ? "rotate-180" : ""}`}
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
              clipRule="evenodd"
            />
          </svg>
        </button>
        {showSimilarity && (
          <div className="border-t border-border px-6 pb-6 pt-4">
            <SimilarityNetwork onAgentClick={onAgentClick} />
          </div>
        )}
      </div>
    </div>
  );
}
