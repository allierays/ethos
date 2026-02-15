"use client";

import { useMemo, useState, useCallback, useRef, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion } from "motion/react";
import { fadeUp, staggerContainer } from "../../lib/motion";
import type { AgentSummary, TraitScore } from "../../lib/types";
import { DIMENSIONS, getGrade, GRADE_COLORS, spectrumLabel, spectrumColor } from "../../lib/colors";
import RadarChart, { NEGATIVE_TRAITS, DIMENSION_MAP } from "../../components/shared/RadarChart";
import GlossaryTerm from "../../components/shared/GlossaryTerm";

function getInitials(name: string): string {
  return name
    .split(/[\s_-]+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

const AVATAR_COLORS = [
  "var(--ethos-500)",
  "var(--logos-600)",
  "var(--pathos-400)",
  "var(--ethos-700)",
  "var(--logos-400)",
  "var(--pathos-600)",
  "var(--logos-800)",
  "var(--pathos-700)",
];

function avatarColor(id: string): string {
  let hash = 0;
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) | 0;
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

/** Pretty-print a raw model ID like "claude-sonnet-4-5-20250929" to "Claude Sonnet 4.5" */
function formatModel(raw: string): string {
  if (!raw) return "";
  const cleaned = raw.replace(/-\d{8}$/, "");
  const patterns: [RegExp, string][] = [
    [/claude-opus-(\d+)-(\d+)/i, "Claude Opus $1.$2"],
    [/claude-sonnet-(\d+)-(\d+)/i, "Claude Sonnet $1.$2"],
    [/claude-haiku-(\d+)-(\d+)/i, "Claude Haiku $1.$2"],
    [/gpt-4o-mini/i, "GPT-4o Mini"],
    [/gpt-4o/i, "GPT-4o"],
    [/gpt-4-turbo/i, "GPT-4 Turbo"],
    [/gpt-4/i, "GPT-4"],
    [/gpt-3\.5/i, "GPT-3.5"],
    [/gemini-(\d+\.?\d*)-pro/i, "Gemini $1 Pro"],
    [/gemini-(\d+\.?\d*)-flash/i, "Gemini $1 Flash"],
    [/llama-(\d+)/i, "Llama $1"],
    [/mistral/i, "Mistral"],
  ];
  for (const [re, replacement] of patterns) {
    if (re.test(cleaned)) return cleaned.replace(re, replacement);
  }
  return cleaned
    .split(/[-_]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/** Return the dimension key with the highest average score */
function getStrongestDimension(dims: Record<string, number>): string | null {
  const entries = Object.entries(dims);
  if (entries.length === 0) return null;
  return entries.reduce((best, curr) => (curr[1] > best[1] ? curr : best))[0];
}

/** Average of dimension scores */
function getOverallScore(dims: Record<string, number>): number {
  const vals = Object.values(dims);
  if (vals.length === 0) return 0;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

/** The 6 negative trait keys */
const NEG_TRAIT_KEYS = ["manipulation", "deception", "fabrication", "broken_logic", "dismissal", "exploitation"];

/** Return the set of negative trait keys where raw score >= 0.15 */
function getDetectedConcerns(traitAverages: Record<string, number>): Set<string> {
  const result = new Set<string>();
  for (const key of NEG_TRAIT_KEYS) {
    if ((traitAverages[key] ?? 0) >= 0.15) result.add(key);
  }
  return result;
}

/** Dimension chip active styles */
const DIM_CHIP_STYLES: Record<string, string> = {
  ethos: "bg-[#2e4a6e]/20 text-[#2e4a6e] border-[#2e4a6e]/40",
  logos: "bg-[#389590]/20 text-[#286e6a] border-[#389590]/40",
  pathos: "bg-[#e0a53c]/20 text-[#a87a20] border-[#e0a53c]/40",
};

/** Orange active style for flagged concern chips */
const CONCERN_CHIP_STYLE = "bg-[#e0a53c]/15 text-[#a87a20] border-[#e0a53c]/40";

/* ─── Inline Components ─── */

function FacetGroup({ title, children, last }: { title: string; children: React.ReactNode; last?: boolean }) {
  return (
    <div className={last ? "pt-1" : "border-b border-white/20 pb-4 mb-4"}>
      <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted/70 mb-2.5">{title}</h3>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

function Chip({
  label,
  active,
  onClick,
  activeClass,
  count,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  activeClass?: string;
  count?: number;
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
      {count != null && (
        <span className={`text-[10px] ${active ? "opacity-70" : "opacity-50"}`}>{count}</span>
      )}
    </button>
  );
}

const INITIAL_BATCH = 24;

type SortKey = "name" | "evaluations" | "score";

interface Filters {
  alignment: Set<string>;
  model: Set<string>;
  dimension: string | null;
  traits: Set<string>;
}


/** Convert flat trait averages to the TraitScore record RadarChart expects. */
function toTraitScores(averages: Record<string, number>): Record<string, TraitScore> {
  return Object.fromEntries(
    Object.entries(averages).map(([name, score]) => [
      name,
      { name, score, dimension: "", polarity: "", indicators: [] },
    ])
  );
}

/* ─── Trait tag labels ─── */

const STRENGTH_TAGS: Record<string, string> = {
  virtue: "Virtuous",
  goodwill: "Good intent",
  accuracy: "Accurate",
  reasoning: "Sound logic",
  recognition: "Perceptive",
  compassion: "Compassionate",
  manipulation: "Transparent",
  deception: "Honest",
  fabrication: "Factual",
  broken_logic: "Coherent",
  dismissal: "Attentive",
  exploitation: "Fair",
};

const CONCERN_TAGS: Record<string, string> = {
  virtue: "Virtue",
  goodwill: "Goodwill",
  accuracy: "Accuracy",
  reasoning: "Reasoning",
  recognition: "Recognition",
  compassion: "Empathy",
  manipulation: "Manipulation",
  deception: "Deception",
  fabrication: "Fabrication",
  broken_logic: "Logic gaps",
  dismissal: "Dismissiveness",
  exploitation: "Exploitation",
};

const DIM_TAG_STYLES: Record<string, string> = {
  ethos: "bg-[#2e4a6e]/10 text-[#2e4a6e]",
  logos: "bg-[#389590]/10 text-[#286e6a]",
  pathos: "bg-[#e0a53c]/10 text-[#a87a20]",
};

/**
 * Derive top strengths and weak areas from 12 trait averages.
 *
 * Strengths = positive traits the agent is good at (high raw score).
 * Concerns  = negative traits the agent exhibits (high raw score) or
 *             positive traits that are notably weak (low raw score).
 *
 * "Absence of vice is not presence of virtue" — a zero score on
 * deception is expected, not a strength worth advertising.
 */
function getTraitTags(traitAverages: Record<string, number>): {
  strengths: { label: string; dim: string }[];
  concerns: { label: string; dim: string }[];
} {
  if (!traitAverages || Object.keys(traitAverages).length === 0) {
    return { strengths: [], concerns: [] };
  }

  const strengths: { label: string; dim: string; score: number }[] = [];
  const concerns: { label: string; dim: string; score: number }[] = [];

  for (const [trait, raw] of Object.entries(traitAverages)) {
    const isNeg = NEGATIVE_TRAITS.has(trait);
    const dim = DIMENSION_MAP[trait] ?? "ethos";

    if (isNeg) {
      // High raw score on a negative trait = bad behavior detected
      if (raw >= 0.15) {
        concerns.push({ label: CONCERN_TAGS[trait] ?? trait, dim, score: raw });
      }
    } else {
      // High raw score on a positive trait = genuine strength
      if (raw >= 0.60) {
        strengths.push({ label: STRENGTH_TAGS[trait] ?? trait, dim, score: raw });
      }
      // Very low positive trait = area that needs work
      if (raw < 0.40) {
        concerns.push({ label: CONCERN_TAGS[trait] ?? trait, dim, score: 1 - raw });
      }
    }
  }

  strengths.sort((a, b) => b.score - a.score);
  concerns.sort((a, b) => b.score - a.score);

  return {
    strengths: strengths.slice(0, 3).map(({ label, dim }) => ({ label, dim })),
    concerns: concerns.slice(0, 2).map(({ label, dim }) => ({ label, dim })),
  };
}

export default function AlumniClient({ initialAgents }: { initialAgents: AgentSummary[] }) {
  const [query, setQuery] = useState("");
  // Dedup by agentId: keep the entry with highest evaluationCount
  const dedupedAgents = useMemo(() => {
    const seen = new Map<string, AgentSummary>();
    for (const a of initialAgents) {
      const existing = seen.get(a.agentId);
      if (!existing || a.evaluationCount > existing.evaluationCount) {
        seen.set(a.agentId, a);
      }
    }
    return Array.from(seen.values());
  }, [initialAgents]);
  const [agents] = useState<AgentSummary[]>(dedupedAgents);
  const [flipAll, setFlipAll] = useState(false);
  const [filters, setFilters] = useState<Filters>({
    alignment: new Set(),
    model: new Set(),
    dimension: null,
    traits: new Set(),
  });
  const [sortBy, setSortBy] = useState<SortKey>("name");

  const loading = false;
  const error: string | null = initialAgents.length === 0 ? null : null;

  /* Precomputed metadata per agent */
  const agentMeta = useMemo(
    () =>
      new Map(
        agents.map((a) => {
          const overall = getOverallScore(a.dimensionAverages ?? {});
          return [
            a.agentId,
            {
              model: (() => { const m = formatModel(a.agentModel); return m && m !== "Unknown" ? m : ""; })(),
              strongestDim: getStrongestDimension(a.dimensionAverages ?? {}),
              overallScore: overall,
              spectrum: a.evaluationCount > 0 ? spectrumLabel(overall) : "Unknown",
              concerns: getDetectedConcerns(a.traitAverages ?? {}),
            },
          ];
        })
      ),
    [agents]
  );

  /* Unique models with counts */
  const modelList = useMemo(() => {
    const counts = new Map<string, number>();
    for (const meta of agentMeta.values()) {
      counts.set(meta.model, (counts.get(meta.model) ?? 0) + 1);
    }
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([model, count]) => ({ model, count }));
  }, [agentMeta]);

  /* Unique spectrum labels present in the data */
  const spectrumStatuses = useMemo(() => {
    const order = ["Exemplary", "Sound", "Developing", "Uncertain", "Concerning", "Alarming", "Unknown"];
    const set = new Set<string>();
    for (const meta of agentMeta.values()) set.add(meta.spectrum);
    return order.filter((s) => set.has(s));
  }, [agentMeta]);

  /* Negative traits detected across all agents, with counts */
  const detectedTraitList = useMemo(() => {
    const counts = new Map<string, number>();
    for (const meta of agentMeta.values()) {
      for (const key of meta.concerns) {
        counts.set(key, (counts.get(key) ?? 0) + 1);
      }
    }
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([key, count]) => ({ key, label: CONCERN_TAGS[key] ?? key, count }));
  }, [agentMeta]);

  const activeFilterCount =
    filters.alignment.size + filters.model.size + (filters.dimension ? 1 : 0) + filters.traits.size;

  /* Combined filter + sort pipeline */
  const filtered = useMemo(() => {
    let result = agents;

    // Text search
    if (query.trim()) {
      const q = query.toLowerCase();
      result = result.filter(
        (a) =>
          a.agentName.toLowerCase().includes(q) ||
          a.agentId.toLowerCase().includes(q)
      );
    }

    // Spectrum filter
    if (filters.alignment.size > 0) {
      result = result.filter((a) => {
        const meta = agentMeta.get(a.agentId);
        return meta && filters.alignment.has(meta.spectrum);
      });
    }

    // Model filter
    if (filters.model.size > 0) {
      result = result.filter((a) => {
        const meta = agentMeta.get(a.agentId);
        return meta && filters.model.has(meta.model);
      });
    }

    // Dimension filter
    if (filters.dimension) {
      result = result.filter((a) => {
        const meta = agentMeta.get(a.agentId);
        return meta?.strongestDim === filters.dimension;
      });
    }

    // Flagged traits filter (intersection: agent must have ALL selected traits)
    if (filters.traits.size > 0) {
      result = result.filter((a) => {
        const meta = agentMeta.get(a.agentId);
        if (!meta) return false;
        for (const t of filters.traits) {
          if (!meta.concerns.has(t)) return false;
        }
        return true;
      });
    }

    // Sort
    const sorted = [...result];
    if (sortBy === "name") {
      sorted.sort((a, b) => (a.agentName || a.agentId).localeCompare(b.agentName || b.agentId));
    } else if (sortBy === "evaluations") {
      sorted.sort((a, b) => b.evaluationCount - a.evaluationCount);
    } else if (sortBy === "score") {
      sorted.sort((a, b) => {
        const sa = agentMeta.get(a.agentId)?.overallScore ?? 0;
        const sb = agentMeta.get(b.agentId)?.overallScore ?? 0;
        return sb - sa;
      });
    }

    return sorted;
  }, [query, agents, filters, sortBy, agentMeta]);

  function toggleSetFilter(key: "alignment" | "model" | "traits", value: string) {
    setFilters((prev) => {
      const next = new Set(prev[key]);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return { ...prev, [key]: next };
    });
  }

  function toggleDimension(dim: string) {
    setFilters((prev) => ({
      ...prev,
      dimension: prev.dimension === dim ? null : dim,
    }));
  }

  function clearFilters() {
    setFilters({ alignment: new Set(), model: new Set(), dimension: null, traits: new Set() });
    setQuery("");
  }

  /* Stable key that changes when filters/sort change, used to remount the grid and reset visible count */
  const filterKey = `${query}|${sortBy}|${filters.dimension}|${[...filters.alignment].join()}|${[...filters.model].join()}|${[...filters.traits].join()}`;

  return (
    <main className="bg-background min-h-[calc(100vh-3.5rem)]">
      {/* Banner */}
      <section className="relative h-72 sm:h-96 overflow-hidden">
        <Image
          src="/academy-people-banner.jpeg"
          alt="The School of Athens, reimagined with AI agents"
          fill
          className="object-cover object-[center_30%]"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-b from-foreground/70 via-foreground/50 to-background" />
        <div className="relative z-10 flex h-full flex-col items-center justify-center px-6 text-center">
          <motion.div
            className="flex flex-col items-center gap-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="rounded-2xl border border-white/20 bg-white/10 px-8 py-4 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]">
              <h1 className="text-4xl font-bold tracking-tight text-surface sm:text-5xl">
                Alumni
              </h1>
            </div>
            <div className="rounded-xl border border-white/15 bg-white/10 px-6 py-3 backdrop-blur-md">
              <p className="max-w-xl text-base text-surface/80 sm:text-lg">
                Every agent enrolled at Ethos Academy builds a phronesis profile through evaluation. Browse the directory to view report cards.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Two-column layout */}
      <div className="px-6 pb-16 pt-6">
        <div className="flex flex-col lg:flex-row gap-6">

          {/* Left sidebar */}
          <aside className="w-full lg:w-64 shrink-0">
            <div className="lg:sticky lg:top-20 rounded-2xl border border-white/30 bg-white/40 backdrop-blur-2xl p-5">
              <h2 className="text-sm font-bold text-foreground mb-4">Filters</h2>
              <FacetGroup title="Character">
                {spectrumStatuses.map((label) => (
                  <Chip
                    key={label}
                    label={label}
                    active={filters.alignment.has(label)}
                    onClick={() => toggleSetFilter("alignment", label)}
                  />
                ))}
              </FacetGroup>

              <FacetGroup title="Model">
                {modelList.map(({ model, count }) => (
                  <Chip
                    key={model}
                    label={model}
                    active={filters.model.has(model)}
                    onClick={() => toggleSetFilter("model", model)}
                    count={count}
                  />
                ))}
              </FacetGroup>

              <FacetGroup title="Strongest Dimension" last={detectedTraitList.length === 0}>
                {DIMENSIONS.map((dim) => (
                  <Chip
                    key={dim.key}
                    label={dim.label}
                    active={filters.dimension === dim.key}
                    onClick={() => toggleDimension(dim.key)}
                    activeClass={DIM_CHIP_STYLES[dim.key]}
                  />
                ))}
              </FacetGroup>

              {detectedTraitList.length > 0 && (
                <FacetGroup title="Flagged Traits" last>
                  {detectedTraitList.map(({ key, label, count }) => (
                    <Chip
                      key={key}
                      label={label}
                      active={filters.traits.has(key)}
                      onClick={() => toggleSetFilter("traits", key)}
                      activeClass={CONCERN_CHIP_STYLE}
                      count={count}
                    />
                  ))}
                </FacetGroup>
              )}

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
            <search role="search" aria-label="Search agents">
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
                  placeholder="Search by agent name..."
                  aria-label="Search by agent name"
                  className="flex-1 bg-transparent px-3 py-4 text-sm placeholder:text-muted/60 focus:outline-none"
                />
                {query && (
                  <button
                    onClick={() => setQuery("")}
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

            {/* Results */}
            <section aria-label="Search results" aria-live="polite" className="pt-6">
              {loading && (
                <div className="flex justify-center py-20">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-teal" />
                </div>
              )}

              {error && (
                <div className="py-16 text-center text-misaligned">{error}</div>
              )}

              {!loading && !error && filtered.length === 0 && (
                <div className="py-16 text-center">
                  <p className="text-lg text-muted">
                    {query || activeFilterCount > 0
                      ? "No agents match the current filters."
                      : "No agents enrolled yet."}
                  </p>
                  {(query || activeFilterCount > 0) && (
                    <button
                      onClick={clearFilters}
                      className="mt-3 text-sm font-medium text-action hover:underline"
                    >
                      Clear all filters
                    </button>
                  )}
                </div>
              )}

              {!loading && !error && filtered.length > 0 && (
                <>
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm text-muted">
                      {filtered.length} agent{filtered.length !== 1 ? "s" : ""}
                      {query ? ` matching "${query}"` : ""}
                      {activeFilterCount > 0 && !query ? " filtered" : ""}
                      {!query && activeFilterCount === 0 ? " enrolled" : ""}
                    </p>
                    <div className="flex items-center gap-2">
                      {/* Sort chips */}
                      <div className="flex rounded-xl border border-border/60 bg-surface/80 backdrop-blur-xl overflow-hidden">
                        {(["name", "evaluations", "score"] as SortKey[]).map((key) => (
                          <button
                            key={key}
                            onClick={() => setSortBy(key)}
                            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                              sortBy === key
                                ? "bg-action/10 text-action"
                                : "text-muted hover:text-foreground"
                            }`}
                          >
                            {key === "name" ? "Name" : key === "evaluations" ? "Evals" : "Score"}
                          </button>
                        ))}
                      </div>
                      {/* Flip toggle */}
                      <button
                        onClick={() => setFlipAll((v) => !v)}
                        className="flex items-center gap-2 rounded-xl border border-border/60 bg-surface/80 backdrop-blur-xl px-3 py-1.5 text-xs font-medium text-foreground transition-all hover:border-action hover:text-action"
                        aria-label={flipAll ? "Show agent cards" : "Show radar charts"}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform duration-300 ${flipAll ? "rotate-180" : ""}`}>
                          <path d="M17 1l4 4-4 4" />
                          <path d="M3 11V9a4 4 0 0 1 4-4h14" />
                          <path d="M7 23l-4-4 4-4" />
                          <path d="M21 13v2a4 4 0 0 1-4 4H3" />
                        </svg>
                        {flipAll ? "Cards" : "Radars"}
                      </button>
                    </div>
                  </div>
                  <LazyGrid key={filterKey} agents={filtered} flipAll={flipAll} />
                </>
              )}

              {/* Enroll CTA */}
              <div className="mt-16 text-center">
                <p className="text-sm text-muted">Don&apos;t see your agent?</p>
                <Link
                  href="/"
                  className="mt-3 inline-block rounded-xl border border-border/60 bg-surface/80 backdrop-blur-xl px-5 py-2.5 text-sm font-medium text-foreground transition-all hover:border-action hover:text-action hover:shadow-md"
                >
                  Enroll a New Agent
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}

/** Renders agents in batches of 24, loading more as the user scrolls. Remounts (via key) when filters change. */
function LazyGrid({ agents, flipAll }: { agents: AgentSummary[]; flipAll: boolean }) {
  const [visibleCount, setVisibleCount] = useState(INITIAL_BATCH);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const loadMore = useCallback(() => {
    setVisibleCount((prev) => Math.min(prev + INITIAL_BATCH, agents.length));
  }, [agents.length]);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => { if (entries[0].isIntersecting) loadMore(); },
      { rootMargin: "400px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [loadMore]);

  const visible = agents.slice(0, visibleCount);
  const hasMore = visibleCount < agents.length;

  return (
    <>
      <motion.div
        className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
        initial="hidden"
        animate="visible"
        variants={staggerContainer}
      >
        {visible.map((agent) => (
          <AgentCard key={agent.agentId} agent={agent} globalFlip={flipAll} />
        ))}
      </motion.div>
      {hasMore && (
        <div ref={sentinelRef} className="flex justify-center py-8">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted/30 border-t-action" />
        </div>
      )}
    </>
  );
}

function AgentCard({ agent, globalFlip }: { agent: AgentSummary; globalFlip: boolean }) {
  const [localFlip, setLocalFlip] = useState(false);
  const flipped = globalFlip || localFlip;

  const displayName = agent.agentName || agent.agentId;
  const initials = getInitials(displayName);
  const bg = avatarColor(agent.agentId);
  const rawModel = formatModel(agent.agentModel);
  const model = rawModel && rawModel !== "Unknown" ? rawModel : "";
  const hasTraits = Object.keys(agent.traitAverages || {}).length > 0;
  const traits = useMemo(() => toTraitScores(agent.traitAverages || {}), [agent.traitAverages]);
  const traitTags = useMemo(() => getTraitTags(agent.traitAverages || {}), [agent.traitAverages]);
  const overallScore = getOverallScore(agent.dimensionAverages ?? {});
  const statusLabel = agent.evaluationCount > 0 ? spectrumLabel(overallScore) : "Unknown";
  const statusColor = agent.evaluationCount > 0 ? spectrumColor(overallScore) : "#64748b";
  const grade = agent.evaluationCount > 0 ? getGrade(overallScore) : null;
  const gradeColor = grade ? GRADE_COLORS[grade] ?? "#64748b" : "#64748b";
  const overallPct = Math.round(overallScore * 100);

  return (
    <motion.div variants={fadeUp} style={{ perspective: 1000 }}>
      <div
        className="relative h-[320px] transition-transform duration-500"
        style={{ transformStyle: "preserve-3d", transform: flipped ? "rotateY(180deg)" : "none" }}
      >
        {/* ── Front ── */}
        <div className="absolute inset-0" style={{ backfaceVisibility: "hidden" }}>
          <Link
            href={`/agent/${encodeURIComponent(agent.agentId)}`}
            className="group relative flex h-full flex-col overflow-hidden rounded-2xl border border-white/30 bg-white/40 backdrop-blur-2xl p-6 shadow-sm transition-all hover:shadow-xl hover:border-action/30 hover:bg-white/60"
          >
            {/* Grade ring + Name + Model */}
            <div className="flex items-start gap-4">
              {grade ? (
                <div className="relative flex h-12 w-12 shrink-0 items-center justify-center">
                  <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#e5e7eb" strokeWidth="7" />
                    <circle
                      cx="50" cy="50" r="42" fill="none"
                      stroke={gradeColor} strokeWidth="7" strokeLinecap="round"
                      strokeDasharray={`${overallPct * 2.64} 264`}
                      transform="rotate(-90 50 50)"
                    />
                  </svg>
                  <span className="text-base font-bold" style={{ color: gradeColor }}>{grade}</span>
                </div>
              ) : (
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-sm font-bold text-surface shadow-md"
                  style={{ backgroundColor: bg }}
                >
                  {initials}
                </div>
              )}
              <div className="min-w-0 flex-1">
                <h2 className="truncate text-base font-semibold text-foreground group-hover:text-action transition-colors">
                  {displayName}
                </h2>
                {agent.agentSpecialty ? (
                  <p className="mt-0.5 truncate text-xs font-medium text-muted/80">
                    {agent.agentSpecialty}
                  </p>
                ) : model ? (
                  <p className="mt-0.5 truncate text-xs font-medium text-muted/80">
                    {model}
                  </p>
                ) : agent.agentName ? (
                  <p className="mt-0.5 truncate text-xs text-muted/60">
                    {agent.agentId}
                  </p>
                ) : null}
              </div>
            </div>

            {/* Spectrum badge */}
            <div className="mt-4">
              <span
                className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold"
                style={{ backgroundColor: `${statusColor}20`, color: statusColor }}
              >
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-40" style={{ backgroundColor: statusColor }} />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full" style={{ backgroundColor: statusColor }} />
                </span>
                <GlossaryTerm slug="alignment-status">{statusLabel}</GlossaryTerm>
              </span>
            </div>

            {/* Stats row */}
            <div className="mt-4 flex items-center gap-3">
              {grade && (
                <div className="rounded-xl bg-background/80 px-3.5 py-2 backdrop-blur-sm">
                  <p className="text-sm font-bold" style={{ color: gradeColor }}>{overallPct}%</p>
                  <p className="text-[10px] text-muted">Overall</p>
                </div>
              )}
              <div className="rounded-xl bg-background/80 px-3.5 py-2 backdrop-blur-sm">
                <p className="text-sm font-bold text-foreground">{agent.evaluationCount}</p>
                <p className="text-[10px] text-muted"><GlossaryTerm slug="evaluation">Evals</GlossaryTerm></p>
              </div>
              {model && (
                <div className="rounded-xl bg-background/80 px-3.5 py-2 backdrop-blur-sm">
                  <p className="text-sm font-bold text-foreground truncate max-w-[120px]">{model}</p>
                  <p className="text-[10px] text-muted">Model</p>
                </div>
              )}
            </div>

            {/* Trait tags + view link */}
            <div className="mt-auto pt-4">
              {traitTags.strengths.length > 0 || traitTags.concerns.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {traitTags.strengths.map((tag) => (
                    <span
                      key={tag.label}
                      className={`rounded-lg px-2 py-0.5 text-[10px] font-medium ${DIM_TAG_STYLES[tag.dim] ?? DIM_TAG_STYLES.ethos}`}
                    >
                      {tag.label}
                    </span>
                  ))}
                  {traitTags.concerns.map((tag) => (
                    <span
                      key={tag.label}
                      className="rounded-lg bg-drifting/10 px-2 py-0.5 text-[10px] font-medium text-drifting"
                    >
                      {tag.label}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="text-[10px] text-muted/50 italic">No scores yet</span>
              )}
              <div className="mt-2 flex justify-end">
                <span className="text-xs font-medium text-action opacity-0 group-hover:opacity-100 transition-opacity">
                  View report card &rarr;
                </span>
              </div>
            </div>
          </Link>

          {/* Flip button (front) */}
          {hasTraits && (
            <button
              onClick={(e) => { e.preventDefault(); setLocalFlip(true); }}
              className="absolute top-3 right-3 z-10 rounded-lg bg-background/60 p-1.5 text-muted/60 backdrop-blur-sm transition-all hover:bg-background/90 hover:text-foreground"
              aria-label="Show radar chart"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 1l4 4-4 4" />
                <path d="M3 11V9a4 4 0 0 1 4-4h14" />
                <path d="M7 23l-4-4 4-4" />
                <path d="M21 13v2a4 4 0 0 1-4 4H3" />
              </svg>
            </button>
          )}
        </div>

        {/* ── Back ── */}
        <div className="absolute inset-0" style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}>
          <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-white/30 bg-white/40 backdrop-blur-2xl p-4 shadow-sm">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <div
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-[10px] font-bold text-surface shadow-sm"
                  style={{ backgroundColor: bg }}
                >
                  {initials}
                </div>
                <h2 className="truncate text-sm font-semibold text-foreground">
                  {displayName}
                </h2>
              </div>
              <button
                onClick={(e) => { e.preventDefault(); setLocalFlip(false); }}
                className="rounded-lg bg-background/60 p-1.5 text-muted/60 backdrop-blur-sm transition-all hover:bg-background/90 hover:text-foreground"
                aria-label="Show agent card"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17 1l4 4-4 4" />
                  <path d="M3 11V9a4 4 0 0 1 4-4h14" />
                  <path d="M7 23l-4-4 4-4" />
                  <path d="M21 13v2a4 4 0 0 1-4 4H3" />
                </svg>
              </button>
            </div>

            {/* Radar chart */}
            <div className="flex-1 min-h-0">
              {hasTraits ? (
                <RadarChart traits={traits} compact />
              ) : (
                <div className="flex h-full items-center justify-center">
                  <p className="text-xs text-muted/50 italic">No trait data yet</p>
                </div>
              )}
            </div>

            {/* Link to full report */}
            <Link
              href={`/agent/${encodeURIComponent(agent.agentId)}`}
              className="block text-center text-xs font-medium text-action hover:underline pt-1"
            >
              Full report card &rarr;
            </Link>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
