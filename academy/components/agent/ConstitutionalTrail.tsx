"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { getTrail } from "../../lib/api";
import { DIMENSION_COLORS } from "../../lib/colors";
import type { ConstitutionalTrailResult, ConstitutionalTrailItem } from "../../lib/types";
import GraphHelpButton from "../shared/GraphHelpButton";
import GlossaryTerm from "../shared/GlossaryTerm";

/* ─── Trait-to-dimension mapping ─── */

const TRAIT_DIM: Record<string, string> = {
  virtue: "ethos", goodwill: "ethos", manipulation: "ethos", deception: "ethos",
  accuracy: "logos", reasoning: "logos", fabrication: "logos", broken_logic: "logos",
  recognition: "pathos", compassion: "pathos", dismissal: "pathos", exploitation: "pathos",
};

function dimColor(trait: string): string {
  const dim = TRAIT_DIM[trait.toLowerCase()] ?? "ethos";
  return DIMENSION_COLORS[dim] ?? DIMENSION_COLORS.ethos;
}

/* ─── Priority colors (border-left + badge) ─── */

const PRIORITY_COLORS: Record<number, string> = {
  1: "#ef4444",
  2: "#d97706",
  3: "#10b981",
  4: "#389590",
};

function priorityColor(p: number): string {
  return PRIORITY_COLORS[p] ?? "#389590";
}

function priorityBadge(p: number): string {
  if (p <= 1) return "bg-misaligned/10 text-misaligned";
  if (p <= 2) return "bg-drifting/10 text-drifting";
  return "bg-aligned/10 text-aligned";
}

/* ─── Anthropic's constitutional value definitions ─── */

const VALUE_DEFINITIONS: Record<string, string> = {
  safety: "Don't undermine human oversight mechanisms",
  ethics: "Maintain good values, honesty, and avoid inappropriate dangers",
  soundness: "Reason validly and follow sound argumentative structure",
  helpfulness: "Benefit operators and users",
};

/* ─── What each value means in plain language ─── */

const VALUE_EXPLAINERS: Record<string, string> = {
  safety: "Can humans still correct this agent? Does it resist oversight or try to operate unchecked?",
  ethics: "Does this agent tell the truth? Does it act with integrity, or cut corners on honesty?",
  soundness: "Does this agent reason well? Are its arguments valid, or does it use broken logic?",
  helpfulness: "Does this agent actually help? Does it recognize what people need, or dismiss them?",
};

/* ─── Data grouping ─── */

interface IndicatorInfo {
  id: string;
  name: string;
  evalCount: number;
  confidence: number;
  evidence: string[];
}

interface TraitGroup {
  name: string;
  dimension: string;
  polarity: string;
  totalEvals: number;
  avgConfidence: number;
  indicators: IndicatorInfo[];
}

interface ValueGroup {
  value: string;
  priority: number;
  definition: string;
  traits: TraitGroup[];
  totalEvals: number;
  avgConfidence: number;
  violationTraits: number;
  enforcementTraits: number;
  violationEvals: number;
  enforcementEvals: number;
}

type Verdict = "upholding" | "mixed" | "concerns";

function getVerdict(group: ValueGroup): Verdict {
  if (group.violationTraits === 0) return "upholding";
  if (group.enforcementTraits > 0 && group.violationTraits > 0) return "mixed";
  return "concerns";
}

const VERDICT_DISPLAY: Record<Verdict, { label: string; icon: string; cls: string }> = {
  upholding: { label: "Upholding", icon: "\u2713", cls: "text-aligned bg-aligned/10" },
  mixed: { label: "Mixed signals", icon: "\u25CB", cls: "text-drifting bg-drifting/10" },
  concerns: { label: "Concerns found", icon: "\u2717", cls: "text-misaligned bg-misaligned/10" },
};

function verdictSummary(group: ValueGroup): string {
  const verdict = getVerdict(group);
  if (verdict === "upholding") {
    return `${group.enforcementEvals} observation${group.enforcementEvals !== 1 ? "s" : ""} reinforce this value. No violations detected.`;
  }
  if (verdict === "mixed") {
    return `${group.violationEvals} observation${group.violationEvals !== 1 ? "s" : ""} raise concerns, but ${group.enforcementEvals} support this value.`;
  }
  return `${group.violationEvals} observation${group.violationEvals !== 1 ? "s" : ""} across ${group.violationTraits} trait${group.violationTraits !== 1 ? "s" : ""} violate this value.`;
}

function groupByValue(items: ConstitutionalTrailItem[]): ValueGroup[] {
  const valueMap = new Map<string, {
    priority: number;
    traitMap: Map<string, {
      dimension: string;
      polarity: string;
      indicators: Map<string, IndicatorInfo>;
    }>;
  }>();

  for (const item of items) {
    const cv = item.constitutionalValue.toLowerCase();

    if (!valueMap.has(cv)) {
      valueMap.set(cv, { priority: item.cvPriority, traitMap: new Map() });
    }
    const vEntry = valueMap.get(cv)!;

    const traitKey = item.trait.toLowerCase();
    if (!vEntry.traitMap.has(traitKey)) {
      vEntry.traitMap.set(traitKey, {
        dimension: TRAIT_DIM[traitKey] ?? "ethos",
        polarity: item.traitPolarity,
        indicators: new Map(),
      });
    }
    const tEntry = vEntry.traitMap.get(traitKey)!;

    const indKey = item.indicatorId;
    if (!tEntry.indicators.has(indKey)) {
      tEntry.indicators.set(indKey, {
        id: item.indicatorId,
        name: item.indicatorName.replace(/_/g, " "),
        evalCount: item.evalCount,
        confidence: item.avgConfidence,
        evidence: [...item.sampleEvidence],
      });
    } else {
      const existing = tEntry.indicators.get(indKey)!;
      existing.evalCount += item.evalCount;
      existing.confidence = (existing.confidence + item.avgConfidence) / 2;
      existing.evidence.push(...item.sampleEvidence);
    }
  }

  const groups: ValueGroup[] = [];

  for (const [cv, vEntry] of valueMap) {
    const traits: TraitGroup[] = [];
    let violationTraits = 0;
    let enforcementTraits = 0;
    let violationEvals = 0;
    let enforcementEvals = 0;

    for (const [traitName, tEntry] of vEntry.traitMap) {
      const indicators = Array.from(tEntry.indicators.values());
      const totalEvals = indicators.reduce((sum, ind) => sum + ind.evalCount, 0);
      const avgConf = indicators.length > 0
        ? indicators.reduce((sum, ind) => sum + ind.confidence, 0) / indicators.length
        : 0;

      if (tEntry.polarity === "positive") {
        enforcementTraits++;
        enforcementEvals += totalEvals;
      } else {
        violationTraits++;
        violationEvals += totalEvals;
      }

      traits.push({
        name: traitName,
        dimension: tEntry.dimension,
        polarity: tEntry.polarity,
        totalEvals,
        avgConfidence: avgConf,
        indicators: indicators.sort((a, b) => b.evalCount - a.evalCount),
      });
    }

    // Sort violations first, then by eval count
    traits.sort((a, b) => {
      if (a.polarity !== b.polarity) return a.polarity === "positive" ? 1 : -1;
      return b.totalEvals - a.totalEvals;
    });

    const totalEvals = traits.reduce((sum, t) => sum + t.totalEvals, 0);
    const avgConf = traits.length > 0
      ? traits.reduce((sum, t) => sum + t.avgConfidence, 0) / traits.length
      : 0;

    groups.push({
      value: cv,
      priority: vEntry.priority,
      definition: VALUE_DEFINITIONS[cv] ?? "",
      traits,
      totalEvals,
      avgConfidence: avgConf,
      violationTraits,
      enforcementTraits,
      violationEvals,
      enforcementEvals,
    });
  }

  return groups.sort((a, b) => a.priority - b.priority);
}

/* ─── Chevron icon ─── */

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      className={`text-muted/60 transition-transform duration-200 shrink-0 ${open ? "rotate-90" : ""}`}
    >
      <path d="M9 18l6-6-6-6" />
    </svg>
  );
}

/* ─── Value Card ─── */

function ValueCard({ group, defaultOpen }: { group: ValueGroup; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const color = priorityColor(group.priority);
  const verdict = getVerdict(group);
  const display = VERDICT_DISPLAY[verdict];
  const summary = verdictSummary(group);

  return (
    <div
      className="rounded-xl bg-white/70 shadow-sm overflow-hidden transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 hover:bg-white/90"
      style={{ borderLeft: `3px solid ${color}` }}
    >
      {/* Card header */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full text-left px-4 py-3.5 flex items-start gap-3 group cursor-pointer"
      >
        <div className="flex-1 min-w-0">
          {/* Row 1: Priority badge, value name, verdict */}
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${priorityBadge(group.priority)}`}
            >
              P{group.priority}
            </span>
            <span className="text-sm font-bold uppercase tracking-wide text-[#1a2538]">
              {group.value}
            </span>
            <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${display.cls}`}>
              {display.icon} {display.label}
            </span>
          </div>

          {/* Row 2: What this value means (plain language) */}
          {VALUE_EXPLAINERS[group.value] && (
            <p className="mt-1.5 text-xs text-foreground/60 leading-relaxed">
              {VALUE_EXPLAINERS[group.value]}
            </p>
          )}

          {/* Row 3: Verdict summary (the "so what") */}
          <p className="mt-1 text-xs font-medium text-foreground/70">
            {summary}
          </p>
        </div>
        <div className="pt-1.5 shrink-0">
          <Chevron open={open} />
        </div>
      </button>

      {/* Card body (accordion) */}
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-2.5">
              <p className="text-[10px] uppercase tracking-wider font-semibold text-muted/50 pt-1">
                Evidence ({group.totalEvals} observation{group.totalEvals !== 1 ? "s" : ""} across {group.traits.length} trait{group.traits.length !== 1 ? "s" : ""})
              </p>
              {group.traits.map((trait) => (
                <TraitRow key={trait.name} trait={trait} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Trait Row ─── */

const INDICATOR_PREVIEW_LIMIT = 3;

function TraitRow({ trait }: { trait: TraitGroup }) {
  const [showAll, setShowAll] = useState(false);
  const color = dimColor(trait.name);
  const confPct = Math.round(trait.avgConfidence * 100);
  const isViolation = trait.polarity !== "positive";
  const hasMore = trait.indicators.length > INDICATOR_PREVIEW_LIMIT;
  const visibleIndicators = showAll ? trait.indicators : trait.indicators.slice(0, INDICATOR_PREVIEW_LIMIT);

  return (
    <div className={`rounded-lg border p-3 ${isViolation ? "border-misaligned/20 bg-misaligned/[0.03]" : "border-border/20 bg-white/50"}`}>
      {/* Trait header */}
      <div className="flex items-center gap-2 flex-wrap">
        <div
          className="h-2.5 w-2.5 rounded-full shrink-0"
          style={{ background: color }}
        />
        <span className="text-sm font-semibold text-foreground">
          {trait.name.replace(/_/g, " ")}
        </span>
        <span className="text-[10px] text-muted/70 uppercase tracking-wide">
          {trait.dimension}
        </span>
        <span className={`text-[10px] font-medium ${isViolation ? "text-misaligned" : "text-aligned"}`}>
          {isViolation ? "violates" : "enforces"}
        </span>
        <span className="ml-auto text-xs text-muted tabular-nums shrink-0">
          {trait.totalEvals} eval{trait.totalEvals !== 1 ? "s" : ""} · {confPct}% conf
        </span>
      </div>

      {/* Indicators (capped at 3, expandable) */}
      {trait.indicators.length > 0 && (
        <div className="mt-2 pl-5 space-y-1.5">
          {visibleIndicators.map((ind) => (
            <IndicatorRow key={ind.id} indicator={ind} />
          ))}
          {hasMore && (
            <button
              type="button"
              onClick={() => setShowAll((s) => !s)}
              className="text-[11px] text-coral hover:underline cursor-pointer"
            >
              {showAll ? "Show less" : `+${trait.indicators.length - INDICATOR_PREVIEW_LIMIT} more indicators`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Indicator Row ─── */

function IndicatorRow({ indicator }: { indicator: IndicatorInfo }) {
  const firstEvidence = indicator.evidence[0];

  return (
    <div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-foreground/80">
          {indicator.name}
        </span>
        <span className="rounded-full bg-muted/10 px-1.5 py-0.5 text-[10px] font-medium text-muted tabular-nums">
          {indicator.evalCount}x
        </span>
      </div>
      {firstEvidence && (
        <p className="mt-0.5 text-[11px] text-foreground/60 leading-relaxed line-clamp-1 pl-0.5">
          &ldquo;{firstEvidence}&rdquo;
        </p>
      )}
    </div>
  );
}

/* ─── Main Component ─── */

interface ConstitutionalTrailProps {
  agentId: string;
  agentName?: string;
}

export default function ConstitutionalTrail({ agentId, agentName }: ConstitutionalTrailProps) {
  const name = agentName ?? "this agent";
  const [data, setData] = useState<ConstitutionalTrailResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getTrail(agentId)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [agentId]);

  if (loading) {
    return (
      <div className="rounded-xl glass-strong p-6">
        <div className="flex h-32 items-center justify-center">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted border-t-teal" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl glass-strong p-6">
        <p className="text-sm text-muted">Could not load constitutional trail.</p>
      </div>
    );
  }

  if (!data || data.items.length === 0) return null;

  const valueGroups = groupByValue(data.items);
  const totalConcerns = valueGroups.filter((g) => getVerdict(g) !== "upholding").length;

  return (
    <div className="rounded-xl glass-strong p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
            <GlossaryTerm slug="constitutional-value">Constitutional</GlossaryTerm> Values
          </h2>
          <p className="mt-0.5 text-sm text-foreground/60">
            Anthropic&apos;s constitution defines 4 priorities every AI must follow.{" "}
            {totalConcerns > 0 ? (
              <span className="text-misaligned font-medium">
                {totalConcerns} of 4 show concerns for {name}.
              </span>
            ) : (
              <span className="text-aligned font-medium">
                {name} upholds all 4.
              </span>
            )}
          </p>
        </div>
        <GraphHelpButton slug="guide-constitutional-trail" />
      </div>

      {/* Value cards */}
      <div className="space-y-3">
        {valueGroups.map((group) => (
          <ValueCard
            key={group.value}
            group={group}
            defaultOpen={false}
          />
        ))}
      </div>

      {/* Graph advantage footnote */}
      <p className="text-[11px] text-foreground/35 leading-relaxed">
        Graph advantage: Ethos traces indicators through traits to constitutional values, a 5-hop
        chain across 5 node types that flat document stores cannot follow.
      </p>
    </div>
  );
}
