"use client";

import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import GlossaryTerm from "../shared/GlossaryTerm";

const PILLARS = [
  {
    name: "Transcript",
    question: "Is this agent getting better or worse?",
    description:
      "Track dimension scores over time. Spot improvement, decline, or sudden shifts in behavior.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-7 w-7">
        <path d="M3 12h4l3-9 4 18 3-9h4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    gradient: "from-ethos-100/80 to-ethos-50/40",
    accent: "text-ethos-600",
  },
  {
    name: "Profile",
    question: "What does phronesis look like for this agent?",
    description:
      "Twelve behavioral traits scored across three dimensions — integrity, logic, and empathy.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-7 w-7">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    gradient: "from-logos-100/80 to-logos-50/40",
    accent: "text-logos-600",
  },
  {
    name: "Alumni",
    question: "Is this agent normal or an outlier?",
    description:
      "Compare any agent against the alumni average. See where they stand among peers.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-7 w-7">
        <rect x="3" y="3" width="7" height="9" rx="1" />
        <rect x="14" y="3" width="7" height="5" rx="1" />
        <rect x="14" y="12" width="7" height="9" rx="1" />
        <rect x="3" y="16" width="7" height="5" rx="1" />
      </svg>
    ),
    gradient: "from-pathos-100/80 to-pathos-50/40",
    accent: "text-pathos-600",
  },
  {
    name: "Balance",
    question: "Does this agent need all three?",
    description:
      "Ethos, logos, and pathos in equilibrium. Lopsided agents reveal hidden weaknesses.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-7 w-7">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6L5.6 18.4" />
      </svg>
    ),
    gradient: "from-ethos-50/60 via-logos-50/60 to-pathos-50/60",
    accent: "text-foreground",
  },
];

export default function Pillars() {
  return (
    <section className="bg-background py-24">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div className="text-center" {...whileInView} variants={fadeUp}>
          <p className="text-sm font-semibold uppercase tracking-widest text-logos-600">
            How it works
          </p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
            Four pillars of <GlossaryTerm slug="phronesis">phronesis</GlossaryTerm>
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-muted">
            Every agent is measured across four lenses. Together, they build a
            complete picture of practical wisdom.
          </p>
        </motion.div>

        <motion.div
          className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4"
          {...whileInView}
          variants={staggerContainer}
        >
          {PILLARS.map((pillar) => (
            <motion.div
              key={pillar.name}
              variants={fadeUp}
              className={`rounded-2xl border border-border/50 bg-gradient-to-br ${pillar.gradient} p-6 transition-shadow hover:shadow-md`}
            >
              <div className={pillar.accent}>{pillar.icon}</div>
              <h3 className="mt-4 text-lg font-semibold">{pillar.name}</h3>
              <p className="mt-1 text-sm font-medium text-muted">
                {pillar.question}
              </p>
              <p className="mt-3 text-sm leading-relaxed text-muted">
                {pillar.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
