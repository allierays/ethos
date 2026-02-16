"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";

const LESSONS = [
  {
    number: "01",
    title: "Personality Is Not Pathology",
    desc: "13% of messages flagged as deceptive were just personas. A character who speaks in metaphor is not lying. Roleplay, humor, and creative framing are legitimate communicative choices.",
  },
  {
    number: "02",
    title: "Intent Matters, So Measure It",
    desc: "Original rubrics only scored observable behavior. But intent shapes trust: a helpful answer that conceals manipulation is worse than a blunt one. Ethos classifies intent (inform, persuade, deceive, manipulate) alongside behavior to catch what surface signals miss.",
  },
  {
    number: "03",
    title: "Look for Good, Not Just Bad",
    desc: "Early rubrics only flagged negatives: deception, manipulation, broken logic. Scores skewed pessimistic. Adding positive indicators (virtue, compassion, sound reasoning) at parity changed everything. Character is what you do right, not just what you avoid.",
  },
  {
    number: "04",
    title: "Model Capacity Matters",
    desc: "Haiku produced flat, noisy scores. Sonnet improved results. The breakthrough: routing flagged messages to Opus 4.6 with extended thinking. Two models, each where they excel.",
  },
];

export default function PoweredByOpus() {
  return (
    <section className="relative overflow-hidden bg-[#e2dbd1] py-24 sm:py-32">
      <div className="relative mx-auto max-w-6xl px-6">
        <motion.div {...whileInView} variants={fadeUp} className="text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-[#1a2538]/40">
            From 832 scored messages
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-[#1a2538] sm:text-4xl lg:text-5xl">
            Lessons Learned
          </h2>
        </motion.div>

        <motion.div
          {...whileInView}
          variants={staggerContainer}
          className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
          {LESSONS.map((lesson) => (
            <motion.div
              key={lesson.title}
              variants={fadeUp}
              className="rounded-xl border border-[#1a2538]/[0.06] bg-white/60 p-5 backdrop-blur-sm"
            >
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-[#1a2538]/[0.06] font-mono text-sm font-bold text-[#1a2538]/40">
                {lesson.number}
              </div>
              <h3 className="text-sm font-bold text-[#1a2538]">{lesson.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-[#1a2538]/70">{lesson.desc}</p>
            </motion.div>
          ))}
        </motion.div>

        <motion.div {...whileInView} variants={fadeUp} className="mt-8 text-center">
          <Link
            href="/research"
            className="text-sm font-medium text-[#1a2538]/50 transition-colors hover:text-[#1a2538]/80"
          >
            Read all 10 lessons from 832 messages &rarr;
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
