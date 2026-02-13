"use client";

import { useEffect } from "react";
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
  ethos: "#3b8a98",
  logos: "#2e4a6e",
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
  const { isOpen, selectedTerm, closeGlossary, selectTerm } = useGlossary();

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) closeGlossary();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, closeGlossary]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.aside
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="fixed right-0 top-0 z-40 flex h-dvh w-96 max-w-[90vw] flex-col border-l border-border bg-white/90 backdrop-blur-xl shadow-xl"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[#1a2538]">
              Glossary
            </h2>
            <button
              onClick={closeGlossary}
              aria-label="Close glossary"
              className="flex h-7 w-7 items-center justify-center rounded-md text-muted hover:bg-border/40 hover:text-foreground transition-colors"
            >
              <XIcon />
            </button>
          </div>

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
                  <TermList onSelect={selectTerm} />
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
  const centerColor = entry.dimension ? DIM_COLORS[entry.dimension] : "#3b8a98";

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
  const color = isPositive ? "#10b981" : "#ef4444";

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
    : "#3b8a98";

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

        {/* Constellation */}
        <motion.div variants={staggerChild}>
          <ConstellationDiagram entry={entry} onSelect={onSelect} />
        </motion.div>

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

function TermList({ onSelect }: { onSelect: (slug: string) => void }) {
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
                  className="flex items-center gap-1.5 px-2 py-1 text-[11px] font-semibold text-foreground/60 hover:text-foreground transition-colors"
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
