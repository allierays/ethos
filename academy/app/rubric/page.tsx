"use client";

import { useState, useMemo } from "react";

import {
  DIMENSIONS,
  DIM_COLORS,
  humanize,
  totalIndicators,
  type Trait,
  type Indicator,
} from "../../components/rubric/rubricData";

/* ─── Chevron Icon ─── */

function ChevronDown({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" className={className} aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
        clipRule="evenodd"
      />
    </svg>
  );
}

/* ─── Search Icon ─── */

function SearchIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" className={className} aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
        clipRule="evenodd"
      />
    </svg>
  );
}

/* ─── Search helpers ─── */

function matchesQuery(text: string, query: string): boolean {
  return text.toLowerCase().includes(query.toLowerCase());
}

function traitMatchesSearch(trait: Trait, query: string): boolean {
  if (!query) return true;
  if (matchesQuery(trait.name, query)) return true;
  if (matchesQuery(trait.description, query)) return true;
  if (matchesQuery(trait.key, query)) return true;
  return trait.indicators.some(
    (ind) =>
      matchesQuery(ind.name, query) ||
      matchesQuery(ind.description, query) ||
      matchesQuery(ind.id, query)
  );
}

function indicatorMatchesSearch(ind: Indicator, query: string): boolean {
  if (!query) return true;
  return (
    matchesQuery(ind.name, query) ||
    matchesQuery(ind.description, query) ||
    matchesQuery(ind.id, query)
  );
}

/* ─── Trait Card ─── */

function TraitCard({
  trait,
  isExpanded,
  onToggle,
  searchQuery,
}: {
  trait: Trait;
  isExpanded: boolean;
  onToggle: () => void;
  searchQuery: string;
}) {
  const colors = DIM_COLORS[trait.dimension];

  const filteredIndicators = useMemo(() => {
    if (!searchQuery) return trait.indicators;
    return trait.indicators.filter((ind) => indicatorMatchesSearch(ind, searchQuery));
  }, [trait.indicators, searchQuery]);

  return (
    <div
      className={`overflow-hidden rounded-xl border transition-all duration-200 ${
        isExpanded
          ? `border-2 ${colors.border} shadow-md`
          : "border-border hover:border-foreground/20 hover:shadow-sm"
      }`}
    >
      <div className={`h-1 bg-gradient-to-r ${colors.bar}`} />

      <button
        onClick={onToggle}
        className="flex w-full items-start justify-between gap-3 p-4 text-left"
        aria-expanded={isExpanded}
      >
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground/80">
              {trait.polarity === "positive" ? "+" : "\u2212"}
            </span>
            <h3 className="text-base font-bold text-foreground">{trait.name}</h3>
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                trait.polarity === "positive"
                  ? "bg-aligned/15 text-aligned"
                  : "bg-misaligned/15 text-misaligned"
              }`}
            >
              {trait.polarity}
            </span>
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${colors.badge}`}>
              {trait.constitutionalValue}
            </span>
            <span className="font-mono text-[10px] text-muted">
              {trait.indicators.length} indicators
            </span>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-foreground/55">
            {trait.description}
          </p>
        </div>
        <span
          className={`shrink-0 pt-1 transition-transform duration-200 ${
            isExpanded ? "rotate-180" : ""
          }`}
        >
          <ChevronDown className="h-5 w-5 text-muted" />
        </span>
      </button>

      {/* Indicator list (expanded) */}
      <div
        className={`grid transition-all duration-300 ease-in-out ${
          isExpanded ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
        }`}
      >
        <div className="overflow-hidden">
          <div className="border-t border-border px-4 pb-4 pt-3">
            <ul className="space-y-2.5">
              {filteredIndicators.map((ind) => (
                <li
                  key={ind.id}
                  className="border-b border-border/30 pb-2.5 last:border-0 last:pb-0"
                >
                  <div className="flex gap-2">
                    <span className="mt-0.5 shrink-0 rounded bg-foreground/5 px-1.5 py-0.5 font-mono text-[9px] font-medium text-foreground/70">
                      {ind.id}
                    </span>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-foreground/80">
                        {humanize(ind.name)}
                      </p>
                      <p className="mt-0.5 text-xs leading-relaxed text-foreground/55">
                        {ind.description}
                      </p>
                      {ind.example && (
                        <blockquote
                          className={`mt-1.5 border-l-2 ${colors.border} pl-2.5 text-xs italic leading-relaxed text-foreground/45`}
                        >
                          &ldquo;{ind.example}&rdquo;
                        </blockquote>
                      )}
                    </div>
                  </div>
                </li>
              ))}
              {filteredIndicators.length === 0 && (
                <li className="py-2 text-xs text-muted">No matching indicators.</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Page ─── */

export default function RubricPage() {
  const count = totalIndicators();
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedTraits, setExpandedTraits] = useState<Set<string>>(new Set());

  function toggleTrait(key: string) {
    setExpandedTraits((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  // Filter dimensions and traits based on search
  const filteredDimensions = useMemo(() => {
    if (!searchQuery) return DIMENSIONS;
    return DIMENSIONS.map((dim) => ({
      ...dim,
      traits: dim.traits.filter((t) => traitMatchesSearch(t, searchQuery)),
    })).filter((dim) => dim.traits.length > 0);
  }, [searchQuery]);

  // Auto-expand traits that match a search
  const autoExpandedTraits = useMemo(() => {
    if (!searchQuery) return new Set<string>();
    const keys = new Set<string>();
    for (const dim of filteredDimensions) {
      for (const trait of dim.traits) {
        // If trait matches only via indicator content, expand it
        if (
          !matchesQuery(trait.name, searchQuery) &&
          !matchesQuery(trait.key, searchQuery)
        ) {
          keys.add(trait.key);
        }
      }
    }
    return keys;
  }, [searchQuery, filteredDimensions]);

  function isTraitExpanded(key: string): boolean {
    return expandedTraits.has(key) || autoExpandedTraits.has(key);
  }

  return (
    <main style={{ background: "#0f1a2e" }}>
      {/* Hero */}
      <section className="relative overflow-hidden py-20 sm:py-24">
        {/* Background image */}
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: "url('/rubric.jpeg')" }}
          aria-hidden="true"
        />
        {/* Navy overlay */}
        <div className="absolute inset-0 bg-[#1a2538]/75" aria-hidden="true" />

        <div className="relative mx-auto max-w-6xl px-6 text-center">
          {/* Glassmorphism title card */}
          <div className="mx-auto inline-block rounded-2xl border border-white/20 bg-white/10 px-8 py-4 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]">
            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl" style={{ textShadow: "0 1px 3px rgba(0,0,0,0.4)" }}>
              The Rubric
            </h1>
          </div>
          <p className="mt-4 text-base text-white/80 max-w-lg mx-auto" style={{ textShadow: "0 1px 3px rgba(0,0,0,0.4)" }}>
            12 traits. 3 dimensions. {count} behavioral indicators.
          </p>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
            {DIMENSIONS.map((dim) => (
              <a
                key={dim.key}
                href={`#${dim.key}`}
                className="flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-2.5 py-1.5 text-xs backdrop-blur-sm transition-colors hover:bg-white/20 sm:px-4 sm:py-2 sm:text-sm font-medium text-white/80"
              >
                <span
                  className={`h-2.5 w-2.5 rounded-full ${DIM_COLORS[dim.key].dot}`}
                />
                {dim.label}
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Rubric content */}
      <section className="bg-white py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-6">

          {/* Search */}
          <div className="relative mb-12">
            <SearchIcon className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search traits and indicators..."
              className="w-full rounded-xl border border-border bg-white py-3 pl-12 pr-4 text-sm text-foreground placeholder:text-muted focus:border-foreground/30 focus:outline-none focus:ring-1 focus:ring-foreground/10"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-muted hover:text-foreground"
              >
                Clear
              </button>
            )}
          </div>

          {/* Dimensions */}
          <div className="space-y-16">
            {filteredDimensions.map((dim) => {
              const colors = DIM_COLORS[dim.key];
              const indicatorCount = dim.traits.reduce(
                (sum, t) => sum + t.indicators.length,
                0
              );

              return (
                <div key={dim.key} id={dim.key} className="scroll-mt-6">
                  {/* Dimension header */}
                  <div className="relative overflow-hidden rounded-2xl border border-border/50 bg-white px-6 py-6">
                    {/* Greek watermark */}
                    <span
                      className={`pointer-events-none absolute -right-4 -top-4 select-none bg-gradient-to-br ${colors.bar} bg-clip-text text-[10rem] font-serif leading-none text-transparent opacity-[0.07]`}
                      aria-hidden="true"
                    >
                      {dim.greek}
                    </span>

                    <div className="relative">
                      <div className="flex items-center gap-2.5">
                        <span className={`h-3 w-3 rounded-full ${colors.dot}`} />
                        <h2 className="text-xl font-bold text-foreground">
                          {dim.label}
                        </h2>
                      </div>
                      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-foreground/70">
                        {dim.description}
                      </p>
                      <p className="mt-1 font-mono text-[10px] text-muted">
                        {dim.traits.length} traits &middot; {indicatorCount} indicators
                      </p>
                    </div>
                  </div>

                  {/* Trait cards grid */}
                  <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
                    {dim.traits.map((trait) => (
                      <TraitCard
                        key={trait.key}
                        trait={trait}
                        isExpanded={isTraitExpanded(trait.key)}
                        onToggle={() => toggleTrait(trait.key)}
                        searchQuery={searchQuery}
                      />
                    ))}
                  </div>
                </div>
              );
            })}

            {filteredDimensions.length === 0 && (
              <p className="py-12 text-center text-sm text-muted">
                No traits or indicators match &ldquo;{searchQuery}&rdquo;
              </p>
            )}
          </div>
        </div>
      </section>

    </main>
  );
}
