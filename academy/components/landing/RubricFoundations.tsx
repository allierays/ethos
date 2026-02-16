"use client";

import { motion } from "motion/react";
import GlossaryTerm from "../shared/GlossaryTerm";
import {
  fadeUp,
  slideInLeft,
  slideInRight,
  staggerContainer,
  whileInView,
} from "@/lib/motion";

export default function RubricFoundations() {
  return (
    <section className="bg-surface border-y border-border">
      <div className="mx-auto max-w-5xl px-6 py-20">
        {/* Section header */}
        <motion.div className="max-w-3xl" variants={fadeUp} {...whileInView}>
          <p className="text-xs font-semibold uppercase tracking-widest text-ethos-600">
            Foundations
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-foreground">
            Where the Rubric Came From
          </h2>
          <p className="mt-4 text-lg text-muted leading-relaxed">
            The project started with research, not code. Claude&apos;s Agent
            Teams worked in parallel, producing 28 research documents before a
            single line of Python. They cross-referenced Claude&apos;s Constitution,
            OpenClaw, Cialdini, Konnikova, and Anthropic&apos;s safety reports
            simultaneously.
          </p>
        </motion.div>

        {/* Source cards */}
        <motion.div
          className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
          variants={staggerContainer}
          {...whileInView}
        >
          {[
            {
              label: "Claude\u2019s Constitution",
              detail:
                "Seven components of honesty, the principal hierarchy, harm avoidance factors",
              accent: "border-ethos-200 bg-ethos-50/50",
              tag: "text-ethos-600",
            },
            {
              label: "Claude 4 System Card",
              detail:
                "16 assessment categories for risks like sycophancy and alignment faking",
              accent: "border-logos-200 bg-logos-50/50",
              tag: "text-logos-600",
            },
            {
              label: "Sabotage Risk Report",
              detail:
                "Where frontier models could undermine oversight, sandbagging, steganography",
              accent: "border-pathos-200 bg-pathos-50/50",
              tag: "text-pathos-600",
            },
            {
              label: "Manipulation Research",
              detail:
                "Thompson\u2019s 1849 confidence game through Cialdini\u2019s six principles of influence",
              accent: "border-border bg-background",
              tag: "text-muted",
            },
          ].map((src) => (
            <motion.div
              key={src.label}
              variants={fadeUp}
              className={`rounded-xl border ${src.accent} p-5`}
            >
              <p
                className={`text-xs font-semibold uppercase tracking-wider ${src.tag}`}
              >
                {src.label}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                {src.detail}
              </p>
            </motion.div>
          ))}
        </motion.div>

        {/* Aristotle framework */}
        <div className="mt-16 grid items-center gap-10 lg:grid-cols-2">
          <motion.div variants={slideInLeft} {...whileInView}>
            <p className="text-xs font-semibold uppercase tracking-widest text-logos-600">
              Organizing structure
            </p>
            <h3 className="mt-3 text-xl font-bold text-foreground">
              Aristotle&apos;s Rhetoric gave Ethos its framework
            </h3>
            <p className="mt-4 text-muted leading-relaxed">
              His three modes of persuasion became the three scoring dimensions.
              His concept of <GlossaryTerm slug="phronesis">phronesis</GlossaryTerm>, practical wisdom, became the graph layer
              that tracks character over time.
            </p>
            <p className="mt-4 text-sm font-medium text-foreground/80">
              Virtue is habit, not a single act. One message tells you nothing. A
              pattern of messages tells you everything.
            </p>
          </motion.div>

          <motion.div
            className="flex flex-col gap-3"
            variants={staggerContainer}
            {...whileInView}
          >
            {[
              {
                greek: "\u1F76\u03B8\u03BF\u03C2",
                name: "Ethos",
                meaning: "Integrity and virtue",
                color: "border-l-ethos-500 bg-ethos-50/40",
              },
              {
                greek: "\u03BB\u03CC\u03B3\u03BF\u03C2",
                name: "Logos",
                meaning: "Logic and reasoning",
                color: "border-l-logos-500 bg-logos-50/40",
              },
              {
                greek: "\u03C0\u03AC\u03B8\u03BF\u03C2",
                name: "Pathos",
                meaning: "Empathy and recognition",
                color: "border-l-pathos-500 bg-pathos-50/40",
              },
            ].map((dim) => (
              <motion.div
                key={dim.name}
                variants={slideInRight}
                className={`flex items-center gap-4 rounded-lg border-l-4 ${dim.color} px-5 py-4`}
              >
                <span className="text-xl font-light text-muted/60 select-none">
                  {dim.greek}
                </span>
                <div>
                  <p className="font-semibold text-foreground">{dim.name}</p>
                  <p className="text-sm text-muted">{dim.meaning}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* Indicator growth */}
        <motion.div
          className="mt-16 rounded-2xl border border-border/50 bg-background p-8"
          variants={fadeUp}
          {...whileInView}
        >
          <div className="flex flex-col items-center gap-6 sm:flex-row">
            <div className="flex shrink-0 items-baseline gap-2">
              <span className="text-5xl font-bold tracking-tight text-ethos-600">
                134
              </span>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-6 w-6 text-muted/40"
              >
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
              <span className="text-5xl font-bold tracking-tight text-logos-600">
                214
              </span>
            </div>
            <div>
              <p className="font-semibold text-foreground">
                Behavioral indicators, grown through real use
              </p>
              <p className="mt-1 text-sm text-muted leading-relaxed">
                The first taxonomy had 134 indicators drawn from 28 research
                documents. Within 24 hours the Sabotage Risk Report contributed
                10 more. By the end of the week, the count reached 214. Every
                indicator traces back to a specific source.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
