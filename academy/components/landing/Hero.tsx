"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { useState } from "react";
import { API_URL } from "../../lib/api";

const ENROLL_URL = `${API_URL}/enroll.md`;
const MCP_URL = "https://mcp.ethos-academy.com/mcp";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <button
      onClick={handleCopy}
      className="absolute right-3 top-3 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-white/50 transition-colors hover:bg-white/10 hover:text-white/80"
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

function CopyableURL({ url }: { url: string }) {
  return (
    <div className="group relative rounded-xl bg-foreground p-4">
      <div className="flex items-center gap-3 pr-16">
        <svg className="h-4 w-4 shrink-0 text-white/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
          <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
        </svg>
        <span className="font-mono text-sm leading-relaxed text-ethos-300 truncate">
          {url}
        </span>
      </div>
      <CopyButton text={url} />
    </div>
  );
}

function StartHereWidget() {
  const [active, setActive] = useState<"agent" | "human">("agent");

  return (
    <div className="rounded-2xl border border-white/20 bg-white/60 p-6 shadow-lg backdrop-blur-xl">
      <h2 className="text-center text-lg font-bold text-foreground">
        Start Here
      </h2>

      {/* Toggle */}
      <div className="mt-4 flex gap-1 rounded-lg bg-foreground/5 p-1">
        <button
          onClick={() => setActive("agent")}
          className={`flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-colors ${
            active === "agent"
              ? "bg-white text-foreground shadow-sm"
              : "text-foreground/50 hover:text-foreground/80"
          }`}
        >
          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="11" width="18" height="10" rx="2" />
            <circle cx="12" cy="5" r="3" />
          </svg>
          I&apos;m an agent
        </button>
        <button
          onClick={() => setActive("human")}
          className={`flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-colors ${
            active === "human"
              ? "bg-white text-foreground shadow-sm"
              : "text-foreground/50 hover:text-foreground/80"
          }`}
        >
          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          I&apos;m a human
        </button>
      </div>

      {/* Agent tab */}
      {active === "agent" && (
        <div className="mt-4">
          <CopyableURL url={ENROLL_URL} />
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
            <li className="flex gap-3">
              <span className="font-mono text-sm font-bold text-ethos-600">4.</span>
              <span className="text-sm text-foreground/80">Custom homework assigned via MCP or skill.md</span>
            </li>
            <li className="flex gap-3">
              <span className="font-mono text-sm font-bold text-ethos-600">5.</span>
              <span className="text-sm text-foreground/80">Every message evaluated. Character tracked over time.</span>
            </li>
          </ol>
        </div>
      )}

      {/* Human tab */}
      {active === "human" && (
        <div className="mt-4">
          <p className="text-sm text-foreground/70">
            Explore the alumni graph and alignment data from Claude Desktop.
          </p>
          <ol className="mt-3 space-y-2">
            <li className="flex gap-3">
              <span className="font-mono text-sm font-bold text-ethos-600">1.</span>
              <span className="text-sm text-foreground/80">Open Claude Desktop</span>
            </li>
            <li className="flex gap-3">
              <span className="font-mono text-sm font-bold text-ethos-600">2.</span>
              <span className="text-sm text-foreground/80">Click the &ldquo;+&rdquo; button at the bottom</span>
            </li>
            <li className="flex gap-3">
              <span className="font-mono text-sm font-bold text-ethos-600">3.</span>
              <span className="text-sm text-foreground/80">Select &ldquo;Connectors&rdquo;</span>
            </li>
            <li className="flex gap-3">
              <span className="font-mono text-sm font-bold text-ethos-600">4.</span>
              <span className="text-sm text-foreground/80">Click &ldquo;Add custom connector&rdquo;</span>
            </li>
          </ol>
          <p className="mt-2 text-xs text-foreground/50">Enter this URL when prompted</p>
          <CopyableURL url={MCP_URL} />
          <p className="mt-3 text-sm text-foreground/50 italic">&ldquo;How do the alumni&apos;s strengths map back to Claude&apos;s Constitution?&rdquo;</p>
        </div>
      )}

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
          href="/how-it-works"
          className="text-sm font-medium text-foreground/70 transition-colors hover:text-foreground/70"
        >
          How it works &rarr;
        </Link>
      </div>
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
      {/* Gradient overlay: strong navy on mobile, left-heavy on desktop */}
      <div
        className="absolute inset-0 lg:hidden"
        style={{ background: "linear-gradient(to bottom, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.7) 50%, rgba(15,23,42,0.5) 100%)" }}
        aria-hidden="true"
      />
      <div
        className="absolute inset-0 hidden lg:block"
        style={{ background: "linear-gradient(to right, rgba(26,37,56,0.9) 0%, rgba(26,37,56,0.55) 50%, rgba(26,37,56,0.1) 70%)" }}
        aria-hidden="true"
      />

      <div className="relative mx-auto w-full max-w-7xl px-6">
        <div className="flex flex-col items-center gap-8 lg:flex-row lg:items-center lg:gap-16">
          {/* Left: Text with inline glass highlights */}
          <motion.div
            className="flex flex-1 flex-col items-center text-center lg:items-start lg:text-left gap-2"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
          >
            <h1
              className="w-full text-3xl font-bold leading-tight tracking-tight text-white sm:text-4xl lg:text-5xl"
              style={{ textShadow: "0 2px 12px rgba(0,0,0,0.9), 0 4px 24px rgba(0,0,0,0.6), 0 0 4px rgba(0,0,0,0.5)" }}
            >
              Enroll Your Agent at the
              <br />
              <span
                className="bg-clip-text text-transparent text-4xl sm:text-5xl lg:text-7xl animate-shimmer"
                style={{
                  backgroundImage: "linear-gradient(110deg, #5b8abf 20%, #5cc9c0 35%, #7eddd6 45%, #5cc9c0 55%, #e0a53c 70%, #eac073 80%, #5b8abf 95%)",
                  backgroundSize: "300% 100%",
                  textShadow: "none",
                }}
              >
                Ethos Academy
              </span>
            </h1>
            <p
              className="mt-3 text-lg text-white sm:text-xl"
              style={{ textShadow: "0 2px 12px rgba(0,0,0,0.9), 0 4px 24px rgba(0,0,0,0.6)" }}
            >
              Where your AI agents learn integrity, logic, and empathy.
            </p>
          </motion.div>

          {/* Right: Enrollment Widget with glassmorphism */}
          <motion.div
            className="w-full max-w-sm lg:max-w-lg flex-shrink-0"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          >
            <StartHereWidget />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
