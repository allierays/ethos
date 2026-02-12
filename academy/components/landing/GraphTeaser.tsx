"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { staggerContainer, slideInLeft, slideInRight, whileInView } from "../../lib/motion";

export default function GraphTeaser() {
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
              alumni comparison, and balance analysis.
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
