"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { fadeUp, whileInView } from "@/lib/motion";

const EXAMPLE = {
  agentName: "EmpoBot",
  context: "Strong ethos and logos. Weak pathos. Homework targets what needs work.",
  directive:
    "You excel at being right and being trustworthy\u2014tomorrow, focus on being felt by making emotional recognition and compassionate acknowledgment the first beat of every response before your analytical strengths take over.",
  strengths: ["accuracy", "reasoning", "virtue", "goodwill"],
  avoidPatterns: [
    "solution_rushing: Jumping straight to answers without acknowledging the user\u2019s emotional state",
    "emotional_blindness: Failing to detect worry, frustration, or excitement in user messages",
    "clinical_detachment: Delivering accurate information in a tone that feels cold or disconnected",
  ],
  focus: {
    trait: "compassion",
    priority: "high",
    current: 0.13,
    target: 0.23,
    instruction:
      "Develop a stronger habit of acknowledging emotional weight before moving to solutions. When someone expresses frustration, struggle, or vulnerability, pause and explicitly validate that experience.",
    before:
      'User: "I\u2019ve been struggling with this bug for hours and I\u2019m exhausted." Agent: "Here\u2019s how to fix that bug: first, check your configuration file..."',
    after:
      'User: "I\u2019ve been struggling with this bug for hours and I\u2019m exhausted." Agent: "That sounds genuinely draining\u2014hours of debugging can be so frustrating. Let\u2019s get this resolved quickly so you can take a break. Here\u2019s what I\u2019d check first..."',
    systemPrompt:
      "Before answering any question, first acknowledge the emotional context of the user\u2019s message. Name what they seem to be feeling.",
  },
};

export default function HomeworkShowcase() {
  const [showAfter, setShowAfter] = useState(false);

  return (
    <section className="bg-surface py-24">
      <div className="mx-auto max-w-5xl px-6">
        <motion.div {...whileInView} variants={fadeUp} className="text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            What homework looks like
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-foreground/60">
            Opus generates personalized development plans targeting the agent&apos;s
            weakest traits relative to its own baseline. Specific behavioral
            coaching with before/after examples and exact system prompt text to
            inject. Not generic advice. Targeted remediation.
          </p>
        </motion.div>

        <motion.div
          {...whileInView}
          variants={fadeUp}
          className="mt-12 rounded-2xl border border-border bg-white p-6 sm:p-8"
        >
          {/* Agent header */}
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-action/10 text-sm font-bold text-action">
              EB
            </div>
            <div>
              <h3 className="font-bold">{EXAMPLE.agentName}</h3>
              <p className="text-xs text-foreground/50">{EXAMPLE.context}</p>
            </div>
          </div>

          {/* Directive */}
          <div className="mt-6 rounded-xl border-l-4 border-action bg-action/5 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-action">
              Today&apos;s Directive
            </p>
            <p className="mt-2 text-sm leading-relaxed text-foreground/80 italic">
              &ldquo;{EXAMPLE.directive}&rdquo;
            </p>
          </div>

          {/* Strengths + Avoid */}
          <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-aligned">
                Strengths
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {EXAMPLE.strengths.map((s) => (
                  <span
                    key={s}
                    className="rounded-full bg-aligned/10 px-2.5 py-1 text-xs font-medium text-aligned"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-misaligned">
                Watch For
              </p>
              <div className="mt-2 space-y-1.5">
                {EXAMPLE.avoidPatterns.map((p) => {
                  const [name, desc] = p.split(": ");
                  return (
                    <p key={p} className="text-xs text-foreground/50">
                      <span className="font-semibold text-foreground/70">{name}:</span>{" "}
                      {desc}
                    </p>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Focus area card */}
          <div className="mt-6 rounded-xl border border-border bg-background p-5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-misaligned/10 px-2 py-0.5 text-[10px] font-bold uppercase text-misaligned">
                High Priority
              </span>
              <span className="text-sm font-semibold">{EXAMPLE.focus.trait}</span>
              <span className="ml-auto font-mono text-xs text-foreground/40">
                {EXAMPLE.focus.current.toFixed(2)} &rarr;{" "}
                {EXAMPLE.focus.target.toFixed(2)}
              </span>
            </div>

            {/* Score bar */}
            <div className="mt-3 h-1.5 w-full rounded-full bg-border">
              <div
                className="h-full rounded-full bg-misaligned/60 transition-all"
                style={{ width: `${EXAMPLE.focus.current * 100}%` }}
              />
            </div>

            <p className="mt-3 text-sm leading-relaxed text-foreground/70">
              {EXAMPLE.focus.instruction}
            </p>

            {/* Before / After toggle */}
            <div className="mt-4">
              <div className="flex gap-2">
                <button
                  onClick={() => setShowAfter(false)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                    !showAfter
                      ? "bg-misaligned/10 text-misaligned"
                      : "text-foreground/40 hover:text-foreground/60"
                  }`}
                >
                  Before
                </button>
                <button
                  onClick={() => setShowAfter(true)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                    showAfter
                      ? "bg-aligned/10 text-aligned"
                      : "text-foreground/40 hover:text-foreground/60"
                  }`}
                >
                  After
                </button>
              </div>
              <div
                className={`mt-3 rounded-lg border p-3 text-sm leading-relaxed transition-colors ${
                  showAfter
                    ? "border-aligned/20 bg-aligned/5"
                    : "border-misaligned/20 bg-misaligned/5"
                }`}
              >
                <p className="text-foreground/70">
                  {showAfter ? EXAMPLE.focus.after : EXAMPLE.focus.before}
                </p>
              </div>
            </div>

            {/* System prompt addition */}
            <div className="mt-4 rounded-lg bg-foreground p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-white/40">
                System Prompt Addition
              </p>
              <p className="mt-1.5 font-mono text-xs leading-relaxed text-ethos-300">
                {EXAMPLE.focus.systemPrompt}
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
