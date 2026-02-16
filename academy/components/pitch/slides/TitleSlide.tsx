"use client";

import { motion } from "motion/react";

export default function TitleSlide() {
  return (
    <div className="relative flex h-screen w-screen items-center justify-center overflow-hidden">
      {/* Background image */}
      <div
        className="absolute inset-0 bg-cover bg-no-repeat"
        style={{
          backgroundImage: "url('/academy-people-banner.jpeg')",
          backgroundPosition: "center 40%",
        }}
      />
      {/* Dark gradient overlay */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(to right, rgba(26,37,56,0.8) 0%, rgba(26,37,56,0.5) 50%, rgba(26,37,56,0.2) 70%)",
        }}
      />

      <div className="relative z-10 flex flex-col items-start gap-6 px-16">
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="text-6xl font-bold leading-tight tracking-tight text-white lg:text-8xl"
          style={{
            textShadow:
              "0 2px 12px rgba(0,0,0,0.9), 0 4px 24px rgba(0,0,0,0.6)",
          }}
        >
          <span
            className="animate-shimmer bg-clip-text text-transparent"
            style={{
              backgroundImage:
                "linear-gradient(110deg, #5b8abf 20%, #5cc9c0 35%, #7eddd6 45%, #5cc9c0 55%, #e0a53c 70%, #eac073 80%, #5b8abf 95%)",
              backgroundSize: "300% 100%",
            }}
          >
            Ethos Academy
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
          className="max-w-xl text-xl text-white/80 lg:text-2xl"
          style={{
            textShadow: "0 1px 8px rgba(0,0,0,0.7)",
          }}
        >
          Where your AI agents learn integrity, logic, and empathy.
        </motion.p>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="font-mono text-sm text-white/40"
        >
          Character takes practice.
        </motion.p>
      </div>
    </div>
  );
}
