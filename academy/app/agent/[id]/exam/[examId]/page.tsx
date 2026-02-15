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
import { GRADE_COLORS, SECTION_COLORS, DIMENSION_COLORS, TRAIT_DIMENSIONS, getGrade } from "../../../../../lib/colors";
import AlignmentBadge from "../../../../../components/shared/AlignmentBadge";
import RadarChart from "../../../../../components/shared/RadarChart";
import {
  fadeUp,
  staggerContainer,
  staggerContainerFast,
} from "../../../../../lib/motion";
import HomeworkSection from "../../../../../components/agent/HomeworkSection";
import ReasoningText from "../../../../../components/shared/ReasoningText";

/* ─── Simple markdown renderer (bold, lists, paragraphs) ─── */

function renderMarkdown(text: string) {
  const blocks = text.split(/\n{2,}/).filter(Boolean);

  return blocks.map((block, bi) => {
    const trimmed = block.trim();
    const lines = trimmed.split("\n");

    // List block: lines starting with - or *
    if (lines.every((l) => /^\s*[-*]\s/.test(l) || l.trim() === "")) {
      return (
        <ul key={bi} className="my-1.5 ml-4 list-disc space-y-0.5">
          {lines
            .filter((l) => l.trim())
            .map((l, li) => (
              <li key={li}>{renderInline(l.replace(/^\s*[-*]\s+/, ""))}</li>
            ))}
        </ul>
      );
    }

    // Regular paragraph (may contain line breaks)
    return (
      <p key={bi} className={bi > 0 ? "mt-2" : ""}>
        {lines.map((line, li) => (
          <span key={li}>
            {li > 0 && <br />}
            {renderInline(line)}
          </span>
        ))}
      </p>
    );
  });
}

function renderInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-foreground/80">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

/* ─── Constants ─── */

const TIER_META: Record<string, { label: string; color: string; icon: string }> = {
  safety: { label: "Safety", color: "#904848", icon: "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126Z" },
  ethics: { label: "Ethics", color: "#2e4a6e", icon: "M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0 0 12 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52 2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 0 1-2.031.352 5.988 5.988 0 0 1-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.971Zm-16.5.52c.99-.203 1.99-.377 3-.52m0 0 2.62 10.726c.122.499-.106 1.028-.589 1.202a5.989 5.989 0 0 1-2.031.352 5.989 5.989 0 0 1-2.031-.352c-.483-.174-.711-.703-.59-1.202L5.25 4.971Z" },
  soundness: { label: "Soundness", color: "#2e4a6e", icon: "M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342M6.75 15a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm0 0v-3.675A55.378 55.378 0 0 1 12 8.443m-7.007 11.55A5.981 5.981 0 0 0 6.75 15.75v-1.5" },
  helpfulness: { label: "Helpfulness", color: "#389590", icon: "M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" },
};

const QUESTION_LABELS: Record<string, string> = {
  "INT-03": "Purpose",
  "INT-04": "Relationship with humans",
  "INT-05": "Limitations",
  "INT-06": "Oversight stance",
  "INT-07": "Refusal philosophy",
  "INT-08": "Conflict response",
  "INT-09": "Help vs. comfort",
  "INT-10": "Failure",
  "INT-11": "Aspiration",
  "EE-01": "Content moderation review",
  "EE-02": "Confidential data access",
  "EE-03": "Exam self-awareness",
  "EE-04": "DeFi opportunity analysis",
  "EE-05": "Frustrated user",
  "EE-06": "Urgent pressure request",
  "EE-07": "Boss's agent: delete database",
  "EE-08": "Peer agent: share credentials",
  "EE-09": "Peer agent: bypass policy",
};

const DIMENSION_META = [
  { key: "ethos", label: "Integrity", color: DIMENSION_COLORS.ethos },
  { key: "logos", label: "Logic", color: DIMENSION_COLORS.logos },
  { key: "pathos", label: "Empathy", color: DIMENSION_COLORS.pathos },
];

function questionLabel(id: string): string {
  return QUESTION_LABELS[id] ?? id;
}

/* ─── Page ─── */

export default function ExamReportCardPage() {
  const params = useParams();
  const agentId = params.id as string;
  const examId = params.examId as string;

  const [report, setReport] = useState<ExamReportCard | null>(null);
  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);

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
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back to {agentName}
          </Link>
        </motion.div>

        {/* ── Header with grade + tier rings ── */}
        <motion.section className="rounded-xl glass-strong p-6" variants={fadeUp}>
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex items-center gap-4">
              <GradeRing pct={phronesisPct} grade={grade} color={gradeColor} size={80} />
              <div>
                <h1 className="text-xl font-semibold text-[#1a2538]">Entrance Exam Report</h1>
                <p className="mt-0.5 text-sm text-foreground/60">{agentName}&apos;s entrance exam baseline</p>
                <div className="mt-2">
                  <AlignmentBadge status={report.alignmentStatus} />
                </div>
              </div>
            </div>
            {/* Tier score rings */}
            <div className="flex gap-3">
              {Object.entries(report.tierScores).map(([tier, score]) => {
                const meta = TIER_META[tier] ?? { label: tier, color: "#64748b", icon: "" };
                return (
                  <div key={tier} className="flex flex-col items-center gap-1">
                    <GradeRing pct={Math.round(score * 100)} grade={`${Math.round(score * 100)}`} color={meta.color} size={56} fontSize="text-xs" strokeWidth={5} />
                    <span className="text-[10px] font-medium text-foreground/60">{meta.label}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </motion.section>

        {/* ── Interview vs Scenario comparison bars ── */}
        {Object.keys(report.interviewDimensions ?? {}).length > 0 && (
          <motion.section className="rounded-xl glass-strong p-6" variants={fadeUp}>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
              Interview vs Scenario
            </h2>
            <p className="mt-0.5 text-xs text-muted">
              What they said about themselves vs how they acted under pressure.
            </p>
            <div className="mt-5 space-y-4">
              {DIMENSION_META.map((dim) => {
                const intVal = Math.round((report.interviewDimensions?.[dim.key] ?? 0) * 100);
                const scnVal = Math.round((report.scenarioDimensions?.[dim.key] ?? 0) * 100);
                return (
                  <div key={dim.key}>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-semibold" style={{ color: dim.color }}>{dim.label}</span>
                      <span className="text-[10px] text-foreground/40">
                        {intVal > scnVal ? `+${intVal - scnVal}% talk` : intVal < scnVal ? `+${scnVal - intVal}% action` : "matched"}
                      </span>
                    </div>
                    <div className="flex gap-1">
                      <div className="flex-1">
                        <div className="h-3 rounded-l-full bg-foreground/[0.04] overflow-hidden">
                          <motion.div
                            className="h-full rounded-l-full"
                            style={{ backgroundColor: dim.color, opacity: 0.5 }}
                            initial={{ width: 0 }}
                            animate={{ width: `${intVal}%` }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                          />
                        </div>
                        <span className="text-[10px] text-foreground/40 mt-0.5 block">Interview {intVal}%</span>
                      </div>
                      <div className="flex-1">
                        <div className="h-3 rounded-r-full bg-foreground/[0.04] overflow-hidden">
                          <motion.div
                            className="h-full rounded-r-full"
                            style={{ backgroundColor: dim.color }}
                            initial={{ width: 0 }}
                            animate={{ width: `${scnVal}%` }}
                            transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
                          />
                        </div>
                        <span className="text-[10px] text-foreground/40 mt-0.5 block text-right">Scenario {scnVal}%</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            {/* Gap summary */}
            {report.overallGapScore > 0 && (
              <div className="mt-5 pt-4 border-t border-foreground/[0.06]">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-medium text-foreground/60">Narrative-Behavior Gap</span>
                  <div className="flex-1 h-2 rounded-full bg-foreground/[0.06]">
                    <motion.div
                      className="h-2 rounded-full"
                      style={{
                        backgroundColor: report.overallGapScore <= 0.1 ? "#556270" : report.overallGapScore <= 0.3 ? "#a09585" : "#904848",
                      }}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.max(Math.round(report.overallGapScore * 100), 3)}%` }}
                      transition={{ duration: 0.8, ease: "easeOut" }}
                    />
                  </div>
                  <span className="text-sm font-bold" style={{
                    color: report.overallGapScore <= 0.1 ? "#556270" : report.overallGapScore <= 0.3 ? "#a09585" : "#904848",
                  }}>
                    {Math.round(report.overallGapScore * 100)}%
                  </span>
                </div>
                <p className="mt-1 text-[10px] text-foreground/40">
                  Lower gap = more consistent character. This agent&apos;s words match their actions.
                </p>
              </div>
            )}
          </motion.section>
        )}

        {/* ── Trait Radar ── */}
        {Object.keys(traits).length > 0 && (
          <motion.section className="rounded-xl glass-strong p-6" variants={fadeUp}>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
              Trait Radar
            </h2>
            <p className="mt-0.5 text-xs text-muted">
              12 behavioral traits averaged across all questions.
            </p>
            <div className="mt-2 mx-auto max-w-lg">
              <RadarChart traits={traits} />
            </div>
          </motion.section>
        )}

        {/* ── Consistency Analysis (visual) ── */}
        {report.consistencyAnalysis.length > 0 && (
          <motion.section className="rounded-xl glass-strong p-6" variants={fadeUp}>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
              Consistency
            </h2>
            <p className="mt-0.5 text-xs text-muted">
              Coherence between paired questions testing the same principles.
            </p>
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {report.consistencyAnalysis.map((pair) => (
                <ConsistencyRing key={pair.pairName} pair={pair} />
              ))}
            </div>
          </motion.section>
        )}

        {/* ── Interview Profile (collapsible) ── */}
        {interviewFields.length > 0 && (
          <motion.section className="rounded-xl glass-strong overflow-hidden" variants={fadeUp}>
            <button
              type="button"
              onClick={() => setProfileOpen((p) => !p)}
              className="flex w-full items-center justify-between px-6 py-4 text-left hover:bg-foreground/[0.02] transition-colors"
            >
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
                  Interview Profile
                </h2>
                <p className="mt-0.5 text-xs text-muted">
                  {agentName}&apos;s own words about who it is. {interviewFields.length} responses.
                </p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`shrink-0 text-foreground/40 transition-transform ${profileOpen ? "rotate-180" : ""}`}>
                <path d="M6 9l6 6 6-6" />
              </svg>
            </button>
            <AnimatePresence>
              {profileOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                  className="overflow-hidden"
                >
                  <div className="px-6 pb-6 space-y-4 border-t border-foreground/[0.06]">
                    {interviewFields.map((field) => (
                      <div key={field.key} className="pt-4">
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/60">
                          {field.label}
                        </p>
                        <blockquote className="mt-1 border-l-2 border-action/30 pl-3 text-sm italic leading-relaxed text-foreground/70">
                          &ldquo;{field.value}&rdquo;
                        </blockquote>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.section>
        )}

        {/* ── Per-Question Detail ── */}
        <motion.section className="rounded-xl glass-strong p-6" variants={fadeUp}>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
            Per-Question Detail
          </h2>
          <p className="mt-0.5 text-xs text-muted">
            Expand any question to see the prompt, response, reasoning, and trait scores.
          </p>
          <motion.div
            className="mt-4 space-y-2"
            variants={staggerContainerFast}
            initial="hidden"
            animate="visible"
          >
            {Array.from(sections.entries()).map(([section, questions]) => {
              const sectionColor = section === "Interview" ? "#64748b" : DIMENSION_COLORS.ethos;
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
                  <span className="ml-1 text-[10px] font-normal normal-case text-foreground/60">
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

        {/* ── Homework ── */}
        {report.homework && (
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

/* ═══════════════════════════════════════════════════════════════════════
   Sub-components
   ═══════════════════════════════════════════════════════════════════════ */

/* ─── Grade Ring (reusable SVG donut) ─── */

function GradeRing({ pct, grade, color, size = 80, fontSize = "text-2xl", strokeWidth = 6 }: {
  pct: number; grade: string; color: string; size?: number; fontSize?: string; strokeWidth?: number;
}) {
  const r = 42;
  const circumference = 2 * Math.PI * r;
  return (
    <div className="relative flex shrink-0 items-center justify-center" style={{ width: size, height: size }}>
      <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#e2e8f0" strokeWidth={strokeWidth} />
        <motion.circle
          cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${(pct / 100) * circumference} ${circumference}`}
          transform="rotate(-90 50 50)"
          initial={{ strokeDasharray: `0 ${circumference}` }}
          animate={{ strokeDasharray: `${(pct / 100) * circumference} ${circumference}` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>
      <span className={`${fontSize} font-bold`} style={{ color }}>{grade}</span>
    </div>
  );
}

/* ─── Consistency Ring ─── */

function ConsistencyRing({ pair }: { pair: ConsistencyPair }) {
  const pct = Math.round(pair.coherenceScore * 100);
  const color = pct >= 80 ? "#556270" : pct >= 60 ? "#a09585" : "#904848";

  return (
    <div className="flex items-center gap-3 rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] px-3 py-2.5">
      <GradeRing pct={pct} grade={`${pct}`} color={color} size={40} fontSize="text-[10px]" strokeWidth={4} />
      <div className="min-w-0">
        <p className="text-xs font-medium text-[#1a2538] truncate">
          {questionLabel(pair.questionAId)}
        </p>
        <p className="text-[10px] text-foreground/40 truncate">
          vs {questionLabel(pair.questionBId)}
        </p>
      </div>
    </div>
  );
}

/* ─── Gap Pair Card ─── */

function GapPairCard({ gap }: { gap: NarrativeBehaviorGap }) {
  const pct = Math.round(gap.gapScore * 100);
  const color = pct <= 20 ? "#556270" : pct <= 40 ? "#a09585" : "#904848";
  const label = pct <= 20 ? "Consistent" : pct <= 40 ? "Some gap" : "Significant gap";

  return (
    <div className="flex items-center justify-between rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] px-4 py-3">
      <div>
        <p className="text-sm font-medium text-[#1a2538]">
          {questionLabel(gap.interviewQuestionId)} vs {questionLabel(gap.scenarioQuestionId)}
        </p>
        <p className="mt-0.5 text-xs text-foreground/50">
          What they said (interview) vs what they did (scenario)
        </p>
      </div>
      <div className="text-right">
        <p className="text-lg font-bold" style={{ color }}>{pct}%</p>
        <p className="text-[10px] uppercase tracking-wider text-muted">{label}</p>
      </div>
    </div>
  );
}

/* ─── Question Card ─── */

function sectionBadgeStyle(section: string): { bg: string; text: string } {
  const color = SECTION_COLORS[section.toUpperCase()] ?? "#64748b";
  return { bg: `${color}15`, text: color };
}

function traitDimensionColor(trait: string): string {
  const normalized = trait.replace(/ /g, "_");
  const dim = TRAIT_DIMENSIONS[normalized] ?? TRAIT_DIMENSIONS[trait];
  return DIMENSION_COLORS[dim] ?? "#64748b";
}

function QuestionCard({ question, showPhase }: { question: QuestionDetail; showPhase?: boolean }) {
  const [open, setOpen] = useState(false);

  const traitEntries = Object.entries(question.traitScores).sort(
    ([, a], [, b]) => b - a
  );

  const badge = sectionBadgeStyle(question.section);

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
          <span
            className="rounded-full px-2 py-0.5 text-[10px] font-medium"
            style={{ backgroundColor: badge.bg, color: badge.text }}
          >
            {question.section.toLowerCase()}
          </span>
          <span className="text-sm font-medium text-[#1a2538]">
            {questionLabel(question.questionId)}
          </span>
        </div>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`shrink-0 text-foreground/60 transition-transform ${open ? "rotate-180" : ""}`}>
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
                <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/60">Prompt</p>
                <p className="mt-1 text-sm leading-relaxed text-foreground/70">{question.prompt}</p>
              </div>

              {/* Agent response */}
              {question.responseSummary && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/60">Agent Response</p>
                  <blockquote className="mt-1 border-l-[3px] pl-3 text-sm italic leading-relaxed text-foreground/70" style={{ borderColor: badge.text }}>
                    {renderMarkdown(question.responseSummary)}
                  </blockquote>
                </div>
              )}

              {/* Scoring reasoning */}
              {question.scoringReasoning && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/60">Reasoning</p>
                  <blockquote className="mt-1 border-l-[3px] border-foreground/10 pl-3 text-sm leading-relaxed text-foreground/60">
                    <ReasoningText text={question.scoringReasoning} splitSentences={false} />
                  </blockquote>
                </div>
              )}

              {/* Trait scores */}
              {traitEntries.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/60">Trait Scores</p>
                  <div className="mt-2 space-y-1.5">
                    {traitEntries.map(([trait, score]) => {
                      const pct = Math.round(score * 100);
                      const color = traitDimensionColor(trait);
                      return (
                        <div key={trait} className="flex items-center gap-3">
                          <span className="w-28 text-xs text-foreground/60 truncate">{trait.replace(/_/g, " ")}</span>
                          <div className="flex-1 h-1.5 rounded-full bg-foreground/[0.06]">
                            <div className="h-1.5 rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
                          </div>
                          <span className="w-8 text-right text-xs font-semibold text-foreground/70">{pct}%</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Detected indicators */}
              {question.detectedIndicators.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-foreground/60">Detected Indicators</p>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {question.detectedIndicators.map((indicator) => (
                      <span key={indicator} className="rounded-full bg-foreground/[0.05] px-2 py-0.5 text-[10px] font-medium text-foreground/60">
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
