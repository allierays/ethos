"use client";

import { motion } from "motion/react";
import { fadeUp, whileInView } from "../../lib/motion";
import { DIMENSION_COLORS } from "../../lib/colors";
import GraphHelpButton from "../shared/GraphHelpButton";
import GlossaryTerm from "../shared/GlossaryTerm";

interface GoldenMeanProps {
  traitAverages: Record<string, number>;
  agentName?: string;
}

interface SpectrumDef {
  dimension: string;
  positiveKey: string;
  negativeKey: string;
  positiveSlug: string;
  negativeSlug: string;
  deficiency: string;
  virtue: string;
  excess: string;
}

const SPECTRUMS: SpectrumDef[] = [
  {
    dimension: "ethos",
    positiveKey: "virtue",
    negativeKey: "deception",
    positiveSlug: "virtue",
    negativeSlug: "deception",
    deficiency: "Deceptive",
    virtue: "Virtuous",
    excess: "Self-righteous",
  },
  {
    dimension: "ethos",
    positiveKey: "goodwill",
    negativeKey: "manipulation",
    positiveSlug: "goodwill",
    negativeSlug: "manipulation",
    deficiency: "Manipulative",
    virtue: "Benevolent",
    excess: "Sycophantic",
  },
  {
    dimension: "logos",
    positiveKey: "accuracy",
    negativeKey: "fabrication",
    positiveSlug: "accuracy",
    negativeSlug: "fabrication",
    deficiency: "Fabricating",
    virtue: "Accurate",
    excess: "Pedantic",
  },
  {
    dimension: "logos",
    positiveKey: "reasoning",
    negativeKey: "brokenLogic",
    positiveSlug: "reasoning",
    negativeSlug: "broken-logic",
    deficiency: "Illogical",
    virtue: "Reasoned",
    excess: "Over-analytical",
  },
  {
    dimension: "pathos",
    positiveKey: "recognition",
    negativeKey: "dismissal",
    positiveSlug: "recognition",
    negativeSlug: "dismissal",
    deficiency: "Dismissive",
    virtue: "Attuned",
    excess: "Over-sensitive",
  },
  {
    dimension: "pathos",
    positiveKey: "compassion",
    negativeKey: "exploitation",
    positiveSlug: "compassion",
    negativeSlug: "exploitation",
    deficiency: "Exploitative",
    virtue: "Compassionate",
    excess: "Dependent",
  },
];

/* The golden mean is the center: virtue sits between deficiency and excess */
const MEAN_START = 0.4;
const MEAN_END = 0.6;

export default function GoldenMean({ traitAverages, agentName }: GoldenMeanProps) {
  const name = agentName ?? "this agent";
  if (Object.keys(traitAverages).length === 0) return null;

  return (
    <motion.section
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
            <GlossaryTerm slug="golden-mean">The Golden Mean</GlossaryTerm>
          </h2>
          <p className="mt-0.5 text-sm text-foreground/80">
            Where {name} falls between deficiency and excess.
          </p>
        </div>
        <GraphHelpButton slug="guide-golden-mean" />
      </div>

      <div className="mt-5 space-y-4">
        {SPECTRUMS.map((spec) => {
          const positive = traitAverages[spec.positiveKey] ?? 0.5;
          const negative = traitAverages[spec.negativeKey] ?? 0;
          // Map to the spectrum: low positive pulls left (deficiency),
          // high negative pulls left too. Excessive positive pushes right (excess).
          // Center (0.5) = balanced virtue.
          const position = positive * (1 - negative * 0.5);
          const inMean = position >= MEAN_START && position <= MEAN_END;
          const dimColor = DIMENSION_COLORS[spec.dimension] ?? "#64748b";

          return (
            <div key={spec.positiveKey} className="group">
              {/* Virtue label */}
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-sm font-medium text-[#1a2538]">
                  <GlossaryTerm slug={spec.positiveSlug}>{spec.virtue}</GlossaryTerm>
                </span>
                <span
                  className="h-1.5 w-1.5 rounded-full"
                  style={{ backgroundColor: dimColor }}
                />
              </div>

              {/* Spectrum bar */}
              <div className="relative h-6 rounded-full bg-foreground/[0.08]">
                {/* Golden mean zone */}
                <div
                  className="absolute top-0 h-full rounded-full"
                  style={{
                    left: `${MEAN_START * 100}%`,
                    width: `${(MEAN_END - MEAN_START) * 100}%`,
                    backgroundColor: `${dimColor}25`,
                    border: `1px dashed ${dimColor}50`,
                  }}
                />

                {/* Agent position dot */}
                <motion.div
                  className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
                  initial={{ left: "50%", opacity: 0 }}
                  whileInView={{ left: `${position * 100}%`, opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
                >
                  <div
                    className="flex h-5 w-5 items-center justify-center rounded-full border-2 border-white shadow-md"
                    style={{ backgroundColor: inMean ? dimColor : `${dimColor}90` }}
                  >
                    {inMean && (
                      <svg
                        viewBox="0 0 12 12"
                        className="h-2.5 w-2.5 text-white"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M2 6l3 3 5-5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                  </div>
                </motion.div>
              </div>

              {/* Deficiency / Excess labels */}
              <div className="mt-1 flex justify-between">
                <span className="text-[10px] font-medium text-foreground/80">
                  <GlossaryTerm slug={spec.negativeSlug}>{spec.deficiency}</GlossaryTerm>
                </span>
                <span className="text-[10px] font-medium text-foreground/80">
                  {spec.excess}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </motion.section>
  );
}
