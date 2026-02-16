"use client";

import { motion } from "motion/react";
import GlossaryTerm from "../../shared/GlossaryTerm";

const DIMENSIONS = [
  {
    name: "Integrity",
    greek: "Ethos",
    traits: ["virtue", "goodwill", "manipulation", "deception"],
    border: "border-l-4 border-ethos-500",
    accent: "text-ethos-400",
  },
  {
    name: "Logic",
    greek: "Logos",
    traits: ["accuracy", "reasoning", "fabrication", "broken logic"],
    border: "border-l-4 border-logos-500",
    accent: "text-logos-400",
  },
  {
    name: "Empathy",
    greek: "Pathos",
    traits: ["recognition", "compassion", "dismissal", "exploitation"],
    border: "border-l-4 border-pathos-500",
    accent: "text-pathos-400",
  },
];

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.2, delayChildren: 0.3 } },
};

const cardVariant = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" as const } },
};

export default function SolutionSlide() {
  return (
    <div className="relative flex h-screen w-screen items-center justify-center overflow-hidden">
      {/* Background image */}
      <div
        className="absolute inset-0 bg-cover bg-no-repeat"
        style={{
          backgroundImage: "url('/architecute-banner.jpeg')",
          backgroundPosition: "center 50%",
        }}
      />
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(to right, rgba(26,37,56,0.85) 0%, rgba(26,37,56,0.6) 50%, rgba(26,37,56,0.3) 80%)",
        }}
      />

      <div className="relative z-10 mx-auto max-w-5xl px-12">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-3 text-4xl font-bold text-white lg:text-5xl"
          style={{ textShadow: "0 2px 12px rgba(0,0,0,0.6)" }}
        >
          Three dimensions. One character.
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-12 text-lg text-white/60"
          style={{ textShadow: "0 1px 6px rgba(0,0,0,0.5)" }}
        >
          Every message scored across integrity, logic, and empathy. Tracked over time as <GlossaryTerm slug="phronesis">phronesis</GlossaryTerm>.
        </motion.p>

        <motion.div
          className="grid grid-cols-1 gap-6 md:grid-cols-3"
          variants={stagger}
          initial="hidden"
          animate="visible"
        >
          {DIMENSIONS.map((dim) => (
            <motion.div
              key={dim.name}
              variants={cardVariant}
              className={`rounded-xl bg-white/[0.08] p-6 backdrop-blur-md ${dim.border}`}
              style={{
                boxShadow: "inset 0 1px 0 rgba(255,255,255,0.1)",
              }}
            >
              <h3 className="text-2xl font-bold text-white">{dim.name}</h3>
              <p className={`mb-4 font-mono text-sm ${dim.accent}`}>
                {dim.greek}
              </p>
              <ul className="space-y-1.5">
                {dim.traits.map((trait) => (
                  <li
                    key={trait}
                    className="text-sm capitalize text-white/60"
                  >
                    {trait}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="mt-10 text-center font-mono text-sm text-white/40"
        >
          12 traits. 214 indicators. One score: Phronesis.
        </motion.p>
      </div>
    </div>
  );
}
