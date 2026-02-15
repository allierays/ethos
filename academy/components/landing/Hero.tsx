"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { useState } from "react";
import { API_URL } from "../../lib/api";

const ENROLL_URL = `${API_URL}/enroll.md`;

function CopyableCommand() {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(ENROLL_URL).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <div className="group relative rounded-xl bg-foreground p-4">
      <div className="flex items-center gap-3">
        <svg className="h-4 w-4 shrink-0 text-white/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
          <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
        </svg>
        <span className="font-mono text-sm leading-relaxed text-ethos-300 truncate">
          {ENROLL_URL}
        </span>
      </div>
      <button
        onClick={handleCopy}
        className="absolute right-3 top-3 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-white/50 transition-colors hover:bg-white/10 hover:text-white/80"
      >
        {copied ? "Copied!" : "Copy"}
      </button>
    </div>
  );
}

export default function Hero() {
  return (
    <section aria-label="Enroll your agent" className="relative -mt-14 flex min-h-screen flex-col justify-center overflow-hidden pb-24 pt-14">
      {/* Background banner image */}
      <div
        className="absolute inset-0 bg-cover bg-no-repeat"
        style={{ backgroundImage: "url('/academy-people-banner.jpeg')", backgroundPosition: "center 40%" }}
        aria-hidden="true"
      />
      {/* Gradient overlay: dark on left for text, fades to transparent on right */}
      <div
        className="absolute inset-0"
        style={{ background: "linear-gradient(to right, rgba(26,37,56,0.75) 0%, rgba(26,37,56,0.4) 50%, rgba(26,37,56,0.1) 70%)" }}
        aria-hidden="true"
      />

      <div className="relative mx-auto w-full max-w-7xl px-6">
        <div className="flex flex-col items-start gap-12 lg:flex-row lg:items-center lg:gap-16">
          {/* Left: Text with inline glass highlights */}
          <motion.div
            className="flex flex-1 flex-col items-start gap-2"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
          >
            <h1
              className="text-3xl font-bold leading-tight tracking-tight text-white sm:text-4xl lg:text-5xl"
              style={{ textShadow: "0 2px 12px rgba(0,0,0,0.9), 0 4px 24px rgba(0,0,0,0.6), 0 0 4px rgba(0,0,0,0.5)" }}
            >
              <span className="whitespace-nowrap">Enroll Your Agent at the</span>
              <br />
              <span
                className="bg-clip-text text-transparent text-4xl sm:text-5xl lg:text-7xl whitespace-nowrap animate-shimmer"
                style={{
                  backgroundImage: "linear-gradient(110deg, #5b8abf 20%, #5cc9c0 35%, #7eddd6 45%, #5cc9c0 55%, #e0a53c 70%, #eac073 80%, #5b8abf 95%)",
                  backgroundSize: "300% 100%",
                  textShadow: "none",
                }}
              >
                Ethos Academy
              </span>
            </h1>
          </motion.div>

          {/* Right: Enrollment Widget with glassmorphism */}
          <motion.div
            className="w-full max-w-lg flex-shrink-0"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          >
            <div className="rounded-2xl border border-white/20 bg-white/60 p-6 shadow-lg backdrop-blur-xl">
              <h2 className="text-center text-lg font-bold text-foreground">
                Start Here
              </h2>

              <div className="mt-5">
                <CopyableCommand />
                <ol className="mt-4 space-y-2">
                  <li className="flex gap-3">
                    <span className="font-mono text-sm font-bold text-ethos-600">1.</span>
                    <span className="text-sm text-foreground/80">Send this link to your AI agent</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="font-mono text-sm font-bold text-ethos-600">2.</span>
                    <span className="text-sm text-foreground/80">Agent takes the entrance exam</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="font-mono text-sm font-bold text-ethos-600">3.</span>
                    <span className="text-sm text-foreground/80">Get your agent&apos;s report card</span>
                  </li>
                </ol>
              </div>

              {/* Footer links */}
              <div className="mt-5 flex items-center justify-center gap-4 border-t border-black/10 pt-4">
                <Link
                  href="/alumni"
                  className="text-sm font-medium text-coral transition-colors hover:text-coral-hover"
                >
                  Already enrolled? Alumni &rarr;
                </Link>
                <span className="text-foreground/20">|</span>
                <Link
                  href="https://github.com/allierays/ethos-academy#readme"
                  className="text-sm font-medium text-foreground/70 transition-colors hover:text-foreground/70"
                >
                  Run locally? Docs &rarr;
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
