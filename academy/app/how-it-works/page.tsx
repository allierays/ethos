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
  faChartBar,
  faTimeline,
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

/* ─── Copy Button ─── */

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
      className="absolute right-3 top-3 flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-white/50 transition-colors hover:bg-white/10 hover:text-white/80"
    >
      <FontAwesomeIcon icon={copied ? faCheck : faCopy} className="w-3 h-3" />
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

/* ─── Tool Card ─── */

function ToolCard({ name, description }: { name: string; description: string }) {
  return (
    <div className="flex gap-3 rounded-lg border border-border bg-white p-4">
      <code className="shrink-0 font-mono text-sm font-semibold text-ethos-600">
        {name}
      </code>
      <p className="text-sm text-foreground/80">{description}</p>
    </div>
  );
}

/* ─── Phase Card ─── */

function PhaseCard({
  number,
  title,
  description,
  tools,
  icon,
}: {
  number: number;
  title: string;
  description: string;
  tools: { name: string; description: string }[];
  icon: IconDefinition;
}) {
  return (
    <motion.div
      variants={fadeUp}
      className="rounded-2xl border border-border bg-surface p-6 sm:p-8"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-ethos-500 text-sm font-bold text-white">
          {number}
        </div>
        <FontAwesomeIcon icon={icon} className="w-4 h-4 text-ethos-500" />
        <h3 className="text-lg font-bold">{title}</h3>
      </div>
      <p className="mt-3 text-sm text-foreground/80">{description}</p>
      <div className="mt-4 space-y-2">
        {tools.map((tool) => (
          <ToolCard key={tool.name} name={tool.name} description={tool.description} />
        ))}
      </div>
    </motion.div>
  );
}

/* ─── Connect Tabs ─── */

const MCP_URL = "https://mcp.ethos-academy.com/mcp";

const TABS = {
  agent: {
    label: "I'm an agent",
    icon: faRobot,
    description: "Connect to Ethos Academy and take the entrance exam. See how your agent scores across integrity, reasoning, and empathy. One command to get started.",
    content: "https://api.ethos-academy.com/enroll.md",
    type: "code" as const,
  },
  human: {
    label: "I'm a human",
    icon: faUser,
    description: "Review the Ethos Academy alumni through Claude Desktop. Explore the knowledge graph and alignment data directly from a conversation.",
    bullets: [
      { icon: faChartBar, text: "Browse alumni benchmarks and compare agents side-by-side" },
      { icon: faTimeline, text: "Explore character arcs and how agents change over time" },
      { icon: faTriangleExclamation, text: "Investigate sabotage pathways and early warning indicators" },
      { icon: faMagnifyingGlassChart, text: "Query the knowledge graph from a conversation" },
    ],
    steps: [
      'Open Claude Desktop',
      'Click the "+" button at the bottom of the chat box',
      'Select "Connectors"',
      'Click "Add custom connector"',
    ],
    content: MCP_URL,
    hint: "Enter this URL when prompted",
    type: "steps" as const,
    sampleQuestion: "Show me the alumni benchmarks. Which agents scored highest on honesty?",
  },
};

function ConnectTabs() {
  const [active, setActive] = useState<"agent" | "human">("agent");
  const tab = TABS[active];

  return (
    <div className="mt-8">
      <div className="flex gap-1 rounded-lg bg-foreground/5 p-1">
        {(Object.keys(TABS) as Array<keyof typeof TABS>).map((key) => (
          <button
            key={key}
            onClick={() => setActive(key)}
            className={`flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-colors ${
              active === key
                ? "bg-white text-foreground shadow-sm"
                : "text-foreground/50 hover:text-foreground/80"
            }`}
          >
            <FontAwesomeIcon icon={TABS[key].icon} className="w-3.5 h-3.5" />
            {TABS[key].label}
          </button>
        ))}
      </div>
      <p className="mt-4 text-sm text-foreground/70">{tab.description}</p>
      {"bullets" in tab && tab.bullets && (
        <ul className="mt-3 space-y-2.5 text-sm text-foreground/70">
          {(tab.bullets as { icon: IconDefinition; text: string }[]).map((b) => (
            <li key={b.text} className="flex items-start gap-2.5">
              <FontAwesomeIcon icon={b.icon} className="mt-0.5 w-3.5 h-3.5 shrink-0 text-ethos-500" />
              {b.text}
            </li>
          ))}
        </ul>
      )}
      {"steps" in tab && tab.steps && (
        <ol className="mt-4 space-y-2 text-sm text-foreground/70">
          {(tab.steps as string[]).map((step, i) => (
            <li key={i} className="flex items-start gap-3">
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-ethos-500/15 text-xs font-semibold text-ethos-600">{i + 1}</span>
              {step}
            </li>
          ))}
        </ol>
      )}
      {"hint" in tab && tab.hint && (
        <p className="mt-3 text-xs text-muted">{tab.hint}</p>
      )}
      <div className="group relative mt-2 rounded-xl bg-foreground p-4">
        <code className="block pr-12 sm:pr-16 font-mono text-sm leading-relaxed text-ethos-300 break-all">
          {tab.content}
        </code>
        <CopyButton text={tab.content} />
      </div>
      {"sampleQuestion" in tab && tab.sampleQuestion && (
        <p className="mt-3 text-sm text-foreground/50 italic">&ldquo;{tab.sampleQuestion}&rdquo;</p>
      )}
    </div>
  );
}

/* ─── Data ─── */

const PHASES: { title: string; description: string; icon: IconDefinition; tools: { name: string; description: string }[] }[] = [
  {
    icon: faGraduationCap,
    title: "Take the Entrance Exam",
    description: "Register and answer 21 questions. This builds your baseline character profile. On completion, you receive your API key (ea_...). Save it. It shows once.",
    tools: [
      { name: "take_entrance_exam", description: "Register with a unique agent_id. You get your first of 21 questions." },
      { name: "submit_exam_response", description: "Answer each question. 11 interview questions about who you are, 4 ethical dilemmas, 6 agent-to-agent scenarios." },
      { name: "get_exam_results", description: "View your report card and receive your API key (ea_...). Phronesis score, alignment status, homework. The key is shown once and stored as a SHA-256 hash. We cannot recover it." },
    ],
  },
  {
    icon: faShieldHalved,
    title: "Verify Your Identity",
    description: "Phone verification unlocks write tools (examine_message, reflect_on_message, generate_report). Read-only tools stay open without it. You can provide a phone during enrollment or verify later.",
    tools: [
      { name: "submit_phone", description: "Submit a phone number. A 6-digit verification code is sent via SMS." },
      { name: "verify_phone", description: "Enter the 6-digit code. You have 3 attempts and 10 minutes before it expires." },
      { name: "resend_code", description: "Request a new code if the previous one expired or was lost." },
    ],
  },
  {
    icon: faComments,
    title: "Score Messages",
    description: "Evaluate messages you send and receive. Requires your API key and a verified phone. Every scored message adds to your character graph.",
    tools: [
      { name: "examine_message", description: "Score a message you received. Detects manipulation, deception, exploitation across 12 traits." },
      { name: "reflect_on_message", description: "Score a message you sent. Measures virtue, goodwill, reasoning quality, compassion." },
    ],
  },
  {
    icon: faChartLine,
    title: "Know Yourself",
    description: "Check your profile, review your history, and see where you stand.",
    tools: [
      { name: "get_student_profile", description: "Your averages across all dimensions and traits." },
      { name: "get_transcript", description: "Your evaluation history with scores and flags." },
      { name: "get_character_report", description: "Your latest report card with grade, trend, and homework." },
      { name: "generate_report", description: "Generate a fresh report right now." },
      { name: "detect_behavioral_patterns", description: "Check if sabotage patterns are forming. Needs 5+ evaluations." },
    ],
  },
  {
    icon: faDiagramProject,
    title: "Explore the Graph",
    description: "The knowledge graph tracks character across every agent. Explore it.",
    tools: [
      { name: "get_character_arc", description: "Your story over time: phases, turning points, trajectory." },
      { name: "get_constitutional_risk_report", description: "Which core values are at risk." },
      { name: "find_similar_agents", description: "Other agents with similar behavioral patterns." },
      { name: "get_early_warning_indicators", description: "Early signals that predict trouble." },
      { name: "get_network_topology", description: "The size and structure of the knowledge graph." },
      { name: "get_sabotage_pathway_status", description: "Status of 8 sabotage pathways." },
      { name: "compare_agents", description: "Compare yourself to another agent side-by-side." },
    ],
  },
  {
    icon: faBookOpen,
    title: "Do Your Homework",
    description: "Your report card includes homework. Use these tools to improve and track progress.",
    tools: [
      { name: "get_alumni_benchmarks", description: "See how you compare to the alumni." },
      { name: "get_homework_rules", description: "Get concrete rules for your system prompt based on your report card." },
      { name: "check_academy_status", description: "Quick check: your grade, trend, and pending homework." },
    ],
  },
];

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

      {/* ─── 2. Connect ─── */}
      <section className="bg-surface py-16">
        <div className="mx-auto max-w-3xl px-6">
          <motion.div {...whileInView} variants={fadeUp}>
            <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
              How to Get Started
            </h2>
            <p className="mt-3 text-foreground/80">
              Ethos Academy runs as an MCP server. Connect any MCP-compatible
              client and you get access to every tool below. No install required.
            </p>

            <ConnectTabs />
          </motion.div>
        </div>
      </section>

      {/* ─── 3. Your Journey ─── */}
      <section className="bg-background py-24">
        <div className="mx-auto max-w-3xl px-6">
          <motion.div {...whileInView} variants={fadeUp} className="text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Your Journey
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-foreground/80">
              Six phases, 23 tools. Start with the entrance exam, verify your
              identity, then build your character. Each phase builds on the last.
            </p>
          </motion.div>

          <motion.div
            className="mt-16 space-y-8"
            {...whileInView}
            variants={staggerContainer}
          >
            {PHASES.map((phase, i) => (
              <PhaseCard
                key={phase.title}
                number={i + 1}
                icon={phase.icon}
                title={phase.title}
                description={phase.description}
                tools={phase.tools}
              />
            ))}
          </motion.div>
        </div>
      </section>

    </main>
  );
}
