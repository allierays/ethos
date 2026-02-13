"use client";

import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import { DIMENSION_COLORS } from "../../lib/colors";
import type { EvaluationHistoryItem } from "../../lib/types";
import GraphHelpButton from "../shared/GraphHelpButton";

interface VirtueHabitsProps {
  history: EvaluationHistoryItem[];
  agentName?: string;
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

  const latest = scores[scores.length - 1];
  const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
  const variance =
    scores.reduce((sum, s) => sum + (s - avg) ** 2, 0) / scores.length;
  const trend = scores[scores.length - 1] - scores[0];
  const isConsistent = variance < 0.03;

  let status: HabitStatus;
  if (latest > 0.7 && isConsistent) {
    status = "established";
  } else if (trend > 0.03) {
    status = "forming";
  } else if (latest > 0.5) {
    status = "emerging";
  } else {
    status = "needs_work";
  }

  return { status, strength: latest, trend, scores };
}

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
            Which of {name}&apos;s virtues are becoming habits?
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-foreground/50">
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

                      {/* Consistency squares: solid = strong, outline = weak */}
                      <div className="mt-1.5 flex gap-1">
                        {habit.scores.map((score, i) => {
                          const strong = score >= 0.7;
                          return (
                            <div
                              key={i}
                              className="h-3 flex-1 rounded-sm"
                              style={
                                strong
                                  ? { backgroundColor: dim.color }
                                  : { border: `1.5px solid ${dim.color}40`, backgroundColor: "transparent" }
                              }
                              title={`Eval ${i + 1}: ${Math.round(score * 100)}%`}
                            />
                          );
                        })}
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
