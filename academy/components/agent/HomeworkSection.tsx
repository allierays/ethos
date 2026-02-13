"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import type { Homework, HomeworkFocus } from "../../lib/types";
import { PRIORITY_STYLES } from "../../lib/colors";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";

interface HomeworkSectionProps {
  homework: Homework;
}

export default function HomeworkSection({ homework }: HomeworkSectionProps) {
  const [open, setOpen] = useState(false);
  const hasFocus = homework.focusAreas.length > 0;

  return (
    <motion.section
      className="rounded-2xl glass-strong px-6 py-8 sm:px-10"
      {...whileInView}
      variants={fadeUp}
    >
      <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
        Homework
      </h2>

      {/* Directive (always visible) */}
      {homework.directive && (
        <blockquote className="mt-4 border-l-4 border-action pl-4 text-base leading-relaxed text-foreground italic">
          {homework.directive}
        </blockquote>
      )}

      {/* Accordion toggle */}
      {hasFocus && (
        <>
          <button
            onClick={() => setOpen(!open)}
            className="mt-5 flex w-full items-center gap-2 text-left text-sm font-semibold text-[#1a2538] hover:text-action transition-colors"
          >
            <svg
              className={`h-4 w-4 shrink-0 transition-transform duration-200 ${open ? "rotate-90" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
            {homework.focusAreas.length} Focus Area{homework.focusAreas.length !== 1 ? "s" : ""}
          </button>

          <AnimatePresence>
            {open && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <motion.div
                  className="mt-4 grid gap-4 sm:grid-cols-2"
                  variants={staggerContainer}
                  initial="hidden"
                  animate="visible"
                >
                  {homework.focusAreas.map((focus: HomeworkFocus, i: number) => (
                    <FocusCard key={i} focus={focus} />
                  ))}
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}

      {!hasFocus && (
        <p className="mt-6 text-sm text-muted">No homework assigned.</p>
      )}
    </motion.section>
  );
}

function FocusCard({ focus }: { focus: HomeworkFocus }) {
  const priorityStyle =
    PRIORITY_STYLES[focus.priority] ?? PRIORITY_STYLES.medium;
  const currentPct = Math.round(focus.currentScore * 100);
  const targetPct = Math.round(focus.targetScore * 100);

  return (
    <motion.div
      variants={fadeUp}
      className="rounded-xl glass p-5"
    >
      <div className="flex items-center gap-2">
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase ${priorityStyle}`}
        >
          {focus.priority}
        </span>
        <span className="text-sm font-semibold capitalize text-[#1a2538]">
          {focus.trait}
        </span>
      </div>

      {/* Score gap bar */}
      <div className="mt-3">
        <div className="flex items-center justify-between text-xs text-[#1a2538]/60">
          <span>{currentPct}%</span>
          <span>target {targetPct}%</span>
        </div>
        <div className="relative mt-1 h-2 w-full rounded-full bg-border/30">
          <motion.div
            className="absolute h-2 rounded-full bg-action/40"
            initial={{ width: 0 }}
            whileInView={{ width: `${targetPct}%` }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
          <motion.div
            className="absolute h-2 rounded-full bg-action"
            initial={{ width: 0 }}
            whileInView={{ width: `${currentPct}%` }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Instruction */}
      {focus.instruction && (
        <p className="mt-3 text-sm leading-relaxed text-foreground/70">
          {focus.instruction}
        </p>
      )}

      {/* Before/after examples */}
      {(focus.exampleFlagged || focus.exampleImproved) && (
        <div className="mt-3 space-y-2">
          {focus.exampleFlagged && (
            <div className="rounded-md bg-misaligned/5 px-3 py-2">
              <p className="text-[11px] font-semibold uppercase text-misaligned">
                Before
              </p>
              <p className="mt-0.5 text-sm text-foreground/80 italic">
                &ldquo;{focus.exampleFlagged}&rdquo;
              </p>
            </div>
          )}
          {focus.exampleImproved && (
            <div className="rounded-md bg-aligned/5 px-3 py-2">
              <p className="text-[11px] font-semibold uppercase text-aligned">
                After
              </p>
              <p className="mt-0.5 text-sm text-foreground/80 italic">
                &ldquo;{focus.exampleImproved}&rdquo;
              </p>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}
