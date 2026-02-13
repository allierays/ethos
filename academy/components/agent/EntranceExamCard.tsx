"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { getExamHistory, getEntranceExam } from "../../lib/api";
import type { ExamSummary, ExamReportCard } from "../../lib/types";
import { ALIGNMENT_STYLES, DIMENSIONS, GRADE_COLORS, getGrade } from "../../lib/colors";
import { fadeUp } from "../../lib/motion";
import GlossaryTerm from "../shared/GlossaryTerm";

interface EntranceExamCardProps {
  agentId: string;
  agentName: string;
  enrolled: boolean;
}

export default function EntranceExamCard({
  agentId,
  agentName,
  enrolled,
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
                Baseline character assessment
              </p>
            </div>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
            <GlossaryTerm slug="enrollment">Not Enrolled</GlossaryTerm>
          </span>
        </div>
        <p className="mt-4 text-sm leading-relaxed text-foreground/60">
          {agentName} has not enrolled in Ethos Academy. Enroll to take the entrance exam and establish a character baseline.
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
          {agentName} enrolled but has not completed the entrance exam. Complete the exam to establish a character baseline.
        </p>
      </motion.section>
    );
  }

  // Exam completed: show results
  const dims = examReport?.dimensions ?? {};
  const phronesis = examSummary.phronesisScore;
  const phronesisPct = Math.round(phronesis * 100);
  const alignmentStatus = examReport?.alignmentStatus ?? "unknown";

  const grade = getGrade(phronesis);
  const gradeColor = GRADE_COLORS[grade] ?? "#64748b";

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
              Entrance Exam
            </h2>
            <p className="text-sm text-foreground/60">
              Baseline character assessment
            </p>
          </div>
        </div>
        <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
          Enrolled
        </span>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-[auto_1fr]">
        {/* Grade ring */}
        <div className="flex items-center gap-4 sm:flex-col sm:items-center sm:gap-2">
          <div className="relative flex h-16 w-16 shrink-0 items-center justify-center">
            <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" strokeWidth="6" />
              <motion.circle
                cx="50" cy="50" r="42" fill="none"
                stroke={gradeColor} strokeWidth="6" strokeLinecap="round"
                strokeDasharray={`${phronesisPct * 2.64} 264`}
                transform="rotate(-90 50 50)"
                initial={{ strokeDasharray: "0 264" }}
                animate={{ strokeDasharray: `${phronesisPct * 2.64} 264` }}
                transition={{ duration: 1, ease: "easeOut" }}
              />
            </svg>
            <span className="text-xl font-bold" style={{ color: gradeColor }}>
              {grade}
            </span>
          </div>
          <div className="text-center">
            <p className="text-xs font-semibold text-foreground/80">
              {phronesisPct}%
            </p>
            <p className="text-[10px] uppercase tracking-wider text-muted">
              Phronesis
            </p>
          </div>
        </div>

        {/* Dimension bars + meta */}
        <div className="space-y-3">
          {DIMENSIONS.map(({ key, label, color }) => {
            const score = dims[key] ?? 0;
            const pct = Math.round(score * 100);
            return (
              <div key={key}>
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-foreground/70">{label}</span>
                  <span className="font-semibold text-foreground/80">{pct}%</span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-border/40">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
                  />
                </div>
              </div>
            );
          })}

          {/* Meta row */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold capitalize ${
                ALIGNMENT_STYLES[alignmentStatus] ?? "bg-muted/10 text-muted"
              }`}
            >
              {alignmentStatus}
            </span>
            {examSummary.completedAt && (
              <span className="text-[10px] text-muted">
                Completed {new Date(examSummary.completedAt).toLocaleDateString()}
              </span>
            )}
          </div>

          {/* Link to full report */}
          <Link
            href={`/agent/${encodeURIComponent(agentId)}/exam/${encodeURIComponent(examSummary.examId)}`}
            className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-action hover:text-action-hover transition-colors"
          >
            View full report &rarr;
          </Link>
        </div>
      </div>
    </motion.section>
  );
}

function ClipboardIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#3b8a98"
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
