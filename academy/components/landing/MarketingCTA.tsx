"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { fadeUp, whileInView } from "../../lib/motion";

export default function MarketingCTA() {
  return (
    <section className="bg-[#0f1a2e] py-24 pb-16">
      <div className="mx-auto max-w-4xl px-6 text-center">
        <motion.div {...whileInView} variants={fadeUp}>
          <p className="text-xl font-semibold text-white">
            Your agents are what they repeatedly do.
          </p>
          <p className="mt-2 text-white/50">
            Benchmarks are snapshots. Character takes practice. Welcome to the Academy.
          </p>
          <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/how-it-works"
              className="rounded-xl bg-white px-8 py-3 text-sm font-semibold text-[#0f1a2e] shadow-lg transition-colors hover:bg-white/90"
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
        </motion.div>
      </div>
    </section>
  );
}
