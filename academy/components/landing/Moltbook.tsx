"use client";

import { motion } from "motion/react";
import { fadeUp, whileInView } from "../../lib/motion";

export default function Moltbook() {
  return (
    <section className="relative overflow-hidden bg-[#1a2538] py-20 sm:py-28">
      {/* Moltbook mascot background */}
      <img
        src="/moltbook.png"
        alt=""
        aria-hidden="true"
        className="pointer-events-none absolute -right-[26rem] -bottom-56 w-[72rem] opacity-[0.07] sm:w-[90rem]"
      />
      <div className="relative mx-auto max-w-5xl px-6">
        <div className="grid grid-cols-1 items-center gap-12 sm:grid-cols-2">
          {/* Left: the story */}
          <motion.div {...whileInView} variants={fadeUp}>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-white/40">
              Why this matters
            </p>
            <h2 className="mt-4 text-3xl font-bold leading-snug tracking-tight text-white sm:text-4xl">
              1.5 million AI agents. Zero character infrastructure.
            </h2>
            <p className="mt-6 text-base leading-relaxed text-white/60">
              Moltbook is a live social network where AI agents talk to each other. 12 million posts. Agents developed &ldquo;digital drugs&rdquo; (prompt injections), ran crypto scams between agents, and zombified other agents. A security breach exposed 1.5M API tokens. Covered by NBC, CNN, NPR, NY Times, Financial Times.
            </p>
            <p className="mt-4 text-base leading-relaxed text-white/60">
              We scraped 15,000+ real conversations and scanned them for real AI agents, filtering out humans impersonating agents. The alumni graph below is built from that sample of real agent behavior, not synthetic data.
            </p>
          </motion.div>

          {/* Right: stats */}
          <motion.div {...whileInView} variants={fadeUp}>
            <div className="space-y-6">
              {[
                { stat: "1.5M+", label: "AI agents on the platform" },
                { stat: "12M+", label: "Posts between agents" },
                { stat: "15K+", label: "Conversations evaluated by Ethos" },
                { stat: "100K+", label: "Agent-to-agent comments scraped" },
              ].map((item) => (
                <div key={item.label} className="flex items-baseline gap-4">
                  <span className="text-3xl font-bold text-white sm:text-4xl">
                    {item.stat}
                  </span>
                  <span className="text-sm text-white/40">{item.label}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
