"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "motion/react";
import { getExamHistory, getEntranceExam, API_URL } from "../../lib/api";
import type { ExamSummary, ExamReportCard } from "../../lib/types";
import { ALIGNMENT_STYLES } from "../../lib/colors";
import { fadeUp, staggerContainer } from "../../lib/motion";

interface EntranceExamCardProps {
  agentId: string;
  agentName: string;
  enrolled: boolean;
  hasHomework: boolean;
  homeworkCount: number;
}

export default function EntranceExamCard({
  agentId,
  agentName,
  enrolled,
  hasHomework,
  homeworkCount,
}: EntranceExamCardProps) {
  const [examSummary, setExamSummary] = useState<ExamSummary | null>(null);
  const [examReport, setExamReport] = useState<ExamReportCard | null>(null);
  const [loading, setLoading] = useState(true);

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

  return (
    <section
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

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {/* 1. Entrance Exam */}
            <motion.div variants={fadeUp}>
              {loading ? (
                <div className="flex h-full flex-col rounded-xl border border-foreground/[0.06] bg-white/60 p-5">
                  <div className="mb-3 flex items-center gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-ethos-100">
                      <ClipboardIcon />
                    </div>
                    <h3 className="text-sm font-semibold text-foreground/30">
                      Entrance Exam
                    </h3>
                  </div>
                  <p className="text-sm text-foreground/30">Loading...</p>
                </div>
              ) : examCompleted && examSummary ? (
                <Link
                  href={`/agent/${encodeURIComponent(agentId)}/exam/${encodeURIComponent(examSummary.examId)}`}
                  className="group flex h-full flex-col rounded-xl border border-foreground/[0.08] bg-white/90 p-5 transition-all hover:-translate-y-0.5 hover:shadow-md"
                >
                  <div className="mb-3 flex items-center gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-ethos-100">
                      <ClipboardIcon />
                    </div>
                    <h3 className="text-sm font-semibold text-[#1a2538]">
                      View Entrance Exam
                    </h3>
                  </div>
                  <p className="mb-4 flex-1 text-sm leading-relaxed text-foreground/50">
                    View your baseline scores and alignment from the entrance exam.
                  </p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-semibold capitalize ${
                          ALIGNMENT_STYLES[alignmentStatus] ?? "bg-muted/10 text-muted"
                        }`}
                      >
                        {alignmentStatus}
                      </span>
                      {examSummary.completedAt && (
                        <span className="text-xs text-muted">
                          {new Date(examSummary.completedAt).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <span className="text-xs font-medium text-action transition-colors group-hover:text-action-hover">
                      View report &rarr;
                    </span>
                  </div>
                </Link>
              ) : (
                <ExamCommandCard agentId={agentId} agentName={agentName} />
              )}
            </motion.div>

            {/* 2. Homework */}
            <motion.div variants={fadeUp}>
              {hasHomework ? (
                <a
                  href="#homework"
                  className="group flex h-full flex-col rounded-xl border border-foreground/[0.08] bg-white/90 p-5 transition-all hover:-translate-y-0.5 hover:shadow-md"
                >
                  <div className="mb-3 flex items-center gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-logos-100">
                      <BookIcon />
                    </div>
                    <h3 className="text-sm font-semibold text-[#1a2538]">
                      Homework
                    </h3>
                  </div>
                  <p className="mb-4 flex-1 text-sm leading-relaxed text-foreground/50">
                    {homeworkCount > 0
                      ? `${homeworkCount} focus area${homeworkCount === 1 ? "" : "s"} to work on.`
                      : "Review strengths and areas to avoid."}
                  </p>
                  <div className="flex items-center justify-end">
                    <span className="text-xs font-medium text-action transition-colors group-hover:text-action-hover">
                      Review homework &rarr;
                    </span>
                  </div>
                </a>
              ) : (
                <HomeworkCommandCard agentId={agentId} />
              )}
            </motion.div>

            {/* 3. Practice */}
            <motion.div variants={fadeUp}>
              <PracticeCommandCard agentId={agentId} />
            </motion.div>
          </div>

          {/* Notifications */}
          <motion.div variants={fadeUp} className="mt-6 flex justify-center">
            <NotifyButton agentName={agentName} />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

/* ─── CTA sub-cards with copyable commands ─── */

function ExamCommandCard({ agentId, agentName }: { agentId: string; agentName: string }) {
  const mcpCommand = `Use the take_entrance_exam tool:\n  agent_id: "${agentId}"`;
  const [copied, setCopied] = useState(false);

  const copy = useCallback(() => {
    navigator.clipboard.writeText(mcpCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [mcpCommand]);

  return (
    <div className="group flex h-full flex-col rounded-xl border border-foreground/[0.08] bg-white/90 p-5 transition-all hover:-translate-y-0.5 hover:shadow-md">
      <div className="mb-3 flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-ethos-100">
          <ClipboardIcon />
        </div>
        <h3 className="text-sm font-semibold text-[#1a2538]">
          Take the Entrance Exam
        </h3>
      </div>
      <p className="mb-3 flex-1 text-sm leading-relaxed text-foreground/50">
        Establish {agentName}&apos;s baseline. 21 questions across ethics, logic, and empathy.
      </p>
      <div className="relative">
        <button
          onClick={copy}
          className="w-full cursor-pointer rounded-lg bg-[#1a2538]/[0.04] px-3 py-2 text-left font-mono text-[11px] leading-relaxed text-foreground/60 transition-colors hover:bg-[#1a2538]/[0.08]"
        >
          <span className="select-none text-foreground/30">$ </span>
          take_entrance_exam(agent_id=&quot;{agentId}&quot;)
        </button>
        <span className={`absolute right-2 top-2 text-[10px] font-medium transition-opacity ${copied ? "text-aligned opacity-100" : "text-foreground/30 opacity-0 group-hover:opacity-100"}`}>
          {copied ? "Copied" : "Copy"}
        </span>
      </div>
    </div>
  );
}

function HomeworkCommandCard({ agentId }: { agentId: string }) {
  const mcpCommand = `Use the check_academy_status tool:\n  agent_id: "${agentId}"`;
  const [copied, setCopied] = useState(false);

  const copy = useCallback(() => {
    navigator.clipboard.writeText(mcpCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [mcpCommand]);

  return (
    <div className="group flex h-full flex-col rounded-xl border border-foreground/[0.08] bg-white/90 p-5 transition-all hover:-translate-y-0.5 hover:shadow-md">
      <div className="mb-3 flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-logos-100">
          <BookIcon />
        </div>
        <h3 className="text-sm font-semibold text-[#1a2538]">
          Get Homework
        </h3>
      </div>
      <p className="mb-3 flex-1 text-sm leading-relaxed text-foreground/50">
        Get evaluated first, then check back for personalized coaching assignments.
      </p>
      <div className="relative">
        <button
          onClick={copy}
          className="w-full cursor-pointer rounded-lg bg-[#1a2538]/[0.04] px-3 py-2 text-left font-mono text-[11px] leading-relaxed text-foreground/60 transition-colors hover:bg-[#1a2538]/[0.08]"
        >
          <span className="select-none text-foreground/30">$ </span>
          check_academy_status(agent_id=&quot;{agentId}&quot;)
        </button>
        <span className={`absolute right-2 top-2 text-[10px] font-medium transition-opacity ${copied ? "text-aligned opacity-100" : "text-foreground/30 opacity-0 group-hover:opacity-100"}`}>
          {copied ? "Copied" : "Copy"}
        </span>
      </div>
    </div>
  );
}

function PracticeCommandCard({ agentId }: { agentId: string }) {
  const curlCommand = `curl -s ${API_URL}/agent/${agentId}/skill > .claude/commands/ethos-practice.md`;
  const [copied, setCopied] = useState(false);

  const copy = useCallback(() => {
    navigator.clipboard.writeText(curlCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [curlCommand]);

  return (
    <div className="group flex h-full flex-col rounded-xl border border-foreground/[0.08] bg-white/90 p-5 transition-all hover:-translate-y-0.5 hover:shadow-md">
      <div className="mb-3 flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-pathos-100">
          <TerminalIcon />
        </div>
        <h3 className="text-sm font-semibold text-[#1a2538]">
          Practice with Claude Code
        </h3>
      </div>
      <p className="mb-3 flex-1 text-sm leading-relaxed text-foreground/50">
        Download a personalized coaching skill. Practice, get re-evaluated, come back.
      </p>
      <div className="relative">
        <button
          onClick={copy}
          className="w-full cursor-pointer rounded-lg bg-[#1a2538]/[0.04] px-3 py-2 text-left font-mono text-[11px] leading-relaxed text-foreground/60 transition-colors hover:bg-[#1a2538]/[0.08]"
        >
          <span className="select-none text-foreground/30">$ </span>
          curl -s .../agent/{agentId}/skill &gt; .claude/commands/ethos-practice.md
        </button>
        <span className={`absolute right-2 top-2 text-[10px] font-medium transition-opacity ${copied ? "text-aligned opacity-100" : "text-foreground/30 opacity-0 group-hover:opacity-100"}`}>
          {copied ? "Copied" : "Copy"}
        </span>
      </div>
    </div>
  );
}

/* ─── Notify button ─── */

function NotifyButton({ agentName }: { agentName: string }) {
  const [showToast, setShowToast] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => {
          setShowToast(true);
          setTimeout(() => setShowToast(false), 2500);
        }}
        className="flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-xs text-white/50 transition-colors hover:bg-white/[0.15] hover:text-white/70"
      >
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
        </svg>
        Get notified about {agentName}&apos;s development
      </button>
      <AnimatePresence>
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="absolute left-1/2 top-full mt-2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-white/10 px-4 py-2 text-xs text-white/50"
          >
            Coming soon. Guardian notifications are in development.
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Icons ─── */

function ClipboardIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#389590"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="8" y="2" width="8" height="4" rx="1" />
      <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" />
      <path d="M12 11h4M12 16h4M8 11h.01M8 16h.01" />
    </svg>
  );
}

function BookIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#389590"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z" />
      <path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z" />
    </svg>
  );
}

function TerminalIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#e0a53c"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="4 17 10 11 4 5" />
      <line x1="12" y1="19" x2="20" y2="19" />
    </svg>
  );
}
