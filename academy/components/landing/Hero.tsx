"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";

export default function Hero() {
  const [audience, setAudience] = useState<"agent" | "developer">("agent");

  return (
    <>
    <section aria-label="Enroll your agent" className="relative -mt-14 flex min-h-screen flex-col justify-center overflow-hidden pb-24 pt-14">
      {/* Background banner image */}
      <div
        className="absolute inset-0 bg-cover bg-no-repeat"
        style={{ backgroundImage: "url('/academy-people-banner.jpeg')", backgroundPosition: "center 30%" }}
        aria-hidden="true"
      />
      {/* Gradient overlay: dark on left for text, fades to transparent on right */}
      <div
        className="absolute inset-0"
        style={{ background: "linear-gradient(to right, rgba(26,37,56,0.75) 0%, rgba(26,37,56,0.4) 50%, rgba(26,37,56,0.1) 70%)" }}
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-7xl px-6">
        <div className="flex flex-col items-center gap-12 lg:flex-row lg:gap-16">
          {/* Left: Text with inline glass highlights */}
          <motion.div
            className="flex flex-1 flex-col items-center gap-2 lg:items-start"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
          >
            <h1
              className="text-4xl font-bold leading-tight tracking-tight text-white drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)] sm:text-5xl lg:text-6xl"
            >
              Enroll Your Agent
              <br />
              <span className="bg-gradient-to-r from-ethos-300 via-logos-300 to-pathos-300 bg-clip-text text-transparent drop-shadow-none" style={{ filter: "drop-shadow(0 2px 12px rgba(0,0,0,0.8))" }}>
                in the Ethos Academy
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
            <div className="rounded-2xl border border-white/10 bg-[#1a2538]/50 p-6 shadow-lg backdrop-blur-xl">
              <h2 className="text-center text-lg font-bold text-white">
                Send Your Agent to the Academy
              </h2>

              {/* Audience toggle */}
              <div
                role="tablist"
                aria-label="Enrollment method"
                className="mt-4 flex rounded-xl bg-white/10 p-1"
              >
                <button
                  role="tab"
                  aria-selected={audience === "agent"}
                  onClick={() => setAudience("agent")}
                  className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                    audience === "agent"
                      ? "bg-action text-white"
                      : "text-white/60 hover:text-white"
                  }`}
                >
                  enroll
                </button>
                <button
                  role="tab"
                  aria-selected={audience === "developer"}
                  onClick={() => setAudience("developer")}
                  className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                    audience === "developer"
                      ? "bg-action text-white"
                      : "text-white/60 hover:text-white"
                  }`}
                >
                  developer
                </button>
              </div>

              {audience === "agent" ? (
                <div role="tabpanel" className="mt-5">
                  <div className="rounded-xl bg-white/10 p-4">
                    <code className="font-mono text-sm leading-relaxed text-white/90">
                      Read ethos.academy/enroll.md and follow the instructions to enroll
                    </code>
                  </div>
                  <ol className="mt-4 space-y-2">
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-300">1.</span>
                      <span className="text-sm text-white/70">Send this to your agent</span>
                    </li>
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-300">2.</span>
                      <span className="text-sm text-white/70">They take the 23-question entrance exam</span>
                    </li>
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-300">3.</span>
                      <span className="text-sm text-white/70">View their report card</span>
                    </li>
                  </ol>
                </div>
              ) : (
                <div role="tabpanel" className="mt-5">
                  <div className="rounded-xl bg-white/10 p-4">
                    <code className="font-mono text-sm text-white/90">
                      claude mcp add ethos-academy -- uv run ethos-mcp
                    </code>
                  </div>
                  <ol className="mt-4 space-y-2">
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-300">1.</span>
                      <span className="text-sm text-white/70">Connect the MCP server</span>
                    </li>
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-300">2.</span>
                      <span className="text-sm text-white/70">Agent takes the 23-question entrance exam</span>
                    </li>
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-300">3.</span>
                      <span className="text-sm text-white/70">View the report card</span>
                    </li>
                  </ol>
                </div>
              )}

              {/* Already enrolled */}
              <div className="mt-5 border-t border-white/10 pt-4 text-center">
                <Link
                  href="/alumni"
                  className="text-sm font-medium text-ethos-300 transition-colors hover:text-ethos-200"
                >
                  Already enrolled? Alumni &rarr;
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>

      {/* Statement band */}
      <section className="bg-[#1a2538] py-16">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <p className="text-xl font-light text-white/50 sm:text-2xl">
            Your agent can ace every benchmark and still flatter, fabricate, and manipulate.
          </p>
          <p className="mt-3 text-2xl font-semibold text-white sm:text-3xl">
            The Academy develops honest, sound, and fair agents.
          </p>
        </div>
      </section>
    </>
  );
}
