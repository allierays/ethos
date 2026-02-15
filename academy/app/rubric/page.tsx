"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { fadeUp, fadeIn } from "../../lib/motion";
import { totalIndicators, DIMENSIONS, DIM_COLORS } from "../../components/rubric/rubricData";
import RubricExplorer from "../../components/rubric/RubricExplorer";

/* ─── SVG Components ─── */

function PillarIcon({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 120"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <rect x="8" y="108" width="48" height="6" rx="1" />
      <rect x="12" y="103" width="40" height="5" rx="1" />
      <line x1="16" y1="103" x2="14" y2="32" />
      <line x1="48" y1="103" x2="50" y2="32" />
      <line x1="24" y1="103" x2="23" y2="32" strokeOpacity="0.4" />
      <line x1="32" y1="103" x2="32" y2="32" strokeOpacity="0.4" />
      <line x1="40" y1="103" x2="41" y2="32" strokeOpacity="0.4" />
      <path d="M14 32 Q14 26 8 24 Q2 22 4 16 Q6 12 12 12" />
      <path d="M50 32 Q50 26 56 24 Q62 22 60 16 Q58 12 52 12" />
      <line x1="12" y1="12" x2="52" y2="12" />
      <rect x="6" y="6" width="52" height="6" rx="1" />
    </svg>
  );
}

/* ─── Page ─── */

export default function RubricPage() {
  const count = totalIndicators();

  return (
    <main>
      {/* 1. Dark Navy Hero */}
      <section className="bg-[#1a2538] py-24 sm:py-32">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="mx-auto mb-8"
          >
            <PillarIcon className="mx-auto h-20 w-20 text-white/20" />
          </motion.div>

          <motion.p
            className="text-sm font-semibold uppercase tracking-widest text-ethos-400"
            initial="hidden"
            animate="visible"
            variants={fadeIn}
          >
            Ethos Academy
          </motion.p>

          <motion.h1
            className="mt-4 text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-white"
            initial="hidden"
            animate="visible"
            variants={fadeUp}
          >
            The Rubric
          </motion.h1>

          <motion.p
            className="mx-auto mt-4 max-w-2xl text-lg text-white/60"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            12 traits. 3 dimensions. {count} behavioral indicators.
          </motion.p>

          <motion.p
            className="mx-auto mt-2 max-w-xl text-sm text-white/40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            Pick a dimension, explore the traits, drill into the details.
          </motion.p>

          <motion.div
            className="mt-8 flex flex-wrap items-center justify-center gap-4"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            {DIMENSIONS.map((dim) => (
              <span
                key={dim.key}
                className="flex items-center gap-2 rounded-full bg-white/10 px-2.5 py-1.5 text-xs sm:px-4 sm:py-2 sm:text-sm font-medium text-white/80"
              >
                <span
                  className={`h-2.5 w-2.5 rounded-full ${DIM_COLORS[dim.key].dot}`}
                />
                {dim.label}
              </span>
            ))}
          </motion.div>
        </div>
      </section>

      {/* 2. Tabbed Explorer */}
      <section className="bg-white py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-6">
          <RubricExplorer />
        </div>
      </section>

      {/* 3. Dark Navy CTA Footer */}
      <section className="bg-[#1a2538] py-20">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <p className="text-xl font-semibold text-white">
            Your agents are what they repeatedly do.
          </p>
          <p className="mt-2 text-white/50">
            Benchmarks are snapshots. Character takes practice. Welcome to the Academy.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/how-it-works"
              className="rounded-xl bg-white px-8 py-3 text-sm font-semibold text-[#1a2538] shadow-lg transition-colors hover:bg-white/90"
            >
              Enroll Your Agent
            </Link>
            <Link
              href="/alumni"
              className="rounded-xl border border-white/30 px-8 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10"
            >
              Meet the Alumni
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
