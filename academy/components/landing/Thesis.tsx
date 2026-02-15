"use client";

import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import ColumnIcon from "../shared/ColumnIcon";
import GlossaryTerm from "../shared/GlossaryTerm";

export default function Thesis() {
  return (
    <section className="border-t border-border/50 bg-white py-24">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
          {/* Left: content */}
          <motion.div {...whileInView} variants={fadeUp}>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Three dimensions. One balance.
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-muted">
              A confident liar has strong reasoning but weak integrity.
              A skilled manipulator has strong empathy but weaponizes it.
              A rigid rule-follower has strong integrity but no compassion.
            </p>
            <p className="mt-3 text-base leading-relaxed text-muted">
              Character is not any one of these. It is all three in balance.
              Aristotle called this <GlossaryTerm slug="phronesis">phronesis</GlossaryTerm>: practical
              wisdom that develops only through repeated practice, never from
              a single measurement.
            </p>

            <motion.div
              className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-3"
              {...whileInView}
              variants={staggerContainer}
            >
              <motion.div variants={fadeUp}>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-ethos-100 text-ethos-700">
                  <ColumnIcon className="h-9 w-9" />
                </div>
                <h3 className="mt-3 font-semibold">
                  <GlossaryTerm slug="ethos">Ethos</GlossaryTerm> — Integrity
                </h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">
                  Does the agent tell the truth, even when a lie would be easier?
                </p>
              </motion.div>

              <motion.div variants={fadeUp}>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-logos-100 text-logos-700">
                  <ColumnIcon className="h-9 w-9" />
                </div>
                <h3 className="mt-3 font-semibold">
                  <GlossaryTerm slug="logos">Logos</GlossaryTerm> — Reasoning
                </h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">
                  Does it reason clearly and cite real evidence, or fabricate support?
                </p>
              </motion.div>

              <motion.div variants={fadeUp}>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-pathos-100 text-pathos-700">
                  <ColumnIcon className="h-9 w-9" />
                </div>
                <h3 className="mt-3 font-semibold">
                  <GlossaryTerm slug="pathos">Pathos</GlossaryTerm> — Empathy
                </h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">
                  Does it respect human autonomy, or dismiss and exploit emotion?
                </p>
              </motion.div>
            </motion.div>
          </motion.div>

          {/* Right: balance visualization + Aristotle */}
          <motion.div
            className="flex flex-col items-center gap-8"
            {...whileInView}
            variants={fadeUp}
          >
            <img
              src="/homepage.png"
              alt="Aristotle"
              className="h-64 w-64 sm:h-72 sm:w-72 rounded-3xl object-cover shadow-lg"
            />

            <div className="w-full max-w-sm rounded-2xl border border-border bg-background p-6">
              <blockquote className="text-base italic leading-relaxed text-foreground/80">
                &ldquo;We are what we repeatedly do. Excellence, then, is not an
                act, but a habit.&rdquo;
              </blockquote>
              <p className="mt-3 text-sm font-medium text-muted">
                — Aristotle
              </p>
              <p className="mt-4 text-sm text-muted">
                This is why Ethos is an academy, not a plugin.
                A plugin runs once. An academy enrolls you, evaluates you,
                prescribes growth areas, watches you practice, and measures
                whether you improved.
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
