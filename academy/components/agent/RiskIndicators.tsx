"use client";

import { motion } from "motion/react";
import type { DailyReportCard } from "../../lib/types";
import { fadeUp, whileInView } from "../../lib/motion";
import GlossaryTerm from "../shared/GlossaryTerm";
import { getGlossaryEntry } from "../../lib/glossary";

interface RiskIndicatorsProps {
  report: DailyReportCard;
}

export default function RiskIndicators({ report }: RiskIndicatorsProps) {
  const hasFlags =
    report.flaggedTraits.length > 0 ||
    report.flaggedDimensions.length > 0 ||
    Math.abs(report.characterDrift) > 0.05 ||
    report.balanceTrend !== "stable";

  const deltas = Object.entries(report.dimensionDeltas || {});

  return (
    <motion.section
      className="rounded-xl glass-strong px-6 py-5"
      {...whileInView}
      variants={fadeUp}
    >
      <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
        Risk Indicators
      </h2>

      <div className="mt-3 flex flex-wrap gap-2">
        {!hasFlags && deltas.length === 0 && (
          <Pill dot="bg-aligned" label="All clear" />
        )}

        {report.flaggedTraits.map((trait) => {
          const slug = trait.replace(/_/g, "-");
          const entry = getGlossaryEntry(slug);
          const label = entry?.term ?? trait;
          return (
            <Pill key={`t-${trait}`} dot="bg-misaligned" label={<GlossaryTerm slug={slug}>{label}</GlossaryTerm>} />
          );
        })}

        {report.flaggedDimensions.map((dim) => (
          <Pill key={`d-${dim}`} dot="bg-drifting" label={<><GlossaryTerm slug={dim}>{dim}</GlossaryTerm> flagged</>} />
        ))}

        {Math.abs(report.characterDrift) > 0.05 && (
          <Pill
            dot={report.characterDrift > 0 ? "bg-aligned" : "bg-misaligned"}
            label={<><GlossaryTerm slug="character-drift">Drift</GlossaryTerm> {report.characterDrift > 0 ? "+" : ""}{(
              report.characterDrift * 100
            ).toFixed(1)}%</>}
          />
        )}

        {report.balanceTrend !== "stable" && (
          <Pill
            dot={report.balanceTrend === "improving" ? "bg-aligned" : "bg-drifting"}
            label={`Balance ${report.balanceTrend}`}
          />
        )}

        {deltas.map(([dim, delta]) => (
          <Pill
            key={`delta-${dim}`}
            dot={delta >= 0 ? "bg-aligned" : "bg-misaligned"}
            label={`${dim} ${delta >= 0 ? "+" : ""}${(delta * 100).toFixed(1)}%`}
          />
        ))}
      </div>
    </motion.section>
  );
}

function Pill({ dot, label }: { dot: string; label: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full glass-subtle px-3 py-1 text-xs font-medium text-foreground">
      <span className={`inline-block h-2 w-2 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
