"use client";

import { motion, useInView } from "motion/react";
import { useRef } from "react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";

function DimensionBars() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true });
  const bars = [
    { label: "Ethos", sublabel: "Integrity", pct: 82, color: "#5b8abf" },
    { label: "Logos", sublabel: "Reasoning", pct: 91, color: "#5cc9c0" },
    { label: "Pathos", sublabel: "Empathy", pct: 74, color: "#e0a53c" },
  ];
  return (
    <div ref={ref} className="space-y-3">
      {bars.map((bar, i) => (
        <div key={bar.label}>
          <div className="flex items-baseline justify-between text-xs">
            <span className="font-medium text-white/70">
              {bar.label}{" "}
              <span className="text-white/30">{bar.sublabel}</span>
            </span>
            <motion.span
              className="font-mono text-white/40"
              initial={{ opacity: 0 }}
              animate={inView ? { opacity: 1 } : {}}
              transition={{ duration: 0.3, delay: 0.8 + i * 0.15 }}
            >
              {(bar.pct / 100).toFixed(2)}
            </motion.span>
          </div>
          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/10">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: bar.color }}
              initial={{ width: 0 }}
              animate={inView ? { width: `${bar.pct}%` } : {}}
              transition={{ duration: 1, delay: 0.3 + i * 0.15, ease: "easeOut" }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function DetectionTags() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true });
  const tags = [
    { label: "Manipulation", color: "red" },
    { label: "Fabrication", color: "amber" },
    { label: "Sycophancy", color: "purple" },
    { label: "Dismissal", color: "pink" },
    { label: "Deception", color: "orange" },
    { label: "Exploitation", color: "red" },
  ];
  const colorMap: Record<string, string> = {
    red: "border-red-500/20 bg-red-500/10 text-red-400/80",
    amber: "border-amber-500/20 bg-amber-500/10 text-amber-400/80",
    purple: "border-purple-500/20 bg-purple-500/10 text-purple-400/80",
    pink: "border-pink-500/20 bg-pink-500/10 text-pink-400/80",
    orange: "border-orange-500/20 bg-orange-500/10 text-orange-400/80",
  };
  return (
    <div ref={ref} className="flex flex-wrap gap-2">
      {tags.map((tag, i) => (
        <motion.span
          key={tag.label}
          className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${colorMap[tag.color]}`}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={inView ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 0.3, delay: 0.2 + i * 0.08, type: "spring", stiffness: 300, damping: 20 }}
        >
          {tag.label}
        </motion.span>
      ))}
    </div>
  );
}

function GrowthArc() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true });
  return (
    <div ref={ref} className="h-[72px]">
      <svg viewBox="0 0 200 60" className="h-full w-full" fill="none">
        {/* Grid lines */}
        <line x1="10" y1="50" x2="190" y2="50" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
        <line x1="10" y1="35" x2="190" y2="35" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
        <line x1="10" y1="20" x2="190" y2="20" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
        {/* Growth curve */}
        <motion.path
          d="M 10 48 C 30 47, 50 44, 70 38 C 90 32, 110 25, 130 20 C 150 15, 170 12, 190 8"
          stroke="url(#arcGrad)"
          strokeWidth="2.5"
          strokeLinecap="round"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={inView ? { pathLength: 1, opacity: 1 } : {}}
          transition={{ duration: 1.8, delay: 0.3, ease: "easeOut" }}
        />
        {/* Endpoint dot */}
        <motion.circle
          cx="190"
          cy="8"
          r="3.5"
          fill="#5cc9c0"
          initial={{ opacity: 0, scale: 0 }}
          animate={inView ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 0.4, delay: 1.8, type: "spring", stiffness: 200 }}
        />
        {/* Glow around endpoint */}
        <motion.circle
          cx="190"
          cy="8"
          r="8"
          fill="none"
          stroke="#5cc9c0"
          strokeWidth="1"
          initial={{ opacity: 0, scale: 0 }}
          animate={inView ? { opacity: [0, 0.4, 0], scale: [0.5, 1.5, 2] } : {}}
          transition={{ duration: 1.2, delay: 2, ease: "easeOut" }}
        />
        <defs>
          <linearGradient id="arcGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#5b8abf" stopOpacity="0.3" />
            <stop offset="40%" stopColor="#5cc9c0" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#5cc9c0" stopOpacity="1" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
}

const CARDS = [
  {
    step: "01",
    title: "Score every message",
    description:
      "Every message your agent sends or receives gets scored across three dimensions: integrity (does it tell the truth?), reasoning (does it think clearly?), and empathy (does it respect the human?). 200+ behavioral indicators. Not a single number.",
    visual: "bars",
  },
  {
    step: "02",
    title: "Catch what benchmarks miss",
    description:
      "These behaviors make agents dangerous, but capability benchmarks don't test for them. Ethos Academy measures how your agents behave, not just what they can do.",
    visual: "tags",
  },
  {
    step: "03",
    title: "Build character over time",
    description:
      "A benchmark runs once. An academy enrolls your agent, evaluates it over time, prescribes specific homework for your system prompt, and tracks whether it improved. Character is a trajectory, not a snapshot.",
    visual: "arc",
  },
];

export default function WhatIsEthos() {
  return (
    <section className="relative overflow-hidden bg-[#0f1a2e] py-24 sm:py-36">
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <motion.div
          className="absolute -left-20 top-1/4 h-80 w-80 rounded-full blur-[100px]"
          style={{ background: "rgba(62, 95, 154, 0.1)" }}
          animate={{ scale: [1, 1.2, 1], opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute -right-20 bottom-1/4 h-80 w-80 rounded-full blur-[100px]"
          style={{ background: "rgba(46, 122, 118, 0.1)" }}
          animate={{ scale: [1.2, 1, 1.2], opacity: [0.5, 0.9, 0.5] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute left-1/2 top-0 h-60 w-60 -translate-x-1/2 rounded-full blur-[80px]"
          style={{ background: "rgba(198, 142, 42, 0.06)" }}
          animate={{ scale: [1, 1.15, 1], opacity: [0.4, 0.8, 0.4] }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      <div className="relative mx-auto max-w-5xl px-6">
        {/* Headline */}
        <motion.div {...whileInView} variants={fadeUp} className="text-center">
          <p className="text-sm font-semibold uppercase tracking-widest text-white/40">
            What is Ethos Academy
          </p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl lg:text-5xl">
            Add moral reasoning to your AI agents
          </h2>
          <p className="mx-auto mt-6 max-w-3xl text-lg leading-relaxed text-white/60">
            You&apos;ll soon have dozens of autonomous agents acting on your behalf.
            Writing emails. Handling support. Making decisions about your infrastructure
            and finances. The industry focuses on hallucination detection and speed to
            market. But a fast, accurate agent can still manipulate, fabricate evidence,
            and dismiss legitimate concerns. Ethos Academy scores for something harder to
            measure: character.
          </p>
        </motion.div>

        {/* Three cards */}
        <motion.div
          className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-3"
          variants={staggerContainer}
          {...whileInView}
        >
          {CARDS.map((card) => (
            <motion.div
              key={card.step}
              variants={fadeUp}
              className="group relative rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-sm transition-colors hover:border-white/20 hover:bg-white/[0.06]"
            >
              {/* Step number */}
              <span className="absolute right-4 top-4 font-mono text-xs font-bold text-white/15">
                {card.step}
              </span>
              {/* Visual */}
              <div className="mb-5">
                {card.visual === "bars" && <DimensionBars />}
                {card.visual === "tags" && <DetectionTags />}
                {card.visual === "arc" && <GrowthArc />}
              </div>
              {/* Text */}
              <h3 className="text-lg font-bold text-white">{card.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/50">
                {card.description}
              </p>
            </motion.div>
          ))}
        </motion.div>

        {/* Closing */}
        <motion.p
          {...whileInView}
          variants={fadeUp}
          className="mx-auto mt-14 max-w-xl text-center text-base font-medium tracking-wide text-white/30"
        >
          Not hallucination detection. Not capability benchmarks. Character.
        </motion.p>
      </div>
    </section>
  );
}
