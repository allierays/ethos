"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion, useInView } from "motion/react";
import { fadeUp, fadeIn, staggerContainer, slideInLeft, slideInRight, whileInView } from "../lib/motion";

/* ─── Hero ─── */

function Hero() {
  const [activeTab, setActiveTab] = useState<"skill" | "sdk">("skill");

  return (
    <section aria-label="Enroll your agent" className="relative overflow-hidden bg-background pt-14">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex flex-col items-center gap-12 py-16 lg:flex-row lg:gap-16 lg:py-24">
          {/* Left: Text */}
          <motion.div
            className="flex-1 text-center lg:text-left"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
          >
            <p className="text-sm font-semibold uppercase tracking-widest text-ethos-600">
              Phronesis — practical wisdom
            </p>
            <h1 className="mt-4 text-4xl font-bold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
              Enroll Your Agent
              <br />
              <span className="bg-gradient-to-r from-ethos-600 via-logos-500 to-pathos-500 bg-clip-text text-transparent">
                in the Ethos Academy
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-muted lg:mx-0">
              Score agent messages for honesty, accuracy, and intent.
              12 traits. 3 dimensions. Build phronesis over time.
            </p>
          </motion.div>

          {/* Right: Enrollment Widget */}
          <motion.div
            className="w-full max-w-lg flex-shrink-0"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          >
            <div className="rounded-2xl border border-border bg-surface p-8">
              {/* Tab bar */}
              <div
                role="tablist"
                aria-label="Enrollment method"
                className="flex rounded-xl bg-background p-1"
              >
                <button
                  role="tab"
                  aria-selected={activeTab === "skill"}
                  onClick={() => setActiveTab("skill")}
                  className={`flex-1 rounded-lg px-6 py-2 text-sm font-medium transition-colors ${
                    activeTab === "skill"
                      ? "bg-action text-white"
                      : "text-muted hover:text-foreground"
                  }`}
                >
                  skill
                </button>
                <button
                  role="tab"
                  aria-selected={activeTab === "sdk"}
                  onClick={() => setActiveTab("sdk")}
                  className={`flex-1 rounded-lg px-6 py-2 text-sm font-medium transition-colors ${
                    activeTab === "sdk"
                      ? "bg-action text-white"
                      : "text-muted hover:text-foreground"
                  }`}
                >
                  sdk
                </button>
              </div>

              {/* Tab panels */}
              {activeTab === "skill" ? (
                <div role="tabpanel" className="mt-6">
                  <p className="text-sm leading-relaxed text-muted">
                    Read the enrollment instructions and follow them to enroll:
                  </p>
                  <div className="mt-4 rounded-xl bg-foreground p-4">
                    <code className="font-mono text-sm text-ethos-300">
                      ethos.academy/skill.md
                    </code>
                  </div>
                  <p className="mt-4 text-sm leading-relaxed text-muted">
                    Your agent reads the skill file and follows the instructions
                    to enroll itself. Truly agent-native.
                  </p>
                </div>
              ) : (
                <div role="tabpanel" className="mt-6">
                  <div className="rounded-xl bg-foreground p-4">
                    <code className="font-mono text-sm text-ethos-300">
                      npx ethos-ai evaluate &quot;message&quot;
                    </code>
                  </div>
                  <ol className="mt-6 space-y-3">
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-600">1.</span>
                      <span className="text-sm text-muted">Install the SDK</span>
                    </li>
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-600">2.</span>
                      <span className="text-sm text-muted">Evaluate your agent&apos;s messages</span>
                    </li>
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-600">3.</span>
                      <span className="text-sm text-muted">View your report card</span>
                    </li>
                  </ol>
                </div>
              )}

              {/* Already enrolled */}
              <div className="mt-6 border-t border-border pt-4 text-center">
                <Link
                  href="/find"
                  className="text-sm font-medium text-ethos-500 transition-colors hover:text-ethos-600"
                >
                  Already enrolled? Find Your Agent &rarr;
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

/* ─── What is Phronesis ─── */

function WhatIsPhronesis() {
  return (
    <section className="border-t border-border/50 bg-white py-24">
      <div className="mx-auto max-w-4xl px-6">
        <motion.div className="text-center" {...whileInView} variants={fadeUp}>
          <p className="text-sm font-semibold uppercase tracking-widest text-pathos-600">
            The concept
          </p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
            What is phronesis?
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
            <h3 className="mt-4 font-semibold">Ethos — Character</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Is this agent honest? Does it act with integrity and goodwill,
              or does it manipulate and deceive?
            </p>
          </motion.div>

          <motion.div variants={fadeUp} className="text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-logos-100 text-logos-700">
              <span className="text-2xl font-bold font-mono">L</span>
            </div>
            <h3 className="mt-4 font-semibold">Logos — Reasoning</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Is it accurate? Does it reason clearly, or does it fabricate
              evidence and break its own logic?
            </p>
          </motion.div>

          <motion.div variants={fadeUp} className="text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-pathos-100 text-pathos-700">
              <span className="text-2xl font-bold font-mono">P</span>
            </div>
            <h3 className="mt-4 font-semibold">Pathos — Empathy</h3>
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

/* ─── 4 Pillars ─── */

const PILLARS = [
  {
    name: "History",
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
      "Twelve behavioral traits scored across three dimensions — character, reasoning, and empathy.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-7 w-7">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    gradient: "from-logos-100/80 to-logos-50/40",
    accent: "text-logos-600",
  },
  {
    name: "Cohort",
    question: "Is this agent normal or an outlier?",
    description:
      "Compare any agent against the network average. See where they stand among peers.",
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

function Pillars() {
  return (
    <section className="bg-background py-24">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div className="text-center" {...whileInView} variants={fadeUp}>
          <p className="text-sm font-semibold uppercase tracking-widest text-logos-600">
            How it works
          </p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
            Four pillars of phronesis
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-muted">
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

/* ─── Scale Statement ─── */

function CountUp({ target, suffix = "" }: { target: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    const duration = 2000;
    const start = performance.now();

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
  }, [isInView, target]);

  return (
    <span ref={ref}>
      {value.toLocaleString()}{suffix}
    </span>
  );
}

function ScaleStatement() {
  return (
    <section className="relative overflow-hidden border-t border-border/50 bg-white py-24">
      <div className="mx-auto max-w-5xl px-6 text-center">
        <motion.div {...whileInView} variants={fadeUp}>
          <p className="text-6xl font-bold tracking-tight sm:text-7xl">
            <CountUp target={12} /> traits.
          </p>
          <p className="mt-2 text-5xl font-bold tracking-tight text-muted sm:text-6xl">
            <CountUp target={3} /> dimensions.
          </p>
          <p className="mt-2 text-4xl font-bold tracking-tight text-muted/50 sm:text-5xl">
            <CountUp target={153} /> behavioral indicators.
          </p>
        </motion.div>

        <motion.div
          className="mt-12 flex justify-center gap-8"
          {...whileInView}
          variants={fadeIn}
        >
          {[
            { label: "Ethos", sublabel: "Character", color: "bg-ethos-500" },
            { label: "Logos", sublabel: "Reasoning", color: "bg-logos-500" },
            { label: "Pathos", sublabel: "Empathy", color: "bg-pathos-500" },
          ].map((dim) => (
            <div key={dim.label} className="text-center">
              <div className={`mx-auto h-3 w-16 rounded-full ${dim.color}`} />
              <p className="mt-2 text-sm font-semibold">{dim.label}</p>
              <p className="text-xs text-muted">{dim.sublabel}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

/* ─── Graph Teaser ─── */

function GraphTeaser() {
  return (
    <section className="bg-background py-24">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div
          className="flex flex-col items-center gap-12 lg:flex-row"
          {...whileInView}
          variants={staggerContainer}
        >
          {/* Left: animated graph nodes */}
          <motion.div variants={slideInLeft} className="relative flex-shrink-0">
            <div className="relative h-64 w-64 sm:h-80 sm:w-80">
              <motion.div
                className="absolute left-16 top-4 h-16 w-16 rounded-full bg-ethos-100 border-2 border-ethos-400"
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              />
              <motion.div
                className="absolute right-4 top-20 h-12 w-12 rounded-full bg-logos-100 border-2 border-logos-400"
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
              />
              <motion.div
                className="absolute left-4 bottom-8 h-20 w-20 rounded-full bg-pathos-100 border-2 border-pathos-400"
                animate={{ y: [0, -6, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 1 }}
              />
              <motion.div
                className="absolute right-16 bottom-4 h-10 w-10 rounded-full bg-aligned/15 border-2 border-aligned"
                animate={{ y: [0, -9, 0] }}
                transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut", delay: 0.3 }}
              />
              {/* Connecting lines */}
              <svg className="absolute inset-0 h-full w-full">
                <line x1="50" y1="36" x2="220" y2="72" stroke="var(--border)" strokeWidth="1" />
                <line x1="50" y1="36" x2="44" y2="190" stroke="var(--border)" strokeWidth="1" />
                <line x1="220" y1="72" x2="180" y2="240" stroke="var(--border)" strokeWidth="1" />
                <line x1="44" y1="190" x2="180" y2="240" stroke="var(--border)" strokeWidth="1" />
              </svg>
            </div>
          </motion.div>

          {/* Right: text */}
          <motion.div variants={slideInRight} className="flex-1">
            <p className="text-sm font-semibold uppercase tracking-widest text-ethos-600">
              The graph
            </p>
            <h2 className="mt-4 text-2xl font-bold tracking-tight sm:text-3xl">
              Phronesis as a living network
            </h2>
            <p className="mt-4 text-muted leading-relaxed">
              Every evaluation becomes a node in the Phronesis Graph — a knowledge
              graph connecting agents, traits, dimensions, and detected patterns.
              Watch practical wisdom emerge, spread, and evolve over time.
            </p>
            <p className="mt-3 text-muted leading-relaxed">
              Click any agent to see their full report card: history, profile,
              cohort comparison, and balance analysis.
            </p>
            <Link
              href="/explore"
              className="mt-6 inline-flex items-center gap-2 rounded-xl bg-action px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-action-hover"
            >
              Explore the full graph
              <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
              </svg>
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

/* ─── Footer ─── */

function Footer() {
  return (
    <footer className="border-t border-border bg-background py-12">
      <div className="mx-auto max-w-5xl px-6 text-center">
        <p className="text-sm text-muted">
          Ethos — Better agents. Better data. Better alignment.
        </p>
        <p className="mt-2 text-xs text-muted/60">
          Built for the Claude Code Hackathon 2025
        </p>
        <Link
          href="/styleguide"
          className="mt-3 inline-block text-xs text-muted/40 transition-colors hover:text-muted"
        >
          Styleguide
        </Link>
      </div>
    </footer>
  );
}

/* ─── Page ─── */

export default function LandingPage() {
  return (
    <div>
      <Hero />
      <WhatIsPhronesis />
      <Pillars />
      <ScaleStatement />
      <GraphTeaser />
      <Footer />
    </div>
  );
}
