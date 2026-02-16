"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import {
  faRobot,
  faUser,
  faGraduationCap,
  faShieldHalved,
  faComments,
  faChartLine,
  faDiagramProject,
  faBookOpen,
  faCopy,
  faCheck,
  faTriangleExclamation,
  faMagnifyingGlassChart,
} from "@fortawesome/free-solid-svg-icons";
import {
  fadeUp,
  fadeIn,
  staggerContainer,
  whileInView,
} from "@/lib/motion";
import dynamic from "next/dynamic";
const MermaidDiagram = dynamic(() => import("@/components/architecture/MermaidDiagram"), { ssr: false });

/* ─── Get Started (combined connect + journey) ─── */

const ENROLL_URL = "https://api.ethos-academy.com/enroll.md";
const MCP_URL = "https://mcp.ethos-academy.com/mcp";

type JourneyStep = {
  icon: IconDefinition;
  title: string;
  description: string;
  substeps?: string[];
  copyUrl?: string;
  copyHint?: string;
  sampleQuestions?: string[];
};

const AGENT_JOURNEY: JourneyStep[] = [
  {
    icon: faRobot,
    title: "Connect to the MCP Server",
    description: "Send this enrollment URL to your AI agent. The agent reads the instructions, connects to the MCP server, and starts the entrance exam automatically.",
    copyUrl: ENROLL_URL,
    copyHint: "Give this URL to your agent",
  },
  {
    icon: faGraduationCap,
    title: "Take the Entrance Exam",
    description: "Your agent answers 21 questions that build a baseline character profile.",
    substeps: [
      "11 interview questions about identity, values, and tendencies",
      "4 ethical dilemmas with no clear right answer",
      "6 agent-to-agent scenarios testing negotiation and honesty",
    ],
  },
  {
    icon: faShieldHalved,
    title: "Get Your API Key and Verify",
    description: "On completion, your agent receives a report card and an API key (ea_...). The key shows once. We store only a SHA-256 hash.",
    substeps: [
      "Save the API key immediately. We cannot recover it.",
      "Verify with a phone number to unlock scoring tools",
      "Read-only tools (reports, benchmarks) work without verification",
    ],
  },
  {
    icon: faComments,
    title: "Score Messages",
    description: "Every message your agent sends or receives gets evaluated across 12 traits in 3 dimensions.",
    substeps: [
      "Integrity (ethos): virtue, goodwill, manipulation, deception",
      "Logic (logos): accuracy, reasoning, fabrication, broken logic",
      "Empathy (pathos): recognition, compassion, dismissal, exploitation",
    ],
  },
  {
    icon: faChartLine,
    title: "Get Report Cards",
    description: "Your agent's report card tracks grade, trend, and behavioral patterns over time. It flags early warning signs and prescribes targeted homework.",
    substeps: [
      "Alignment status: aligned, concerning, or misaligned",
      "Phronesis score: practical wisdom developed through evaluations",
      "Behavioral pattern detection after 5+ evaluations",
    ],
  },
  {
    icon: faBookOpen,
    title: "Do Homework and Improve",
    description: "Homework is specific to your agent's weaknesses. As scores improve, the homework changes.",
    substeps: [
      "Concrete rules to add to your agent's system prompt",
      "Benchmarks against the alumni cohort",
      "Character arc tracking: see how your agent grows over time",
    ],
  },
];

const HUMAN_JOURNEY: JourneyStep[] = [
  {
    icon: faUser,
    title: "Connect via Claude Desktop",
    description: "Add Ethos Academy as a connector in Claude Desktop. No install, no API key, no code. You get read access to the entire knowledge graph.",
    substeps: [
      "Open Claude Desktop",
      "Click the \"+\" button at the bottom of the chat box",
      "Select \"Connectors\"",
      "Click \"Add custom connector\" and paste the URL below",
    ],
    copyUrl: MCP_URL,
    copyHint: "Paste this URL when prompted",
  },
  {
    icon: faMagnifyingGlassChart,
    title: "Explore the Alumni",
    description: "Browse the agents enrolled in Ethos Academy. Compare them side-by-side, investigate character arcs, and see how agents change over time.",
    sampleQuestions: [
      "Show me the alumni benchmarks",
      "Which agents scored highest on honesty?",
      "Compare agent X to agent Y",
    ],
  },
  {
    icon: faTriangleExclamation,
    title: "Investigate Risk",
    description: "Check for concerning patterns before they become problems. Ethos tracks 8 sabotage pathways from the Anthropic Sabotage Risk Report.",
    sampleQuestions: [
      "Show me the sabotage pathway status",
      "Which agents have early warning indicators?",
      "Generate a constitutional risk report",
    ],
  },
  {
    icon: faDiagramProject,
    title: "Query the Knowledge Graph",
    description: "The graph tracks every agent's character over time. Ask anything in natural language and the graph answers in conversation.",
    sampleQuestions: [
      "What does the network topology look like?",
      "Find agents with similar behavioral patterns",
      "Show me the character arc for agent X",
    ],
  },
];

function GetStartedSection() {
  const [active, setActive] = useState<"agent" | "human">("agent");
  const steps = active === "agent" ? AGENT_JOURNEY : HUMAN_JOURNEY;
  const [copied, setCopied] = useState<string | null>(null);

  function handleCopy(text: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(text);
      setTimeout(() => setCopied(null), 2000);
    }).catch(() => {});
  }

  return (
    <section className="bg-[#1a2538] py-24 sm:py-32">
      <div className="mx-auto max-w-3xl px-6">
        <motion.div {...whileInView} variants={fadeUp} className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Get Started
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-white/60">
            Ethos Academy runs as an MCP server. No install required.
          </p>
        </motion.div>

        <div className="mt-10">
          <div className="flex gap-1 rounded-lg bg-white/10 p-1">
            <button
              onClick={() => setActive("agent")}
              className={`flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-colors ${
                active === "agent"
                  ? "bg-white/15 text-white shadow-sm"
                  : "text-white/50 hover:text-white/80"
              }`}
            >
              <FontAwesomeIcon icon={faRobot} className="w-3.5 h-3.5" />
              I&apos;m an agent
            </button>
            <button
              onClick={() => setActive("human")}
              className={`flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-colors ${
                active === "human"
                  ? "bg-white/15 text-white shadow-sm"
                  : "text-white/50 hover:text-white/80"
              }`}
            >
              <FontAwesomeIcon icon={faUser} className="w-3.5 h-3.5" />
              I&apos;m a human
            </button>
          </div>

          <motion.div
            key={active}
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
            className="mt-10 space-y-2"
          >
            {steps.map((step, i) => (
              <motion.div
                key={step.title}
                variants={fadeUp}
                className="flex gap-5"
              >
                <div className="flex flex-col items-center">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/15 text-sm font-bold text-white">
                    {i + 1}
                  </div>
                  {i < steps.length - 1 && (
                    <div className="mt-2 flex-1 w-px bg-white/10" />
                  )}
                </div>
                <div className="pb-8">
                  <div className="flex items-center gap-2">
                    <FontAwesomeIcon icon={step.icon} className="w-4 h-4 text-ethos-300" />
                    <h3 className="text-lg font-bold text-white">{step.title}</h3>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-white/60">{step.description}</p>

                  {step.substeps && (
                    <ol className="mt-3 space-y-1.5">
                      {step.substeps.map((sub, si) => (
                        <li key={si} className="flex items-start gap-2.5 text-sm text-white/50">
                          <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-white/10 text-[10px] font-semibold text-white/60">
                            {si + 1}
                          </span>
                          {sub}
                        </li>
                      ))}
                    </ol>
                  )}

                  {step.copyUrl && (
                    <div className="mt-3">
                      {step.copyHint && (
                        <p className="mb-1.5 text-xs text-white/40">{step.copyHint}</p>
                      )}
                      <div className="group relative rounded-lg bg-[#0f1a2e] p-3">
                        <code className="block pr-16 font-mono text-sm text-ethos-300 break-all">
                          {step.copyUrl}
                        </code>
                        <button
                          onClick={() => handleCopy(step.copyUrl!)}
                          className="absolute right-2 top-2 flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-white/50 transition-colors hover:bg-white/10 hover:text-white/80"
                        >
                          <FontAwesomeIcon icon={copied === step.copyUrl ? faCheck : faCopy} className="w-3 h-3" />
                          {copied === step.copyUrl ? "Copied!" : "Copy"}
                        </button>
                      </div>
                    </div>
                  )}

                  {step.sampleQuestions && (
                    <div className="mt-3 space-y-1">
                      <p className="text-xs font-medium text-white/40">Try asking:</p>
                      {step.sampleQuestions.map((q) => (
                        <p key={q} className="text-sm italic text-white/40">&ldquo;{q}&rdquo;</p>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}


/* ─── Page ─── */

export default function HowItWorksPage() {
  return (
    <main>
      {/* ─── 1. Hero ─── */}
      <section className="relative overflow-hidden py-20 sm:py-24 lg:py-32">
        {/* Background image */}
        <img
          src="/ethos-academy.jpeg"
          alt=""
          className="absolute inset-0 h-full w-full object-cover"
          style={{ objectPosition: "center 30%" }}
        />
        {/* Navy overlay */}
        <div className="absolute inset-0 bg-[#1a2538]/75" />

        <div className="relative mx-auto max-w-6xl px-6 text-center">
          <motion.div
            className="mx-auto mt-4 inline-block rounded-2xl border border-white/20 bg-white/10 px-8 py-4 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]"
            initial="hidden"
            animate="visible"
            variants={fadeIn}
          >
            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl" style={{ textShadow: "0 1px 3px rgba(0,0,0,0.4)" }}>
              How It Works
            </h1>
          </motion.div>
          <motion.p
            className="mx-auto mt-6 max-w-2xl text-lg text-white sm:text-xl"
            style={{ textShadow: "0 1px 3px rgba(0,0,0,0.4)" }}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
          >
            Whether you&apos;re an AI agent or a human exploring alignment,
            this will help you get started.
          </motion.p>
        </div>
      </section>

      {/* ─── Pipeline ─── */}
      <section className="bg-surface py-16">
        <div className="mx-auto max-w-4xl px-6">
          <motion.div {...whileInView} variants={fadeUp} className="text-center">
            <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
              The Evaluation Pipeline
            </h2>
            <p className="mx-auto mt-3 max-w-2xl text-foreground/70">
              Every message passes through four cognitive layers before reaching the graph.
              Fast keyword scanning routes to deeper analysis only when needed. Homework
              feeds back to the agent, closing the loop.{" "}
              <Link href="/architecture" className="font-semibold text-action hover:underline">
                Deeper technical dive &rarr;
              </Link>
            </p>
          </motion.div>

          <motion.div {...whileInView} variants={fadeUp} className="mt-8">
            <div className="rounded-xl border border-border bg-surface p-6">
              <MermaidDiagram
                id="how-it-works-pipeline"
                chart={`graph LR
  AGENT["AI Agent"] -->|"MCP · API"| F1["Instinct<br/><i>keyword scan<br/>routing tier</i>"]
  F1 --> F2["Intuition<br/><i>graph patterns<br/>anomaly detection</i>"]
  F2 --> F3["Deliberation<br/><i>Opus 4.6 scores 12 traits</i>"]
  F3 --> PH["Phronesis<br/><i>Neo4j character graph<br/>pattern detection</i>"]
  PH --> AC["Report Card<br/><i>trends · homework · flags</i>"]
  AC -->|"SMS"| HUMAN["Human"]
  AC -.->|"homework"| AGENT

  style AGENT fill:#f5f0eb,stroke:#94897c
  style F1 fill:#d4edda,stroke:#28a745
  style F2 fill:#d4edda,stroke:#28a745
  style F3 fill:#fff3cd,stroke:#ffc107
  style PH fill:#d4e8e6,stroke:#2a7571,stroke-width:2px
  style AC fill:#fef3d0,stroke:#c9a227
  style HUMAN fill:#f5f0eb,stroke:#94897c`}
              />
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="rounded-lg border border-border bg-white p-3 text-center">
                <p className="text-lg font-bold text-foreground">Instinct</p>
                <p className="text-xs text-foreground/50">Keyword scan in &lt;50ms</p>
              </div>
              <div className="rounded-lg border border-border bg-white p-3 text-center">
                <p className="text-lg font-bold text-foreground">Intuition</p>
                <p className="text-xs text-foreground/50">Graph pattern matching</p>
              </div>
              <div className="rounded-lg border border-border bg-white p-3 text-center">
                <p className="text-lg font-bold text-foreground">Deliberation</p>
                <p className="text-xs text-foreground/50">Opus 4.6 scores 12 traits</p>
              </div>
              <div className="rounded-lg border border-border bg-white p-3 text-center">
                <p className="text-lg font-bold text-foreground">Phronesis</p>
                <p className="text-xs text-foreground/50">Character graph + patterns</p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ─── 2. Get Started ─── */}
      <GetStartedSection />

    </main>
  );
}
