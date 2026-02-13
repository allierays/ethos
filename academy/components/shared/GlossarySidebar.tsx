"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useGlossary } from "../../lib/GlossaryContext";
import {
  ALL_GLOSSARY_ENTRIES,
  getGlossaryByCategory,
  type GlossaryEntry,
} from "../../lib/glossary";

const DIM_COLORS: Record<string, string> = {
  ethos: "#3b8a98",
  logos: "#2e4a6e",
  pathos: "#e0a53c",
};

const CATEGORIES: { key: GlossaryEntry["category"]; label: string }[] = [
  { key: "dimension", label: "Dimensions" },
  { key: "trait", label: "Traits" },
  { key: "framework", label: "Framework" },
];

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
            {selectedTerm ? (
              <TermDetail entry={selectedTerm} onSelect={selectTerm} />
            ) : (
              <TermList onSelect={selectTerm} />
            )}
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

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
    <div>
      <div className="flex items-center gap-2">
        <span
          className="inline-block h-3 w-3 rounded-full"
          style={{ backgroundColor: accentColor }}
        />
        <h3 className="text-lg font-semibold text-[#1a2538]">{entry.term}</h3>
      </div>

      <div className="mt-1 flex flex-wrap gap-1.5">
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
      </div>

      <p className="mt-4 text-sm leading-relaxed text-foreground/80">
        {entry.definition}
      </p>

      {entry.relatedTerms && entry.relatedTerms.length > 0 && (
        <div className="mt-5">
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
        </div>
      )}
    </div>
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
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
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
