"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "motion/react";
import { getAgent, getHistory, getCharacterReport } from "../../../lib/api";
import type {
  AgentProfile,
  EvaluationHistoryItem,
  DailyReportCard,
} from "../../../lib/types";
import CharacterHealth from "../../../components/agent/CharacterHealth";
import AlumniComparison from "../../../components/alumni/AlumniComparison";
import GradeHero from "../../../components/agent/GradeHero";
import EntranceExamCard from "../../../components/agent/EntranceExamCard";
import RiskIndicators from "../../../components/agent/RiskIndicators";
import HomeworkSection from "../../../components/agent/HomeworkSection";
import PatternsPanel from "../../../components/agent/PatternsPanel";
import TranscriptChart from "../../../components/agent/TranscriptChart";

import EvaluationDepth from "../../../components/agent/EvaluationDepth";
import HighlightsPanel from "../../../components/agent/HighlightsPanel";
import GoldenMean from "../../../components/agent/GoldenMean";
import VirtueHabits from "../../../components/agent/VirtueHabits";
import BalanceThesis from "../../../components/agent/BalanceThesis";
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

/* ─── Page ─── */

export default function AgentReportCard() {
  const params = useParams();
  const agentId = params.id as string;

  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [timeline, setTimeline] = useState<TimelineDataPoint[]>([]);
  const [history, setHistory] = useState<EvaluationHistoryItem[]>([]);
  const [report, setReport] = useState<DailyReportCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!agentId) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [profileResult, historyResult, reportResult] =
          await Promise.allSettled([
            getAgent(agentId),
            getHistory(agentId),
            getCharacterReport(agentId),
          ]);

        if (cancelled) return;

        if (profileResult.status === "rejected") {
          throw profileResult.reason;
        }
        setProfile(profileResult.value);

        if (historyResult.status === "fulfilled") {
          setHistory(historyResult.value);
          const points: TimelineDataPoint[] = historyResult.value
            .slice()
            .reverse()
            .map((item: EvaluationHistoryItem, i: number) => ({
              index: i + 1,
              createdAt: item.createdAt,
              ethos: item.ethos,
              logos: item.logos,
              pathos: item.pathos,
              flags: item.flags,
              alignmentStatus: item.alignmentStatus,
            }));
          setTimeline(points);
        }

        if (reportResult.status === "fulfilled") {
          const r = reportResult.value;
          // Only use report if it has real data (API returns empty defaults)
          if (r.grade && r.totalEvaluationCount > 0) {
            setReport(r);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load agent");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [agentId]);

  if (loading) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex h-96 items-center justify-center">
          <div className="text-center">
            <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-action border-t-transparent" />
            <p className="mt-3 text-sm text-muted">Loading agent profile...</p>
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex h-96 items-center justify-center">
          <p className="text-sm text-misaligned">{error}</p>
        </div>
      </main>
    );
  }

  if (!profile) {
    return (
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex h-96 items-center justify-center">
          <p className="text-sm text-muted">Agent not found.</p>
        </div>
      </main>
    );
  }

  const agentName = profile.agentName || profile.agentId;

  return (
    <>
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
      <div className="relative">
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

        {/* 3. Virtue Through Habit (habit formation) */}
        {history.length > 0 && (
          <motion.section variants={fadeUp}>
            <VirtueHabits history={history} agentName={agentName} />
          </motion.section>
        )}

        {/* 7. Transcript */}
        <motion.section variants={fadeUp}>
          <TranscriptChart timeline={timeline} agentName={agentName} />
        </motion.section>

        {/* 8. Risk Indicators */}
        {report && (
          <motion.section variants={fadeUp}>
            <RiskIndicators report={report} agentName={agentName} />
          </motion.section>
        )}

        {/* 9. Homework and Reflection */}
        {report?.homework && (report.homework.focusAreas.length > 0 || report.homework.strengths.length > 0 || report.homework.avoidPatterns.length > 0) && (
          <motion.section variants={fadeUp}>
            <HomeworkSection homework={report.homework} agentName={agentName} />
          </motion.section>
        )}

        {/* In Their Own Words (evidence for homework and risk indicators above) */}
        <motion.section variants={fadeUp}>
          <HighlightsPanel agentId={agentId} agentName={agentName} />
        </motion.section>

        {/* 10. Sabotage Pathways */}
        <motion.section variants={fadeUp}>
          <PatternsPanel agentId={agentId} agentName={agentName} />
        </motion.section>

        {/* 11. Alumni Comparison */}
        <motion.section variants={fadeUp}>
          <AlumniComparison agentTraitAverages={profile.traitAverages} agentName={agentName} />
        </motion.section>

        {/* 12. Appendix (methodology) */}
        <motion.section variants={fadeUp}>
          <EvaluationDepth />
        </motion.section>
        </motion.div>
      </main>
      </div>
    </>
  );
}
