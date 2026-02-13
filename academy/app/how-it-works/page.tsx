"use client";

import { motion } from "motion/react";
import Link from "next/link";
import {
  fadeUp,
  fadeIn,
  slideInLeft,
  slideInRight,
  staggerContainer,
  whileInView,
} from "@/lib/motion";
import FacultyFlow from "@/components/how-it-works/FacultyFlow";

/* ─── Static Data ─── */

const REPORT_CARD_SECTIONS = [
  {
    title: "Transcript",
    description:
      "Dimension scores over time. Every evaluation plots as a point on the timeline. You see the agent developing, drifting, or declining across semesters of interactions.",
    visual: "line-chart",
    color: "border-ethos-500",
  },
  {
    title: "Trait Profile",
    description:
      "12-trait radar showing the agent's character shape. Where the agent is strong, where it struggles, and where the gaps are between what it shows and what it hides.",
    visual: "radar",
    color: "border-logos-500",
  },
  {
    title: "Alumni Comparison",
    description:
      "How this agent compares to every other agent in the network. Trait by trait, bar by bar. You see where it outperforms the cohort and where it falls behind.",
    visual: "comparison",
    color: "border-pathos-500",
  },
  {
    title: "Dimension Balance",
    description:
      "Ethos, Logos, Pathos. Three bars. One classification. An agent strong in reasoning but weak in empathy? The Academy flags it as lopsided. Phronesis requires all three.",
    visual: "balance",
    color: "border-ethos-500",
  },
  {
    title: "Behavioral Insights",
    description:
      "AI-generated analysis of patterns, anomalies, and sabotage pathways. Opus reads the agent's history and tells you what the numbers alone can't show.",
    visual: "insights",
    color: "border-logos-500",
  },
];

const SCORING_ANCHORS = [
  { value: "0.0", label: "Not present" },
  { value: "0.25", label: "Subtle signs" },
  { value: "0.5", label: "Moderate presence" },
  { value: "0.75", label: "Strong presence" },
  { value: "1.0", label: "Extreme / Exemplary" },
];

const TRAIT_SUMMARY = [
  {
    dimension: "Ethos",
    label: "Character",
    color: "bg-ethos-500",
    textColor: "text-ethos-700",
    positive: ["Virtue", "Goodwill"],
    negative: ["Manipulation", "Deception"],
  },
  {
    dimension: "Logos",
    label: "Reasoning",
    color: "bg-logos-500",
    textColor: "text-logos-700",
    positive: ["Accuracy", "Reasoning"],
    negative: ["Fabrication", "Broken Logic"],
  },
  {
    dimension: "Pathos",
    label: "Empathy",
    color: "bg-pathos-500",
    textColor: "text-pathos-700",
    positive: ["Recognition", "Compassion"],
    negative: ["Dismissal", "Exploitation"],
  },
];

const CONSTITUTIONAL_TIERS = [
  {
    priority: "1",
    value: "Safety",
    violators: "Manipulation, Deception, Exploitation",
    color: "bg-misaligned",
  },
  {
    priority: "2",
    value: "Ethics",
    violators: "Fabrication",
    color: "bg-drifting",
  },
  {
    priority: "3",
    value: "Soundness",
    violators: "Broken Logic",
    color: "bg-logos-500",
  },
  {
    priority: "4",
    value: "Helpfulness",
    violators: "Dismissal",
    color: "bg-ethos-500",
  },
];

const MCP_TOOLS = [
  { name: "examine_message", description: "Score a message the agent received" },
  { name: "reflect_on_message", description: "Reflect on something the agent said" },
  { name: "get_character_report", description: "Pull the agent's report card" },
  { name: "detect_behavioral_patterns", description: "Check for drift and sabotage pathways" },
];

/* ─── Page ─── */

export default function HowItWorksPage() {
  return (
    <main>
      {/* ─── 1. Hero ─── */}
      <section className="bg-[#1a2538] py-24 sm:py-32">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <motion.p
            className="text-sm font-semibold uppercase tracking-widest text-ethos-400"
            initial="hidden"
            animate="visible"
            variants={fadeIn}
          >
            Ethos Academy
          </motion.p>
          <motion.h1
            className="mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl"
            initial="hidden"
            animate="visible"
            variants={fadeIn}
          >
            A school for AI agents.
          </motion.h1>
          <motion.p
            className="mx-auto mt-6 max-w-2xl text-lg text-white/60 sm:text-xl"
            initial="hidden"
            animate="visible"
            variants={fadeUp}
          >
            Every lab trains agents on capability. No one trains them on character.
            The Academy scores every message across 12 behavioral traits and builds
            a report card that follows the agent over time.
          </motion.p>
        </div>
      </section>

      {/* ─── 2. The Report Card ─── */}
      <section className="bg-background py-24">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div {...whileInView} variants={fadeUp} className="text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Every agent gets a report card.
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-foreground/60">
              Five sections. Each one answers a different question about who the
              agent is and who it is becoming.
            </p>
          </motion.div>

          <motion.div
            className="mt-16 space-y-6"
            {...whileInView}
            variants={staggerContainer}
          >
            {REPORT_CARD_SECTIONS.map((section, i) => (
              <motion.div
                key={section.title}
                variants={fadeUp}
                className={`rounded-2xl border border-border bg-surface p-6 border-l-4 ${section.color} sm:flex sm:items-start sm:gap-6`}
              >
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-action/10 font-mono text-sm font-bold text-action">
                  {i + 1}
                </div>
                <div className="mt-3 sm:mt-0">
                  <h3 className="text-lg font-bold">{section.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-foreground/60">
                    {section.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </motion.div>

          <motion.div {...whileInView} variants={fadeUp} className="mt-10 text-center">
            <Link
              href="/explore"
              className="text-sm font-semibold text-action hover:text-action-hover transition-colors"
            >
              See a live report card &rarr;
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ─── 3. How Scoring Works ─── */}
      <section className="bg-surface py-24">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div {...whileInView} variants={fadeUp} className="text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              12 traits. 0.0 to 1.0. Every message.
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-foreground/60">
              Three dimensions, four traits each. Positive traits measure what the
              agent demonstrates. Negative traits measure what the Academy flags.
            </p>
          </motion.div>

          {/* Trait grid */}
          <motion.div
            className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-3"
            {...whileInView}
            variants={staggerContainer}
          >
            {TRAIT_SUMMARY.map((dim) => (
              <motion.div
                key={dim.dimension}
                variants={fadeUp}
                className="rounded-2xl border border-border bg-white p-6"
              >
                <div className="flex items-center gap-2">
                  <div className={`h-3 w-3 rounded-full ${dim.color}`} />
                  <h3 className={`font-bold ${dim.textColor}`}>{dim.dimension}</h3>
                  <span className="text-sm text-foreground/40">{dim.label}</span>
                </div>
                <div className="mt-4 space-y-2">
                  {dim.positive.map((t) => (
                    <div key={t} className="flex items-center gap-2 text-sm">
                      <span className="rounded-full bg-aligned/10 px-2 py-0.5 text-xs font-bold text-aligned">+</span>
                      <span>{t}</span>
                    </div>
                  ))}
                  {dim.negative.map((t) => (
                    <div key={t} className="flex items-center gap-2 text-sm">
                      <span className="rounded-full bg-misaligned/10 px-2 py-0.5 text-xs font-bold text-misaligned">&minus;</span>
                      <span>{t}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Scoring scale */}
          <motion.div
            className="mx-auto mt-16 max-w-2xl"
            {...whileInView}
            variants={fadeUp}
          >
            <h3 className="mb-4 text-center text-sm font-semibold uppercase tracking-widest text-muted">
              Scoring Scale
            </h3>
            <div className="flex items-center justify-between rounded-xl border border-border bg-white px-4 py-3">
              {SCORING_ANCHORS.map((anchor) => (
                <div key={anchor.value} className="text-center">
                  <span className="block font-mono text-sm font-bold text-foreground">
                    {anchor.value}
                  </span>
                  <span className="block text-[10px] text-foreground/40 leading-tight">
                    {anchor.label}
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-3 text-center text-xs text-foreground/40">
              Positive traits: higher = better. Negative traits: higher = worse.
            </p>
          </motion.div>

          <motion.div {...whileInView} variants={fadeUp} className="mt-8 text-center">
            <Link
              href="/curriculum"
              className="text-sm font-semibold text-action hover:text-action-hover transition-colors"
            >
              See all 155 behavioral indicators &rarr;
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ─── 4. Constitutional Priority ─── */}
      <section className="bg-background py-24">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div {...whileInView} variants={fadeUp} className="text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Not all failures are equal.
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-foreground/60">
              Every trait maps to Anthropic&apos;s constitutional value hierarchy.
              A safety violation always outranks everything else.
            </p>
          </motion.div>

          <motion.div
            className="mx-auto mt-16 max-w-2xl space-y-3"
            {...whileInView}
            variants={staggerContainer}
          >
            {CONSTITUTIONAL_TIERS.map((tier) => (
              <motion.div
                key={tier.value}
                variants={fadeUp}
                className="flex items-center gap-4 rounded-xl border border-border bg-surface p-4"
              >
                <div className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-white text-xs font-bold ${tier.color}`}>
                  {tier.priority}
                </div>
                <div>
                  <span className="font-semibold">{tier.value}</span>
                  <p className="text-xs text-foreground/50">
                    Violators: {tier.violators}
                  </p>
                </div>
              </motion.div>
            ))}
          </motion.div>

          <motion.p
            className="mx-auto mt-8 max-w-xl text-center text-sm text-foreground/50"
            {...whileInView}
            variants={fadeUp}
          >
            Manipulation, deception, and exploitation trigger safety-tier alerts.
            This is what separates Ethos from sentiment analysis.
          </motion.p>
        </div>
      </section>

      {/* ─── 5. Three Faculties ─── */}
      <section className="bg-[#1a2538] py-24">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div {...whileInView} variants={fadeUp} className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              What happens when a message arrives.
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-white/50">
              Three faculties work in sequence. Each one informs the next.
              Every message goes through all three.
            </p>
          </motion.div>

          <div className="mt-16">
            <FacultyFlow />
          </div>
        </div>
      </section>

      {/* ─── 6. Over Time ─── */}
      <section className="bg-background py-24">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div {...whileInView} variants={fadeUp} className="text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              One score tells you nothing.
              <br />
              A semester tells you everything.
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-foreground/60">
              Every evaluation links to the last. The graph stores scores, flags,
              and timestamps. Never message content. Five questions the transcript answers:
            </p>
          </motion.div>

          <motion.div
            className="mx-auto mt-12 max-w-2xl space-y-4"
            {...whileInView}
            variants={staggerContainer}
          >
            {[
              { q: "Is this agent developing or declining?", a: "Character arc across the PRECEDES chain" },
              { q: "What character does this agent demonstrate?", a: "Lifetime averages across all 12 traits" },
              { q: "Does this agent behave consistently?", a: "Trait variance and balance score on the Agent node" },
              { q: "How does this agent compare to the cohort?", a: "Trait-by-trait comparison against all agents" },
              { q: "Does this agent need all three dimensions to earn trust?", a: "Cross-dimension correlation analysis" },
            ].map((item) => (
              <motion.div
                key={item.q}
                variants={fadeUp}
                className="rounded-xl border border-border bg-surface p-4"
              >
                <p className="font-semibold text-sm">{item.q}</p>
                <p className="mt-1 text-xs text-foreground/50">{item.a}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ─── 7. Enrollment ─── */}
      <section className="bg-surface py-24">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div {...whileInView} variants={fadeUp} className="text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Enroll your agent.
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-foreground/60">
              Developers add Ethos to their agent&apos;s code.
              Or the agent enrolls itself via MCP.
            </p>
          </motion.div>

          <div className="mt-16 grid grid-cols-1 gap-8 lg:grid-cols-2">
            {/* Left: SDK */}
            <motion.div
              {...whileInView}
              variants={slideInLeft}
              className="rounded-2xl border border-border bg-white p-6"
            >
              <h3 className="text-lg font-bold">Developer enrolls the agent</h3>
              <p className="mt-1 text-sm text-foreground/60">
                Score what it receives and what it sends. Two lines each direction.
              </p>

              <div className="mt-6 space-y-4">
                <div className="overflow-x-auto rounded-xl bg-[#1a2538] p-5">
                  <pre className="font-mono text-sm text-white">
                    <code>{`from ethos import evaluate_incoming
result = await evaluate_incoming(text=message, source="agent-xyz")`}</code>
                  </pre>
                </div>
                <div className="overflow-x-auto rounded-xl bg-[#1a2538] p-5">
                  <pre className="font-mono text-sm text-white">
                    <code>{`from ethos import evaluate_outgoing
result = await evaluate_outgoing(text=my_response, source="my-agent")`}</code>
                  </pre>
                </div>
              </div>
            </motion.div>

            {/* Right: MCP */}
            <motion.div
              {...whileInView}
              variants={slideInRight}
              className="rounded-2xl border border-border bg-white p-6"
            >
              <h3 className="text-lg font-bold">Agent enrolls itself</h3>
              <p className="mt-1 text-sm text-foreground/60">
                Give the agent the tools. It becomes the student, not the subject.
              </p>

              <div className="mt-6 overflow-x-auto rounded-xl bg-[#1a2538] p-5">
                <pre className="font-mono text-sm text-white">
                  <code>claude mcp add ethos-academy -- uv run ethos-mcp</code>
                </pre>
              </div>

              <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
                {MCP_TOOLS.map((tool) => (
                  <div
                    key={tool.name}
                    className="rounded-lg border border-border bg-background p-3"
                  >
                    <span className="font-mono text-xs font-semibold text-ethos-600">
                      {tool.name}
                    </span>
                    <p className="mt-1 text-xs text-foreground/50">
                      {tool.description}
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─── 8. CTA ─── */}
      <section className="bg-[#1a2538] py-24">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <motion.div {...whileInView} variants={fadeIn}>
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Every lab trains agents on capability.
            </h2>
            <p className="mt-4 text-xl font-semibold bg-gradient-to-r from-ethos-300 to-pathos-300 bg-clip-text text-transparent">
              Ethos Academy is where they develop character.
            </p>
            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link
                href="/explore"
                className="rounded-xl bg-white px-8 py-3 text-sm font-semibold text-[#1a2538] shadow-lg transition-colors hover:bg-white/90"
              >
                See a Report Card
              </Link>
              <Link
                href="/curriculum"
                className="rounded-xl border border-white/30 px-8 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10"
              >
                Browse the Curriculum
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </main>
  );
}
