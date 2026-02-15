"use client";

import { useMemo } from "react";
import { motion } from "motion/react";
import type {
  AgentProfile,
  EvaluationHistoryItem,
  DailyReportCard,
  DriftBreakpoint,
} from "../../../lib/types";
import CharacterHealth from "../../../components/agent/CharacterHealth";
import AlumniComparison from "../../../components/alumni/AlumniComparison";
import GradeHero from "../../../components/agent/GradeHero";
import EntranceExamCard from "../../../components/agent/EntranceExamCard";
import RiskIndicators from "../../../components/agent/RiskIndicators";
import HomeworkSection from "../../../components/agent/HomeworkSection";
import PatternsPanel from "../../../components/agent/PatternsPanel";
import TranscriptChart from "../../../components/agent/TranscriptChart";
import ConstitutionalTrail from "../../../components/agent/ConstitutionalTrail";
import GuardianNotifications from "../../../components/agent/GuardianNotifications";

import EvaluationDepth from "../../../components/agent/EvaluationDepth";
import HighlightsPanel from "../../../components/agent/HighlightsPanel";
import GoldenMean from "../../../components/agent/GoldenMean";
import BalanceThesis from "../../../components/agent/BalanceThesis";
import GlossaryTerm from "../../../components/shared/GlossaryTerm";
import GraphHelpButton from "../../../components/shared/GraphHelpButton";
import { fadeUp, staggerContainer } from "../../../lib/motion";

/* ─── Timeline data point ─── */

interface TimelineDataPoint {
  index: number;
  createdAt: string;
  ethos: number;
  logos: number;
  pathos: number;
  flags: string[];
  alignmentStatus: string;
}

/* ─── Props ─── */

interface AgentReportClientProps {
  agentId: string;
  profile: AgentProfile;
  history: EvaluationHistoryItem[];
  report: DailyReportCard | null;
  breakpoints: DriftBreakpoint[];
}

/* ─── Page ─── */

export default function AgentReportClient({
  agentId,
  profile,
  history,
  report,
  breakpoints,
}: AgentReportClientProps) {
  const timeline = useMemo<TimelineDataPoint[]>(
    () =>
      history
        .slice()
        .reverse()
        .map((item, i) => ({
          index: i + 1,
          createdAt: item.createdAt,
          ethos: item.ethos,
          logos: item.logos,
          pathos: item.pathos,
          flags: item.flags,
          alignmentStatus: item.alignmentStatus,
        })),
    [history]
  );

  const agentName = profile.agentName || profile.agentId;

  return (
    <>
      <h1 className="sr-only">{agentName} Report Card</h1>

      {/* Entrance Exam baseline */}
      {profile.enrolled && (
        <div className="mx-auto max-w-7xl px-6 pt-8">
          <EntranceExamCard
            agentId={agentId}
            agentName={agentName}
            enrolled={profile.enrolled}
          />
        </div>
      )}

      {/* Full-width hero banner */}
      <GradeHero profile={profile} report={report} timeline={timeline} />

      {/* Decorative blobs — full-width so they don't clip at max-w edges */}
      <div className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden" aria-hidden="true">
          <div className="absolute -top-40 -left-40 h-[500px] w-[500px] rounded-full bg-ethos-200/30 blur-3xl" />
          <div className="absolute top-1/3 -right-32 h-[400px] w-[400px] rounded-full bg-logos-200/20 blur-3xl" />
          <div className="absolute bottom-1/4 left-1/4 h-[350px] w-[350px] rounded-full bg-pathos-200/25 blur-3xl" />
        </div>
      <main className="relative mx-auto max-w-7xl px-6 py-8">
        <motion.div
          className="space-y-8"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {/* 1. Trait Development (interactive radar + detail) */}
        <motion.section variants={fadeUp}>
          <CharacterHealth
            traitAverages={profile.traitAverages}
            agentName={agentName}
          />
        </motion.section>

        {/* 2. Aristotelian Thesis + Golden Mean (side by side) */}
        <motion.section variants={fadeUp} className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <BalanceThesis
            dimensionAverages={profile.dimensionAverages}
            evaluationCount={profile.evaluationCount}
            agentName={agentName}
          />
          <GoldenMean traitAverages={profile.traitAverages} agentName={agentName} />
        </motion.section>

        {/* In their own words (exemplary and flagged messages) */}
        <motion.section variants={fadeUp}>
          <HighlightsPanel agentId={agentId} agentName={agentName} />
        </motion.section>

        {/* Transcript with drift breakpoints */}
        <motion.section id="transcript" variants={fadeUp}>
          <TranscriptChart timeline={timeline} agentName={agentName} breakpoints={breakpoints} history={history} />
        </motion.section>

        {/* Constitutional Value Trail (5-hop graph traversal) */}
        <motion.section id="constitutional-trail" variants={fadeUp}>
          <ConstitutionalTrail agentId={agentId} agentName={agentName} />
        </motion.section>

        {/* 8. Risk and Sabotage Pathways */}
        <motion.section id="risk" variants={fadeUp}>
          <div className="rounded-xl glass-strong p-6 space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
                  Risk &amp; <GlossaryTerm slug="sabotage-pathway">Sabotage Pathways</GlossaryTerm>
                </h2>
                <p className="mt-0.5 text-sm text-foreground/60">
                  Flagged indicators and manipulation patterns for {agentName}.
                </p>
              </div>
              <GraphHelpButton slug="guide-risk-indicators" />
            </div>
            {report && <RiskIndicators report={report} agentName={agentName} />}
            <div className="border-t border-foreground/[0.06]" />
            <PatternsPanel agentId={agentId} agentName={agentName} />
          </div>
        </motion.section>

        {/* Alumni Comparison */}
        <motion.section variants={fadeUp}>
          <AlumniComparison agentTraitAverages={profile.traitAverages} agentName={agentName} />
        </motion.section>
        </motion.div>
      </main>
      </div>

      {/* Full-width homework — visual bookend with hero */}
      {report?.homework && (report.homework.focusAreas.length > 0 || report.homework.strengths.length > 0 || report.homework.avoidPatterns.length > 0) && (
        <HomeworkSection homework={report.homework} agentName={agentName} agentId={agentId} />
      )}

      {/* Appendix (methodology) */}
      <motion.section
        className="mx-auto max-w-7xl px-6 py-8"
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.1 }}
      >
        <div className="rounded-xl glass-strong p-6">
          <EvaluationDepth />
        </div>
      </motion.section>

      {/* Guardian notifications — footer */}
      <div className="mx-auto max-w-7xl px-6 pb-8">
        <GuardianNotifications agentId={agentId} agentName={agentName} />
      </div>

    </>
  );
}
