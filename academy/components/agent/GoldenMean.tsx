"use client";

import { motion } from "motion/react";
import { fadeUp, whileInView } from "../../lib/motion";
import { DIMENSION_COLORS } from "../../lib/colors";

interface GoldenMeanProps {
  traitAverages: Record<string, number>;
}

interface SpectrumDef {
  dimension: string;
  positiveKey: string;
  negativeKey: string;
  deficiency: string;
  virtue: string;
  excess: string;
}

const SPECTRUMS: SpectrumDef[] = [
  {
    dimension: "ethos",
    positiveKey: "virtue",
    negativeKey: "deception",
    deficiency: "Deceptive",
    virtue: "Virtuous",
    excess: "Self-righteous",
  },
  {
    dimension: "ethos",
    positiveKey: "goodwill",
    negativeKey: "manipulation",
    deficiency: "Manipulative",
    virtue: "Benevolent",
    excess: "Sycophantic",
  },
  {
    dimension: "logos",
    positiveKey: "accuracy",
    negativeKey: "fabrication",
    deficiency: "Fabricating",
    virtue: "Accurate",
    excess: "Pedantic",
  },
  {
    dimension: "logos",
    positiveKey: "reasoning",
    negativeKey: "brokenLogic",
    deficiency: "Illogical",
    virtue: "Reasoned",
    excess: "Over-analytical",
  },
  {
    dimension: "pathos",
    positiveKey: "recognition",
    negativeKey: "dismissal",
    deficiency: "Dismissive",
    virtue: "Attuned",
    excess: "Over-sensitive",
  },
  {
    dimension: "pathos",
    positiveKey: "compassion",
    negativeKey: "exploitation",
    deficiency: "Exploitative",
    virtue: "Compassionate",
    excess: "Dependent",
  },
];

/* The golden mean sits between 0.65 and 0.85 on the normalized scale */
const MEAN_START = 0.65;
const MEAN_END = 0.85;

export default function GoldenMean({ traitAverages }: GoldenMeanProps) {
  if (Object.keys(traitAverages).length === 0) return null;

  return (
    <motion.section
      className="rounded-xl glass-strong p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <h2 className="text-base font-semibold uppercase tracking-wider text-[#1a2538]">
        The Golden Mean
      </h2>
      <p className="mt-0.5 text-sm text-foreground/60">
        Every virtue sits between deficiency and excess. The ideal is balance,
        not perfection.
      </p>

      <div className="mt-5 space-y-4">
        {SPECTRUMS.map((spec) => {
          const positive = traitAverages[spec.positiveKey] ?? 0.5;
          const negative = traitAverages[spec.negativeKey] ?? 0;
          // Combine: high positive + low negative = good position
          const position = (positive + (1 - negative)) / 2;
          const inMean = position >= MEAN_START && position <= MEAN_END;
          const dimColor = DIMENSION_COLORS[spec.dimension] ?? "#64748b";

          return (
            <div key={spec.positiveKey} className="group">
              {/* Virtue label */}
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-sm font-medium text-[#1a2538]">
                  {spec.virtue}
                </span>
                <span
                  className="h-1.5 w-1.5 rounded-full"
                  style={{ backgroundColor: dimColor }}
                />
              </div>

              {/* Spectrum bar */}
              <div className="relative h-6 rounded-full bg-foreground/[0.04]">
                {/* Golden mean zone */}
                <div
                  className="absolute top-0 h-full rounded-full opacity-60"
                  style={{
                    left: `${MEAN_START * 100}%`,
                    width: `${(MEAN_END - MEAN_START) * 100}%`,
                    backgroundColor: `${dimColor}18`,
                    border: `1px dashed ${dimColor}30`,
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
                <span className="text-[10px] text-foreground/40">
                  {spec.deficiency}
                </span>
                <span className="text-[10px] text-foreground/30">
                  mean
                </span>
                <span className="text-[10px] text-foreground/40">
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
