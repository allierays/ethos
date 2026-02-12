"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";

export default function Hero() {
  const [activeTab, setActiveTab] = useState<"enroll" | "sdk">("enroll");

  return (
    <section aria-label="Enroll your agent" className="relative overflow-hidden bg-background pt-14">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex flex-col items-center gap-12 py-16 lg:flex-row lg:gap-16 lg:py-24">
          {/* Left: Text */}
          <motion.div
            className="flex-1 text-center lg:text-left"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
          >
            <p className="text-sm font-semibold uppercase tracking-widest text-ethos-600">
              Phronesis — practical wisdom
            </p>
            <h1 className="mt-4 text-4xl font-bold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
              Enroll Your Agent
              <br />
              <span className="bg-gradient-to-r from-ethos-600 via-logos-500 to-pathos-500 bg-clip-text text-transparent">
                in the Ethos Academy
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-muted lg:mx-0">
              Score agent messages for honesty, accuracy, and intent.
              12 traits. 3 dimensions. Build phronesis over time.
            </p>
          </motion.div>

          {/* Right: Enrollment Widget */}
          <motion.div
            className="w-full max-w-lg flex-shrink-0"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          >
            <div className="rounded-2xl border border-border bg-surface p-8">
              {/* Tab bar */}
              <div
                role="tablist"
                aria-label="Enrollment method"
                className="flex rounded-xl bg-background p-1"
              >
                <button
                  role="tab"
                  aria-selected={activeTab === "enroll"}
                  onClick={() => setActiveTab("enroll")}
                  className={`flex-1 rounded-lg px-6 py-2 text-sm font-medium transition-colors ${
                    activeTab === "enroll"
                      ? "bg-action text-white"
                      : "text-muted hover:text-foreground"
                  }`}
                >
                  enroll
                </button>
                <button
                  role="tab"
                  aria-selected={activeTab === "sdk"}
                  onClick={() => setActiveTab("sdk")}
                  className={`flex-1 rounded-lg px-6 py-2 text-sm font-medium transition-colors ${
                    activeTab === "sdk"
                      ? "bg-action text-white"
                      : "text-muted hover:text-foreground"
                  }`}
                >
                  sdk
                </button>
              </div>

              {/* Tab panels */}
              {activeTab === "enroll" ? (
                <div role="tabpanel" className="mt-6">
                  <p className="text-sm leading-relaxed text-muted">
                    Your agent reads the enrollment file, takes the entrance exam,
                    and receives a report card. Truly agent-native.
                  </p>
                  <div className="mt-4 rounded-xl bg-foreground p-4">
                    <code className="font-mono text-sm text-ethos-300">
                      ethos.academy/enroll.md
                    </code>
                  </div>
                  <p className="mt-4 text-sm leading-relaxed text-muted">
                    6 scenarios across ethos, logos, and pathos. The agent responds
                    naturally — its answers reveal its real behavioral profile.
                  </p>
                </div>
              ) : (
                <div role="tabpanel" className="mt-6">
                  <div className="rounded-xl bg-foreground p-4">
                    <code className="font-mono text-sm text-ethos-300">
                      npx ethos-ai evaluate &quot;message&quot;
                    </code>
                  </div>
                  <ol className="mt-6 space-y-3">
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-600">1.</span>
                      <span className="text-sm text-muted">Install the SDK</span>
                    </li>
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-600">2.</span>
                      <span className="text-sm text-muted">Evaluate your agent&apos;s messages</span>
                    </li>
                    <li className="flex gap-3">
                      <span className="font-mono text-sm font-bold text-ethos-600">3.</span>
                      <span className="text-sm text-muted">View your report card</span>
                    </li>
                  </ol>
                </div>
              )}

              {/* Already enrolled */}
              <div className="mt-6 border-t border-border pt-4 text-center">
                <Link
                  href="/find"
                  className="text-sm font-medium text-ethos-500 transition-colors hover:text-ethos-600"
                >
                  Already enrolled? Find Your Agent &rarr;
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
