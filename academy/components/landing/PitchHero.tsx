"use client";

import { motion } from "motion/react";

export default function PitchHero() {
  return (
    <section className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-[#1a2538] px-6">
      {/* Background banner image */}
      <div
        className="absolute inset-0 bg-cover bg-no-repeat"
        style={{ backgroundImage: "url('/academy-people-banner.jpeg')", backgroundPosition: "center 40%" }}
        aria-hidden="true"
      />
      {/* Gradient overlay: dark center for text readability, fading to reveal image at edges */}
      <div
        className="absolute inset-0"
        style={{ background: "radial-gradient(ellipse at center, rgba(26,37,56,0.92) 0%, rgba(26,37,56,0.75) 50%, rgba(26,37,56,0.45) 100%)" }}
        aria-hidden="true"
      />

      <div className="relative flex flex-col items-center text-center">
        {/* Ethos Academy */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-5xl font-bold tracking-tight text-white sm:text-6xl lg:text-8xl"
        >
          <span
            className="bg-clip-text text-transparent animate-shimmer"
            style={{
              backgroundImage: "linear-gradient(110deg, #5b8abf 20%, #5cc9c0 35%, #7eddd6 45%, #5cc9c0 55%, #e0a53c 70%, #eac073 80%, #5b8abf 95%)",
              backgroundSize: "300% 100%",
            }}
          >
            Ethos Academy
          </span>
        </motion.h1>

        {/* Tagline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3, ease: "easeOut" }}
          className="mt-6 text-xl text-white/90 sm:text-2xl lg:text-3xl"
        >
          Where your AI agents learn integrity, logic, and empathy.
        </motion.p>

        {/* Stats line */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mt-10 flex items-center gap-4 text-sm text-white/60 sm:gap-6 sm:text-base"
        >
          <span>3 dimensions</span>
          <span className="h-3 w-px bg-white/30" />
          <span>12 traits</span>
          <span className="h-3 w-px bg-white/30" />
          <span>214 indicators</span>
          <span className="h-3 w-px bg-white/30" />
          <span>1 living graph</span>
        </motion.div>

        {/* Bottom context */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 1.1 }}
          className="mt-16 text-xs tracking-widest text-white/50 uppercase"
        >
          Built for the Claude Code Hackathon 2026
        </motion.p>
      </div>
    </section>
  );
}
