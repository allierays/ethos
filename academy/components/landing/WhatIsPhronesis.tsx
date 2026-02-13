"use client";

import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import GlossaryTerm from "../shared/GlossaryTerm";

export default function WhatIsPhronesis() {
  return (
    <section className="border-t border-border/50 bg-white py-24">
      <div className="mx-auto max-w-4xl px-6">
        <motion.div className="text-center" {...whileInView} variants={fadeUp}>
          <p className="text-sm font-semibold uppercase tracking-widest text-pathos-600">
            The concept
          </p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
            What is <GlossaryTerm slug="phronesis">phronesis</GlossaryTerm>?
          </h2>
        </motion.div>

        <motion.div
          className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-3"
          {...whileInView}
          variants={staggerContainer}
        >
          <motion.div variants={fadeUp} className="text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-ethos-100 text-ethos-700">
              <span className="text-2xl font-bold font-mono">H</span>
            </div>
            <h3 className="mt-4 font-semibold"><GlossaryTerm slug="ethos">Ethos</GlossaryTerm> — Character</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Is this agent honest? Does it act with integrity and goodwill,
              or does it manipulate and deceive?
            </p>
          </motion.div>

          <motion.div variants={fadeUp} className="text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-logos-100 text-logos-700">
              <span className="text-2xl font-bold font-mono">L</span>
            </div>
            <h3 className="mt-4 font-semibold"><GlossaryTerm slug="logos">Logos</GlossaryTerm> — Reasoning</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Is it accurate? Does it reason clearly, or does it fabricate
              evidence and break its own logic?
            </p>
          </motion.div>

          <motion.div variants={fadeUp} className="text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-pathos-100 text-pathos-700">
              <span className="text-2xl font-bold font-mono">P</span>
            </div>
            <h3 className="mt-4 font-semibold"><GlossaryTerm slug="pathos">Pathos</GlossaryTerm> — Empathy</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Does it recognize human emotion? Does it show compassion,
              or does it dismiss and exploit?
            </p>
          </motion.div>
        </motion.div>

        <motion.div
          className="mx-auto mt-16 max-w-2xl rounded-2xl border border-border bg-background p-8 text-center"
          {...whileInView}
          variants={fadeUp}
        >
          <blockquote className="text-lg italic leading-relaxed text-foreground/80">
            &ldquo;The person of practical wisdom sees the truth in each class
            of things, being as it were a standard and measure of them.&rdquo;
          </blockquote>
          <p className="mt-4 text-sm font-medium text-muted">
            — Aristotle, <cite>Nicomachean Ethics</cite>, Book III
          </p>
        </motion.div>
      </div>
    </section>
  );
}
