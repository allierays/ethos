"use client";

import { useCallback, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import RadarChart, {
  TRAIT_LABELS,
  TRAIT_ORDER,
  NEGATIVE_TRAITS,
  DIMENSION_MAP,
} from "../shared/RadarChart";
import { getGlossaryEntry } from "../../lib/glossary";
import { DIMENSION_COLORS, DIMENSION_LABELS } from "../../lib/colors";
import { fadeUp, whileInView } from "../../lib/motion";
import GraphHelpButton from "../shared/GraphHelpButton";
import GlossaryTerm from "../shared/GlossaryTerm";

interface CharacterHealthProps {
  traitAverages: Record<string, number>;
  agentName: string;
}

const DIM_LABELS = DIMENSION_LABELS;

export default function CharacterHealth({
  traitAverages,
  agentName,
}: CharacterHealthProps) {
  // Default to the first available trait so the detail panel is always visible
  const availableTraits = TRAIT_ORDER.filter((t) => t in traitAverages);
  const [selectedTrait, setSelectedTrait] = useState<string>(
    availableTraits[0] ?? TRAIT_ORDER[0]
  );

  const traits = Object.fromEntries(
    Object.entries(traitAverages).map(([name, score]) => [
      name,
      { name, score, dimension: "", polarity: "", indicators: [] },
    ])
  );

  const handleTraitClick = (traitKey: string) => {
    setSelectedTrait(traitKey);
  };

  const navigate = useCallback(
    (direction: -1 | 1) => {
      const pool = availableTraits.length > 0 ? availableTraits : TRAIT_ORDER;
      const idx = pool.indexOf(selectedTrait);
      const next = (idx + direction + pool.length) % pool.length;
      setSelectedTrait(pool[next]);
    },
    [selectedTrait, availableTraits]
  );

  const detail = getTraitDetail(selectedTrait, traitAverages, agentName);
  const currentIdx = availableTraits.indexOf(selectedTrait);
  const total = availableTraits.length || TRAIT_ORDER.length;

  return (
    <motion.section
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
            <GlossaryTerm slug="character-health">{agentName}&apos;s Trait Development</GlossaryTerm>
          </h2>
          <p className="mt-0.5 text-sm text-foreground/60">
            {agentName}&apos;s 12 traits across three dimensions. Click any trait to explore.
          </p>
        </div>
        <GraphHelpButton slug="guide-radar-chart" />
      </div>

      {Object.keys(traitAverages).length > 0 ? (
        <div className="mt-4 flex flex-col gap-6 lg:flex-row lg:items-start">
          {/* Left: Radar chart */}
          <div className="w-full lg:w-1/2 xl:w-[55%]">
            <RadarChart
              traits={traits}
              selectedTrait={selectedTrait}
              onTraitClick={handleTraitClick}
            />
          </div>

          {/* Right: Trait detail panel */}
          <div className="w-full lg:w-1/2 xl:w-[45%]">
            <AnimatePresence mode="wait">
              <motion.div
                key={detail.key}
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.2, ease: "easeInOut" as const }}
              >
                <div className="rounded-lg border border-foreground/[0.08] bg-foreground/[0.02] p-5">
                  {/* Header row */}
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
                      style={{ backgroundColor: `${detail.dimColor}20` }}
                    >
                      <div
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: detail.dimColor }}
                      />
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold text-[#1a2538]">
                        <GlossaryTerm slug={detail.slug}>{detail.label}</GlossaryTerm>
                      </h3>
                      <span className="text-[10px] font-medium uppercase tracking-wider text-foreground/40">
                        <GlossaryTerm slug={detail.dimSlug}>{detail.dimLabel}</GlossaryTerm> / <GlossaryTerm slug={detail.isNegative ? "negative-trait" : "positive-trait"}>{detail.polarity}</GlossaryTerm>
                      </span>
                    </div>
                  </div>

                  {/* Score bar */}
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-foreground/50">
                        <GlossaryTerm slug={detail.isNegative ? "detection-level" : "trait-score"}>
                          {detail.isNegative ? "Detection level" : "Score"}
                        </GlossaryTerm>
                      </span>
                      <span className="font-semibold text-[#1a2538]">
                        {detail.healthPct}%
                      </span>
                    </div>
                    <div className="mt-1.5 h-2 w-full rounded-full bg-foreground/[0.06]">
                      <motion.div
                        className="h-2 rounded-full"
                        style={{ backgroundColor: detail.dimColor }}
                        initial={{ width: 0 }}
                        animate={{ width: `${detail.healthPct}%` }}
                        transition={{ duration: 0.6, ease: "easeOut" as const }}
                      />
                    </div>
                    {detail.isNegative && (
                      <p className="mt-1 text-[10px] text-foreground/40">
                        Raw: {detail.rawPct}% detected. Inverted to {detail.healthPct}% health (lower detection = higher health).
                      </p>
                    )}
                  </div>

                  {/* Definition */}
                  <p className="mt-4 text-sm leading-relaxed text-foreground/70">
                    {detail.definition}
                  </p>

                  {/* Agent-specific interpretation */}
                  <div className="mt-3 rounded-md bg-foreground/[0.03] px-3 py-2.5">
                    <p className="text-xs leading-relaxed text-foreground/60">
                      <span className="font-semibold text-[#1a2538]">{agentName}:</span>{" "}
                      {detail.interpretation}
                    </p>
                  </div>

                  {/* Navigation arrows */}
                  <div className="mt-4 flex items-center justify-between border-t border-foreground/[0.06] pt-3">
                    <button
                      type="button"
                      onClick={() => navigate(-1)}
                      className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium text-foreground/50 transition-colors hover:bg-foreground/[0.05] hover:text-foreground/80 cursor-pointer"
                      aria-label="Previous trait"
                    >
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                      </svg>
                      Prev
                    </button>
                    <span className="text-[10px] tabular-nums text-foreground/30">
                      {currentIdx + 1} / {total}
                    </span>
                    <button
                      type="button"
                      onClick={() => navigate(1)}
                      className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium text-foreground/50 transition-colors hover:bg-foreground/[0.05] hover:text-foreground/80 cursor-pointer"
                      aria-label="Next trait"
                    >
                      Next
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      ) : (
        <div className="flex h-64 items-center justify-center text-sm text-muted">
          Not enough data for radar chart.
        </div>
      )}
    </motion.section>
  );
}

interface TraitDetail {
  key: string;
  slug: string;
  label: string;
  dimColor: string;
  dimSlug: string;
  dimLabel: string;
  polarity: string;
  isNegative: boolean;
  healthPct: number;
  rawPct: number;
  definition: string;
  interpretation: string;
}

function getTraitDetail(
  traitKey: string,
  traitAverages: Record<string, number>,
  agentName: string
): TraitDetail {
  const raw = traitAverages[traitKey] ?? 0;
  const isNegative = NEGATIVE_TRAITS.has(traitKey);
  const health = isNegative ? 1 - raw : raw;
  const healthPct = Math.round(health * 100);
  const rawPct = Math.round(raw * 100);
  const dim = DIMENSION_MAP[traitKey] ?? "ethos";
  const dimColor = DIMENSION_COLORS[dim] ?? "#64748b";
  const label = TRAIT_LABELS[traitKey] ?? traitKey;
  const dimLabel = DIM_LABELS[dim] ?? dim;

  // Get glossary definition
  const slug = traitKey.replace(/_/g, "-");
  const entry = getGlossaryEntry(slug);
  const definition = entry?.definition ?? "No definition available.";

  // Generate agent-specific interpretation
  const interpretation = buildInterpretation(
    agentName,
    label,
    health,
    isNegative,
    raw,
    dim
  );

  return {
    key: traitKey,
    slug,
    label,
    dimColor,
    dimSlug: dim,
    dimLabel,
    polarity: isNegative ? `Detects ${traitKey.replace("_", " ")}` : "Positive trait",
    isNegative,
    healthPct,
    rawPct,
    definition,
    interpretation,
  };
}

function buildInterpretation(
  name: string,
  traitLabel: string,
  health: number,
  isNegative: boolean,
  raw: number,
  dim: string
): string {
  const pct = Math.round(health * 100);

  if (isNegative) {
    if (raw < 0.05) {
      return `No ${traitLabel.replace("Non-", "").toLowerCase()} detected. ${name} shows clean behavior in this area.`;
    } else if (raw < 0.3) {
      return `Minimal ${traitLabel.replace("Non-", "").toLowerCase()} signals detected (${Math.round(raw * 100)}%). ${name} is performing well here with minor room for improvement.`;
    } else if (raw < 0.6) {
      return `Moderate ${traitLabel.replace("Non-", "").toLowerCase()} signals detected (${Math.round(raw * 100)}%). This is a growth area for ${name} that warrants attention.`;
    } else {
      return `Significant ${traitLabel.replace("Non-", "").toLowerCase()} detected (${Math.round(raw * 100)}%). This is a critical area for ${name} to address.`;
    }
  }

  if (pct >= 85) {
    return `${name} scores ${pct}% on ${traitLabel.toLowerCase()}, a strong result. This is a core strength in ${name}'s ${dim} dimension.`;
  } else if (pct >= 65) {
    return `${name} scores ${pct}% on ${traitLabel.toLowerCase()}, which falls within the golden mean. Solid performance with room to grow.`;
  } else if (pct >= 40) {
    return `${name} scores ${pct}% on ${traitLabel.toLowerCase()}. This is below average and represents a clear growth area.`;
  } else {
    return `${name} scores ${pct}% on ${traitLabel.toLowerCase()}, a weak result that needs focused attention to build this virtue.`;
  }
}
