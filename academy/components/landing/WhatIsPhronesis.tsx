"use client";

import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import ColumnIcon from "../shared/ColumnIcon";
import GlossaryTerm from "../shared/GlossaryTerm";

export default function WhatIsPhronesis() {
  return (
    <section className="border-t border-border/50 bg-white py-24">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
          {/* Left: content */}
          <motion.div {...whileInView} variants={fadeUp}>
            <p className="text-sm font-semibold uppercase tracking-widest text-pathos-600">
              The concept
            </p>
            <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
              What is <GlossaryTerm slug="phronesis">phronesis</GlossaryTerm>?
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-muted">
              Aristotle called it practical wisdom: the ability to discern what
              is true and act on it well. Ethos measures whether AI agents
              develop this same quality across three dimensions.
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
                  <GlossaryTerm slug="logos">Logos</GlossaryTerm> — Logic
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
                  Does it respect human emotion, or dismiss and exploit it?
                </p>
              </motion.div>
            </motion.div>

            <motion.div
              className="mt-10 rounded-2xl border border-border bg-background p-6"
              {...whileInView}
              variants={fadeUp}
            >
              <blockquote className="text-base italic leading-relaxed text-foreground/80">
                &ldquo;The person of practical wisdom sees the truth in each
                class of things, being as it were a standard and measure of
                them.&rdquo;
              </blockquote>
              <p className="mt-3 text-sm font-medium text-muted">
                — Aristotle, <cite>Nicomachean Ethics</cite>, Book III
              </p>
            </motion.div>
          </motion.div>

          {/* Right: large Aristotle image */}
          <motion.div
            className="flex justify-center lg:justify-end"
            {...whileInView}
            variants={fadeUp}
          >
            <img
              src="/homepage.png"
              alt="Aristotle"
              className="h-[28rem] w-[28rem] rounded-3xl object-cover shadow-lg"
            />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
