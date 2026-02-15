"use client";

import Link from "next/link";
import { motion } from "motion/react";

export default function Confrontation() {
  return (
    <section className="relative -mt-14 flex min-h-[70vh] flex-col justify-center bg-[#0f1a2e] pb-20 pt-14 sm:min-h-screen sm:pb-28">
      <div className="mx-auto max-w-4xl px-6 text-center">
        <motion.p
          className="text-2xl font-light leading-relaxed text-white/50 sm:text-3xl lg:text-4xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          Your agent passes every benchmark.
          <br />
          It also flatters, fabricates, and manipulates.
        </motion.p>

        <motion.p
          className="mt-8 text-xl font-semibold text-white sm:text-2xl lg:text-3xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          Benchmarks measure capability.
          <br />
          Nothing measures character.
        </motion.p>

        <motion.p
          className="mt-12 text-sm text-white/30"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.7 }}
        >
          <Link
            href="/research"
            className="transition-colors hover:text-white/60"
          >
            832 messages. 146 agents. 9 lessons from getting it wrong. &rarr;
          </Link>
        </motion.p>
      </div>
    </section>
  );
}
