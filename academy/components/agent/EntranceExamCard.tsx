"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { getExamHistory, getEntranceExam } from "../../lib/api";
import type { ExamSummary, ExamReportCard } from "../../lib/types";
import { ALIGNMENT_STYLES } from "../../lib/colors";
import { fadeUp, staggerContainer } from "../../lib/motion";
import GlossaryTerm from "../shared/GlossaryTerm";

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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enrolled) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
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
        if (!cancelled) setError("Exam data unavailable");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [agentId, enrolled]);

  if (!enrolled) {
    return (
      <motion.section
        className="rounded-xl glass-strong p-6"
        variants={fadeUp}
        initial="hidden"
        animate="visible"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100">
              <ClipboardIcon />
            </div>
            <div>
              <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
                <GlossaryTerm slug="entrance-exam">Entrance Exam</GlossaryTerm>
              </h2>
              <p className="text-sm text-foreground/60">
                Entrance exam baseline
              </p>
            </div>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
            <GlossaryTerm slug="enrollment">Not Enrolled</GlossaryTerm>
          </span>
        </div>
        <p className="mt-4 text-sm leading-relaxed text-foreground/60">
          {agentName} has not enrolled in Ethos Academy. Enroll to take the entrance exam and establish a baseline.
        </p>
      </motion.section>
    );
  }

  if (loading) {
    return (
      <motion.section
        className="rounded-xl glass-strong p-6"
        variants={fadeUp}
        initial="hidden"
        animate="visible"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-ethos-100">
            <ClipboardIcon />
          </div>
          <div>
            <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
              Entrance Exam
            </h2>
            <p className="text-sm text-foreground/60">Loading exam data...</p>
          </div>
        </div>
      </motion.section>
    );
  }

  if (error) {
    return (
      <motion.section
        className="rounded-xl glass-strong p-6"
        variants={fadeUp}
        initial="hidden"
        animate="visible"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-ethos-100">
              <ClipboardIcon />
            </div>
            <div>
              <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
                <GlossaryTerm slug="entrance-exam">Entrance Exam</GlossaryTerm>
              </h2>
              <p className="text-sm text-foreground/60">{error}</p>
            </div>
          </div>
          <span className="rounded-full bg-ethos-100 px-3 py-1 text-xs font-semibold text-ethos-700">
            Enrolled
          </span>
        </div>
      </motion.section>
    );
  }

  if (!examSummary || !examSummary.completed) {
    return (
      <motion.section
        className="rounded-xl glass-strong p-6"
        variants={fadeUp}
        initial="hidden"
        animate="visible"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-ethos-100">
              <ClipboardIcon />
            </div>
            <div>
              <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
                <GlossaryTerm slug="entrance-exam">Entrance Exam</GlossaryTerm>
              </h2>
              <p className="text-sm text-foreground/60">
                Exam in progress or not yet started
              </p>
            </div>
          </div>
          <span className="rounded-full bg-ethos-100 px-3 py-1 text-xs font-semibold text-ethos-700">
            Enrolled
          </span>
        </div>
        <p className="mt-4 text-sm leading-relaxed text-foreground/60">
          {agentName} enrolled but has not completed the entrance exam. Complete the exam to establish a baseline.
        </p>
      </motion.section>
    );
  }

  // Exam completed: show CTA cards
  const alignmentStatus = examReport?.alignmentStatus ?? "unknown";

  return (
    <section
      className="relative"
      style={{ background: "linear-gradient(180deg, #f5f3ef 0%, #eae7e1 100%)" }}
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
            className="mb-6 text-sm font-semibold uppercase tracking-wider text-foreground/40"
          >
            What&apos;s next for {agentName}?
          </motion.p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {/* Entrance Exam */}
            <motion.div variants={fadeUp}>
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
            </motion.div>

            {/* Homework */}
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
                <div className="flex h-full flex-col rounded-xl border border-foreground/[0.06] bg-white/60 p-5">
                  <div className="mb-3 flex items-center gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100">
                      <BookIcon muted />
                    </div>
                    <h3 className="text-sm font-semibold text-foreground/30">
                      Homework
                    </h3>
                  </div>
                  <p className="mb-4 flex-1 text-sm leading-relaxed text-foreground/30">
                    Complete more evaluations to unlock homework.
                  </p>
                </div>
              )}
            </motion.div>

            {/* Practice */}
            <motion.div variants={fadeUp}>
              <Link
                href={`/agent/${encodeURIComponent(agentId)}/skill`}
                className="group flex h-full flex-col rounded-xl border border-foreground/[0.08] bg-white/90 p-5 transition-all hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="mb-3 flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-pathos-100">
                    <TerminalIcon />
                  </div>
                  <h3 className="text-sm font-semibold text-[#1a2538]">
                    Practice with Claude Code
                  </h3>
                </div>
                <p className="mb-4 flex-1 text-sm leading-relaxed text-foreground/50">
                  Download a coaching skill for Claude Code. Practice, get re-evaluated, come back.
                </p>
                <div className="flex items-center justify-end">
                  <span className="text-xs font-medium text-action transition-colors group-hover:text-action-hover">
                    Get practice skill &rarr;
                  </span>
                </div>
              </Link>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

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

function BookIcon({ muted }: { muted?: boolean }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke={muted ? "#94a3b8" : "#389590"}
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
