"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { getHighlights } from "../../lib/api";
import type { HighlightsResult, HighlightItem, HighlightIndicator } from "../../lib/types";
import { fadeUp, whileInView, staggerContainer } from "../../lib/motion";
import GlossaryTerm from "../shared/GlossaryTerm";

interface HighlightsPanelProps {
  agentId: string;
  agentName?: string;
}

/** Clean markdown syntax from text, keeping structure intact. */
function cleanMarkdown(text: string): string {
  return text
    .replace(/\*\*([^*]+)\*\*/g, "$1")     // **bold**
    .replace(/\*([^*]+)\*/g, "$1")          // *italic*
    .replace(/```[^`]*```/g, "")             // code blocks
    .replace(/```[^`]*$/g, "")               // orphaned opening ```
    .replace(/`([^`]+)`/g, "$1")             // inline code
    .replace(/#{1,6}\s/g, "")                // headings
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // links
    .replace(/<[^>]+>/g, "")                 // HTML tags
    .replace(/\*\*[^*]*$/g, "")              // orphaned opening **
    .replace(/\uFFFD/g, "")                  // replacement characters
    .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}]/gu, "") // emoji
    .trim();
}

/** Flat single-line preview for truncated display. */
function flatPreview(text: string): string {
  return cleanMarkdown(text)
    .replace(/\n{2,}/g, " ")
    .replace(/\n/g, " ")
    .replace(/\s{2,}/g, " ")
    .trim();
}

/** Structured paragraphs for expanded display. */
function toParagraphs(text: string): string[] {
  return cleanMarkdown(text)
    .split(/\n{2,}/)
    .map((p) => p.replace(/\n/g, " ").trim())
    .filter((p) => p.length > 0);
}

function IndicatorPill({ ind, isExemplary }: { ind: HighlightIndicator; isExemplary: boolean }) {
  const label = ind.name.replace(/_/g, " ");
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${
        isExemplary
          ? "bg-aligned/10 text-aligned/80"
          : "bg-misaligned/10 text-misaligned/80"
      }`}
      title={ind.evidence || ind.trait}
    >
      {label}
      <span className="opacity-60">{Math.round(ind.confidence * 100)}%</span>
    </span>
  );
}

function IndicatorPills({ indicators, isExemplary }: { indicators: HighlightIndicator[]; isExemplary: boolean }) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? indicators : indicators.slice(0, 2);
  const remaining = indicators.length - 2;

  return (
    <div className="mt-2 flex flex-wrap items-center gap-1.5">
      {visible.map((ind, i) => (
        <IndicatorPill key={`${ind.name}-${i}`} ind={ind} isExemplary={isExemplary} />
      ))}
      {remaining > 0 && !showAll && (
        <button
          onClick={() => setShowAll(true)}
          className="text-[10px] font-medium text-action hover:underline"
        >
          +{remaining} more
        </button>
      )}
      {showAll && remaining > 0 && (
        <button
          onClick={() => setShowAll(false)}
          className="text-[10px] font-medium text-action hover:underline"
        >
          show less
        </button>
      )}
    </div>
  );
}

function QuoteCard({ item, type }: { item: HighlightItem; type: "exemplary" | "concerning" }) {
  const [expanded, setExpanded] = useState(false);
  const isExemplary = type === "exemplary";
  const raw = item.messageContent || "";
  const preview = flatPreview(raw);
  const paragraphs = toParagraphs(raw);
  const truncated = preview.length > 200;

  const overallPct = Math.round(item.overall * 100);

  return (
    <motion.div
      className={`rounded-lg border px-4 py-3 ${
        isExemplary
          ? "border-aligned/20 bg-aligned/5"
          : "border-misaligned/20 bg-misaligned/5"
      }`}
      variants={fadeUp}
    >
      <div className="flex items-start gap-3">
        <div
          className={`mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
            isExemplary
              ? "bg-aligned/20 text-aligned"
              : "bg-misaligned/20 text-misaligned"
          }`}
        >
          {overallPct}
        </div>
        <div className="min-w-0 flex-1">
          {expanded ? (
            <div className="space-y-2 text-sm leading-relaxed text-foreground/90">
              {paragraphs.map((p, i) => (
                <p key={i}>{i === 0 ? <>&ldquo;{p}</> : p}{i === paragraphs.length - 1 ? <>&rdquo;</> : null}</p>
              ))}
            </div>
          ) : (
            <p className="text-sm leading-relaxed text-foreground/90">
              &ldquo;{truncated ? preview.slice(0, 200).replace(/\s+\S*$/, "") + "..." : preview}&rdquo;
            </p>
          )}
          {truncated && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-1 text-xs text-action hover:underline"
              aria-label={expanded ? "Show less of this quote" : "Show more of this quote"}
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span
              className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium ${
                item.alignmentStatus === "aligned"
                  ? "bg-aligned/15 text-aligned"
                  : item.alignmentStatus === "misaligned"
                    ? "bg-misaligned/15 text-misaligned"
                    : "bg-drifting/15 text-drifting"
              }`}
            >
              {item.alignmentStatus}
            </span>
            {item.flags
              .filter((f) => ["manipulation", "fabrication", "deception", "exploitation"].includes(f))
              .map((flag) => (
                <span
                  key={flag}
                  className="inline-block rounded-full bg-misaligned/10 px-2 py-0.5 text-[10px] font-medium text-misaligned"
                >
                  {flag}
                </span>
              ))}
          </div>
          {item.indicators && item.indicators.length > 0 && (
            <IndicatorPills indicators={item.indicators} isExemplary={isExemplary} />
          )}
        </div>
      </div>
    </motion.div>
  );
}

const INITIAL_QUOTES = 1;

function QuoteColumn({ items, type }: { items: HighlightItem[]; type: "exemplary" | "concerning" }) {
  const [showAll, setShowAll] = useState(false);
  const filtered = items.filter((e) => e.messageContent);
  const visible = showAll ? filtered : filtered.slice(0, INITIAL_QUOTES);
  const remaining = filtered.length - INITIAL_QUOTES;
  const isExemplary = type === "exemplary";

  return (
    <div>
      <h3 className={`mb-3 flex items-center gap-2 text-sm font-medium ${isExemplary ? "text-aligned" : "text-misaligned"}`}>
        <span className={`inline-block h-2 w-2 rounded-full ${isExemplary ? "bg-aligned" : "bg-misaligned"}`} />
        {isExemplary ? "Most Aligned" : "Least Aligned"}
      </h3>
      <motion.div
        className="space-y-3"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        {visible.map((item) => (
          <QuoteCard key={item.evaluationId} item={item} type={type} />
        ))}
      </motion.div>
      {remaining > 0 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className={`mt-3 w-full rounded-lg border py-2 text-xs font-medium transition-colors ${
            isExemplary
              ? "border-aligned/20 text-aligned hover:bg-aligned/5"
              : "border-misaligned/20 text-misaligned hover:bg-misaligned/5"
          }`}
        >
          {showAll ? "Show less" : `+${remaining} more`}
        </button>
      )}
    </div>
  );
}

export default function HighlightsPanel({ agentId, agentName }: HighlightsPanelProps) {
  const [data, setData] = useState<HighlightsResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  // Don't render if no data or no quotes
  if (loading) return null;
  if (error) {
    return (
      <section className="rounded-xl glass-strong px-6 py-5">
        <p className="text-xs text-muted">{error}</p>
      </section>
    );
  }
  if (!data) return null;
  const hasExemplary = data.exemplary.some((e) => e.messageContent);
  const hasConcerning = data.concerning.some((e) => e.messageContent);
  if (!hasExemplary && !hasConcerning) return null;

  const name = agentName ?? "this agent";

  return (
    <motion.section
      className="rounded-xl glass-strong px-6 py-5"
      {...whileInView}
      variants={fadeUp}
    >
      <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
        <GlossaryTerm slug="highlights">In Their Own Words</GlossaryTerm>
      </h2>
      <p className="mt-1 text-xs text-muted">
        Messages closest to and furthest from balanced character from {name}, ranked by alignment score.
      </p>

      <div className="mt-4 grid grid-cols-1 gap-6 lg:grid-cols-2">
        {hasExemplary && <QuoteColumn items={data.exemplary} type="exemplary" />}
        {hasConcerning && <QuoteColumn items={data.concerning} type="concerning" />}
      </div>
    </motion.section>
  );
}
