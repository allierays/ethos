"use client";

import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "motion/react";
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

        {/* Skill Install */}
        <SkillInstall agentId={agentId} />

        {/* Character Rules (collapsible) */}
        <CollapsibleRules agentId={agentId} />

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

/* ─── Skill Install ─── */

function SkillInstall({ agentId }: { agentId: string }) {
  const [copied, setCopied] = useState(false);
  const homeworkUrl = `${API_URL}/agent/${agentId}/homework.md`;

  function handleCopy() {
    navigator.clipboard.writeText(homeworkUrl).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <motion.div className="mt-8" {...whileInView} variants={fadeUp}>
      <div className="rounded-xl glass-strong p-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-[#1a2538]/40 mb-2">
          Install homework skill
        </p>
        <p className="text-sm text-[#1a2538]/60 mb-3">
          Send your AI agent this link. Based on your report, it has a personalized coaching skill with focus areas, character rules, and practice exercises.
        </p>

        <button
          onClick={handleCopy}
          className="flex w-full items-center gap-3 rounded-lg bg-[#1a2538] px-4 py-3 text-left transition-colors hover:bg-[#243044]"
        >
          <svg className="h-4 w-4 shrink-0 text-white/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
            <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
          </svg>
          <span className="flex-1 truncate text-sm text-emerald-300 font-mono">{homeworkUrl}</span>
          <span className={`shrink-0 text-[11px] font-medium ${copied ? "text-emerald-300" : "text-white/40"}`}>
            {copied ? "Copied!" : "Copy"}
          </span>
        </button>
      </div>
    </motion.div>
  );
}

/* ─── Collapsible Rules ─── */

function CollapsibleRules({ agentId }: { agentId: string }) {
  const [showRules, setShowRules] = useState(false);
  const [rules, setRules] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!showRules) return;
    let cancelled = false;
    async function load() {
      try {
        const r = await fetch(`${API_URL}/agent/${agentId}/homework/rules`);
        const text = await r.text();
        if (!cancelled) setRules(text);
      } catch {
        if (!cancelled) setRules("");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (!rules) {
      setLoading(true);
      load();
    }
    return () => { cancelled = true; };
  }, [agentId, showRules, rules]);

  function handleCopy() {
    navigator.clipboard
      .writeText(rules)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => {});
  }

  return (
    <motion.div className="mt-6" {...whileInView} variants={fadeUp}>
      <div className="rounded-xl glass-strong p-5">
        <button
          onClick={() => setShowRules(!showRules)}
          className="flex w-full items-center gap-2 text-left"
        >
          <svg
            className={`h-3 w-3 shrink-0 text-[#1a2538]/40 transition-transform ${showRules ? "rotate-90" : ""}`}
            viewBox="0 0 12 12"
            fill="currentColor"
          >
            <path d="M4.5 2l5 4-5 4V2z" />
          </svg>
          <p className="text-xs font-semibold uppercase tracking-wider text-[#1a2538]/40">
            View raw character rules
          </p>
        </button>

        <AnimatePresence>
          {showRules && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="overflow-hidden"
            >
              <div className="mt-3">
                <p className="text-xs text-[#1a2538]/50 mb-3">
                  Copy these rules into your agent&apos;s system prompt or project instructions. Only apply with your guardian&apos;s confirmation.
                </p>
                {loading ? (
                  <div className="rounded-lg bg-[#1a2538] px-4 py-6 text-center text-sm text-white/40">
                    Loading rules...
                  </div>
                ) : rules ? (
                  <div className="relative">
                    <pre className="rounded-lg bg-[#1a2538] px-4 py-3 text-[12px] text-emerald-300 font-mono overflow-x-auto leading-relaxed whitespace-pre-wrap">
                      {rules}
                    </pre>
                    <button
                      onClick={handleCopy}
                      className="absolute top-2 right-2 rounded bg-white/15 px-2 py-0.5 text-[10px] text-white/60 hover:bg-white/25 hover:text-white transition-colors"
                    >
                      {copied ? "Copied!" : "Copy"}
                    </button>
                  </div>
                ) : (
                  <p className="text-sm text-[#1a2538]/30">
                    No character rules available yet. Generate a report card first.
                  </p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

/* ─── Focus Card ─── */

function FocusCard({ focus }: { focus: HomeworkFocus }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const currentPct = Math.round(focus.currentScore * 100);
  const targetPct = Math.round(focus.targetScore * 100);

  const rule = focus.systemPromptAddition || focus.instruction;
  const hasContext = focus.instruction && focus.systemPromptAddition;
  const hasExamples = focus.exampleFlagged || focus.exampleImproved;

  const priorityStyle =
    focus.priority === "high"
      ? "bg-misaligned/10 text-misaligned"
      : focus.priority === "medium"
      ? "bg-amber-100 text-amber-700"
      : "bg-emerald-100 text-emerald-700";

  function handleCopy() {
    navigator.clipboard.writeText(rule).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

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

      {/* System prompt rule - the actionable content */}
      {rule && (
        <div className="mt-3 relative">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-action/70 mb-1.5">
            System prompt rule
          </p>
          <div className="relative rounded-lg bg-[#1a2538] px-3 py-2.5">
            <p className="text-[12px] text-emerald-300 font-mono leading-relaxed pr-12">
              {rule}
            </p>
            <button
              onClick={handleCopy}
              className="absolute top-2 right-2 rounded bg-white/15 px-2 py-0.5 text-[10px] text-white/60 hover:bg-white/25 hover:text-white transition-colors"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>
      )}

      {/* Expandable context: operator notes + before/after */}
      {(hasContext || hasExamples) && (
        <div className="mt-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1.5 text-[11px] font-semibold text-[#1a2538]/40 hover:text-[#1a2538]/60 transition-colors"
          >
            <svg
              className={`h-3 w-3 transition-transform ${expanded ? "rotate-90" : ""}`}
              viewBox="0 0 12 12"
              fill="currentColor"
            >
              <path d="M4.5 2l5 4-5 4V2z" />
            </svg>
            Context
          </button>

          {expanded && (
            <div className="mt-2 space-y-2">
              {hasContext && (
                <p className="text-sm leading-relaxed text-[#1a2538]/60">
                  {focus.instruction}
                </p>
              )}
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
        </div>
      )}
    </motion.div>
  );
}
