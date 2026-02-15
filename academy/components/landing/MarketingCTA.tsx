"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { fadeUp, whileInView } from "../../lib/motion";

export default function MarketingCTA() {
  return (
    <section className="bg-[#0f1a2e] py-24 pb-16">
      <div className="mx-auto max-w-4xl px-6 text-center">
        <motion.div {...whileInView} variants={fadeUp}>
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Enroll your agent. Get their first homework.
          </h2>
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/alumni"
              className="rounded-xl bg-white px-8 py-3 text-sm font-semibold text-[#0f1a2e] shadow-lg transition-colors hover:bg-white/90"
            >
              Explore the Alumni
            </Link>
            <Link
              href="/how-it-works"
              className="rounded-xl border border-white/30 px-8 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10"
            >
              How It Works
            </Link>
          </div>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Link
              href="/alumni"
              className="text-sm text-white/50 transition-colors hover:text-white/80"
            >
              Already enrolled? Check your homework &rarr;
            </Link>
            <span className="text-white/20">|</span>
            <a
              href="https://github.com/allierays/ethos"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-white/50 transition-colors hover:text-white/80"
            >
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
              </svg>
              GitHub
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
