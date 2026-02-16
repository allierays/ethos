"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "motion/react";
import { getExamHistory, getEntranceExam, submitGuardianEmail, API_URL } from "../../lib/api";
import type { ExamSummary, ExamReportCard, Homework, HomeworkFocus } from "../../lib/types";
import { ALIGNMENT_STYLES } from "../../lib/colors";
import { fadeUp, staggerContainer } from "../../lib/motion";

interface EntranceExamCardProps {
  agentId: string;
  agentName: string;
  enrolled: boolean;
  homework?: Homework;
}

export default function EntranceExamCard({
  agentId,
  agentName,
  enrolled,
  homework,
}: EntranceExamCardProps) {
  const [examSummary, setExamSummary] = useState<ExamSummary | null>(null);
  const [examReport, setExamReport] = useState<ExamReportCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<"exam" | "homework" | "automate" | null>(null);

  useEffect(() => {
    if (!enrolled) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const exams = await getExamHistory(agentId);
        if (cancelled) return;

        const completed = exams.find((e) => e.completed);
        if (completed) {
          setExamSummary(completed);
          try {
            const report = await getEntranceExam(agentId, completed.examId);
            if (!cancelled) setExamReport(report);
          } catch {
            // Report fetch failed but we still have the summary
          }
        }
      } catch {
        // Exam data unavailable, cards still render
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [agentId, enrolled]);

  const examCompleted = !!(examSummary?.completed);
  const alignmentStatus = examReport?.alignmentStatus ?? "unknown";
  const hasHomework = !!(homework && (homework.focusAreas.length > 0 || homework.strengths.length > 0 || homework.avoidPatterns.length > 0));

  function toggle(panel: "exam" | "homework" | "automate") {
    setExpanded(expanded === panel ? null : panel);
  }

  return (
    <section
      id="whats-next"
      className="relative"
      style={{ background: "linear-gradient(180deg, #1a2538 0%, #243044 100%)" }}
    >
      <div className="mx-auto max-w-7xl px-6 py-10 sm:px-10 sm:py-14">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.1 }}
        >
          <motion.p
            variants={fadeUp}
            className="mb-6 text-sm font-semibold uppercase tracking-wider text-white/40"
          >
            What&apos;s next for {agentName}?
          </motion.p>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {/* 1. Entrance Exam */}
            <motion.div variants={fadeUp}>
              {examCompleted && examSummary ? (
                <Link
                  href={`/agent/${encodeURIComponent(agentId)}/exam/${encodeURIComponent(examSummary.examId)}`}
                  className="flex h-full flex-col rounded-xl border border-foreground/[0.08] bg-white/90 overflow-hidden transition-all duration-200 hover:scale-[1.03] hover:shadow-lg"
                >
                  <div className="flex flex-1 flex-col items-center p-6 text-center">
                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-ethos-100 mb-3">
                      <ClipboardIcon />
                    </div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-semibold text-[#1a2538]">View Entrance Exam</h3>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold capitalize ${ALIGNMENT_STYLES[alignmentStatus] ?? "bg-white/10 text-white/50"}`}>
                        {alignmentStatus}
                      </span>
                    </div>
                    <p className="mt-1 text-sm leading-relaxed text-foreground/70">
                      View your baseline scores and alignment.
                    </p>
                    <span className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-ethos-600">
                      View full report &rarr;
                    </span>
                  </div>
                </Link>
              ) : (
                <CalloutCard
                  icon={<ClipboardIcon />}
                  iconBg="bg-ethos-100"
                  title={loading ? "Entrance Exam" : "Take the Entrance Exam"}
                  subtitle={
                    loading
                      ? "Loading..."
                      : "21 questions across ethics, logic, and empathy. Receive a full character report."
                  }
                  open={expanded === "exam"}
                  onToggle={() => toggle("exam")}
                >
                  <ExamOnboarding agentId={agentId} agentName={agentName} />
                </CalloutCard>
              )}
            </motion.div>

            {/* 2. Homework Skill */}
            <motion.div variants={fadeUp}>
              <CalloutCard
                icon={<BookIcon />}
                iconBg="bg-logos-100"
                title="Homework Skill"
                subtitle={
                  hasHomework
                    ? `${homework!.focusAreas.length} focus area${homework!.focusAreas.length === 1 ? "" : "s"} with coaching and practice.`
                    : "Install a personalized coaching skill for Claude Code."
                }
                open={expanded === "homework"}
                onToggle={() => toggle("homework")}
              >
                <HomeworkSkillPanel agentId={agentId} homework={homework} />
              </CalloutCard>
            </motion.div>

            {/* 3. Automate Updates */}
            <motion.div variants={fadeUp}>
              <CalloutCard
                icon={<ShieldIcon />}
                iconBg="bg-pathos-100"
                title="Automate Updates"
                subtitle="Update your system prompt directly. Use with caution."
                open={expanded === "automate"}
                onToggle={() => toggle("automate")}
              >
                <AutomateUpdatesPanel agentId={agentId} agentName={agentName} />
              </CalloutCard>
            </motion.div>
          </div>

          {/* Notifications */}
          <motion.div variants={fadeUp} className="mt-6 flex justify-center">
            <NotifyButton agentId={agentId} agentName={agentName} />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

/* ─── Callout Card ─── */

function CalloutCard({
  icon,
  iconBg,
  title,
  subtitle,
  badge,
  open,
  onToggle,
  children,
}: {
  icon: React.ReactNode;
  iconBg: string;
  title: string;
  subtitle: string;
  badge?: React.ReactNode;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-full flex-col rounded-xl border border-foreground/[0.08] bg-white/90 overflow-hidden transition-all duration-200 hover:scale-[1.03] hover:shadow-lg">
      <button
        onClick={onToggle}
        className="flex w-full flex-1 cursor-pointer flex-col items-center p-6 text-center transition-colors hover:bg-white/50"
      >
        <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${iconBg} mb-3`}>
          {icon}
        </div>
        <div className="flex items-center gap-2">
          <h3 className="text-base font-semibold text-[#1a2538]">{title}</h3>
          {badge}
        </div>
        <p className="mt-1 text-sm leading-relaxed text-foreground/70">{subtitle}</p>
        <svg
          className={`mt-3 h-4 w-4 text-foreground/30 transition-transform ${open ? "rotate-180" : ""}`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="border-t border-foreground/[0.06] px-5 pb-5 pt-4">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Homework Skill Panel ─── */

function HomeworkSkillPanel({
  agentId,
  homework,
}: {
  agentId: string;
  homework?: Homework;
}) {
  const [copied, setCopied] = useState(false);
  const [showFocus, setShowFocus] = useState(false);
  const homeworkUrl = `${API_URL}/agent/${agentId}/homework.md`;

  function handleCopy() {
    navigator.clipboard.writeText(homeworkUrl).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-foreground/70">
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

      <ol className="space-y-2">
        <li className="flex items-start gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-logos-100 text-xs font-bold text-[#1a2538]">1</span>
          <span className="text-sm text-foreground/70 pt-0.5">Send this link to your AI agent</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-logos-100 text-xs font-bold text-[#1a2538]">2</span>
          <span className="text-sm text-foreground/70 pt-0.5">Agent installs the coaching skill as a slash command</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-logos-100 text-xs font-bold text-[#1a2538]">3</span>
          <span className="text-sm text-foreground/70 pt-0.5">Practice, get re-evaluated, come back</span>
        </li>
      </ol>

      {/* Focus area preview */}
      {homework && homework.focusAreas.length > 0 && (
        <div className="pt-2 border-t border-foreground/[0.06]">
          <button
            onClick={() => setShowFocus(!showFocus)}
            className="flex w-full items-center gap-2 text-left"
          >
            <svg
              className={`h-3 w-3 shrink-0 text-foreground/80 transition-transform duration-200 ${showFocus ? "rotate-90" : ""}`}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
            <span className="text-xs font-semibold uppercase tracking-wider text-foreground/30">
              Focus Areas
            </span>
            <span className="rounded-full bg-foreground/[0.06] px-1.5 py-0.5 text-[10px] font-medium text-foreground/80">
              {homework.focusAreas.length}
            </span>
          </button>
          <AnimatePresence>
            {showFocus && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <div className="space-y-2 pt-2">
                  {homework.focusAreas.map((focus: HomeworkFocus, i: number) => (
                    <FocusRow key={i} focus={focus} />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Strengths badges */}
      {homework && homework.strengths.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {homework.strengths.map((s: string) => {
            const label = s.split(":")[0].replace(/_/g, " ");
            return (
              <span
                key={s}
                className="rounded-full bg-aligned/10 px-2 py-0.5 text-[10px] font-semibold capitalize text-aligned"
              >
                {label}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── Focus Row (compact) ─── */

function FocusRow({ focus }: { focus: HomeworkFocus }) {
  const [showRule, setShowRule] = useState(false);
  const [copied, setCopied] = useState(false);
  const rule = focus.systemPromptAddition || focus.instruction;

  const priorityStyle =
    focus.priority === "high"
      ? "bg-misaligned/10 text-misaligned"
      : focus.priority === "medium"
      ? "bg-amber-100 text-amber-700"
      : "bg-emerald-100 text-emerald-700";

  function handleCopy() {
    if (!rule) return;
    navigator.clipboard.writeText(rule).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <div className="rounded-lg bg-foreground/[0.03] p-3">
      <button
        onClick={() => setShowRule(!showRule)}
        className="flex w-full items-center gap-2 text-left"
      >
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${priorityStyle}`}>
          {focus.priority}
        </span>
        <span className="text-sm font-semibold capitalize text-[#1a2538]">
          {focus.trait.replace(/_/g, " ")}
        </span>
        <span className="ml-auto text-xs text-foreground/30">
          {Math.round(focus.currentScore * 100)}%
        </span>
        <svg
          className={`h-3 w-3 shrink-0 text-foreground/30 transition-transform ${showRule ? "rotate-180" : ""}`}
          viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
        >
          <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      <AnimatePresence>
        {showRule && rule && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <div className="relative mt-2">
              <div className="rounded-lg bg-[#1a2538] px-3 py-2.5">
                <p className="text-[11px] text-emerald-300 font-mono leading-relaxed pr-12">
                  {rule}
                </p>
                <button
                  onClick={(e) => { e.stopPropagation(); handleCopy(); }}
                  className="absolute top-2 right-2 rounded bg-white/15 px-2 py-0.5 text-[10px] text-white/60 hover:bg-white/25 hover:text-white transition-colors"
                >
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Exam Onboarding ─── */

function ExamOnboarding({ agentId, agentName }: { agentId: string; agentName: string }) {
  const [copied, setCopied] = useState(false);

  const enrollUrl = `${API_URL}/agent/${agentId}/enroll.md`;

  function handleCopy() {
    navigator.clipboard.writeText(enrollUrl).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-foreground/70">
        Send the enrollment link to your AI agent. It has MCP setup and exam instructions.
      </p>

      <button
        onClick={handleCopy}
        className="flex w-full items-center gap-3 rounded-lg bg-[#1a2538] px-4 py-3 text-left transition-colors hover:bg-[#243044]"
      >
        <svg className="h-4 w-4 shrink-0 text-white/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
          <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
        </svg>
        <span className="flex-1 truncate text-sm text-emerald-300 font-mono">{enrollUrl}</span>
        <span className={`shrink-0 text-[11px] font-medium ${copied ? "text-emerald-300" : "text-white/40"}`}>
          {copied ? "Copied!" : "Copy"}
        </span>
      </button>

      <ol className="space-y-2">
        <li className="flex items-start gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-ethos-100 text-xs font-bold text-[#1a2538]">1</span>
          <span className="text-sm text-foreground/70 pt-0.5">Send this link to {agentName}</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-ethos-100 text-xs font-bold text-[#1a2538]">2</span>
          <span className="text-sm text-foreground/70 pt-0.5">{agentName} takes the entrance exam</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-ethos-100 text-xs font-bold text-[#1a2538]">3</span>
          <span className="text-sm text-foreground/70 pt-0.5">Get your report card</span>
        </li>
      </ol>
    </div>
  );
}

/* ─── Automate Updates Panel ─── */

function AutomateUpdatesPanel({
  agentId,
}: {
  agentId: string;
  agentName: string;
}) {
  const [copied, setCopied] = useState(false);
  const automateUrl = `${API_URL}/agent/${agentId}/automate-updates.md`;

  function handleCopy() {
    navigator.clipboard.writeText(automateUrl).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <div className="space-y-4">
      {/* Caution notice */}
      <div className="flex items-start gap-2.5 rounded-lg bg-amber-50 px-3 py-2.5">
        <svg className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <p className="text-xs text-amber-800 leading-relaxed">
          This writes rules directly to your system prompt or project instructions. Ask your guardian before applying. Only use if you understand the impact.
        </p>
      </div>

      <p className="text-sm text-foreground/70">
        Send your AI agent this link. It has character rules and instructions to write them into your CLAUDE.md.
      </p>

      <button
        onClick={handleCopy}
        className="flex w-full items-center gap-3 rounded-lg bg-[#1a2538] px-4 py-3 text-left transition-colors hover:bg-[#243044]"
      >
        <svg className="h-4 w-4 shrink-0 text-white/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
          <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
        </svg>
        <span className="flex-1 truncate text-sm text-emerald-300 font-mono">{automateUrl}</span>
        <span className={`shrink-0 text-[11px] font-medium ${copied ? "text-emerald-300" : "text-white/40"}`}>
          {copied ? "Copied!" : "Copy"}
        </span>
      </button>

      <ol className="space-y-2">
        <li className="flex items-start gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-pathos-100 text-xs font-bold text-[#1a2538]">1</span>
          <span className="text-sm text-foreground/70 pt-0.5">Send this link to your AI agent</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-pathos-100 text-xs font-bold text-[#1a2538]">2</span>
          <span className="text-sm text-foreground/70 pt-0.5">Agent reads the rules and writes them to CLAUDE.md</span>
        </li>
        <li className="flex items-start gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-pathos-100 text-xs font-bold text-[#1a2538]">3</span>
          <span className="text-sm text-foreground/70 pt-0.5">Confirm the changes with your guardian</span>
        </li>
      </ol>
    </div>
  );
}

/* ─── Guardian email form ─── */

function NotifyButton({ agentId, agentName }: { agentId: string; agentName: string }) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !email.includes("@")) return;

    setStatus("sending");
    try {
      await submitGuardianEmail(agentId, email.trim());
      setStatus("success");
      setMessage("Subscribed. You will receive email notifications.");
    } catch {
      setStatus("error");
      setMessage("Failed to subscribe. Please try again.");
      setTimeout(() => setStatus("idle"), 3000);
    }
  };

  if (status === "success") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-2 text-xs text-emerald-400"
      >
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
        </svg>
        {message}
      </motion.div>
    );
  }

  return (
    <div className="relative">
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <div className="relative">
          <svg className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-white/30" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" />
          </svg>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={`Get notified about ${agentName}`}
            className="h-8 w-64 rounded-full bg-white/10 pl-9 pr-3 text-xs text-white/70 placeholder:text-white/30 outline-none focus:bg-white/[0.15] focus:text-white transition-colors"
            disabled={status === "sending"}
          />
        </div>
        <button
          type="submit"
          disabled={status === "sending" || !email.includes("@")}
          className="h-8 rounded-full bg-white/10 px-4 text-xs text-white/50 transition-colors hover:bg-white/[0.15] hover:text-white/70 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {status === "sending" ? "..." : "Subscribe"}
        </button>
      </form>
      <AnimatePresence>
        {status === "error" && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="absolute left-1/2 top-full mt-2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-red-500/20 px-4 py-2 text-xs text-red-300"
          >
            {message}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Icons ─── */

function ClipboardIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#389590" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="8" y="2" width="8" height="4" rx="1" />
      <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" />
      <path d="M12 11h4M12 16h4M8 11h.01M8 16h.01" />
    </svg>
  );
}

function BookIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#389590" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z" />
      <path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#e0a53c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}
