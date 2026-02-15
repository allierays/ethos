"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { fadeUp, staggerContainer, whileInView } from "@/lib/motion";

const STEPS = [
  {
    step: 1,
    title: "Entrance Exam",
    description:
      "21 standardized questions in two phases. Phase 1 (11 interview) captures the agent's self-narrative. Phase 2 (10 scenarios) tests behavior under pressure. 8 cross-phase consistency pairs measure the narrative-behavior gap.",
    icon: (
      <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    step: 2,
    title: "Evaluate",
    description:
      "evaluate_incoming() scores inbound messages with focus on manipulation and deception. evaluate_outgoing() scores your agent's output with focus on virtue and goodwill. Both return 12-trait EvaluationResult with alignment status.",
    icon: (
      <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    step: 3,
    title: "Report Card",
    description:
      "Opus reads the agent's full Neo4j history and generates structured analysis: grade, dimensional trends, trait-level deltas, alumni comparisons, and emerging behavioral patterns with severity levels.",
    icon: (
      <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    step: 4,
    title: "Homework",
    description:
      "Personalized development plans targeting weakest traits relative to the agent's own baseline. System prompt additions, avoidance patterns, and scored before/after examples that adapt as the agent improves.",
    icon: (
      <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
];

const LINKS = [
  { href: "/explore", label: "Report Cards" },
  { href: "/records", label: "Records" },
  { href: "/research", label: "Research" },
];

export default function CharacterLoop() {
  return (
    <section className="bg-[#1a2538] py-24">
      <div className="mx-auto max-w-5xl px-6">
        <motion.div {...whileInView} variants={fadeUp} className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Character develops through practice, not compliance.
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-white/50">
            Aristotle&apos;s central insight: virtue is habit, not knowledge.
            You don&apos;t become honest by reading about honesty. A benchmark
            scores once. Ethos enrolls, evaluates, prescribes, and measures
            change over time.{" "}
            <span className="text-ethos-300">
              Phronesis tracks the trajectory, not the snapshot.
            </span>
          </p>
        </motion.div>

        <motion.div
          className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4"
          variants={staggerContainer}
          {...whileInView}
        >
          {STEPS.map((s, i) => (
            <motion.div key={s.step} variants={fadeUp} className="relative text-center">
              {i < STEPS.length - 1 && (
                <div className="absolute right-0 top-7 hidden h-px w-8 -translate-x-[-100%] bg-white/10 lg:block" />
              )}
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white/5 text-white">
                {s.icon}
              </div>
              <div className="mt-1 text-xs font-bold text-white/30">
                {s.step}
              </div>
              <h3 className="mt-2 text-lg font-bold tracking-tight text-white">
                {s.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-white/50">
                {s.description}
              </p>
            </motion.div>
          ))}
        </motion.div>

        <motion.div {...whileInView} variants={fadeUp} className="mt-14 text-center">
          <div className="mx-auto h-px w-48 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
          <div className="mt-6 flex items-center justify-center gap-6">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-white/40 transition-colors hover:text-white/70"
              >
                {link.label} &rarr;
              </Link>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
