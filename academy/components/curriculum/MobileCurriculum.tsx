"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  DIMENSIONS,
  DIM_COLORS,
  humanize,
  type Dimension,
  type Trait,
} from "./curriculumData";
import {
  fadeUp,
  staggerContainer,
  staggerContainerFast,
  whileInView,
} from "@/lib/motion";

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

/* ─── Trait Accordion ─── */

function TraitAccordion({ trait }: { trait: Trait }) {
  const [open, setOpen] = useState(false);
  const colors = DIM_COLORS[trait.dimension];

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-white shadow-sm">
      <div className={`h-1 bg-gradient-to-r ${colors.bar}`} />
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-start justify-between gap-3 p-4 text-left"
        aria-expanded={open}
      >
        <div>
          <h4 className="text-sm font-bold text-foreground">{trait.name}</h4>
          <div className="mt-1.5 flex items-center gap-2">
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                trait.polarity === "positive"
                  ? "bg-aligned/15 text-aligned"
                  : "bg-misaligned/15 text-misaligned"
              }`}
            >
              {trait.polarity === "positive" ? "+" : "\u2212"} {trait.polarity}
            </span>
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${colors.badge}`}>
              {trait.constitutionalValue}
            </span>
            <span className="font-mono text-[10px] text-muted">
              {trait.indicators.length}
            </span>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-foreground/60">
            {trait.description}
          </p>
        </div>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="shrink-0"
        >
          <ChevronDown className="h-5 w-5 text-muted" />
        </motion.span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="border-t border-border px-4 pb-4 pt-3">
              <motion.ul
                className="space-y-2.5"
                initial="hidden"
                animate="visible"
                variants={staggerContainerFast}
              >
                {trait.indicators.map((ind) => (
                  <motion.li
                    key={ind.id}
                    variants={fadeUp}
                    className="border-b border-border/30 pb-2.5 last:border-0 last:pb-0"
                  >
                    <div className="flex gap-2">
                      <span className="mt-0.5 shrink-0 rounded bg-foreground/5 px-1.5 py-0.5 font-mono text-[9px] font-medium text-foreground/50">
                        {ind.id}
                      </span>
                      <div className="min-w-0">
                        <p className="text-[11px] font-semibold text-foreground/80">
                          {humanize(ind.name)}
                        </p>
                        <p className="mt-0.5 text-[11px] leading-relaxed text-foreground/55">
                          {ind.description}
                        </p>
                        {ind.example && (
                          <blockquote
                            className={`mt-1 border-l-2 ${colors.border} pl-2 text-[11px] italic leading-relaxed text-foreground/45`}
                          >
                            &ldquo;{ind.example}&rdquo;
                          </blockquote>
                        )}
                      </div>
                    </div>
                  </motion.li>
                ))}
              </motion.ul>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Dimension Accordion ─── */

function DimensionAccordion({ dimension }: { dimension: Dimension }) {
  const [open, setOpen] = useState(false);
  const colors = DIM_COLORS[dimension.key];
  const indicatorCount = dimension.traits.reduce(
    (sum, t) => sum + t.indicators.length,
    0
  );

  return (
    <motion.div variants={fadeUp}>
      <div className={`rounded-2xl border-l-4 ${colors.border} bg-white shadow-sm`}>
        <button
          onClick={() => setOpen(!open)}
          className="flex w-full items-start justify-between gap-3 p-5 text-left"
          aria-expanded={open}
        >
          <div>
            <div className="flex items-center gap-2.5">
              <span className={`h-3 w-3 rounded-full ${colors.dot}`} />
              <h3 className="text-lg font-bold text-foreground">
                {dimension.label}
                <span className="ml-2 font-normal text-muted">
                  ({dimension.greek})
                </span>
              </h3>
            </div>
            <p className="mt-0.5 text-xs font-medium text-muted">{dimension.name}</p>
            <p className="mt-2 text-sm leading-relaxed text-foreground/60">
              {dimension.description}
            </p>
            <p className="mt-2 font-mono text-[10px] text-muted">
              {dimension.traits.length} traits &middot; {indicatorCount} indicators
            </p>
          </div>
          <motion.span
            animate={{ rotate: open ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="shrink-0 pt-1"
          >
            <ChevronDown className="h-5 w-5 text-muted" />
          </motion.span>
        </button>

        <AnimatePresence initial={false}>
          {open && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="overflow-hidden"
            >
              <div className="space-y-3 px-5 pb-5 pt-1">
                {dimension.traits.map((trait) => (
                  <TraitAccordion key={trait.key} trait={trait} />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

/* ─── Export ─── */

export default function MobileCurriculum() {
  return (
    <div className="px-4 py-8">
      <motion.div
        className="space-y-4"
        {...whileInView}
        variants={staggerContainer}
      >
        {DIMENSIONS.map((dim) => (
          <DimensionAccordion key={dim.key} dimension={dim} />
        ))}
      </motion.div>
    </div>
  );
}
