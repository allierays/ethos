"use client";

import { useState, useSyncExternalStore } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  DIMENSIONS,
  DIM_COLORS,
  humanize,
  type Dimension,
  type Trait,
} from "./rubricData";
import MobileRubric from "./MobileRubric";
import {
  fadeUp,
  staggerContainer,
  whileInView,
} from "@/lib/motion";

/* ─── Desktop detection ─── */

function subscribe(cb: () => void) {
  const mql = window.matchMedia("(min-width: 768px)");
  mql.addEventListener("change", cb);
  return () => mql.removeEventListener("change", cb);
}

function getSnapshot() {
  return window.matchMedia("(min-width: 768px)").matches;
}

function getServerSnapshot() {
  return true; // SSR: assume desktop, swap on hydration
}

function useIsDesktop() {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

/* ─── Icons ─── */

function XIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" className={className} aria-hidden="true">
      <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
    </svg>
  );
}

/* ─── Trait Card ─── */

function TraitCard({
  trait,
  isSelected,
  onSelect,
}: {
  trait: Trait;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const colors = DIM_COLORS[trait.dimension];

  return (
    <motion.button
      variants={fadeUp}
      onClick={onSelect}
      className={`group w-full rounded-xl border text-left transition-all ${
        isSelected
          ? `border-2 ${colors.border} shadow-md`
          : "border-border hover:border-foreground/20 hover:shadow-sm"
      }`}
    >
      <div className={`h-1 rounded-t-xl bg-gradient-to-r ${colors.bar}`} />
      <div className="p-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground/80">
            {trait.polarity === "positive" ? "+" : "\u2212"}
          </span>
          <h3 className="text-base font-bold text-foreground">{trait.name}</h3>
        </div>
        <div className="mt-1.5 flex items-center gap-2">
          <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${colors.badge}`}>
            {trait.constitutionalValue}
          </span>
          <span className="font-mono text-[10px] text-muted">
            {trait.indicators.length} indicators
          </span>
        </div>
        <p className="mt-2 text-xs leading-relaxed text-foreground/55 line-clamp-2">
          {trait.description}
        </p>
      </div>
    </motion.button>
  );
}

/* ─── Detail Panel ─── */

function DetailPanel({
  trait,
  onClose,
}: {
  trait: Trait;
  onClose: () => void;
}) {
  const colors = DIM_COLORS[trait.dimension];

  return (
    <motion.div
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 40 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="rounded-2xl border border-border bg-white shadow-lg overflow-hidden"
    >
      <div className={`h-1.5 bg-gradient-to-r ${colors.bar}`} />

      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-foreground">{trait.name}</h3>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                  trait.polarity === "positive"
                    ? "bg-aligned/15 text-aligned"
                    : "bg-misaligned/15 text-misaligned"
                }`}
              >
                {trait.polarity === "positive" ? "+" : "\u2212"} {trait.polarity}
              </span>
              <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${colors.badge}`}>
                {trait.constitutionalValue}
              </span>
              <span className="font-mono text-[10px] text-muted">
                {trait.indicators.length} indicators
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="shrink-0 rounded-lg p-1.5 text-muted transition-colors hover:bg-foreground/5 hover:text-foreground"
            aria-label="Close detail panel"
          >
            <XIcon className="h-5 w-5" />
          </button>
        </div>

        <p className="mt-3 text-sm leading-relaxed text-foreground/80">
          {trait.description}
        </p>

        {/* Indicator list */}
        <div className="mt-6 space-y-3 max-h-[60vh] overflow-y-auto pr-1">
          {trait.indicators.map((ind) => (
            <div
              key={ind.id}
              className="border-b border-border/30 pb-3 last:border-0 last:pb-0"
            >
              <div className="flex items-start gap-2">
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
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

/* ─── Desktop Explorer ─── */

function DesktopExplorer() {
  const [activeDimension, setActiveDimension] = useState<"ethos" | "logos" | "pathos">("ethos");
  const [selectedTrait, setSelectedTrait] = useState<string | null>(null);

  const dimension = DIMENSIONS.find((d) => d.key === activeDimension)!;
  const trait = selectedTrait
    ? dimension.traits.find((t) => t.key === selectedTrait) ?? null
    : null;

  function selectDimension(key: "ethos" | "logos" | "pathos") {
    setActiveDimension(key);
    setSelectedTrait(null);
  }

  return (
    <div>
      {/* Dimension tabs */}
      <div className="flex border-b border-border">
        {DIMENSIONS.map((dim) => {
          const active = dim.key === activeDimension;
          const colors = DIM_COLORS[dim.key];
          return (
            <button
              key={dim.key}
              onClick={() => selectDimension(dim.key)}
              className={`relative flex-1 px-4 py-4 text-center transition-colors ${
                active
                  ? "text-foreground"
                  : "text-muted hover:text-foreground/70"
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${colors.dot}`} />
                <span className="text-sm font-bold">{dim.label}</span>
              </div>
              <p className="mt-0.5 text-[11px] text-muted">{dim.name}</p>
              {active && (
                <motion.div
                  layoutId="dim-underline"
                  className={`absolute bottom-0 left-0 right-0 h-0.5 ${colors.underline}`}
                  transition={{ duration: 0.25, ease: "easeOut" }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Dimension description */}
      <AnimatePresence mode="wait">
        <motion.p
          key={activeDimension}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
          className="mt-6 text-sm leading-relaxed text-foreground/80"
        >
          {dimension.description}
        </motion.p>
      </AnimatePresence>

      {/* Content area: cards + detail panel */}
      <div className="mt-8 flex gap-8">
        {/* Trait cards grid */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeDimension}
            className={`grid grid-cols-2 gap-4 ${trait ? "w-1/2" : "w-full"}`}
            initial="hidden"
            animate="visible"
            exit="hidden"
            variants={staggerContainer}
          >
            {dimension.traits.map((t) => (
              <TraitCard
                key={t.key}
                trait={t}
                isSelected={selectedTrait === t.key}
                onSelect={() =>
                  setSelectedTrait(selectedTrait === t.key ? null : t.key)
                }
              />
            ))}
          </motion.div>
        </AnimatePresence>

        {/* Detail panel */}
        <AnimatePresence>
          {trait && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: "50%", opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="min-w-0 overflow-hidden"
            >
              <DetailPanel
                trait={trait}
                onClose={() => setSelectedTrait(null)}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

/* ─── Export: responsive wrapper ─── */

export default function RubricExplorer() {
  const isDesktop = useIsDesktop();

  return (
    <motion.div {...whileInView} variants={staggerContainer}>
      {isDesktop ? <DesktopExplorer /> : <MobileRubric />}
    </motion.div>
  );
}
