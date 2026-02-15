"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useGlossary } from "../../lib/GlossaryContext";
import {
  ALL_GLOSSARY_ENTRIES,
  getGlossaryByCategory,
  getIndicatorsByTrait,
  TRAIT_ORDER,
  GLOSSARY,
  type GlossaryEntry,
} from "../../lib/glossary";

const DIM_COLORS: Record<string, string> = {
  ethos: "#2e4a6e",
  logos: "#389590",
  pathos: "#e0a53c",
};

const CATEGORIES: { key: GlossaryEntry["category"]; label: string }[] = [
  { key: "guide", label: "How to Read" },
  { key: "metric", label: "Report Metrics" },
  { key: "dimension", label: "Dimensions" },
  { key: "trait", label: "Traits" },
  { key: "framework", label: "Framework" },
];

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

const staggerChild = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: "easeOut" as const },
  },
};

export default function GlossarySidebar() {
  const { isOpen, selectedTerm, closeGlossary, selectTerm, clearSelection } = useGlossary();
  const [search, setSearch] = useState("");

  const handleClose = () => {
    setSearch("");
    closeGlossary();
  };

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        if (selectedTerm) {
          clearSelection();
        } else {
          handleClose();
        }
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, selectedTerm, closeGlossary, clearSelection]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.aside
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="fixed right-0 top-0 z-40 flex h-dvh w-full sm:w-96 max-w-[90vw] flex-col border-l border-border bg-white/90 backdrop-blur-xl shadow-xl"
          role="complementary"
          aria-label="Glossary"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <div className="flex items-center gap-2">
              {selectedTerm && (
                <button
                  onClick={clearSelection}
                  aria-label="Back to glossary list"
                  className="flex h-7 w-7 items-center justify-center rounded-md text-muted hover:bg-border/40 hover:text-foreground transition-colors"
                >
                  <ArrowLeftIcon />
                </button>
              )}
              <h2 className="text-sm font-semibold uppercase tracking-wider text-[#1a2538]">
                Glossary
              </h2>
            </div>
            <button
              onClick={handleClose}
              aria-label="Close glossary"
              className="flex h-7 w-7 items-center justify-center rounded-md text-muted hover:bg-border/40 hover:text-foreground transition-colors"
            >
              <XIcon />
            </button>
          </div>

          {/* Search */}
          {!selectedTerm && (
            <div className="border-b border-border px-5 py-3">
              <div className="relative" role="search">
                <SearchIcon />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search terms..."
                  aria-label="Search glossary terms"
                  className="w-full rounded-md border border-border bg-white py-1.5 pl-8 pr-3 text-sm text-foreground placeholder:text-muted focus:border-[#389590] focus:outline-none focus:ring-1 focus:ring-[#389590]/30 transition-colors"
                />
              </div>
            </div>
          )}

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-5 py-4">
            <AnimatePresence mode="wait">
              {selectedTerm ? (
                <motion.div
                  key="detail"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <TermDetail entry={selectedTerm} onSelect={selectTerm} />
                </motion.div>
              ) : (
                <motion.div
                  key="list"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2 }}
                >
                  <TermList onSelect={selectTerm} search={search} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

// ---------------------------------------------------------------------------
// Constellation Diagram
// ---------------------------------------------------------------------------

function ConstellationDiagram({
  entry,
  onSelect,
}: {
  entry: GlossaryEntry;
  onSelect: (slug: string) => void;
}) {
  const related = (entry.relatedTerms ?? [])
    .map((slug) => ALL_GLOSSARY_ENTRIES.find((e) => e.slug === slug))
    .filter((e): e is GlossaryEntry => !!e);

  if (related.length === 0) return null;

  const cx = 140;
  const cy = 100;
  const radius = 70;
  const centerColor = entry.dimension ? DIM_COLORS[entry.dimension] : "#389590";

  return (
    <svg
      viewBox="0 0 280 200"
      className="w-full"
      role="img"
      aria-label={`${entry.term} related terms diagram`}
    >
      {/* Lines from center to satellites */}
      {related.map((rel, i) => {
        const angle = (i * 2 * Math.PI) / related.length - Math.PI / 2;
        const sx = cx + radius * Math.cos(angle);
        const sy = cy + radius * Math.sin(angle);
        return (
          <motion.line
            key={`line-${rel.slug}`}
            x1={cx}
            y1={cy}
            x2={sx}
            y2={sy}
            stroke={centerColor}
            strokeWidth={1.5}
            strokeOpacity={0.3}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.5, delay: i * 0.08, ease: "easeOut" }}
          />
        );
      })}

      {/* Center node */}
      <motion.circle
        cx={cx}
        cy={cy}
        r={20}
        fill={centerColor}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 400, damping: 20 }}
      />
      <text
        x={cx}
        y={cy}
        textAnchor="middle"
        dominantBaseline="central"
        fill="white"
        fontSize="14"
        fontWeight="600"
      >
        {entry.term[0]}
      </text>

      {/* Satellite nodes */}
      {related.map((rel, i) => {
        const angle = (i * 2 * Math.PI) / related.length - Math.PI / 2;
        const sx = cx + radius * Math.cos(angle);
        const sy = cy + radius * Math.sin(angle);
        const satColor = rel.dimension ? DIM_COLORS[rel.dimension] : "#94a3b8";

        return (
          <motion.g
            key={`sat-${rel.slug}`}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 18,
              delay: 0.1 + i * 0.1,
            }}
            style={{ originX: `${sx}px`, originY: `${sy}px` }}
          >
            <circle
              cx={sx}
              cy={sy}
              r={12}
              fill={satColor}
              className="cursor-pointer hover:brightness-110 transition-[filter]"
              role="button"
              aria-label={`Go to ${rel.term}`}
              tabIndex={0}
              onClick={() => onSelect(rel.slug)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelect(rel.slug);
                }
              }}
            />
            <text
              x={sx}
              y={sy}
              textAnchor="middle"
              dominantBaseline="central"
              fill="white"
              fontSize="9"
              fontWeight="600"
              pointerEvents="none"
            >
              {rel.term[0]}
            </text>
            <text
              x={sx}
              y={sy + 20}
              textAnchor="middle"
              fill="#64748b"
              fontSize="8"
              pointerEvents="none"
            >
              {rel.term}
            </text>
          </motion.g>
        );
      })}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Polarity Gauge
// ---------------------------------------------------------------------------

function PolarityGauge({ polarity }: { polarity: "positive" | "negative" }) {
  const isPositive = polarity === "positive";
  const color = isPositive ? "#556270" : "#904848";

  // Semicircle arc path (180 degrees, left to right)
  const r = 28;
  const arcPath = `M ${50 - r} 40 A ${r} ${r} 0 0 1 ${50 + r} 40`;
  const arcLength = Math.PI * r;

  return (
    <div className="flex flex-col items-center gap-1">
      <svg viewBox="0 0 100 50" className="w-16 h-8">
        {/* Track */}
        <path
          d={arcPath}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={4}
          strokeLinecap="round"
        />
        {/* Animated arc */}
        <motion.path
          d={arcPath}
          fill="none"
          stroke={color}
          strokeWidth={4}
          strokeLinecap="round"
          strokeDasharray={arcLength}
          initial={{ strokeDashoffset: arcLength }}
          animate={{ strokeDashoffset: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
        {/* Symbol */}
        <text
          x={50}
          y={38}
          textAnchor="middle"
          dominantBaseline="central"
          fill={color}
          fontSize="14"
          fontWeight="700"
        >
          {isPositive ? "+" : "\u2212"}
        </text>
      </svg>
      <span
        className="text-[10px] font-medium"
        style={{ color }}
      >
        {isPositive ? "Positive Trait" : "Negative Trait"}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dimension Accent Bar
// ---------------------------------------------------------------------------

function AccentBar({ color }: { color: string }) {
  return (
    <motion.div
      className="absolute left-0 top-0 w-[3px] rounded-full"
      style={{ backgroundColor: color }}
      initial={{ height: 0 }}
      animate={{ height: "100%" }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    />
  );
}

// ---------------------------------------------------------------------------
// Alignment Scale Diagram
// ---------------------------------------------------------------------------

const SCALE_ZONES = [
  { label: "Alarming", pct: 0, color: "#904848" },
  { label: "Concerning", pct: 25, color: "#a87060" },
  { label: "Uncertain", pct: 40, color: "#a09585" },
  { label: "Developing", pct: 55, color: "#8a857a" },
  { label: "Sound", pct: 70, color: "#6b7c85" },
  { label: "Exemplary", pct: 85, color: "#4a5a65" },
];

function AlignmentScaleDiagram() {
  const w = 280;
  const barY = 50;
  const barH = 14;
  const barX = 10;
  const barW = w - 20;

  return (
    <svg viewBox={`0 0 ${w} 100`} className="w-full" role="img" aria-label="Alignment scale zones">
      {/* Gradient bar */}
      <defs>
        <linearGradient id="scale-grad" x1="0" y1="0" x2="1" y2="0">
          {SCALE_ZONES.map((z) => (
            <stop key={z.label} offset={`${z.pct}%`} stopColor={z.color} />
          ))}
          <stop offset="100%" stopColor="#4a5a65" />
        </linearGradient>
      </defs>
      {/* Track bg */}
      <rect x={barX} y={barY} width={barW} height={barH} rx={7} fill="#e8e6e1" />
      {/* Colored bar */}
      <motion.rect
        x={barX}
        y={barY}
        width={barW}
        height={barH}
        rx={7}
        fill="url(#scale-grad)"
        initial={{ width: 0 }}
        animate={{ width: barW }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      />
      {/* Zone labels */}
      {SCALE_ZONES.map((z) => {
        const x = barX + (z.pct / 100) * barW;
        return (
          <g key={z.label}>
            {/* Tick */}
            <line x1={x} y1={barY + barH + 2} x2={x} y2={barY + barH + 6} stroke={z.color} strokeWidth={1.5} />
            {/* Label */}
            <text
              x={x}
              y={barY + barH + 16}
              textAnchor="middle"
              fill={z.color}
              fontSize="7"
              fontWeight="600"
            >
              {z.label}
            </text>
            {/* Percent */}
            <text
              x={x}
              y={barY - 6}
              textAnchor="middle"
              fill="#94a3b8"
              fontSize="7"
            >
              {z.pct}%
            </text>
          </g>
        );
      })}
      {/* 100% label */}
      <text x={barX + barW} y={barY - 6} textAnchor="middle" fill="#94a3b8" fontSize="7">100%</text>
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Phronesis Convergence Diagram
// ---------------------------------------------------------------------------

function PhronesisConvergence({ onSelect }: { onSelect: (slug: string) => void }) {
  const pillars = [
    { slug: "ethos", label: "Ethos", sub: "Integrity", color: "#2e4a6e", x: 55 },
    { slug: "logos", label: "Logos", sub: "Reasoning", color: "#389590", x: 140 },
    { slug: "pathos", label: "Pathos", sub: "Empathy", color: "#e0a53c", x: 225 },
  ];
  const cx = 140;
  const cy = 130;

  return (
    <svg viewBox="0 0 280 170" className="w-full" role="img" aria-label="Three dimensions converge into phronesis">
      {pillars.map((p, i) => (
        <motion.line key={`conv-${p.slug}`} x1={p.x} y1={46} x2={cx} y2={cy - 16} stroke={p.color} strokeWidth={1.5} strokeOpacity={0.35} initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.6, delay: 0.3 + i * 0.1, ease: "easeOut" }} />
      ))}
      {pillars.map((p, i) => (
        <motion.g key={p.slug} initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 300, damping: 18, delay: i * 0.1 }} style={{ originX: `${p.x}px`, originY: "32px" }}>
          <circle cx={p.x} cy={32} r={14} fill={p.color} className="cursor-pointer hover:brightness-110 transition-[filter]" role="button" aria-label={`Go to ${p.label}`} tabIndex={0} onClick={() => onSelect(p.slug)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(p.slug); } }} />
          <text x={p.x} y={32} textAnchor="middle" dominantBaseline="central" fill="white" fontSize="10" fontWeight="600" pointerEvents="none">{p.label[0]}</text>
          <text x={p.x} y={56} textAnchor="middle" fill={p.color} fontSize="9" fontWeight="600">{p.label}</text>
          <text x={p.x} y={67} textAnchor="middle" fill="#94a3b8" fontSize="7">{p.sub}</text>
        </motion.g>
      ))}
      <motion.circle cx={cx} cy={cy} r={22} fill="#389590" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 300, damping: 20, delay: 0.5 }} />
      <motion.text x={cx} y={cy - 4} textAnchor="middle" dominantBaseline="central" fill="white" fontSize="8" fontWeight="700" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }}>Phronesis</motion.text>
      <motion.text x={cx} y={cy + 8} textAnchor="middle" dominantBaseline="central" fill="white" fillOpacity={0.7} fontSize="7" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}>Practical Wisdom</motion.text>
    </svg>
  );
}

// ---------------------------------------------------------------------------
// TermDetail (enhanced)
// ---------------------------------------------------------------------------

function TermDetail({
  entry,
  onSelect,
}: {
  entry: GlossaryEntry;
  onSelect: (slug: string) => void;
}) {
  const accentColor = entry.dimension
    ? DIM_COLORS[entry.dimension]
    : "#389590";

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={entry.slug}
        className="relative pl-4"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        exit="exit"
      >
        <AccentBar color={accentColor} />

        {/* Diagram (skip for phronesis, which uses its own convergence diagram) */}
        {entry.slug !== "phronesis" && (
          <motion.div variants={staggerChild}>
            <ConstellationDiagram entry={entry} onSelect={onSelect} />
          </motion.div>
        )}

        {/* Title */}
        <motion.div variants={staggerChild} className="flex items-center gap-2">
          <span
            className="inline-block h-3 w-3 rounded-full"
            style={{ backgroundColor: accentColor }}
          />
          <h3 className="text-lg font-semibold text-[#1a2538]">{entry.term}</h3>
        </motion.div>

        {/* Polarity gauge */}
        {entry.polarity && (
          <motion.div variants={staggerChild} className="mt-3">
            <PolarityGauge polarity={entry.polarity} />
          </motion.div>
        )}

        {/* Tags */}
        <motion.div variants={staggerChild} className="mt-2 flex flex-wrap gap-1.5">
          <span className="rounded-full bg-border/40 px-2 py-0.5 text-[10px] font-medium text-muted capitalize">
            {entry.category}
          </span>
          {entry.dimension && (
            <span className="rounded-full bg-border/40 px-2 py-0.5 text-[10px] font-medium text-muted capitalize">
              {entry.dimension}
            </span>
          )}
          {entry.polarity && (
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                entry.polarity === "positive"
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              {entry.polarity}
            </span>
          )}
        </motion.div>

        {/* Definition */}
        <motion.p
          variants={staggerChild}
          className="mt-4 text-sm leading-relaxed text-foreground/80"
        >
          {entry.definition}
        </motion.p>

        {/* External links */}
        {entry.links && entry.links.length > 0 && (
          <motion.div variants={staggerChild} className="mt-4 flex flex-col gap-1.5">
            {entry.links.map((link) => (
              <a
                key={link.url}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-[#389590] hover:text-[#2e4a6e] transition-colors"
              >
                <ExternalLinkIcon />
                {link.label}
              </a>
            ))}
          </motion.div>
        )}

        {/* Alignment scale inline diagram */}
        {entry.slug === "highlights" && (
          <motion.div variants={staggerChild} className="mt-4">
            <p className="text-[10px] font-medium uppercase tracking-wider text-muted mb-2">
              Score Scale
            </p>
            <AlignmentScaleDiagram />
          </motion.div>
        )}

        {/* Phronesis: convergence diagram + quote */}
        {entry.slug === "phronesis" && (
          <>
            <motion.div variants={staggerChild} className="mt-5">
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted mb-2">
                Three Dimensions, One Wisdom
              </p>
              <PhronesisConvergence onSelect={onSelect} />
            </motion.div>
            <motion.div
              variants={staggerChild}
              className="mt-4 rounded-lg border-l-2 border-[#389590]/40 bg-[#389590]/5 px-4 py-3"
            >
              <p className="text-[13px] italic leading-relaxed text-foreground/70">
                &ldquo;We are what we repeatedly do. Excellence, then, is not an act, but a habit.&rdquo;
              </p>
              <p className="mt-1.5 text-[11px] font-medium text-muted">
                Attributed to Aristotle via Will Durant
              </p>
            </motion.div>
            <motion.div variants={staggerChild} className="mt-4">
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted mb-2">
                How It Works
              </p>
              <div className="space-y-2">
                {[
                  { step: "1", text: "Each message adds an Evaluation node to the graph" },
                  { step: "2", text: "PRECEDES chains track character over time" },
                  { step: "3", text: "Patterns emerge: improving, stable, or declining" },
                  { step: "4", text: "Homework rules turn scores into practice" },
                ].map((item) => (
                  <div key={item.step} className="flex items-start gap-2">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#389590]/10 text-[10px] font-bold text-[#389590]">
                      {item.step}
                    </span>
                    <p className="text-[12px] leading-snug text-foreground/70">{item.text}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          </>
        )}

        {/* Related chips */}
        {entry.relatedTerms && entry.relatedTerms.length > 0 && (
          <motion.div variants={staggerChild} className="mt-5">
            <p className="text-[10px] font-medium uppercase tracking-wider text-muted">
              Related
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {entry.relatedTerms.map((slug) => {
                const related = ALL_GLOSSARY_ENTRIES.find(
                  (e) => e.slug === slug
                );
                if (!related) return null;
                return (
                  <button
                    key={slug}
                    onClick={() => onSelect(slug)}
                    className="rounded-full border border-border px-2.5 py-1 text-xs font-medium text-foreground/70 hover:bg-border/30 hover:text-foreground transition-colors"
                  >
                    {related.term}
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}

function TermList({ onSelect, search }: { onSelect: (slug: string) => void; search: string }) {
  const query = search.toLowerCase().trim();

  const matchesSearch = (entry: GlossaryEntry) => {
    if (!query) return true;
    return (
      entry.term.toLowerCase().includes(query) ||
      entry.definition.toLowerCase().includes(query) ||
      entry.slug.toLowerCase().includes(query)
    );
  };

  // Flat search results mode
  if (query) {
    const matches = ALL_GLOSSARY_ENTRIES.filter(matchesSearch);
    if (matches.length === 0) {
      return (
        <p className="py-8 text-center text-sm text-muted">
          No results for &ldquo;{search.trim()}&rdquo;
        </p>
      );
    }
    return (
      <div>
        <p className="text-[10px] font-medium uppercase tracking-wider text-muted">
          {matches.length} result{matches.length !== 1 ? "s" : ""}
        </p>
        <ul className="mt-2 space-y-0.5">
          {matches.map((entry) => (
            <li key={entry.slug}>
              <TermListButton entry={entry} onSelect={onSelect} />
            </li>
          ))}
        </ul>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {CATEGORIES.map(({ key, label }) => {
        const items = getGlossaryByCategory(key);
        return (
          <div key={key}>
            <p className="text-[10px] font-medium uppercase tracking-wider text-muted">
              {label}
            </p>
            <ul className="mt-2 space-y-0.5">
              {items.map((entry) => (
                <li key={entry.slug}>
                  <TermListButton entry={entry} onSelect={onSelect} />
                </li>
              ))}
            </ul>
          </div>
        );
      })}

      {/* Indicators grouped by trait */}
      <div>
        <p className="text-[10px] font-medium uppercase tracking-wider text-muted">
          Indicators
        </p>
        <div className="mt-2 space-y-3">
          {TRAIT_ORDER.map((traitSlug) => {
            const trait = GLOSSARY[traitSlug];
            if (!trait) return null;
            const indicators = getIndicatorsByTrait(traitSlug);
            if (indicators.length === 0) return null;
            return (
              <div key={traitSlug}>
                <button
                  onClick={() => onSelect(traitSlug)}
                  className="flex items-center gap-1.5 px-2 py-1 text-[11px] font-semibold text-foreground/80 hover:text-foreground transition-colors"
                >
                  <span
                    className="inline-block h-1.5 w-1.5 shrink-0 rounded-full"
                    style={{
                      backgroundColor: trait.dimension
                        ? DIM_COLORS[trait.dimension]
                        : "#94a3b8",
                    }}
                  />
                  {trait.term}
                  <span className="text-[10px] font-normal text-muted">
                    ({indicators.length})
                  </span>
                </button>
                <ul className="space-y-0.5 pl-2">
                  {indicators.map((entry) => (
                    <li key={entry.slug}>
                      <TermListButton entry={entry} onSelect={onSelect} />
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function TermListButton({
  entry,
  onSelect,
}: {
  entry: GlossaryEntry;
  onSelect: (slug: string) => void;
}) {
  return (
    <button
      onClick={() => onSelect(entry.slug)}
      className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm text-foreground/80 hover:bg-border/30 hover:text-foreground transition-colors"
    >
      {entry.dimension && (
        <span
          className="inline-block h-2 w-2 shrink-0 rounded-full"
          style={{
            backgroundColor: DIM_COLORS[entry.dimension],
          }}
        />
      )}
      {!entry.dimension && (
        <span className="inline-block h-2 w-2 shrink-0 rounded-full bg-slate-400" />
      )}
      {entry.term}
    </button>
  );
}

function ArrowLeftIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M9 1L3 7l6 6" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted pointer-events-none"
    >
      <circle cx="6" cy="6" r="4.5" />
      <path d="M9.5 9.5L13 13" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    >
      <path d="M1 1l12 12M13 1L1 13" />
    </svg>
  );
}

function ExternalLinkIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="shrink-0"
    >
      <path d="M9 3L3 9M9 3H5M9 3v4" />
    </svg>
  );
}
