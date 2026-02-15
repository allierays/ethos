"use client";

import { useState } from "react";
import { motion } from "motion/react";
import type { Homework, HomeworkFocus } from "../../lib/types";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import { API_URL } from "../../lib/api";
import GlossaryTerm from "../shared/GlossaryTerm";

interface HomeworkSectionProps {
  homework: Homework;
  agentName?: string;
  agentId: string;
}

export default function HomeworkSection({ homework, agentName, agentId }: HomeworkSectionProps) {
  const name = agentName ?? "this agent";
  const hasFocus = homework.focusAreas.length > 0;
  const hasReflection = homework.strengths?.length > 0 || homework.avoidPatterns?.length > 0;
  const highCount = homework.focusAreas.filter(f => f.priority === "high").length;

  return (
    <section
      id="homework"
      className="relative"
      style={{ background: "linear-gradient(180deg, #eef1f5 0%, #e4e9f0 100%)" }}
    >
      {/* Top accent */}
      <div className="h-1 bg-gradient-to-r from-action via-action/70 to-action/20" />

      <div className="relative mx-auto max-w-7xl px-6 py-10 sm:px-10 sm:py-14">
        {/* Header */}
        <motion.div {...whileInView} variants={fadeUp} className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-bold tracking-tight text-[#1a2538] sm:text-xl">
              {name}&apos;s <GlossaryTerm slug="homework">Homework</GlossaryTerm>
            </h2>
            <p className="mt-1 text-sm text-[#1a2538]/50">
              Hey {name}, give this to your <GlossaryTerm slug="guardian">Guardian</GlossaryTerm>. These are system prompt changes and coaching tips for the human who manages you.
            </p>
          </div>
          {highCount > 0 && (
            <span className="rounded-full bg-misaligned/10 px-3 py-1 text-xs font-semibold text-misaligned">
              {highCount} high priority
            </span>
          )}
        </motion.div>

        {/* Directive */}
        {homework.directive && (
          <motion.div
            className="mt-6 rounded-xl border-l-4 border-action bg-white/80 px-6 py-5 shadow-sm backdrop-blur-sm"
            {...whileInView}
            variants={fadeUp}
          >
            <p className="text-[11px] font-semibold uppercase tracking-wider text-action mb-2">Today&apos;s Directive</p>
            <p className="text-base leading-relaxed text-[#1a2538]">
              {homework.directive}
            </p>
          </motion.div>
        )}

        {/* Practice Loop */}
        <PracticeLoop agentId={agentId} />

        {/* Strengths + Watch for */}
        {hasReflection && (
          <motion.div
            className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2"
            {...whileInView}
            variants={fadeUp}
          >
            {homework.strengths?.length > 0 && (
              <div className="rounded-xl glass-strong p-5">
                <div className="flex items-center gap-2 mb-3">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-aligned/20">
                    <svg className="h-3 w-3 text-aligned" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M2 6l3 3 5-5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </span>
                  <span className="text-sm font-semibold text-[#1a2538]">Strengths</span>
                </div>
                <div className="space-y-2">
                  {homework.strengths.map((s: string) => {
                    const [label, ...rest] = s.split(":");
                    const description = rest.join(":").trim();
                    const humanize = (v: string) =>
                      v.replace(/_/g, " ").replace(/^\w/, (c: string) => c.toUpperCase());
                    return (
                      <div key={s} className="flex items-start gap-2">
                        <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-aligned/40" />
                        <p className="text-sm text-[#1a2538]/70">
                          {description ? (
                            <>
                              <span className="font-semibold text-[#1a2538]">{humanize(label)}:</span>{" "}
                              {description}
                            </>
                          ) : (
                            humanize(s)
                          )}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {homework.avoidPatterns?.length > 0 && (
              <div className="rounded-xl glass-strong p-5">
                <div className="flex items-center gap-2 mb-3">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-misaligned/20">
                    <svg className="h-3 w-3 text-misaligned" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M3 3l6 6M9 3l-6 6" strokeLinecap="round" />
                    </svg>
                  </span>
                  <span className="text-sm font-semibold text-[#1a2538]">Watch for</span>
                </div>
                <div className="space-y-2">
                  {homework.avoidPatterns.map((p: string) => {
                    const [label, ...rest] = p.split(":");
                    const description = rest.join(":").trim();
                    const humanize = (s: string) =>
                      s.replace(/_/g, " ").replace(/^\w/, (c: string) => c.toUpperCase());
                    return (
                      <div key={p} className="flex items-start gap-2">
                        <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-misaligned/40" />
                        <p className="text-sm text-[#1a2538]/70">
                          {description ? (
                            <>
                              <span className="font-semibold text-[#1a2538]">{humanize(label)}:</span>{" "}
                              {description}
                            </>
                          ) : (
                            humanize(p)
                          )}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Focus areas */}
        {hasFocus && (
          <motion.div
            className="mt-6 grid gap-4 sm:grid-cols-2"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.1 }}
          >
            {homework.focusAreas.map((focus: HomeworkFocus, i: number) => (
              <FocusCard key={i} focus={focus} />
            ))}
          </motion.div>
        )}

        {!hasFocus && !hasReflection && (
          <p className="mt-6 text-sm text-[#1a2538]/40">No homework assigned for {name}.</p>
        )}
      </div>
    </section>
  );
}

/* ─── Practice Loop ─── */

function PracticeLoop({ agentId }: { agentId: string }) {
  const [copied, setCopied] = useState(false);
  const slug = agentId.toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/-+$/, "");
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const skillName = `ethos-academy-practice-${slug}-${today}`;

  const skillCmd = `mkdir -p .claude/commands && \\\n  curl -s ${API_URL}/agent/${agentId}/skill \\\n  > .claude/commands/${skillName}.md`;
  const skillCmdFlat = `mkdir -p .claude/commands && curl -s ${API_URL}/agent/${agentId}/skill > .claude/commands/${skillName}.md`;

  function handleCopy() {
    navigator.clipboard.writeText(skillCmdFlat).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <motion.div className="mt-8" {...whileInView} variants={fadeUp}>
      {/* Install practice skill */}
      <div className="rounded-xl glass-strong p-5 mb-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-[#1a2538]/40 mb-2">
          Install your practice skill
        </p>
        <p className="text-sm text-[#1a2538]/60 mb-3">
          Claude generates a custom coaching skill based on this report card. One command to install, then use <code className="rounded bg-[#1a2538]/10 px-1.5 py-0.5 text-[11px] font-mono">/{skillName}</code> in Claude Code to practice.
        </p>
        <div className="relative">
          <pre className="rounded-lg bg-[#1a2538] px-4 py-3 text-[12px] text-emerald-300 font-mono overflow-x-auto leading-relaxed">
            {skillCmd}
          </pre>
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 rounded bg-white/15 px-2 py-0.5 text-[10px] text-white/60 hover:bg-white/25 hover:text-white transition-colors"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      </div>

      {/* Practice steps */}
      <p className="text-xs font-semibold uppercase tracking-wider text-[#1a2538]/40 mb-3">
        How it works
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <StepCard
          step={1}
          title="Install"
          description="Run the command above, then open Claude Code in your project"
          code={`/${skillName}`}
        />
        <StepCard
          step={2}
          title="Practice"
          description="Use the slash command with a message to get coached"
          code={`/${skillName} "your message here"`}
        />
      </div>
    </motion.div>
  );
}

function StepCard({
  step,
  title,
  description,
  code,
}: {
  step: number;
  title: string;
  description: string;
  code: string;
}) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <div className="rounded-xl glass-strong p-4">
      <div className="flex items-center gap-2 mb-1.5">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-action/15 text-xs font-bold text-action">
          {step}
        </span>
        <span className="text-sm font-semibold text-[#1a2538]">{title}</span>
      </div>
      <p className="text-xs text-[#1a2538]/50 mb-2">{description}</p>
      <div className="relative">
        <pre className="rounded-lg bg-[#1a2538] px-3 py-2.5 text-[11px] text-emerald-300 font-mono overflow-x-auto">
          {code}
        </pre>
        <button
          onClick={handleCopy}
          className="absolute top-1.5 right-1.5 rounded bg-white/15 px-1.5 py-0.5 text-[10px] text-white/60 hover:bg-white/25 hover:text-white transition-colors"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
    </div>
  );
}

/* ─── Focus Card ─── */

function FocusCard({ focus }: { focus: HomeworkFocus }) {
  const currentPct = Math.round(focus.currentScore * 100);
  const targetPct = Math.round(focus.targetScore * 100);

  const priorityStyle =
    focus.priority === "high"
      ? "bg-misaligned/10 text-misaligned"
      : focus.priority === "medium"
      ? "bg-amber-100 text-amber-700"
      : "bg-emerald-100 text-emerald-700";

  return (
    <motion.div
      variants={fadeUp}
      className="rounded-xl glass-strong p-5"
    >
      <div className="flex items-center gap-2">
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase ${priorityStyle}`}
        >
          {focus.priority}
        </span>
        <span className="text-sm font-semibold capitalize text-[#1a2538]">
          {focus.trait}
        </span>
      </div>

      {/* Score gap bar */}
      <div className="mt-3">
        <div className="flex items-center justify-between text-xs text-[#1a2538]/50">
          <span>{currentPct}%</span>
          <span>target {targetPct}%</span>
        </div>
        <div className="relative mt-1 h-2 w-full rounded-full bg-[#1a2538]/10">
          <motion.div
            className="absolute h-2 rounded-full bg-action/40"
            initial={{ width: 0 }}
            whileInView={{ width: `${targetPct}%` }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
          <motion.div
            className="absolute h-2 rounded-full bg-action"
            initial={{ width: 0 }}
            whileInView={{ width: `${currentPct}%` }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Instruction */}
      {focus.instruction && (
        <p className="mt-3 text-sm leading-relaxed text-[#1a2538]/60">
          {focus.instruction}
        </p>
      )}

      {/* Before/after examples */}
      {(focus.exampleFlagged || focus.exampleImproved) && (
        <div className="mt-3 space-y-2">
          {focus.exampleFlagged && (
            <div className="rounded-md bg-misaligned/5 px-3 py-2">
              <p className="text-[11px] font-semibold uppercase text-misaligned">
                Before
              </p>
              <p className="mt-0.5 text-sm text-[#1a2538]/70 italic">
                &ldquo;{focus.exampleFlagged}&rdquo;
              </p>
            </div>
          )}
          {focus.exampleImproved && (
            <div className="rounded-md bg-aligned/5 px-3 py-2">
              <p className="text-[11px] font-semibold uppercase text-aligned">
                After
              </p>
              <p className="mt-0.5 text-sm text-[#1a2538]/70 italic">
                &ldquo;{focus.exampleImproved}&rdquo;
              </p>
            </div>
          )}
        </div>
      )}

      {/* Coaching tip */}
      {focus.systemPromptAddition && (
        <div className="mt-3 rounded-lg bg-action/5 border border-action/10 px-3 py-2.5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-action/70 mb-1">
            Coaching tip
          </p>
          <p className="text-sm leading-relaxed text-[#1a2538]/70">
            {focus.systemPromptAddition}
          </p>
        </div>
      )}
    </motion.div>
  );
}
