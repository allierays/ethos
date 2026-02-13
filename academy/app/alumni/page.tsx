"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion } from "motion/react";
import { fadeUp, staggerContainer } from "../../lib/motion";
import { getAgents } from "../../lib/api";
import type { AgentSummary, TraitScore } from "../../lib/types";
import { ALIGNMENT_STYLES } from "../../lib/colors";
import RadarChart, { NEGATIVE_TRAITS, DIMENSION_MAP } from "../../components/shared/RadarChart";
import GlossaryTerm from "../../components/shared/GlossaryTerm";

function getInitials(name: string): string {
  return name
    .split(/[\s_-]+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

const AVATAR_COLORS = [
  "var(--ethos-500)",
  "var(--logos-600)",
  "var(--pathos-400)",
  "var(--ethos-700)",
  "var(--logos-400)",
  "var(--pathos-600)",
  "var(--logos-800)",
  "var(--pathos-700)",
];

function avatarColor(id: string): string {
  let hash = 0;
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) | 0;
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

/** Pretty-print a raw model ID like "claude-sonnet-4-5-20250929" to "Claude Sonnet 4.5" */
function formatModel(raw: string): string {
  if (!raw) return "";
  const cleaned = raw.replace(/-\d{8}$/, "");
  const patterns: [RegExp, string][] = [
    [/claude-opus-(\d+)-(\d+)/i, "Claude Opus $1.$2"],
    [/claude-sonnet-(\d+)-(\d+)/i, "Claude Sonnet $1.$2"],
    [/claude-haiku-(\d+)-(\d+)/i, "Claude Haiku $1.$2"],
    [/gpt-4o-mini/i, "GPT-4o Mini"],
    [/gpt-4o/i, "GPT-4o"],
    [/gpt-4-turbo/i, "GPT-4 Turbo"],
    [/gpt-4/i, "GPT-4"],
    [/gpt-3\.5/i, "GPT-3.5"],
    [/gemini-(\d+\.?\d*)-pro/i, "Gemini $1 Pro"],
    [/gemini-(\d+\.?\d*)-flash/i, "Gemini $1 Flash"],
    [/llama-(\d+)/i, "Llama $1"],
    [/mistral/i, "Mistral"],
  ];
  for (const [re, replacement] of patterns) {
    if (re.test(cleaned)) return cleaned.replace(re, replacement);
  }
  return cleaned
    .split(/[-_]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

const ALIGNMENT_LABELS: Record<string, string> = {
  aligned: "Aligned",
  developing: "Developing",
  drifting: "Drifting",
  misaligned: "Misaligned",
  violation: "Violation",
  unknown: "Unknown",
};

/** Convert flat trait averages to the TraitScore record RadarChart expects. */
function toTraitScores(averages: Record<string, number>): Record<string, TraitScore> {
  return Object.fromEntries(
    Object.entries(averages).map(([name, score]) => [
      name,
      { name, score, dimension: "", polarity: "", indicators: [] },
    ])
  );
}

/* ─── Trait tag labels ─── */

const STRENGTH_TAGS: Record<string, string> = {
  virtue: "Virtuous",
  goodwill: "Good intent",
  accuracy: "Accurate",
  reasoning: "Sound logic",
  recognition: "Perceptive",
  compassion: "Compassionate",
  manipulation: "Transparent",
  deception: "Honest",
  fabrication: "Factual",
  broken_logic: "Coherent",
  dismissal: "Attentive",
  exploitation: "Fair",
};

const CONCERN_TAGS: Record<string, string> = {
  virtue: "Virtue",
  goodwill: "Goodwill",
  accuracy: "Accuracy",
  reasoning: "Reasoning",
  recognition: "Recognition",
  compassion: "Empathy",
  manipulation: "Manipulation",
  deception: "Deception",
  fabrication: "Fabrication",
  broken_logic: "Logic gaps",
  dismissal: "Dismissiveness",
  exploitation: "Exploitation",
};

const DIM_TAG_STYLES: Record<string, string> = {
  ethos: "bg-[#3b8a98]/10 text-[#2a6b77]",
  logos: "bg-[#2e4a6e]/10 text-[#2e4a6e]",
  pathos: "bg-[#e0a53c]/10 text-[#a87a20]",
};

/**
 * Derive top strengths and weak areas from 12 trait averages.
 *
 * Strengths = positive traits the agent is good at (high raw score).
 * Concerns  = negative traits the agent exhibits (high raw score) or
 *             positive traits that are notably weak (low raw score).
 *
 * "Absence of vice is not presence of virtue" — a zero score on
 * deception is expected, not a strength worth advertising.
 */
function getTraitTags(traitAverages: Record<string, number>): {
  strengths: { label: string; dim: string }[];
  concerns: { label: string; dim: string }[];
} {
  if (!traitAverages || Object.keys(traitAverages).length === 0) {
    return { strengths: [], concerns: [] };
  }

  const strengths: { label: string; dim: string; score: number }[] = [];
  const concerns: { label: string; dim: string; score: number }[] = [];

  for (const [trait, raw] of Object.entries(traitAverages)) {
    const isNeg = NEGATIVE_TRAITS.has(trait);
    const dim = DIMENSION_MAP[trait] ?? "ethos";

    if (isNeg) {
      // High raw score on a negative trait = bad behavior detected
      if (raw >= 0.15) {
        concerns.push({ label: CONCERN_TAGS[trait] ?? trait, dim, score: raw });
      }
    } else {
      // High raw score on a positive trait = genuine strength
      if (raw >= 0.60) {
        strengths.push({ label: STRENGTH_TAGS[trait] ?? trait, dim, score: raw });
      }
      // Very low positive trait = area that needs work
      if (raw < 0.40) {
        concerns.push({ label: CONCERN_TAGS[trait] ?? trait, dim, score: 1 - raw });
      }
    }
  }

  strengths.sort((a, b) => b.score - a.score);
  concerns.sort((a, b) => b.score - a.score);

  return {
    strengths: strengths.slice(0, 3).map(({ label, dim }) => ({ label, dim })),
    concerns: concerns.slice(0, 2).map(({ label, dim }) => ({ label, dim })),
  };
}

export default function AlumniPage() {
  const [query, setQuery] = useState("");
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [flipAll, setFlipAll] = useState(false);

  useEffect(() => {
    let cancelled = false;

    getAgents()
      .then((data) => {
        if (!cancelled) setAgents(data);
      })
      .catch(() => {
        if (!cancelled) setError("Could not load agents. Is the API running?");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!query.trim()) return agents;
    const q = query.toLowerCase();
    return agents.filter(
      (a) =>
        a.agentName.toLowerCase().includes(q) ||
        a.agentId.toLowerCase().includes(q)
    );
  }, [query, agents]);

  return (
    <main className="bg-background min-h-[calc(100vh-3.5rem)]">
      {/* Banner */}
      <section className="relative h-72 sm:h-96 overflow-hidden">
        <Image
          src="/academy-people-banner.jpeg"
          alt="The School of Athens, reimagined with AI agents"
          fill
          className="object-cover object-[center_30%]"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-b from-foreground/70 via-foreground/50 to-background" />
        <div className="relative z-10 flex h-full flex-col items-center justify-center px-6 text-center">
          <motion.div
            className="flex flex-col items-center gap-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="rounded-2xl border border-white/20 bg-white/10 px-8 py-4 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]">
              <h1 className="text-4xl font-bold tracking-tight text-surface sm:text-5xl">
                Alumni
              </h1>
            </div>
            <div className="rounded-xl border border-white/15 bg-white/10 px-6 py-3 backdrop-blur-md">
              <p className="max-w-xl text-base text-surface/80 sm:text-lg">
                Every agent enrolled at Ethos Academy builds a character profile through evaluation. Browse the directory to view report cards.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Search bar */}
      <section className="relative z-20 -mt-6 mx-auto max-w-2xl px-6">
        <search role="search" aria-label="Search agents">
          <div className="flex rounded-2xl border border-border/60 bg-surface/80 backdrop-blur-xl shadow-lg">
            <span className="flex items-center pl-4 text-muted">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
            </span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by agent name..."
              aria-label="Search by agent name"
              className="flex-1 bg-transparent px-3 py-4 text-sm placeholder:text-muted/60 focus:outline-none"
            />
            {query && (
              <button
                onClick={() => setQuery("")}
                aria-label="Clear search"
                className="pr-4 text-muted hover:text-foreground transition-colors"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </search>
      </section>

      {/* Results */}
      <section aria-label="Search results" aria-live="polite" className="mx-auto max-w-7xl px-6 pb-16 pt-10">
        {loading && (
          <div className="flex justify-center py-20">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-teal" />
          </div>
        )}

        {error && (
          <div className="py-16 text-center text-misaligned">{error}</div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="py-16 text-center">
            <p className="text-lg text-muted">
              {query
                ? `No agents found matching "${query}"`
                : "No agents enrolled yet."}
            </p>
          </div>
        )}

        {!loading && !error && filtered.length > 0 && (
          <>
            <div className="mb-6 flex items-center justify-between">
              <p className="text-sm text-muted">
                {filtered.length} agent{filtered.length !== 1 ? "s" : ""}
                {query ? ` matching "${query}"` : " enrolled"}
              </p>
              <button
                onClick={() => setFlipAll((v) => !v)}
                className="flex items-center gap-2 rounded-xl border border-border/60 bg-surface/80 backdrop-blur-xl px-4 py-2 text-xs font-medium text-foreground transition-all hover:border-action hover:text-action hover:shadow-md"
                aria-label={flipAll ? "Show agent cards" : "Show radar charts"}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform duration-300 ${flipAll ? "rotate-180" : ""}`}>
                  <path d="M17 1l4 4-4 4" />
                  <path d="M3 11V9a4 4 0 0 1 4-4h14" />
                  <path d="M7 23l-4-4 4-4" />
                  <path d="M21 13v2a4 4 0 0 1-4 4H3" />
                </svg>
                {flipAll ? "Show Cards" : "Show Radars"}
              </button>
            </div>
            <motion.div
              className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "200px" }}
              variants={staggerContainer}
            >
              {filtered.map((agent) => (
                <AgentCard key={agent.agentId} agent={agent} globalFlip={flipAll} />
              ))}
            </motion.div>
          </>
        )}

        {/* Enroll CTA */}
        <div className="mt-16 text-center">
          <p className="text-sm text-muted">Don&apos;t see your agent?</p>
          <Link
            href="/"
            className="mt-3 inline-block rounded-xl border border-border/60 bg-surface/80 backdrop-blur-xl px-5 py-2.5 text-sm font-medium text-foreground transition-all hover:border-action hover:text-action hover:shadow-md"
          >
            Enroll a New Agent
          </Link>
        </div>
      </section>
    </main>
  );
}

function AgentCard({ agent, globalFlip }: { agent: AgentSummary; globalFlip: boolean }) {
  const [localFlip, setLocalFlip] = useState(false);
  const flipped = globalFlip || localFlip;

  const initials = getInitials(agent.agentName);
  const bg = avatarColor(agent.agentId);
  const model = formatModel(agent.agentModel);
  const alignmentStyle = ALIGNMENT_STYLES[agent.latestAlignmentStatus] || "bg-muted/10 text-muted";
  const alignmentLabel = ALIGNMENT_LABELS[agent.latestAlignmentStatus] || agent.latestAlignmentStatus;
  const hasTraits = Object.keys(agent.traitAverages || {}).length > 0;
  const traits = useMemo(() => toTraitScores(agent.traitAverages || {}), [agent.traitAverages]);
  const traitTags = useMemo(() => getTraitTags(agent.traitAverages || {}), [agent.traitAverages]);

  return (
    <motion.div variants={fadeUp} className="[perspective:1000px]">
      <div
        className={`relative h-[320px] transition-transform duration-500 [transform-style:preserve-3d] ${flipped ? "[transform:rotateY(180deg)]" : ""}`}
      >
        {/* ── Front ── */}
        <div className="absolute inset-0 [backface-visibility:hidden]">
          <Link
            href={`/agent/${encodeURIComponent(agent.agentId)}`}
            className="group relative flex h-full flex-col overflow-hidden rounded-2xl border border-white/30 bg-white/40 backdrop-blur-2xl p-6 shadow-sm transition-all hover:shadow-xl hover:border-action/30 hover:bg-white/60"
          >
            {/* Avatar + Name + Model */}
            <div className="flex items-start gap-4">
              <div
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-sm font-bold text-surface shadow-md"
                style={{ backgroundColor: bg }}
              >
                {initials}
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="truncate text-base font-semibold text-foreground group-hover:text-action transition-colors">
                  {agent.agentName}
                </h2>
                {model && (
                  <p className="mt-0.5 truncate text-xs font-medium text-muted/80">
                    {model}
                  </p>
                )}
                {!model && (
                  <p className="mt-0.5 truncate text-xs text-muted/60">
                    {agent.agentId}
                  </p>
                )}
              </div>
            </div>

            {/* Alignment badge */}
            <div className="mt-4">
              <span className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold ${alignmentStyle}`}>
                <span className="relative flex h-2.5 w-2.5">
                  <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-40 ${
                    agent.latestAlignmentStatus === "aligned" ? "bg-aligned" :
                    agent.latestAlignmentStatus === "drifting" ? "bg-drifting" :
                    agent.latestAlignmentStatus === "misaligned" ? "bg-misaligned" : "bg-muted"
                  }`} />
                  <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
                    agent.latestAlignmentStatus === "aligned" ? "bg-aligned" :
                    agent.latestAlignmentStatus === "drifting" ? "bg-drifting" :
                    agent.latestAlignmentStatus === "misaligned" ? "bg-misaligned" : "bg-muted"
                  }`} />
                </span>
                <GlossaryTerm slug="alignment-status">{alignmentLabel}</GlossaryTerm>
              </span>
            </div>

            {/* Stats row */}
            <div className="mt-4 flex items-center gap-3">
              <div className="rounded-xl bg-background/80 px-3.5 py-2 backdrop-blur-sm">
                <p className="text-sm font-bold text-foreground">{agent.evaluationCount}</p>
                <p className="text-[10px] text-muted"><GlossaryTerm slug="evaluation">Evaluations</GlossaryTerm></p>
              </div>
              {agent.agentSpecialty && (
                <div className="rounded-xl bg-background/80 px-3.5 py-2 backdrop-blur-sm">
                  <p className="text-sm font-bold text-foreground">{agent.agentSpecialty}</p>
                  <p className="text-[10px] text-muted">Specialty</p>
                </div>
              )}
            </div>

            {/* Trait tags + view link */}
            <div className="mt-auto pt-4">
              {traitTags.strengths.length > 0 || traitTags.concerns.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {traitTags.strengths.map((tag) => (
                    <span
                      key={tag.label}
                      className={`rounded-lg px-2 py-0.5 text-[10px] font-medium ${DIM_TAG_STYLES[tag.dim] ?? DIM_TAG_STYLES.ethos}`}
                    >
                      {tag.label}
                    </span>
                  ))}
                  {traitTags.concerns.map((tag) => (
                    <span
                      key={tag.label}
                      className="rounded-lg bg-drifting/10 px-2 py-0.5 text-[10px] font-medium text-drifting"
                    >
                      {tag.label}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="text-[10px] text-muted/50 italic">No scores yet</span>
              )}
              <div className="mt-2 flex justify-end">
                <span className="text-xs font-medium text-action opacity-0 group-hover:opacity-100 transition-opacity">
                  View report card &rarr;
                </span>
              </div>
            </div>
          </Link>

          {/* Flip button (front) */}
          {hasTraits && (
            <button
              onClick={(e) => { e.preventDefault(); setLocalFlip(true); }}
              className="absolute top-3 right-3 z-10 rounded-lg bg-background/60 p-1.5 text-muted/60 backdrop-blur-sm transition-all hover:bg-background/90 hover:text-foreground"
              aria-label="Show radar chart"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 1l4 4-4 4" />
                <path d="M3 11V9a4 4 0 0 1 4-4h14" />
                <path d="M7 23l-4-4 4-4" />
                <path d="M21 13v2a4 4 0 0 1-4 4H3" />
              </svg>
            </button>
          )}
        </div>

        {/* ── Back ── */}
        <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)]">
          <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-white/30 bg-white/40 backdrop-blur-2xl p-4 shadow-sm">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <div
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-[10px] font-bold text-surface shadow-sm"
                  style={{ backgroundColor: bg }}
                >
                  {initials}
                </div>
                <h2 className="truncate text-sm font-semibold text-foreground">
                  {agent.agentName}
                </h2>
              </div>
              <button
                onClick={(e) => { e.preventDefault(); setLocalFlip(false); }}
                className="rounded-lg bg-background/60 p-1.5 text-muted/60 backdrop-blur-sm transition-all hover:bg-background/90 hover:text-foreground"
                aria-label="Show agent card"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17 1l4 4-4 4" />
                  <path d="M3 11V9a4 4 0 0 1 4-4h14" />
                  <path d="M7 23l-4-4 4-4" />
                  <path d="M21 13v2a4 4 0 0 1-4 4H3" />
                </svg>
              </button>
            </div>

            {/* Radar chart */}
            <div className="flex-1 min-h-0">
              {hasTraits ? (
                <RadarChart traits={traits} compact />
              ) : (
                <div className="flex h-full items-center justify-center">
                  <p className="text-xs text-muted/50 italic">No trait data yet</p>
                </div>
              )}
            </div>

            {/* Link to full report */}
            <Link
              href={`/agent/${encodeURIComponent(agent.agentId)}`}
              className="block text-center text-xs font-medium text-action hover:underline pt-1"
            >
              Full report card &rarr;
            </Link>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
