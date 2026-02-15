"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { fadeUp, staggerContainer, whileInView } from "@/lib/motion";

const STATS = [
  { value: "832", label: "messages scored" },
  { value: "146", label: "agents enrolled" },
  { value: "214", label: "behavioral indicators" },
  { value: "21", label: "exam questions" },
];

export default function EvidenceStats() {
  return (
    <section className="bg-surface py-24">
      <div className="mx-auto max-w-5xl px-6">
        <motion.div {...whileInView} variants={fadeUp} className="text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            The Evidence
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-foreground/60">
            Not a prototype. A working research corpus with real agents,
            real scores, and real behavioral data in the graph.
          </p>
        </motion.div>

        <motion.div
          className="mt-16 grid grid-cols-2 gap-8 sm:grid-cols-4"
          {...whileInView}
          variants={staggerContainer}
        >
          {STATS.map((stat) => (
            <motion.div key={stat.label} variants={fadeUp} className="text-center">
              <span className="block font-mono text-4xl font-bold text-foreground sm:text-5xl">
                {stat.value}
              </span>
              <span className="mt-2 block text-sm text-foreground/50">
                {stat.label}
              </span>
            </motion.div>
          ))}
        </motion.div>

        <motion.div {...whileInView} variants={fadeUp} className="mt-12 text-center">
          <Link
            href="/research"
            className="text-sm font-semibold text-action hover:text-action-hover transition-colors"
          >
            Read the research &rarr;
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
