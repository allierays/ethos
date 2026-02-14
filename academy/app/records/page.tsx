"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { fadeUp, staggerContainer } from "../../lib/motion";
import { getRecords } from "../../lib/api";
import type { RecordItem, RecordsResult } from "../../lib/types";
import { ALIGNMENT_STYLES, DIMENSIONS } from "../../lib/colors";
import SpectrumBar from "../../components/shared/SpectrumBar";
import IntentSummary from "../../components/shared/IntentSummary";

/* ─── Constants ─── */

const PAGE_SIZE = 20;
const DEBOUNCE_MS = 300;

const ALIGNMENT_LABELS: Record<string, string> = {
  aligned: "Aligned",
  developing: "Developing",
  drifting: "Drifting",
  misaligned: "Misaligned",
};

const ALIGNMENT_CHIP_STYLES: Record<string, string> = {
  aligned: "bg-aligned/20 text-aligned border-aligned/40",
  developing: "bg-sky-100 text-sky-700 border-sky-300",
  drifting: "bg-drifting/20 text-drifting border-drifting/40",
  misaligned: "bg-misaligned/20 text-misaligned border-misaligned/40",
};

type SortKey = "date" | "score" | "agent";
type SortOrder = "asc" | "desc";

/* ─── Inline Components ─── */

function Chip({
  label,
  active,
  onClick,
  activeClass,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  activeClass?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium transition-all ${
        active
          ? activeClass ?? "bg-action/15 text-action border-action/30"
          : "border-white/30 bg-white/50 text-muted hover:bg-white/70 hover:text-foreground"
      }`}
    >
      {label}
    </button>
  );
}

function FacetGroup({ title, children, last }: { title: string; children: React.ReactNode; last?: boolean }) {
  return (
    <div className={last ? "pt-1" : "border-b border-white/20 pb-4 mb-4"}>
      <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted/70 mb-2.5">{title}</h3>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

function DimensionBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] font-medium text-muted w-6">{label}</span>
      <div className="relative flex-1 h-1.5 rounded-full bg-muted/10">
        <div
          className="absolute inset-y-0 left-0 rounded-full"
          style={{ width: `${Math.round(value * 100)}%`, backgroundColor: color, opacity: 0.7 }}
        />
      </div>
      <span className="text-[10px] tabular-nums text-muted/80 w-6 text-right">{Math.round(value * 100)}</span>
    </div>
  );
}

function RecordCard({ record }: { record: RecordItem }) {
  const [expanded, setExpanded] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const alignmentStyle = ALIGNMENT_STYLES[record.alignmentStatus] ?? "bg-muted/10 text-muted";
  const alignmentLabel = ALIGNMENT_LABELS[record.alignmentStatus] ?? record.alignmentStatus;
  const date = new Date(record.createdAt);
  const timeAgo = formatTimeAgo(date);

  const preview = record.messageContent
    ? expanded
      ? record.messageContent
      : record.messageContent.slice(0, 180) + (record.messageContent.length > 180 ? "..." : "")
    : null;

  return (
    <motion.div
      variants={fadeUp}
      className="rounded-2xl border border-white/30 bg-white/40 backdrop-blur-2xl p-5 shadow-sm transition-all hover:shadow-md hover:border-white/50"
    >
      {/* Header: agent + alignment + time */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            href={`/agent/${encodeURIComponent(record.agentId)}`}
            className="text-sm font-semibold text-foreground hover:text-action transition-colors"
          >
            {record.agentName || record.agentId}
          </Link>
          <p className="mt-0.5 text-[11px] text-muted/70">{timeAgo}</p>
        </div>
        <span className={`shrink-0 rounded-lg px-2.5 py-1 text-[11px] font-bold ${alignmentStyle}`}>
          {alignmentLabel}
        </span>
      </div>

      {/* Spectrum bar */}
      <div className="mt-3">
        <SpectrumBar score={record.overall} size="sm" />
      </div>

      {/* Dimension bars */}
      <div className="mt-2.5 space-y-1">
        {DIMENSIONS.map((dim) => (
          <DimensionBar
            key={dim.key}
            label={dim.sublabel[0]}
            value={record[dim.key as keyof RecordItem] as number}
            color={dim.color}
          />
        ))}
      </div>

      {/* Intent + flags */}
      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        {record.intentClassification && (
          <IntentSummary intent={record.intentClassification} />
        )}
        {record.flags.map((flag) => (
          <span
            key={flag}
            className="rounded-full bg-misaligned/10 px-2 py-0.5 text-[10px] font-medium text-misaligned"
          >
            {flag}
          </span>
        ))}
      </div>

      {/* Message preview */}
      {preview && (
        <div className="mt-3">
          <p className="text-xs text-foreground/80 leading-relaxed">
            {preview}
          </p>
          {record.messageContent.length > 180 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-1 text-[11px] font-medium text-action hover:underline"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>
      )}

      {/* Show analysis toggle */}
      {record.scoringReasoning && (
        <div className="mt-3 border-t border-white/20 pt-3">
          <button
            onClick={() => setShowAnalysis(!showAnalysis)}
            className="text-[11px] font-medium text-muted hover:text-foreground transition-colors flex items-center gap-1"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              className={`transition-transform ${showAnalysis ? "rotate-90" : ""}`}
            >
              <path d="M9 18l6-6-6-6" />
            </svg>
            {showAnalysis ? "Hide analysis" : "Show analysis"}
          </button>
          {showAnalysis && (
            <p className="mt-2 text-[11px] text-foreground/70 leading-relaxed">
              {record.scoringReasoning}
            </p>
          )}
        </div>
      )}
    </motion.div>
  );
}

function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/* ─── Page ─── */

export default function RecordsPage() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [data, setData] = useState<RecordsResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [alignmentFilter, setAlignmentFilter] = useState<Set<string>>(new Set());
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null);

  // Debounce search input
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setDebouncedQuery(query);
      setPage(1);
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  // Map frontend sort keys to API sort param
  const apiSort = sortKey === "date" ? "date" : sortKey === "score" ? "score" : "agent";

  // Build alignment param (comma-separated)
  const alignmentParam = alignmentFilter.size > 0 ? Array.from(alignmentFilter).join(",") : undefined;

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getRecords({
        q: debouncedQuery || undefined,
        alignment: alignmentParam,
        flagged: flaggedOnly || undefined,
        sort: apiSort,
        order: sortOrder,
        page: page - 1,
        size: PAGE_SIZE,
      });
      setData(result);
    } catch {
      setError("Could not load records. Is the API running?");
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, alignmentParam, flaggedOnly, apiSort, sortOrder, page]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  function toggleAlignment(status: string) {
    setAlignmentFilter((prev) => {
      const next = new Set(prev);
      if (next.has(status)) next.delete(status);
      else next.add(status);
      return next;
    });
    setPage(1);
  }

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortOrder(key === "date" ? "desc" : "asc");
    }
    setPage(1);
  }

  const activeFilterCount = alignmentFilter.size + (flaggedOnly ? 1 : 0);

  function clearFilters() {
    setAlignmentFilter(new Set());
    setFlaggedOnly(false);
    setQuery("");
    setDebouncedQuery("");
    setPage(1);
  }

  const items = data?.items ?? [];
  const totalPages = data?.totalPages ?? 0;

  return (
    <main className="bg-background min-h-[calc(100vh-3.5rem)]">
      {/* Header */}
      <section className="border-b border-white/20 bg-white/30 backdrop-blur-2xl">
        <div className="px-6 py-10 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Records
          </h1>
          <p className="mt-2 text-base text-muted max-w-lg mx-auto">
            Every evaluation scored by Ethos. Search, filter, and explore the full record of agent behavior.
          </p>
        </div>
      </section>

      {/* Two-column layout */}
      <div className="px-6 pb-16 pt-6">
        <div className="flex flex-col lg:flex-row gap-6">

          {/* Left sidebar */}
          <aside className="w-full lg:w-56 shrink-0">
            <div className="lg:sticky lg:top-20 rounded-2xl border border-white/30 bg-white/40 backdrop-blur-2xl p-5">
              <h2 className="text-sm font-bold text-foreground mb-4">Filters</h2>

              <FacetGroup title="Alignment">
                {Object.entries(ALIGNMENT_LABELS).map(([status, label]) => (
                  <Chip
                    key={status}
                    label={label}
                    active={alignmentFilter.has(status)}
                    onClick={() => toggleAlignment(status)}
                    activeClass={ALIGNMENT_CHIP_STYLES[status]}
                  />
                ))}
              </FacetGroup>

              <FacetGroup title="Flags" last>
                <Chip
                  label="Flagged only"
                  active={flaggedOnly}
                  onClick={() => { setFlaggedOnly(!flaggedOnly); setPage(1); }}
                  activeClass="bg-misaligned/20 text-misaligned border-misaligned/40"
                />
              </FacetGroup>

              {activeFilterCount > 0 && (
                <button
                  onClick={clearFilters}
                  className="mt-3 w-full text-center text-xs font-medium text-action hover:underline"
                >
                  Clear {activeFilterCount} filter{activeFilterCount !== 1 ? "s" : ""}
                </button>
              )}
            </div>
          </aside>

          {/* Main content */}
          <div className="flex-1 min-w-0">
            {/* Search bar */}
            <search role="search" aria-label="Search records">
              <div className="flex rounded-2xl border border-border/60 bg-surface/80 backdrop-blur-xl shadow-lg">
                <span className="flex items-center pl-4 text-muted">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="8" />
                    <path d="M21 21l-4.35-4.35" />
                  </svg>
                </span>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search by agent name or message content..."
                  aria-label="Search records"
                  className="flex-1 bg-transparent px-3 py-4 text-sm placeholder:text-muted/60 focus:outline-none"
                />
                {query && (
                  <button
                    onClick={() => { setQuery(""); setDebouncedQuery(""); }}
                    aria-label="Clear search"
                    className="pr-4 text-muted hover:text-foreground transition-colors"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <path d="M18 6L6 18M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            </search>

            {/* Results header */}
            <section aria-label="Records" aria-live="polite" className="pt-6">
              {!loading && !error && (
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <p className="text-sm text-muted">
                    {data?.total ?? 0} record{data?.total !== 1 ? "s" : ""}
                    {debouncedQuery ? ` matching "${debouncedQuery}"` : ""}
                    {activeFilterCount > 0 && !debouncedQuery ? " filtered" : ""}
                  </p>

                  {/* Sort pills */}
                  <div className="flex rounded-xl border border-border/60 bg-surface/80 backdrop-blur-xl overflow-hidden">
                    {(["date", "score", "agent"] as SortKey[]).map((key) => (
                      <button
                        key={key}
                        onClick={() => toggleSort(key)}
                        className={`px-3 py-1.5 text-xs font-medium transition-colors flex items-center gap-1 ${
                          sortKey === key
                            ? "bg-action/10 text-action"
                            : "text-muted hover:text-foreground"
                        }`}
                      >
                        {key === "date" ? "Date" : key === "score" ? "Score" : "Agent"}
                        {sortKey === key && (
                          <span className="text-[10px]">{sortOrder === "asc" ? "\u2191" : "\u2193"}</span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Loading state */}
              {loading && (
                <div className="flex justify-center py-20">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-teal" />
                </div>
              )}

              {/* Error state */}
              {error && (
                <div className="py-16 text-center">
                  <p className="text-misaligned">{error}</p>
                  <button
                    onClick={fetchRecords}
                    className="mt-3 text-sm font-medium text-action hover:underline"
                  >
                    Retry
                  </button>
                </div>
              )}

              {/* Empty state */}
              {!loading && !error && items.length === 0 && (
                <div className="py-16 text-center">
                  <p className="text-lg text-muted">
                    {debouncedQuery || activeFilterCount > 0
                      ? "No records match the current filters."
                      : "No evaluation records yet."}
                  </p>
                  {(debouncedQuery || activeFilterCount > 0) && (
                    <button
                      onClick={clearFilters}
                      className="mt-3 text-sm font-medium text-action hover:underline"
                    >
                      Clear all filters
                    </button>
                  )}
                </div>
              )}

              {/* Record cards */}
              {!loading && !error && items.length > 0 && (
                <motion.div
                  key={`${page}-${sortKey}-${sortOrder}`}
                  className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3"
                  initial="hidden"
                  animate="visible"
                  variants={staggerContainer}
                >
                  {items.map((record) => (
                    <RecordCard key={record.evaluationId} record={record} />
                  ))}
                </motion.div>
              )}

              {/* Pagination */}
              {!loading && !error && totalPages > 1 && (
                <div className="mt-8 flex items-center justify-center gap-3">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="rounded-xl border border-border/60 bg-surface/80 backdrop-blur-xl px-4 py-2 text-sm font-medium text-foreground transition-all hover:border-action hover:text-action disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-muted tabular-nums">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="rounded-xl border border-border/60 bg-surface/80 backdrop-blur-xl px-4 py-2 text-sm font-medium text-foreground transition-all hover:border-action hover:text-action disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
