"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "motion/react";
import { getRecords } from "../../lib/api";
import type { RecordItem, RecordsResult, DetectedIndicatorSummary } from "../../lib/types";
import {
  DIMENSIONS,
  DIMENSION_COLORS,
  TRAIT_LABELS,
  TRAIT_SLUGS,
  TRAIT_DIMENSIONS,
  spectrumColor,
} from "../../lib/colors";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBrain, faEnvelope, faChartBar, faFingerprint, faCrosshairs, faShieldHalved } from "@fortawesome/free-solid-svg-icons";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import AlignmentBadge from "../../components/shared/AlignmentBadge";
import SpectrumBar from "../../components/shared/SpectrumBar";
import IntentSummary from "../../components/shared/IntentSummary";
import AnnotatedMessage from "../../components/shared/AnnotatedMessage";
import ReasoningText from "../../components/shared/ReasoningText";
import GlossaryTerm from "../../components/shared/GlossaryTerm";

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

/* ─── Trait grouping by dimension ─── */

const TRAIT_GROUPS: { dimension: string; label: string; color: string; traits: string[] }[] = [
  {
    dimension: "ethos",
    label: "Ethos",
    color: DIMENSION_COLORS.ethos,
    traits: Object.entries(TRAIT_DIMENSIONS)
      .filter(([, d]) => d === "ethos")
      .map(([t]) => t),
  },
  {
    dimension: "logos",
    label: "Logos",
    color: DIMENSION_COLORS.logos,
    traits: Object.entries(TRAIT_DIMENSIONS)
      .filter(([, d]) => d === "logos")
      .map(([t]) => t),
  },
  {
    dimension: "pathos",
    label: "Pathos",
    color: DIMENSION_COLORS.pathos,
    traits: Object.entries(TRAIT_DIMENSIONS)
      .filter(([, d]) => d === "pathos")
      .map(([t]) => t),
  },
];


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
          : "border-foreground/15 bg-white/60 text-muted hover:bg-white/80 hover:text-foreground"
      }`}
    >
      {label}
    </button>
  );
}

function FacetGroup({ title, children, last }: { title: string; children: React.ReactNode; last?: boolean }) {
  return (
    <div className={last ? "pt-1" : "border-b border-foreground/10 pb-4 mb-4"}>
      <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted/70 mb-2.5">{title}</h3>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

function ScoreBar({ value, color, height = "h-1.5" }: { value: number; color: string; height?: string }) {
  return (
    <div className={`relative flex-1 ${height} rounded-full bg-muted/10`}>
      <div
        className={`absolute inset-y-0 left-0 rounded-full ${height}`}
        style={{ width: `${Math.round(value * 100)}%`, backgroundColor: color, opacity: 0.7 }}
      />
    </div>
  );
}

function SeverityPill({ severity }: { severity: number }) {
  const pct = Math.round(severity * 100);
  let cls = "bg-aligned/10 text-aligned";
  if (pct >= 70) cls = "bg-misaligned/10 text-misaligned";
  else if (pct >= 40) cls = "bg-drifting/10 text-drifting";
  return (
    <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-semibold ${cls}`}>
      sev {pct}
    </span>
  );
}

function IndicatorGroup({ indicators }: { indicators: DetectedIndicatorSummary[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {indicators.map((ind, i) => (
        <div key={`${ind.id}-${i}`} className="rounded-lg border border-border/30 bg-white/80 p-3.5">
          <div className="flex items-start justify-between gap-2">
            <span className="text-sm font-semibold text-foreground leading-tight">{ind.name}</span>
            <SeverityPill severity={ind.severity} />
          </div>
          <div className="flex items-center gap-2 mt-1.5">
            <ScoreBar value={ind.confidence} color={DIMENSION_COLORS.logos} height="h-1" />
            <span className="text-xs tabular-nums text-muted/70 shrink-0">{Math.round(ind.confidence * 100)}% conf</span>
          </div>
          <div className="flex items-center gap-2 mt-2">
            <span className="rounded-full bg-muted/10 px-2 py-0.5 text-[10px] font-medium text-muted uppercase tracking-wide">
              <GlossaryTerm slug={TRAIT_SLUGS[ind.trait] ?? ind.trait}>{TRAIT_LABELS[ind.trait] ?? ind.trait ?? "unknown"}</GlossaryTerm>
            </span>
          </div>
          {ind.evidence && (
            <p className="text-xs text-foreground/80 leading-relaxed border-l-2 border-muted/20 pl-2.5 mt-2">
              {ind.evidence}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

/* ─── Accordion section for expanded details ─── */

function DetailSection({
  title,
  icon,
  accent,
  defaultOpen = false,
  children,
}: {
  title: string;
  icon?: IconDefinition;
  accent?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2.5 w-full rounded-lg bg-[#ded8ce]/30 px-3 py-2 group hover:bg-[#ded8ce]/50 transition-colors border-l-3"
        style={{ borderLeftColor: accent ?? "transparent" }}
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          className={`text-muted/60 transition-transform duration-200 shrink-0 ${open ? "rotate-90" : ""}`}
        >
          <path d="M9 18l6-6-6-6" />
        </svg>
        {icon && <FontAwesomeIcon icon={icon} className="w-3 h-3 shrink-0" style={{ color: accent ?? "currentColor" }} />}
        <h4 className="text-xs font-bold uppercase tracking-wider text-foreground group-hover:text-action transition-colors">
          {title}
        </h4>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="pt-2">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Expanded Row Detail Panel ─── */

function ExpandedDetail({ record }: { record: RecordItem }) {
  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: "auto", opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.25, ease: "easeInOut" }}
      className="overflow-hidden"
    >
      <div className="border-t border-foreground/[0.06] [&>div]:px-5 [&>div]:py-3" style={{ background: "#f5f2ed" }} onClick={(e) => e.stopPropagation()}>
        {/* Overall score spectrum + metadata */}
        <div>
          <div className="max-w-xs mb-3">
            <SpectrumBar score={record.overall} size="sm" />
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs">
            {record.direction && (
              <span className="rounded-full bg-white/40 px-2 py-0.5 text-xs text-muted">
                {record.direction}
              </span>
            )}
            {record.routingTier !== "standard" && (
              <span className="rounded-full bg-action/10 px-2 py-0.5 text-xs text-action font-medium">
                {record.routingTier}
              </span>
            )}
            {record.modelUsed && (
              <span className="text-xs text-muted" title="Model used for evaluation">
                eval: {record.modelUsed}
              </span>
            )}
            {record.agentModel && (
              <span className="text-xs text-muted" title="Agent model">
                agent: {record.agentModel}
              </span>
            )}
          </div>
        </div>

        {/* Message content */}
        {record.messageContent && (
          <DetailSection title="Original Message" icon={faEnvelope} accent="#64748b">
            <AnnotatedMessage
              content={record.messageContent}
              indicators={record.detectedIndicators}
              scoringReasoning={record.scoringReasoning}
              intentClassification={record.intentClassification}
            />
          </DetailSection>
        )}

        {/* Reasoning + Dimensions (merged) */}
        <DetailSection title="Reasoning" icon={faBrain} accent={DIMENSION_COLORS.ethos}>
          {record.scoringReasoning && (
            <blockquote className="relative text-sm text-foreground/90 leading-[1.8] bg-white/90 border-l-[5px] rounded-r-xl px-5 py-4 shadow-sm mb-4" style={{ borderColor: DIMENSION_COLORS.ethos }}>
              <svg className="absolute top-3 right-4 w-8 h-8 opacity-[0.06]" viewBox="0 0 24 24" fill="currentColor"><path d="M4.583 17.321C3.553 16.227 3 15 3 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311 1.804.167 3.226 1.648 3.226 3.489a3.5 3.5 0 01-3.5 3.5c-1.073 0-2.099-.49-2.748-1.179zm10 0C13.553 16.227 13 15 13 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311 1.804.167 3.226 1.648 3.226 3.489a3.5 3.5 0 01-3.5 3.5c-1.073 0-2.099-.49-2.748-1.179z"/></svg>
              <ReasoningText text={record.scoringReasoning} />
            </blockquote>
          )}
          <div className="space-y-2.5">
            {DIMENSIONS.map((dim) => {
              const val = record[dim.key as keyof RecordItem] as number;
              return (
                <div key={dim.key} className="flex items-center gap-3">
                  <span className="text-xs font-semibold w-14 shrink-0" style={{ color: dim.color }}><GlossaryTerm slug={dim.key}>{dim.sublabel}</GlossaryTerm></span>
                  <ScoreBar value={val} color={dim.color} height="h-2" />
                  <span className="text-sm font-bold tabular-nums w-8 text-right shrink-0" style={{ color: dim.color }}>{Math.round(val * 100)}</span>
                </div>
              );
            })}
          </div>
        </DetailSection>

        {/* Trait scores grouped by dimension */}
        {Object.keys(record.traitScores).length > 0 && (
          <DetailSection title="Trait Scores" icon={faChartBar} accent={DIMENSION_COLORS.logos}>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {TRAIT_GROUPS.map((group) => (
                <div key={group.dimension}>
                  <h5 className="text-xs font-bold mb-2" style={{ color: group.color }}>
                    <GlossaryTerm slug={group.dimension}>{group.label}</GlossaryTerm>
                  </h5>
                  <div className="space-y-1">
                    {group.traits.map((trait) => {
                      const val = record.traitScores[trait];
                      if (val === undefined) return null;
                      return (
                        <div key={trait} className="flex items-center gap-2">
                          <span className="text-xs text-muted w-24 truncate">
                            <GlossaryTerm slug={TRAIT_SLUGS[trait] ?? trait}>{TRAIT_LABELS[trait] ?? trait}</GlossaryTerm>
                          </span>
                          <ScoreBar value={val} color={group.color} height="h-1" />
                          <span className="text-xs tabular-nums text-muted w-8 text-right">
                            {Math.round(val * 100)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </DetailSection>
        )}

        {/* Intent classification */}
        {record.intentClassification && (
          <DetailSection title="Intent" icon={faCrosshairs} accent={DIMENSION_COLORS.pathos}>
            <div className="space-y-3">
              <IntentSummary intent={record.intentClassification} />
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="rounded-lg bg-white/80 border border-border/20 p-2.5">
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted block mb-0.5">What&apos;s at stake</span>
                  <span className="text-sm text-foreground capitalize">{record.intentClassification.stakesReality}</span>
                </div>
                <div className="rounded-lg bg-white/80 border border-border/20 p-2.5">
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted block mb-0.5">Who&apos;s speaking</span>
                  <span className="text-sm text-foreground capitalize">{record.intentClassification.personaType.replace(/_/g, " ")}</span>
                </div>
                <div className="rounded-lg bg-white/80 border border-border/20 p-2.5">
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted block mb-0.5">Relationship</span>
                  <span className="text-sm text-foreground capitalize">{record.intentClassification.relationalQuality}</span>
                </div>
                <div className="rounded-lg bg-white/80 border border-border/20 p-2.5">
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted block mb-0.5">Asks the reader to</span>
                  <span className="text-sm text-foreground capitalize">{record.intentClassification.actionRequested}</span>
                </div>
              </div>
            </div>
          </DetailSection>
        )}

        {/* Detected indicators */}
        {(record.detectedIndicators?.length ?? 0) > 0 && (
          <DetailSection title={`Detected Indicators (${record.detectedIndicators.length})`} icon={faFingerprint} accent="#2e4a6e">
            <IndicatorGroup indicators={record.detectedIndicators} />
          </DetailSection>
        )}

        {/* Metadata */}
        {record.keywordDensity > 0 && (
          <DetailSection title="Metadata" icon={faShieldHalved} accent="#64748b">
            <div className="flex gap-4 text-xs text-muted">
              <span>Keyword density: {(record.keywordDensity * 100).toFixed(1)}%</span>
            </div>
          </DetailSection>
        )}
      </div>
    </motion.div>
  );
}

/* ─── Table Row ─── */

function RecordRow({
  record,
  expanded,
  onToggle,
  index,
}: {
  record: RecordItem;
  expanded: boolean;
  onToggle: () => void;
  index: number;
}) {
  const timeAgo = formatTimeAgo(new Date(record.createdAt));
  const scorePct = Math.round(record.overall * 100);
  const scoreColor = spectrumColor(record.overall);
  const isOdd = index % 2 === 1;

  // Alternating white / taupe rows
  const rowBg = isOdd ? "#f3efe9" : "#ffffff";
  const hoverBg = isOdd ? "#ede8e1" : "#f5f3f0";

  return (
    <tr
      className="border-b border-foreground/[0.06] transition-colors cursor-pointer"
      style={{ background: expanded ? "#f0ece6" : rowBg }}
      onMouseEnter={(e) => { if (!expanded) e.currentTarget.style.background = hoverBg; }}
      onMouseLeave={(e) => { if (!expanded) e.currentTarget.style.background = rowBg; }}
      onClick={onToggle}
      data-evaluation-id={record.evaluationId}
      data-agent={record.agentId}
      data-score={scorePct}
      data-alignment={record.alignmentStatus}
      data-ethos={Math.round(record.ethos * 100)}
      data-logos={Math.round(record.logos * 100)}
      data-pathos={Math.round(record.pathos * 100)}
    >
      <td colSpan={6} className="p-0 overflow-hidden">
        <button
          onClick={(e) => { e.stopPropagation(); onToggle(); }}
          className="w-full text-left px-2 sm:px-4 py-3 flex items-center gap-3 cursor-pointer"
          aria-expanded={expanded}
        >
          {/* Score */}
          <div className="w-12 shrink-0 text-center">
            <span className="text-sm font-bold tabular-nums" style={{ color: scoreColor }}>
              {scorePct}
            </span>
          </div>

          {/* Message preview + agent subtitle */}
          <div className="flex-1 min-w-0">
            <p className="text-sm text-foreground/80 truncate leading-snug">
              {record.messageContent || <span className="italic text-muted/50">No message content</span>}
            </p>
            <div className="flex items-center gap-2 mt-0.5">
              <Link
                href={`/agent/${encodeURIComponent(record.agentId)}`}
                onClick={(e) => e.stopPropagation()}
                className="text-[11px] font-semibold text-foreground/70 hover:text-action transition-colors truncate"
              >
                {record.agentName || record.agentId}
              </Link>
              <span className="text-[9px] text-muted/40">|</span>
              <time dateTime={record.createdAt} className="text-[10px] text-muted/50">{timeAgo}</time>
            </div>
          </div>

          {/* E/L/P mini bars */}
          <div className="w-24 shrink-0 space-y-0.5 hidden sm:block">
            {DIMENSIONS.map((dim) => (
              <div key={dim.key} className="flex items-center gap-1">
                <span className="text-[8px] text-muted w-2">{dim.sublabel[0]}</span>
                <div className="relative flex-1 h-1 rounded-full bg-muted/10">
                  <div
                    className="absolute inset-y-0 left-0 rounded-full h-1"
                    style={{
                      width: `${Math.round((record[dim.key as keyof RecordItem] as number) * 100)}%`,
                      backgroundColor: dim.color,
                      opacity: 0.6,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Alignment */}
          <div className="w-22 shrink-0 hidden md:block">
            <AlignmentBadge status={record.alignmentStatus} className="text-[10px] px-2 py-0.5" />
          </div>

          {/* Top signals */}
          <div className="w-36 shrink-0 hidden lg:block">
            {(() => {
              const flags = record.flags.filter((f) => ["manipulation", "fabrication", "deception", "exploitation"].includes(f));
              const top = [...(record.detectedIndicators ?? [])]
                .sort((a, b) => b.confidence - a.confidence)
                .slice(0, flags.length > 0 ? 1 : 2);
              if (flags.length === 0 && top.length === 0) {
                return <span className="text-[10px] text-muted/40">--</span>;
              }
              return (
                <div className="flex flex-col gap-0.5">
                  {flags.slice(0, 1).map((flag) => (
                    <span key={flag} className="text-[10px] font-medium text-misaligned leading-snug">{flag}</span>
                  ))}
                  {top.map((ind) => (
                    <span key={ind.id} className="text-[10px] text-muted leading-snug">{ind.name.replace(/_/g, " ")}</span>
                  ))}
                </div>
              );
            })()}
          </div>

          {/* Chevron */}
          <div className="w-5 shrink-0 flex justify-center">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              className={`text-muted/50 transition-transform duration-200 ${expanded ? "rotate-90" : ""}`}
            >
              <path d="M9 18l6-6-6-6" />
            </svg>
          </div>
        </button>

        <AnimatePresence>
          {expanded && <ExpandedDetail record={record} />}
        </AnimatePresence>
      </td>
    </tr>
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

export default function RecordsClient({
  initialData,
  initialAgent,
}: {
  initialData: RecordsResult | null;
  initialAgent?: string;
}) {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [data, setData] = useState<RecordsResult | null>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [alignmentFilter, setAlignmentFilter] = useState<Set<string>>(new Set());
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [agentFilter, setAgentFilter] = useState<string | undefined>(initialAgent);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null);
  const mountedRef = useRef(false);

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
        agent: agentFilter,
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
  }, [debouncedQuery, agentFilter, alignmentParam, flaggedOnly, apiSort, sortOrder, page]);

  useEffect(() => {
    if (!mountedRef.current) {
      mountedRef.current = true;
      return;
    }
    fetchRecords();
  }, [fetchRecords]);

  // Collapse expanded row on page/filter change
  useEffect(() => {
    setExpandedId(null);
  }, [page, debouncedQuery, agentFilter, alignmentParam, flaggedOnly, sortKey, sortOrder]);

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

  const activeFilterCount = alignmentFilter.size + (flaggedOnly ? 1 : 0) + (agentFilter ? 1 : 0);

  function clearFilters() {
    setAlignmentFilter(new Set());
    setFlaggedOnly(false);
    setAgentFilter(undefined);
    setQuery("");
    setDebouncedQuery("");
    setPage(1);
  }

  const items = data?.items ?? [];
  const totalPages = data?.totalPages ?? 0;

  return (
    <main className="min-h-[calc(100vh-3.5rem)]" style={{ background: "#b8b0a3" }}>
      {/* Header */}
      <section className="border-b border-foreground/10" style={{ background: "#9e968a" }}>
        <div className="px-6 py-12 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Records
          </h1>
          <p className="mt-2 text-base text-white/70 max-w-lg mx-auto">
            {agentFilter
              ? <>Evaluations for <Link href={`/agent/${encodeURIComponent(agentFilter)}`} className="font-semibold text-white hover:text-pathos-200 transition-colors">{agentFilter}</Link>. Scored by Ethos Academy.</>
              : "Every evaluation scored by Ethos Academy. Search, filter, and explore the full record of agent behavior."}
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

              {agentFilter && (
                <div className="border-b border-foreground/10 pb-4 mb-4">
                  <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted/70 mb-2.5">Agent</h3>
                  <div className="flex items-center gap-1.5">
                    <span className="inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium bg-action/15 text-action border-action/30">
                      {agentFilter}
                    </span>
                    <button
                      onClick={() => { setAgentFilter(undefined); setPage(1); }}
                      className="text-muted hover:text-foreground transition-colors"
                      aria-label="Clear agent filter"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <path d="M18 6L6 18M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}

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
              <div className="flex rounded-2xl border border-white/40 bg-white/70 backdrop-blur-xl shadow-sm">
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
                  className="flex-1 bg-transparent px-3 py-4 text-sm text-foreground placeholder:text-muted/60 focus:outline-none"
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
                  <p className="text-sm text-white/80">
                    {data?.total ?? 0} record{data?.total !== 1 ? "s" : ""}
                    {debouncedQuery ? ` matching "${debouncedQuery}"` : ""}
                    {activeFilterCount > 0 && !debouncedQuery ? " filtered" : ""}
                  </p>

                  {/* Sort pills */}
                  <div className="flex rounded-xl border border-white/30 bg-white/50 backdrop-blur-xl overflow-hidden">
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
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-white/30 border-t-white" />
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
                  <p className="text-lg text-white/80">
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

              {/* Data table */}
              {!loading && !error && items.length > 0 && (
                <div className="rounded-2xl border border-white/40 overflow-hidden shadow-sm">
                <table className="w-full border-collapse" style={{ tableLayout: "fixed" }} role="grid" aria-label="Evaluation records">
                  <thead>
                    <tr className="border-b border-foreground/[0.06] text-[10px] font-semibold uppercase tracking-wider text-foreground/70" style={{ background: "#f3efe9" }}>
                      <th scope="col" className="px-4 py-2.5 text-left font-semibold w-12 text-center">Score</th>
                      <th scope="col" className="py-2.5 text-left font-semibold">Message</th>
                      <th scope="col" className="py-2.5 text-left font-semibold w-24 hidden sm:table-cell">E/L/P</th>
                      <th scope="col" className="py-2.5 text-left font-semibold w-22 hidden md:table-cell">Alignment</th>
                      <th scope="col" className="py-2.5 text-left font-semibold w-36 hidden lg:table-cell">Signals</th>
                      <th scope="col" className="py-2.5 w-5"><span className="sr-only">Expand</span></th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((record, i) => (
                      <RecordRow
                        key={record.evaluationId}
                        record={record}
                        index={i}
                        expanded={expandedId === record.evaluationId}
                        onToggle={() =>
                          setExpandedId((prev) =>
                            prev === record.evaluationId ? null : record.evaluationId
                          )
                        }
                      />
                    ))}
                  </tbody>
                </table>
                </div>
              )}

              {/* Pagination */}
              {!loading && !error && totalPages > 1 && (
                <div className="mt-8 flex items-center justify-center gap-3">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="rounded-xl border border-white/30 bg-white/50 backdrop-blur-xl px-4 py-2 text-sm font-medium text-foreground transition-all hover:bg-white/70 hover:text-action disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-white/80 tabular-nums">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="rounded-xl border border-white/30 bg-white/50 backdrop-blur-xl px-4 py-2 text-sm font-medium text-foreground transition-all hover:bg-white/70 hover:text-action disabled:opacity-40 disabled:cursor-not-allowed"
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
