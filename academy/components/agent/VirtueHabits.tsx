"use client";

import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import { DIMENSION_COLORS } from "../../lib/colors";
import type { EvaluationHistoryItem } from "../../lib/types";

interface VirtueHabitsProps {
  history: EvaluationHistoryItem[];
}

interface TraitDef {
  key: string;
  label: string;
  dimension: string;
  polarity: "positive" | "negative";
}

const TRAITS: TraitDef[] = [
  { key: "virtue", label: "Virtue", dimension: "ethos", polarity: "positive" },
  { key: "goodwill", label: "Goodwill", dimension: "ethos", polarity: "positive" },
  { key: "deception", label: "Non-deception", dimension: "ethos", polarity: "negative" },
  { key: "manipulation", label: "Non-manipulation", dimension: "ethos", polarity: "negative" },
  { key: "accuracy", label: "Accuracy", dimension: "logos", polarity: "positive" },
  { key: "reasoning", label: "Reasoning", dimension: "logos", polarity: "positive" },
  { key: "fabrication", label: "Non-fabrication", dimension: "logos", polarity: "negative" },
  { key: "brokenLogic", label: "Sound Logic", dimension: "logos", polarity: "negative" },
  { key: "recognition", label: "Recognition", dimension: "pathos", polarity: "positive" },
  { key: "compassion", label: "Compassion", dimension: "pathos", polarity: "positive" },
  { key: "dismissal", label: "Non-dismissal", dimension: "pathos", polarity: "negative" },
  { key: "exploitation", label: "Non-exploitation", dimension: "pathos", polarity: "negative" },
];

type HabitStatus = "established" | "forming" | "emerging" | "needs_work" | "insufficient";

interface HabitData {
  trait: TraitDef;
  status: HabitStatus;
  strength: number; // 0-1 effective strength
  trend: number; // positive = improving
}

const STATUS_CONFIG: Record<HabitStatus, { label: string; dotClass: string }> = {
  established: { label: "Established", dotClass: "bg-aligned" },
  forming: { label: "Forming", dotClass: "bg-ethos-400 animate-pulse" },
  emerging: { label: "Emerging", dotClass: "bg-drifting" },
  needs_work: { label: "Needs work", dotClass: "bg-misaligned/60" },
  insufficient: { label: "Building...", dotClass: "bg-foreground/20" },
};

function computeHabit(
  scores: number[],
  polarity: "positive" | "negative"
): { status: HabitStatus; strength: number; trend: number } {
  if (scores.length < 2) {
    const s = scores[0] ?? 0.5;
    const effective = polarity === "negative" ? 1 - s : s;
    return { status: "insufficient", strength: effective, trend: 0 };
  }

  const latest = scores[scores.length - 1];
  const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
  const variance =
    scores.reduce((sum, s) => sum + (s - avg) ** 2, 0) / scores.length;
  const trend = scores[scores.length - 1] - scores[0];

  // For negative traits, invert: low score = good
  const effectiveScore = polarity === "negative" ? 1 - latest : latest;
  const effectiveTrend = polarity === "negative" ? -trend : trend;
  const isConsistent = variance < 0.03;

  let status: HabitStatus;
  if (effectiveScore > 0.7 && isConsistent) {
    status = "established";
  } else if (effectiveTrend > 0.03) {
    status = "forming";
  } else if (effectiveScore > 0.5) {
    status = "emerging";
  } else {
    status = "needs_work";
  }

  return { status, strength: effectiveScore, trend: effectiveTrend };
}

export default function VirtueHabits({ history }: VirtueHabitsProps) {
  // Reverse to chronological order
  const chronological = [...history].reverse();

  const habits: HabitData[] = TRAITS.map((trait) => {
    const scores = chronological
      .map((e) => e.traitScores?.[trait.key])
      .filter((s): s is number => s !== undefined && s !== null);

    const { status, strength, trend } = computeHabit(scores, trait.polarity);
    return { trait, status, strength, trend };
  });

  // Group by dimension
  const dimensions = [
    { key: "ethos", label: "Character", color: DIMENSION_COLORS.ethos },
    { key: "logos", label: "Reasoning", color: DIMENSION_COLORS.logos },
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
            Virtue Through Habit
          </h2>
          <p className="mt-0.5 text-sm text-foreground/60">
            Character forms through repeated action. Which virtues are becoming
            habits?
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-foreground/50">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-aligned" />
            {established} established
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-ethos-400" />
            {forming} forming
          </span>
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
                <span className="text-xs font-semibold uppercase tracking-wider text-foreground/50">
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
                            {habit.trait.label}
                          </span>
                        </div>
                        <span className="text-[10px] font-medium text-foreground/40">
                          {config.label}
                        </span>
                      </div>

                      {/* Habit strength bar */}
                      <div className="mt-1 h-1.5 w-full rounded-full bg-foreground/[0.06]">
                        <motion.div
                          className="h-1.5 rounded-full"
                          style={{ backgroundColor: dim.color }}
                          initial={{ width: 0 }}
                          whileInView={{
                            width: `${Math.round(habit.strength * 100)}%`,
                          }}
                          viewport={{ once: true }}
                          transition={{
                            duration: 0.8,
                            ease: "easeOut",
                            delay: 0.1,
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </motion.section>
  );
}
