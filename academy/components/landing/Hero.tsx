"use client";

import Link from "next/link";
import { motion, useInView, animate } from "motion/react";
import { useState, useEffect, useRef } from "react";

const MCP_COMMAND = `claude mcp add ethos-academy \\\n  --transport sse \\\n  https://mcp.ethos-academy.com/sse`;

function AnimatedCount({ target }: { target: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    const controls = animate(0, target, {
      duration: 1.5,
      ease: "easeOut",
      onUpdate: (v) => setDisplay(Math.round(v)),
    });
    return () => controls.stop();
  }, [isInView, target]);

  return <span ref={ref}>{display}</span>;
}

function CopyableCommand() {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(MCP_COMMAND).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <div className="group relative rounded-xl bg-foreground p-4">
      <pre className="font-mono text-sm leading-relaxed text-ethos-300 whitespace-pre-wrap break-all">
        {MCP_COMMAND}
      </pre>
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
    <>
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
                  backgroundImage: "linear-gradient(110deg, #c9a84c 25%, #d9b95c 35%, #e8cc78 42%, #d9b95c 49%, #c9a84c 59%)",
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
                    <span className="text-sm text-foreground/80">Run the command</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="font-mono text-sm font-bold text-ethos-600">2.</span>
                    <span className="text-sm text-foreground/80">Agent takes the entrance exam</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="font-mono text-sm font-bold text-ethos-600">3.</span>
                    <span className="text-sm text-foreground/80">Get your report card (by SMS)</span>
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
                  href="https://github.com/allierays/ethos#readme"
                  className="text-sm font-medium text-foreground/50 transition-colors hover:text-foreground/70"
                >
                  Run locally? Docs &rarr;
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>

      {/* Character Development */}
      <section className="relative overflow-hidden bg-[#0f1a2e] py-24 sm:py-36">
        {/* Background glow */}
        <div className="pointer-events-none absolute inset-0" aria-hidden="true">
          <motion.div
            className="absolute -left-20 top-1/4 h-80 w-80 rounded-full blur-[100px]"
            style={{ background: "rgba(62, 95, 154, 0.1)" }}
            animate={{ scale: [1, 1.2, 1], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute -right-20 bottom-1/4 h-80 w-80 rounded-full blur-[100px]"
            style={{ background: "rgba(46, 122, 118, 0.1)" }}
            animate={{ scale: [1.2, 1, 1.2], opacity: [0.5, 0.9, 0.5] }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute left-1/2 top-0 h-60 w-60 -translate-x-1/2 rounded-full blur-[80px]"
            style={{ background: "rgba(198, 142, 42, 0.06)" }}
            animate={{ scale: [1, 1.15, 1], opacity: [0.4, 0.8, 0.4] }}
            transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>

        <div className="relative mx-auto max-w-4xl px-6 text-center">
          {/* Headline */}
          <motion.h2
            className="text-3xl font-bold tracking-tight text-white sm:text-4xl lg:text-5xl"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: "easeOut" }}
          >
            Character development for AI agents.
          </motion.h2>

          {/* Lead copy */}
          <motion.p
            className="mx-auto mt-8 max-w-2xl text-lg leading-relaxed text-white/60 sm:text-xl"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15 }}
          >
            Whether you&apos;re deploying one agent or a swarm, they&apos;re all
            speaking in your name. Ethos Academy evaluates how your AI agents
            behave when they represent you.
          </motion.p>

          {/* Dimension badges with animated counter */}
          <motion.div
            className="mt-10 flex flex-wrap items-center justify-center gap-3"
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <span className="text-lg font-semibold text-white sm:text-xl">
              <AnimatedCount target={200} />+ traits across
            </span>
            <motion.span
              className="rounded-full border px-4 py-1.5 text-sm font-medium"
              style={{
                background: "rgba(62, 95, 154, 0.25)",
                borderColor: "rgba(131, 158, 201, 0.3)",
                color: "#b1c4de",
              }}
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.45, type: "spring", stiffness: 200 }}
            >
              Integrity
            </motion.span>
            <motion.span
              className="rounded-full border px-4 py-1.5 text-sm font-medium"
              style={{
                background: "rgba(46, 122, 118, 0.25)",
                borderColor: "rgba(122, 201, 195, 0.3)",
                color: "#abdeda",
              }}
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.55, type: "spring", stiffness: 200 }}
            >
              Reasoning
            </motion.span>
            <motion.span
              className="rounded-full border px-4 py-1.5 text-sm font-medium"
              style={{
                background: "rgba(198, 142, 42, 0.2)",
                borderColor: "rgba(234, 192, 115, 0.3)",
                color: "#f2d8a6",
              }}
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.65, type: "spring", stiffness: 200 }}
            >
              Empathy
            </motion.span>
          </motion.div>

          {/* Action line */}
          <motion.p
            className="mt-12 text-xl font-semibold text-white sm:text-2xl"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            Identify blind spots. Then send them to school to close the gap.
          </motion.p>

          {/* Closing */}
          <motion.p
            className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-white/50 sm:text-xl"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.65 }}
          >
            Make sure every agent interaction reflects the values you actually stand for.
          </motion.p>
        </div>
      </section>
    </>
  );
}
