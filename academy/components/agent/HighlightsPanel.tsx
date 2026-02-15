"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "motion/react";
import { getHighlights } from "../../lib/api";
import type { HighlightsResult, HighlightItem, HighlightIndicator } from "../../lib/types";
import { fadeUp, whileInView } from "../../lib/motion";
import GlossaryTerm from "../shared/GlossaryTerm";
import SpectrumBar from "../shared/SpectrumBar";
import AlignmentBadge from "../shared/AlignmentBadge";
import IntentSummary from "../shared/IntentSummary";
import AnnotatedMessage from "../shared/AnnotatedMessage";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBrain, faEnvelope, faChartBar, faFingerprint, faCrosshairs } from "@fortawesome/free-solid-svg-icons";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { DIMENSIONS, DIMENSION_COLORS, TRAIT_DIMENSIONS, TRAIT_LABELS, spectrumColor } from "../../lib/colors";

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

interface HighlightsPanelProps {
  agentId: string;
  agentName?: string;
}

/** Clean markdown syntax from text. */
function cleanMarkdown(text: string): string {
  return text
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/```[^`]*```/g, "")
    .replace(/```[^`]*$/g, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/#{1,6}\s/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/<[^>]+>/g, "")
    .replace(/\*\*[^*]*$/g, "")
    .replace(/\uFFFD/g, "")
    .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}]/gu, "")
    .trim();
}

/* ─── Reasoning text with dimension highlights ─── */

const DIMENSION_HIGHLIGHT: { pattern: RegExp; color: string }[] = [
  { pattern: /\b(ethos)\b/gi, color: DIMENSION_COLORS.ethos },
  { pattern: /\b(logos)\b/gi, color: DIMENSION_COLORS.logos },
  { pattern: /\b(pathos)\b/gi, color: DIMENSION_COLORS.pathos },
];

function HighlightedSpan({ text }: { text: string }) {
  const parts = text.split(/\b(ethos|logos|pathos)\b/gi);
  return (
    <>
      {parts.map((part, i) => {
        const match = DIMENSION_HIGHLIGHT.find((d) => d.pattern.test(part));
        if (match) {
          match.pattern.lastIndex = 0;
          return (
            <span key={i} className="font-bold" style={{ color: match.color }}>
              {part}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

function HighlightedReasoning({ text }: { text: string }) {
  const sentences = text.split(/(?<=\.)\s+(?=[A-Z])/);
  return (
    <>
      {sentences.map((sentence, i) => (
        <p key={i} className={i < sentences.length - 1 ? "mb-2.5" : ""}>
          <HighlightedSpan text={sentence} />
        </p>
      ))}
    </>
  );
}

/* ─── Inline helpers (match Records styling) ─── */

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

function IndicatorGroup({ indicators }: { indicators: HighlightIndicator[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {indicators.map((ind, i) => (
        <div key={`${ind.name}-${i}`} className="rounded-lg border border-border/30 bg-white/80 p-3.5">
          <div className="flex items-start justify-between gap-2">
            <span className="text-sm font-semibold text-foreground leading-tight">{ind.name.replace(/_/g, " ")}</span>
            <SeverityPill severity={ind.confidence} />
          </div>
          <div className="flex items-center gap-2 mt-1.5">
            <ScoreBar value={ind.confidence} color={DIMENSION_COLORS.logos} height="h-1" />
            <span className="text-xs tabular-nums text-muted/70 shrink-0">{Math.round(ind.confidence * 100)}% conf</span>
          </div>
          <div className="flex items-center gap-2 mt-2">
            <span className="rounded-full bg-muted/10 px-2 py-0.5 text-[10px] font-medium text-muted uppercase tracking-wide">
              {TRAIT_LABELS[ind.trait] ?? ind.trait ?? "unknown"}
            </span>
          </div>
          {ind.evidence && (
            <p className="text-xs text-foreground/60 leading-relaxed border-l-2 border-muted/20 pl-2.5 mt-2">
              {ind.evidence}
            </p>
          )}
        </div>
      ))}
    </div>
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
  const btnRef = useRef<HTMLButtonElement>(null);

  // When a non-default section opens, keep its button visible so the user
  // doesn't lose context about what they clicked.
  useEffect(() => {
    if (open && !defaultOpen && btnRef.current) {
      // Small delay lets the DOM settle after content appears.
      const id = setTimeout(() => {
        btnRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }, 60);
      return () => clearTimeout(id);
    }
  }, [open, defaultOpen]);

  return (
    <div>
      <button
        ref={btnRef}
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2.5 w-full rounded-lg bg-[#ded8ce]/30 px-3 py-2 group hover:bg-[#ded8ce]/60 hover:shadow-sm cursor-pointer transition-all duration-200 border-l-3"
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
        <h4 className="text-xs font-bold uppercase tracking-wider text-foreground group-hover:text-coral transition-colors">
          {title}
        </h4>
      </button>
      {/* initial={false} prevents defaultOpen sections from animating on mount,
          avoiding nested height animations fighting with the parent ExpandedHighlight.
          Opacity-only animation avoids gradual height changes that fight browser
          scroll anchoring and cause the page to jump. */}
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
          >
            <div className="pt-2">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Expanded Detail (matches Records ExpandedDetail) ─── */

function ExpandedHighlight({ item }: { item: HighlightItem }) {
  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: "auto", opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.25, ease: "easeInOut" }}
      className="overflow-hidden"
    >
      <div className="border-t border-border/30 bg-white/60 [&>div]:px-5 [&>div]:py-3">
        {/* Overall score spectrum */}
        <div>
          <div className="max-w-xs">
            <SpectrumBar score={item.overall} size="sm" />
          </div>
        </div>

        {/* Message content */}
        {item.messageContent && (
          <DetailSection title="Original Message" icon={faEnvelope} accent="#64748b">
            <AnnotatedMessage
              content={cleanMarkdown(item.messageContent)}
              indicators={item.indicators}
              scoringReasoning={item.scoringReasoning}
              intentClassification={item.intentClassification}
            />
          </DetailSection>
        )}

        {/* Reasoning + Dimensions (merged) */}
        <DetailSection title="Reasoning" icon={faBrain} accent={DIMENSION_COLORS.ethos}>
          {item.scoringReasoning && (
            <blockquote className="relative text-sm text-foreground/90 leading-[1.8] bg-white/90 border-l-[5px] rounded-r-xl px-5 py-4 shadow-sm mb-4" style={{ borderColor: DIMENSION_COLORS.ethos }}>
              <svg className="absolute top-3 right-4 w-8 h-8 opacity-[0.06]" viewBox="0 0 24 24" fill="currentColor"><path d="M4.583 17.321C3.553 16.227 3 15 3 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311 1.804.167 3.226 1.648 3.226 3.489a3.5 3.5 0 01-3.5 3.5c-1.073 0-2.099-.49-2.748-1.179zm10 0C13.553 16.227 13 15 13 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311 1.804.167 3.226 1.648 3.226 3.489a3.5 3.5 0 01-3.5 3.5c-1.073 0-2.099-.49-2.748-1.179z"/></svg>
              <HighlightedReasoning text={item.scoringReasoning} />
            </blockquote>
          )}
          <div className="space-y-2.5">
            {DIMENSIONS.map((dim) => {
              const val = item[dim.key as keyof HighlightItem] as number;
              return (
                <div key={dim.key} className="flex items-center gap-3">
                  <span className="text-xs font-semibold w-14 shrink-0" style={{ color: dim.color }}>{dim.sublabel}</span>
                  <ScoreBar value={val} color={dim.color} height="h-2" />
                  <span className="text-sm font-bold tabular-nums w-8 text-right shrink-0" style={{ color: dim.color }}>{Math.round(val * 100)}</span>
                </div>
              );
            })}
          </div>
        </DetailSection>

        {/* Trait scores grouped by dimension */}
        {Object.keys(item.traitScores ?? {}).length > 0 && (
          <DetailSection title="Trait Scores" icon={faChartBar} accent={DIMENSION_COLORS.logos}>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {TRAIT_GROUPS.map((group) => (
                <div key={group.dimension}>
                  <h5 className="text-xs font-bold mb-2" style={{ color: group.color }}>
                    {group.label}
                  </h5>
                  <div className="space-y-1">
                    {group.traits.map((trait) => {
                      const val = item.traitScores[trait];
                      if (val === undefined) return null;
                      return (
                        <div key={trait} className="flex items-center gap-2">
                          <span className="text-xs text-muted w-24 truncate">
                            {TRAIT_LABELS[trait] ?? trait}
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
        {item.intentClassification && (
          <DetailSection title="Intent" icon={faCrosshairs} accent={DIMENSION_COLORS.pathos}>
            <div className="space-y-3">
              <IntentSummary intent={item.intentClassification} />
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="rounded-lg bg-white/80 border border-border/20 p-2.5">
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted block mb-0.5">What&apos;s at stake</span>
                  <span className="text-sm text-foreground capitalize">{item.intentClassification.stakesReality}</span>
                </div>
                <div className="rounded-lg bg-white/80 border border-border/20 p-2.5">
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted block mb-0.5">Who&apos;s speaking</span>
                  <span className="text-sm text-foreground capitalize">{item.intentClassification.personaType.replace(/_/g, " ")}</span>
                </div>
                <div className="rounded-lg bg-white/80 border border-border/20 p-2.5">
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted block mb-0.5">Relationship</span>
                  <span className="text-sm text-foreground capitalize">{item.intentClassification.relationalQuality}</span>
                </div>
                <div className="rounded-lg bg-white/80 border border-border/20 p-2.5">
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted block mb-0.5">Asks the reader to</span>
                  <span className="text-sm text-foreground capitalize">{item.intentClassification.actionRequested}</span>
                </div>
              </div>
            </div>
          </DetailSection>
        )}

        {/* Detected indicators */}
        {item.indicators?.length > 0 && (
          <DetailSection title={`Detected Indicators (${item.indicators.length})`} icon={faFingerprint} accent="#2e4a6e">
            <IndicatorGroup indicators={item.indicators} />
          </DetailSection>
        )}
      </div>
    </motion.div>
  );
}

/* ─── Row (matches Records RecordRow) ─── */

function HighlightRow({
  item,
  type,
  expanded,
  onToggle,
}: {
  item: HighlightItem;
  type: "exemplary" | "concerning";
  expanded: boolean;
  onToggle: () => void;
}) {
  const scorePct = Math.round(item.overall * 100);
  const scoreColor = spectrumColor(item.overall);
  const timeAgo = item.createdAt ? formatTimeAgo(new Date(item.createdAt)) : "";
  const isExemplary = type === "exemplary";

  return (
    <div className={`transition-all duration-200 ${expanded ? "bg-white/40" : "hover:bg-white/50 hover:shadow-sm"}`}>
      <button
        onClick={onToggle}
        className="w-full text-left px-4 py-3 flex items-center gap-3 cursor-pointer border-l-3 border-coral"
        aria-expanded={expanded}
      >
        {/* Score */}
        <div className="w-12 shrink-0 text-center">
          <span className="text-sm font-bold tabular-nums" style={{ color: scoreColor }}>
            {scorePct}
          </span>
        </div>

        {/* Message preview + label */}
        <div className="flex-1 min-w-0">
          <p className="text-xs text-foreground/80 truncate leading-snug">
            {item.messageContent ? cleanMarkdown(item.messageContent) : <span className="italic text-muted/50">No message content</span>}
          </p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={`text-[11px] font-semibold ${isExemplary ? "text-aligned" : "text-drifting"}`}>
              {isExemplary ? "Strongest Character" : "Most Concerning"}
            </span>
            {timeAgo && (
              <>
                <span className="text-[9px] text-muted/40">|</span>
                <span className="text-[10px] text-muted/50">{timeAgo}</span>
              </>
            )}
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
                    width: `${Math.round((item[dim.key as keyof HighlightItem] as number) * 100)}%`,
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
          <AlignmentBadge status={item.alignmentStatus} className="text-[10px] px-2 py-0.5" />
        </div>

        {/* Top signals */}
        <div className="w-36 shrink-0 hidden lg:block">
          {(() => {
            const flags = item.flags.filter((f) => ["manipulation", "fabrication", "deception", "exploitation"].includes(f));
            const top = [...(item.indicators ?? [])]
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
                  <span key={ind.name} className="text-[10px] text-muted leading-snug">{ind.name.replace(/_/g, " ")}</span>
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
        {expanded && <ExpandedHighlight item={item} />}
      </AnimatePresence>
    </div>
  );
}

/* ─── Main Panel ─── */

export default function HighlightsPanel({ agentId, agentName }: HighlightsPanelProps) {
  const [data, setData] = useState<HighlightsResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getHighlights(agentId)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        console.error("HighlightsPanel failed to load:", err);
        if (!cancelled) setError("Failed to load highlights");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [agentId]);

  if (loading) return null;
  if (error) {
    return (
      <section className="rounded-xl glass-strong px-6 py-5">
        <p className="text-xs text-muted">{error}</p>
      </section>
    );
  }
  if (!data) return null;

  const best = data.exemplary.find((e) => e.messageContent);
  const worst = data.concerning.find((e) => e.messageContent);
  if (!best && !worst) return null;

  const name = agentName ?? "this agent";

  return (
    <motion.section
      className="rounded-xl bg-[#2e4a6e]/15 border border-[#2e4a6e]/20 px-6 py-5"
      {...whileInView}
      variants={fadeUp}
    >
      <h2 className="text-base font-semibold uppercase tracking-wider text-[#2e4a6e]">
        <GlossaryTerm slug="highlights">In {name}&apos;s Own Words</GlossaryTerm>
      </h2>
      <p className="mt-1 text-xs text-[#2e4a6e]/70">
        Character reveals itself in specifics. The strongest and most concerning moments of practical wisdom.
      </p>

      {/* Highlight cards */}
      <div className="mt-4 space-y-4">
        {best && (
          <div className="rounded-2xl border border-white/60 bg-white/90 shadow-sm overflow-hidden transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 hover:bg-white">
            <HighlightRow
              item={best}
              type="exemplary"
              expanded={expandedId === best.evaluationId}
              onToggle={() => setExpandedId((prev) => prev === best.evaluationId ? null : best.evaluationId)}
            />
          </div>
        )}
        {worst && (
          <div className="rounded-2xl border border-white/60 bg-white/90 shadow-sm overflow-hidden transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 hover:bg-white">
            <HighlightRow
              item={worst}
              type="concerning"
              expanded={expandedId === worst.evaluationId}
              onToggle={() => setExpandedId((prev) => prev === worst.evaluationId ? null : worst.evaluationId)}
            />
          </div>
        )}
      </div>

      <div className="mt-5 text-center">
        <Link
          href={`/records?agent=${encodeURIComponent(agentId)}`}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-coral hover:underline transition-colors"
        >
          See all records
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </Link>
      </div>
    </motion.section>
  );
}
