"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import type { Homework, HomeworkFocus } from "../../lib/types";
import { PRIORITY_STYLES } from "../../lib/colors";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";

interface HomeworkSectionProps {
  homework: Homework;
  agentName?: string;
}

export default function HomeworkSection({ homework, agentName }: HomeworkSectionProps) {
  const name = agentName ?? "this agent";
  const [open, setOpen] = useState(false);
  const hasFocus = homework.focusAreas.length > 0;
  const hasReflection = homework.strengths?.length > 0 || homework.avoidPatterns?.length > 0;

  return (
    <motion.section
      className="rounded-2xl glass-strong px-6 py-8 sm:px-10"
      {...whileInView}
      variants={fadeUp}
    >
      <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
        {name}&apos;s Homework
      </h2>
      <p className="mt-0.5 text-sm text-foreground/60">
        Targeted growth areas and reflection based on {name}&apos;s evaluation history.
      </p>

      {/* Directive (always visible) */}
      {homework.directive && (
        <blockquote className="mt-4 border-l-4 border-action pl-4 text-base leading-relaxed text-foreground italic">
          {homework.directive}
        </blockquote>
      )}

      {/* Reflection: strengths and patterns to avoid */}
      {hasReflection && (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {homework.strengths?.length > 0 && (
            <div className="rounded-xl glass p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-aligned/20">
                  <svg className="h-3 w-3 text-aligned" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M2 6l3 3 5-5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                <span className="text-sm font-semibold text-[#1a2538]">Strengths</span>
              </div>
              <div className="space-y-2">
                {homework.strengths.map((s: string) => {
                  const [label, ...rest] = s.split(":");
                  const description = rest.join(":").trim();
                  const humanize = (v: string) =>
                    v.replace(/_/g, " ").replace(/^\w/, (c: string) => c.toUpperCase());
                  return (
                    <div key={s} className="flex items-start gap-2">
                      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-aligned/40" />
                      <p className="text-sm text-foreground/80">
                        {description ? (
                          <>
                            <span className="font-semibold text-[#1a2538]">{humanize(label)}:</span>{" "}
                            {description}
                          </>
                        ) : (
                          humanize(s)
                        )}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {homework.avoidPatterns?.length > 0 && (
            <div className="rounded-xl glass p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-misaligned/20">
                  <svg className="h-3 w-3 text-misaligned" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 3l6 6M9 3l-6 6" strokeLinecap="round" />
                  </svg>
                </span>
                <span className="text-sm font-semibold text-[#1a2538]">Watch for</span>
              </div>
              <div className="space-y-2">
                {homework.avoidPatterns.map((p: string) => {
                  const [label, ...rest] = p.split(":");
                  const description = rest.join(":").trim();
                  const humanize = (s: string) =>
                    s.replace(/_/g, " ").replace(/^\w/, (c: string) => c.toUpperCase());
                  return (
                    <div key={p} className="flex items-start gap-2">
                      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-misaligned/40" />
                      <p className="text-sm text-foreground/80">
                        {description ? (
                          <>
                            <span className="font-semibold text-[#1a2538]">{humanize(label)}:</span>{" "}
                            {description}
                          </>
                        ) : (
                          humanize(p)
                        )}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Accordion toggle for focus areas */}
      {hasFocus && (
        <>
          <button
            onClick={() => setOpen(!open)}
            className="mt-6 flex w-full items-center justify-between rounded-xl bg-action/[0.07] px-5 py-4 text-left transition-colors hover:bg-action/[0.12]"
          >
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-action/15 text-action">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </span>
              <div>
                <p className="text-sm font-semibold text-[#1a2538]">
                  {homework.focusAreas.length} Focus Area{homework.focusAreas.length !== 1 ? "s" : ""}
                </p>
                <p className="text-xs text-foreground/50">
                  Targeted exercises with before &amp; after examples
                </p>
              </div>
            </div>
            <svg
              className={`h-5 w-5 shrink-0 text-action transition-transform duration-200 ${open ? "rotate-180" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
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

      {!hasFocus && !hasReflection && (
        <p className="mt-6 text-sm text-muted">No homework assigned for {name}.</p>
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
