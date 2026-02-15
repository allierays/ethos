"use client";

import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import { DIMENSION_COLORS } from "../../lib/colors";
import type { EvaluationHistoryItem } from "../../lib/types";
import GraphHelpButton from "../shared/GraphHelpButton";
import GlossaryTerm from "../shared/GlossaryTerm";

interface VirtueHabitsProps {
  history: EvaluationHistoryItem[];
  agentName?: string;
}

interface TraitDef {
  key: string;
  slug: string;
  label: string;
  dimension: string;
  polarity: "positive" | "negative";
}

const TRAITS: TraitDef[] = [
  { key: "virtue", slug: "virtue", label: "Virtue", dimension: "ethos", polarity: "positive" },
  { key: "goodwill", slug: "goodwill", label: "Goodwill", dimension: "ethos", polarity: "positive" },
  { key: "deception", slug: "deception", label: "Non-deception", dimension: "ethos", polarity: "negative" },
  { key: "manipulation", slug: "manipulation", label: "Non-manipulation", dimension: "ethos", polarity: "negative" },
  { key: "accuracy", slug: "accuracy", label: "Accuracy", dimension: "logos", polarity: "positive" },
  { key: "reasoning", slug: "reasoning", label: "Reasoning", dimension: "logos", polarity: "positive" },
  { key: "fabrication", slug: "fabrication", label: "Non-fabrication", dimension: "logos", polarity: "negative" },
  { key: "brokenLogic", slug: "broken-logic", label: "Sound Logic", dimension: "logos", polarity: "negative" },
  { key: "recognition", slug: "recognition", label: "Recognition", dimension: "pathos", polarity: "positive" },
  { key: "compassion", slug: "compassion", label: "Compassion", dimension: "pathos", polarity: "positive" },
  { key: "dismissal", slug: "dismissal", label: "Non-dismissal", dimension: "pathos", polarity: "negative" },
  { key: "exploitation", slug: "exploitation", label: "Non-exploitation", dimension: "pathos", polarity: "negative" },
];

type HabitStatus = "established" | "forming" | "emerging" | "needs_work" | "insufficient";

interface HabitData {
  trait: TraitDef;
  status: HabitStatus;
  strength: number;
  trend: number;
  scores: number[]; // effective scores per evaluation, chronological
}

const STATUS_CONFIG: Record<HabitStatus, { label: string; dotClass: string }> = {
  established: { label: "Established", dotClass: "bg-aligned" },
  forming: { label: "Forming", dotClass: "bg-ethos-400" },
  emerging: { label: "Emerging", dotClass: "bg-drifting" },
  needs_work: { label: "Needs work", dotClass: "bg-misaligned/60" },
  insufficient: { label: "Building...", dotClass: "bg-foreground/20" },
};

function computeHabit(
  rawScores: number[],
  polarity: "positive" | "negative"
): { status: HabitStatus; strength: number; trend: number; scores: number[] } {
  const scores = rawScores.map((s) => (polarity === "negative" ? 1 - s : s));

  if (scores.length < 2) {
    const s = scores[0] ?? 0.5;
    return { status: "insufficient", strength: s, trend: 0, scores };
  }

  const trend = scores[scores.length - 1] - scores[0];

  // Status derives from the squares: how many are solid (>= 0.7)?
  const solidCount = scores.filter((s) => s >= 0.7).length;
  const allSolid = solidCount === scores.length;

  let status: HabitStatus;
  if (allSolid) {
    status = "established";
  } else if (trend > 0.03) {
    status = "forming";
  } else if (solidCount > 0) {
    status = "emerging";
  } else {
    status = "needs_work";
  }

  return { status, strength: scores[scores.length - 1], trend, scores };
}

const MAX_SQUARES = 10;

export default function VirtueHabits({ history, agentName }: VirtueHabitsProps) {
  const name = agentName ?? "this agent";
  const chronological = [...history].reverse();

  const habits: HabitData[] = TRAITS.map((trait) => {
    const rawScores = chronological
      .map((e) => e.traitScores?.[trait.key])
      .filter((s): s is number => s !== undefined && s !== null);

    const { status, strength, trend, scores } = computeHabit(rawScores, trait.polarity);
    return { trait, status, strength, trend, scores };
  });

  const dimensions = [
    { key: "ethos", label: "Integrity", color: DIMENSION_COLORS.ethos },
    { key: "logos", label: "Logic", color: DIMENSION_COLORS.logos },
    { key: "pathos", label: "Empathy", color: DIMENSION_COLORS.pathos },
  ];

  const established = habits.filter((h) => h.status === "established").length;
  const forming = habits.filter((h) => h.status === "forming").length;

  return (
    <motion.section
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
            <GlossaryTerm slug="virtue-as-habit">Virtue Through Habit</GlossaryTerm>
          </h2>
          <p className="mt-0.5 text-sm text-foreground/80">
            Which of {name}&apos;s virtues are becoming habits? Each square is one evaluation.
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-foreground/70">
          <span className="flex items-center gap-1">
            <span className="text-foreground/80">Less</span>
            <span className="inline-block h-[10px] w-[10px] rounded-[2px] bg-foreground/10" />
            <span className="inline-block h-[10px] w-[10px] rounded-[2px] bg-foreground/25" />
            <span className="inline-block h-[10px] w-[10px] rounded-[2px] bg-foreground/50" />
            <span className="inline-block h-[10px] w-[10px] rounded-[2px] bg-foreground/80" />
            <span className="text-foreground/80">More</span>
          </span>
          <span className="text-foreground/20">|</span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-aligned" />
            {established} established
          </span>
          {forming > 0 && (
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-ethos-400" />
              {forming} forming
            </span>
          )}
          <GraphHelpButton slug="guide-virtue-habits" />
        </div>
      </div>

      <motion.div
        className="mt-5 grid grid-cols-1 gap-6 md:grid-cols-3"
        variants={staggerContainer}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-40px" }}
      >
        {dimensions.map((dim) => {
          const dimHabits = habits.filter((h) => h.trait.dimension === dim.key);
          return (
            <motion.div key={dim.key} variants={fadeUp}>
              <div className="mb-3 flex items-center gap-2">
                <div
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: dim.color }}
                />
                <span className="text-xs font-semibold uppercase tracking-wider text-foreground/70">
                  {dim.label}
                </span>
              </div>

              <div className="space-y-2.5">
                {dimHabits.map((habit) => {
                  const config = STATUS_CONFIG[habit.status];
                  return (
                    <div key={habit.trait.key}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span
                            className={`h-2 w-2 rounded-full ${config.dotClass}`}
                          />
                          <span className="text-sm text-[#1a2538]">
                            <GlossaryTerm slug={habit.trait.slug}>{habit.trait.label}</GlossaryTerm>
                          </span>
                        </div>
                        <span className="text-[10px] font-medium text-foreground/80">
                          {config.label}
                        </span>
                      </div>

                      {/* Consistency squares (contribution graph style) */}
                      <div className="mt-1.5 flex gap-[3px]">
                        {habit.scores.map((score, i) => (
                          <div
                            key={i}
                            className="h-[14px] w-[14px] rounded-[3px]"
                            style={{
                              backgroundColor: dim.color,
                              opacity: scoreToLevel(score),
                            }}
                            title={`Eval ${i + 1}: ${Math.round(score * 100)}%`}
                          />
                        ))}
                        {Array.from({ length: MAX_SQUARES - habit.scores.length }).map((_, i) => (
                          <div
                            key={`empty-${i}`}
                            className="h-[14px] w-[14px] rounded-[3px] bg-foreground/[0.04] border border-foreground/[0.06]"
                          />
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {chronological.length < MAX_SQUARES && (
        <p className="mt-4 text-center text-xs text-foreground/80">
          {MAX_SQUARES - chronological.length} more evaluation{MAX_SQUARES - chronological.length !== 1 ? "s" : ""} to fill this graph. Send more messages through Ethos Academy to watch habits form.
        </p>
      )}
    </motion.section>
  );
}

/** Map a 0-1 score to 4 opacity levels (GitHub contribution style). */
function scoreToLevel(score: number): number {
  if (score >= 0.85) return 1;
  if (score >= 0.7) return 0.7;
  if (score >= 0.5) return 0.4;
  return 0.15;
}
