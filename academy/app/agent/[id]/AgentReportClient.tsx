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
import PatternsPanel from "../../../components/agent/PatternsPanel";
import TranscriptChart from "../../../components/agent/TranscriptChart";
import ConstitutionalTrail from "../../../components/agent/ConstitutionalTrail";
import HighlightsPanel from "../../../components/agent/HighlightsPanel";
import GoldenMean from "../../../components/agent/GoldenMean";
import BalanceThesis from "../../../components/agent/BalanceThesis";
import GlossaryTerm from "../../../components/shared/GlossaryTerm";
import GraphHelpButton from "../../../components/shared/GraphHelpButton";
import TableOfContents from "../../../components/shared/TableOfContents";
import { useScrollSpy } from "../../../lib/useScrollSpy";
import { fadeUp, staggerContainer } from "../../../lib/motion";
import { exportReportCard } from "../../../lib/export-markdown";

const REPORT_TOC_SECTIONS = [
  { id: "traits", label: "Traits" },
  { id: "balance", label: "Balance" },
  { id: "highlights", label: "Highlights" },
  { id: "transcript", label: "Transcript" },
  { id: "constitutional-trail", label: "Constitution" },
  { id: "risk", label: "Risk" },
  { id: "alumni", label: "Alumni" },
  { id: "whats-next", label: "What's Next" },
];

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
  const sectionIds = useMemo(() => REPORT_TOC_SECTIONS.map((s) => s.id), []);
  const activeSection = useScrollSpy(sectionIds);

  return (
    <>
      <h1 className="sr-only">{agentName} Report Card</h1>

      {/* Full-width hero banner */}
      <GradeHero profile={profile} report={report} timeline={timeline} />

      {/* Decorative blobs */}
      <div className="relative">
        <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden" aria-hidden="true">
          <div className="absolute -top-40 -left-40 h-[500px] w-[500px] rounded-full bg-ethos-200/30 blur-3xl" />
          <div className="absolute top-1/3 -right-32 h-[400px] w-[400px] rounded-full bg-logos-200/20 blur-3xl" />
          <div className="absolute bottom-1/4 left-1/4 h-[350px] w-[350px] rounded-full bg-pathos-200/25 blur-3xl" />
        </div>
      <main className="relative mx-auto max-w-7xl px-6 py-8 lg:grid lg:grid-cols-[180px_1fr] lg:gap-10">
        {/* Sticky sidebar TOC (desktop) */}
        <aside className="hidden lg:block">
          <nav className="sticky top-20">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-foreground/40 mb-3">
              On this page
            </p>
            <ul className="space-y-1">
              {REPORT_TOC_SECTIONS.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    onClick={() => {
                      const el = document.getElementById(s.id);
                      el?.scrollIntoView({ behavior: "smooth", block: "start" });
                    }}
                    className={`block w-full text-left text-[13px] py-1 pl-3 border-l-2 transition-colors ${
                      activeSection === s.id
                        ? "border-action text-foreground font-semibold"
                        : "border-transparent text-foreground/50 hover:text-foreground/80 hover:border-foreground/20"
                    }`}
                  >
                    {s.label}
                  </button>
                </li>
              ))}
            </ul>
            <div className="mt-6 border-t border-border pt-4">
              <button
                onClick={() => exportReportCard(profile, report, history)}
                className="inline-flex items-center gap-1.5 text-xs font-medium text-foreground/50 transition-colors hover:text-foreground"
              >
                <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Export Markdown
              </button>
            </div>
          </nav>
        </aside>

        {/* Mobile horizontal TOC */}
        <div className="lg:hidden">
          <TableOfContents sections={REPORT_TOC_SECTIONS} />
        </div>

        {/* Content */}
        <motion.div
          className="min-w-0 space-y-8"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {/* 1. Trait Development (interactive radar + detail) */}
        <motion.section id="traits" variants={fadeUp}>
          <CharacterHealth
            traitAverages={profile.traitAverages}
            agentName={agentName}
          />
        </motion.section>

        {/* 2. Aristotelian Thesis + Golden Mean (side by side) */}
        <motion.section id="balance" variants={fadeUp} className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <BalanceThesis
            dimensionAverages={profile.dimensionAverages}
            evaluationCount={profile.evaluationCount}
            agentName={agentName}
          />
          <GoldenMean traitAverages={profile.traitAverages} agentName={agentName} />
        </motion.section>

        {/* In their own words (exemplary and flagged messages) */}
        <motion.section id="highlights" variants={fadeUp}>
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
                <p className="mt-0.5 text-sm text-foreground/80">
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
        <motion.section id="alumni" variants={fadeUp}>
          <AlumniComparison agentTraitAverages={profile.traitAverages} agentName={agentName} />
        </motion.section>
        </motion.div>
      </main>
      </div>

      {/* What's next CTA cards + notifications — always visible */}
      <div id="whats-next" />
      <EntranceExamCard
        agentId={agentId}
        agentName={agentName}
        enrolled={profile.enrolled}
        homework={report?.homework}
      />

    </>
  );
}
