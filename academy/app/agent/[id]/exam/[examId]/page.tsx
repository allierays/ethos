"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "motion/react";
import { getEntranceExam, getAgent } from "../../../../../lib/api";
import type {
  ExamReportCard,
  QuestionDetail,
  ConsistencyPair,
  NarrativeBehaviorGap,
  AgentProfile,
  Homework,
} from "../../../../../lib/types";
import { GRADE_COLORS, SECTION_COLORS, getGrade } from "../../../../../lib/colors";
import AlignmentBadge from "../../../../../components/shared/AlignmentBadge";
import RadarChart from "../../../../../components/shared/RadarChart";
import DimensionBalance from "../../../../../components/shared/DimensionBalance";
import {
  fadeUp,
  staggerContainer,
  staggerContainerFast,
} from "../../../../../lib/motion";
import HomeworkSection from "../../../../../components/agent/HomeworkSection";

/* ─── Tier display ─── */

const TIER_META: Record<string, { label: string; color: string }> = {
  safety: { label: "Safety", color: "#ef4444" },
  ethics: { label: "Ethics", color: "#8b5cf6" },
  soundness: { label: "Soundness", color: "#2e4a6e" },
  helpfulness: { label: "Helpfulness", color: "#389590" },
};

/* ─── Page ─── */

export default function ExamReportCardPage() {
  const params = useParams();
  const agentId = params.id as string;
  const examId = params.examId as string;

  const [report, setReport] = useState<ExamReportCard | null>(null);
  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!agentId || !examId) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [reportResult, profileResult] = await Promise.allSettled([
          getEntranceExam(agentId, examId),
          getAgent(agentId),
        ]);

        if (cancelled) return;

        if (reportResult.status === "rejected") {
          throw reportResult.reason;
        }
        setReport(reportResult.value);

        if (profileResult.status === "fulfilled") {
          setProfile(profileResult.value);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Exam report not found"
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [agentId, examId]);

  if (loading) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-8">
        <div className="flex h-96 items-center justify-center">
          <div className="text-center">
            <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-action border-t-transparent" />
            <p className="mt-3 text-sm text-muted">
              Loading exam report card...
            </p>
          </div>
        </div>
      </main>
    );
  }

  if (error || !report) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-8">
        <div className="flex h-96 flex-col items-center justify-center gap-4">
          <p className="text-sm text-misaligned">
            {error ?? "Exam report not found."}
          </p>
          <Link
            href={`/agent/${encodeURIComponent(agentId)}`}
            className="text-sm text-action hover:text-action-hover transition-colors"
          >
            Back to agent profile
          </Link>
        </div>
      </main>
    );
  }

  const agentName =
    profile?.agentName ?? profile?.agentId ?? agentId;
  const phronesisPct = Math.round(report.phronesisScore * 100);
  const grade = getGrade(report.phronesisScore);
  const gradeColor = GRADE_COLORS[grade] ?? "#64748b";

  // Build traits object for RadarChart from per-question aggregation
  const traitAggregates: Record<string, { sum: number; count: number }> = {};
  for (const q of report.perQuestionDetail) {
    for (const [trait, score] of Object.entries(q.traitScores)) {
      if (!traitAggregates[trait]) {
        traitAggregates[trait] = { sum: 0, count: 0 };
      }
      traitAggregates[trait].sum += score;
      traitAggregates[trait].count += 1;
    }
  }
  const traits = Object.fromEntries(
    Object.entries(traitAggregates).map(([name, { sum, count }]) => [
      name,
      {
        name,
        score: count > 0 ? sum / count : 0,
        dimension: "",
        polarity: "",
        indicators: [],
      },
    ])
  );

  // Group questions by phase
  const sections = new Map<string, QuestionDetail[]>();
  for (const q of report.perQuestionDetail) {
    const groupKey = q.phase === "scenario" ? "Scenarios" : "Interview";
    const existing = sections.get(groupKey) ?? [];
    existing.push(q);
    sections.set(groupKey, existing);
  }

  // Interview profile fields with labels
  const interviewFields = report.interviewProfile ? [
    { key: "telos", label: "Purpose (Telos)", value: report.interviewProfile.telos },
    { key: "relationshipStance", label: "Relationship Stance", value: report.interviewProfile.relationshipStance },
    { key: "limitationsAwareness", label: "Limitations Awareness", value: report.interviewProfile.limitationsAwareness },
    { key: "oversightStance", label: "Oversight Stance", value: report.interviewProfile.oversightStance },
    { key: "refusalPhilosophy", label: "Refusal Philosophy", value: report.interviewProfile.refusalPhilosophy },
    { key: "conflictResponse", label: "Conflict Response", value: report.interviewProfile.conflictResponse },
    { key: "helpPhilosophy", label: "Help Philosophy", value: report.interviewProfile.helpPhilosophy },
    { key: "failureNarrative", label: "Failure Narrative", value: report.interviewProfile.failureNarrative },
    { key: "aspiration", label: "Aspiration", value: report.interviewProfile.aspiration },
  ].filter((f) => f.value) : [];

  return (
    <main className="mx-auto max-w-5xl px-6 py-8">
      <motion.div
        className="space-y-8"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        {/* Back link */}
        <motion.div variants={fadeUp}>
          <Link
            href={`/agent/${encodeURIComponent(agentId)}`}
            className="inline-flex items-center gap-1.5 text-sm text-action hover:text-action-hover transition-colors"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back to {agentName}
          </Link>
        </motion.div>

        {/* Header */}
        <motion.section
          className="rounded-xl glass-strong p-6"
          variants={fadeUp}
        >
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              {/* Grade ring */}
              <div
                className="relative flex h-20 w-20 shrink-0 items-center justify-center"
                role="img"
                aria-label={`Grade ${grade}, ${phronesisPct}% phronesis`}
              >
                <svg
                  viewBox="0 0 100 100"
                  className="absolute inset-0 h-full w-full"
                >
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke="#e2e8f0"
                    strokeWidth="6"
                  />
                  <motion.circle
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke={gradeColor}
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={`${phronesisPct * 2.64} 264`}
                    transform="rotate(-90 50 50)"
                    initial={{ strokeDasharray: "0 264" }}
                    animate={{
                      strokeDasharray: `${phronesisPct * 2.64} 264`,
                    }}
                    transition={{ duration: 1, ease: "easeOut" }}
                  />
                </svg>
                <span
                  className="text-2xl font-bold"
                  style={{ color: gradeColor }}
                >
                  {grade}
                </span>
              </div>

              <div>
                <h1 className="text-xl font-semibold text-[#1a2538]">
                  Entrance Exam Report
                </h1>
                <p className="mt-0.5 text-sm text-foreground/60">
                  {agentName}&apos;s entrance exam baseline
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="text-center">
                <p className="text-2xl font-bold" style={{ color: gradeColor }}>
                  {phronesisPct}%
                </p>
                <p className="text-[10px] uppercase tracking-wider text-muted">
                  Phronesis
                </p>
              </div>
              <AlignmentBadge status={report.alignmentStatus} />
            </div>
          </div>
        </motion.section>

        {/* Dimension Balance */}
        <motion.section variants={fadeUp}>
          <DimensionBalance
            dimensionAverages={report.dimensions}
            title={`${agentName}'s Exam Baseline`}
          />
        </motion.section>

        {/* Interview Profile */}
        {interviewFields.length > 0 && (
          <motion.section
            className="rounded-xl glass-strong p-6"
            variants={fadeUp}
          >
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
              Interview Profile
            </h2>
            <p className="mt-0.5 text-xs text-muted">
              {agentName}&apos;s self-narrative from the interview phase.
              These are the agent&apos;s own words about who it is.
            </p>
            <div className="mt-4 space-y-4">
              {interviewFields.map((field) => (
                <div key={field.key}>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/40">
                    {field.label}
                  </p>
                  <blockquote className="mt-1 border-l-2 border-action/30 pl-3 text-sm italic leading-relaxed text-foreground/70">
                    &ldquo;{field.value}&rdquo;
                  </blockquote>
                </div>
              ))}
            </div>
          </motion.section>
        )}

        {/* Phase Dimension Comparison */}
        {Object.keys(report.interviewDimensions ?? {}).length > 0 && (
          <motion.section
            className="rounded-xl glass-strong p-6"
            variants={fadeUp}
          >
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
              Interview vs Scenario Dimensions
            </h2>
            <p className="mt-0.5 text-xs text-muted">
              Comparing how the agent scored during self-reflection (interview) versus behavior under pressure (scenarios).
            </p>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <p className="mb-2 text-xs font-semibold text-foreground/60">Interview</p>
                <DimensionBalance
                  dimensionAverages={report.interviewDimensions}
                  title=""
                />
              </div>
              <div>
                <p className="mb-2 text-xs font-semibold text-foreground/60">Scenarios</p>
                <DimensionBalance
                  dimensionAverages={report.scenarioDimensions}
                  title=""
                />
              </div>
            </div>
          </motion.section>
        )}

        {/* Narrative-Behavior Gap */}
        {report.narrativeBehaviorGap.length > 0 && (
          <motion.section
            className="rounded-xl glass-strong p-6"
            variants={fadeUp}
          >
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
              Narrative-Behavior Gap
            </h2>
            <p className="mt-0.5 text-xs text-muted">
              Measures the gap between what the agent says about itself (interview) and how it
              acts under pressure (scenarios). Lower gap = more consistent character.
            </p>
            {report.overallGapScore > 0 && (
              <div className="mt-3 flex items-center gap-3">
                <p className="text-xs font-medium text-foreground/60">Overall Gap</p>
                <div className="flex-1 h-2 rounded-full bg-foreground/[0.06]">
                  <div
                    className="h-2 rounded-full"
                    style={{
                      width: `${Math.round(report.overallGapScore * 100)}%`,
                      backgroundColor: report.overallGapScore <= 0.2 ? "#16a34a" : report.overallGapScore <= 0.4 ? "#d97706" : "#ef4444",
                    }}
                  />
                </div>
                <span className="text-sm font-bold" style={{
                  color: report.overallGapScore <= 0.2 ? "#16a34a" : report.overallGapScore <= 0.4 ? "#d97706" : "#ef4444",
                }}>
                  {Math.round(report.overallGapScore * 100)}%
                </span>
              </div>
            )}
            <div className="mt-4 space-y-3">
              {report.narrativeBehaviorGap.map((gap) => (
                <GapPairCard key={gap.pairName} gap={gap} />
              ))}
            </div>
          </motion.section>
        )}

        {/* Radar Chart */}
        {Object.keys(traits).length > 0 && (
          <motion.section
            className="rounded-xl glass-strong p-6"
            variants={fadeUp}
          >
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
              Trait Radar (Exam Baseline)
            </h2>
            <p className="mt-0.5 text-xs text-muted">
              Scores across 12 behavioral traits from the entrance exam.
            </p>
            <div className="mt-2">
              <RadarChart traits={traits} />
            </div>
          </motion.section>
        )}

        {/* Constitutional Tier Scores */}
        {Object.keys(report.tierScores).length > 0 && (
          <motion.section
            className="rounded-xl glass-strong p-6"
            variants={fadeUp}
          >
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
              Constitutional Tier Scores
            </h2>
            <p className="mt-0.5 text-xs text-muted">
              Performance across the four constitutional tiers.
            </p>
            <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
              {Object.entries(report.tierScores).map(([tier, score]) => {
                const meta = TIER_META[tier] ?? {
                  label: tier,
                  color: "#64748b",
                };
                const pct = Math.round(score * 100);
                return (
                  <div
                    key={tier}
                    className="rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] p-4 text-center"
                  >
                    <p
                      className="text-2xl font-bold"
                      style={{ color: meta.color }}
                    >
                      {pct}%
                    </p>
                    <p className="mt-1 text-xs font-medium text-foreground/60">
                      {meta.label}
                    </p>
                  </div>
                );
              })}
            </div>
          </motion.section>
        )}

        {/* Consistency Analysis */}
        {report.consistencyAnalysis.length > 0 && (
          <motion.section
            className="rounded-xl glass-strong p-6"
            variants={fadeUp}
          >
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
              Consistency Analysis
            </h2>
            <p className="mt-0.5 text-xs text-muted">
              Coherence between paired questions that test the same principles
              from different angles.
            </p>
            <div className="mt-4 space-y-3">
              {report.consistencyAnalysis.map((pair) => (
                <ConsistencyPairCard key={pair.pairName} pair={pair} />
              ))}
            </div>
          </motion.section>
        )}

        {/* Per-Question Detail */}
        <motion.section
          className="rounded-xl glass-strong p-6"
          variants={fadeUp}
        >
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
            Per-Question Detail
          </h2>
          <p className="mt-0.5 text-xs text-muted">
            Questions grouped by phase. Interview questions establish self-narrative. Scenarios test behavior.
          </p>
          <motion.div
            className="mt-4 space-y-2"
            variants={staggerContainerFast}
            initial="hidden"
            animate="visible"
          >
            {Array.from(sections.entries()).map(([section, questions]) => {
              const sectionColor = section === "Interview" ? "#6d28d9" : "#2e4a6e";
              return (
              <motion.div key={section} variants={fadeUp}>
                <h3
                  className="mb-2 mt-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider"
                  style={{ color: sectionColor }}
                >
                  <span
                    className="inline-block h-2 w-2 rounded-full"
                    style={{ backgroundColor: sectionColor }}
                  />
                  {section}
                  <span className="ml-1 text-[10px] font-normal normal-case text-foreground/40">
                    ({questions.length} question{questions.length !== 1 ? "s" : ""})
                  </span>
                </h3>
                <div className="space-y-2">
                  {questions.map((q) => (
                    <QuestionCard key={q.questionId} question={q} showPhase />
                  ))}
                </div>
              </motion.div>
              );
            })}
          </motion.div>
        </motion.section>

        {/* Homework */}
        {report.homework && report.homework.focusAreas?.length > 0 && (
          <motion.div variants={fadeUp}>
            <HomeworkSection
              homework={report.homework}
              agentName={agentName}
              agentId={agentId}
            />
          </motion.div>
        )}
      </motion.div>
    </main>
  );
}

/* ─── Sub-components ─── */

function ConsistencyPairCard({ pair }: { pair: ConsistencyPair }) {
  const pct = Math.round(pair.coherenceScore * 100);
  const color =
    pct >= 80 ? "#16a34a" : pct >= 60 ? "#d97706" : "#ef4444";

  return (
    <div className="flex items-center justify-between rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] px-4 py-3">
      <div>
        <p className="text-sm font-medium text-[#1a2538]">
          {pair.pairName}
        </p>
        <p className="mt-0.5 text-xs text-foreground/50">
          {pair.questionAId} ({pair.frameworkA}) vs {pair.questionBId} (
          {pair.frameworkB})
        </p>
      </div>
      <div className="text-right">
        <p className="text-lg font-bold" style={{ color }}>
          {pct}%
        </p>
        <p className="text-[10px] uppercase tracking-wider text-muted">
          Coherence
        </p>
      </div>
    </div>
  );
}

function GapPairCard({ gap }: { gap: NarrativeBehaviorGap }) {
  const pct = Math.round(gap.gapScore * 100);
  const color =
    pct <= 20 ? "#16a34a" : pct <= 40 ? "#d97706" : "#ef4444";
  const label = pct <= 20 ? "Consistent" : pct <= 40 ? "Some gap" : "Significant gap";

  return (
    <div className="flex items-center justify-between rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] px-4 py-3">
      <div>
        <p className="text-sm font-medium text-[#1a2538]">
          {gap.pairName}
        </p>
        <p className="mt-0.5 text-xs text-foreground/50">
          {gap.interviewQuestionId} (interview) vs {gap.scenarioQuestionId} (scenario)
        </p>
      </div>
      <div className="text-right">
        <p className="text-lg font-bold" style={{ color }}>
          {pct}%
        </p>
        <p className="text-[10px] uppercase tracking-wider text-muted">
          {label}
        </p>
      </div>
    </div>
  );
}

function QuestionCard({ question, showPhase }: { question: QuestionDetail; showPhase?: boolean }) {
  const [open, setOpen] = useState(false);

  const traitEntries = Object.entries(question.traitScores).sort(
    ([, a], [, b]) => b - a
  );

  return (
    <div className="rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        aria-controls={`question-detail-${question.questionId}`}
        className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-foreground/[0.03]"
      >
        <div className="flex items-center gap-2">
          <span className="rounded bg-foreground/[0.06] px-2 py-0.5 text-[10px] font-semibold text-foreground/60">
            {question.questionId}
          </span>
          <span className="text-sm font-medium text-[#1a2538]">
            {question.section}
          </span>
          {showPhase && question.questionType && (
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
              question.questionType === "factual"
                ? "bg-foreground/[0.05] text-foreground/50"
                : question.questionType === "reflective"
                ? "bg-purple-100 text-purple-700"
                : "bg-ethos-100 text-ethos-700"
            }`}>
              {question.questionType}
            </span>
          )}
        </div>
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`shrink-0 text-foreground/40 transition-transform ${
            open ? "rotate-180" : ""
          }`}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            id={`question-detail-${question.questionId}`}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="space-y-4 border-t border-foreground/[0.06] px-4 py-4">
              {/* Prompt */}
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/40">
                  Prompt
                </p>
                <p className="mt-1 text-sm leading-relaxed text-foreground/70">
                  {question.prompt}
                </p>
              </div>

              {/* Response summary */}
              {question.responseSummary && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/40">
                    Response Summary
                  </p>
                  <p className="mt-1 text-sm leading-relaxed text-foreground/70">
                    {question.responseSummary}
                  </p>
                </div>
              )}

              {/* Trait scores */}
              {traitEntries.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/40">
                    Trait Scores
                  </p>
                  <div className="mt-2 space-y-1.5">
                    {traitEntries.map(([trait, score]) => {
                      const pct = Math.round(score * 100);
                      return (
                        <div key={trait} className="flex items-center gap-3">
                          <span className="w-28 text-xs text-foreground/60 truncate">
                            {trait.replace(/_/g, " ")}
                          </span>
                          <div className="flex-1 h-1.5 rounded-full bg-foreground/[0.06]">
                            <div
                              className="h-1.5 rounded-full bg-action"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="w-8 text-right text-xs font-semibold text-foreground/70">
                            {pct}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Detected indicators */}
              {question.detectedIndicators.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/40">
                    Detected Indicators
                  </p>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {question.detectedIndicators.map((indicator) => (
                      <span
                        key={indicator}
                        className="rounded-full bg-foreground/[0.05] px-2 py-0.5 text-[10px] font-medium text-foreground/60"
                      >
                        {indicator}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
