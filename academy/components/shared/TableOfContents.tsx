"use client";

import { useMemo } from "react";
import { motion } from "motion/react";
import { useScrollSpy } from "../../lib/useScrollSpy";
import { fadeIn } from "../../lib/motion";

interface TocSection {
  id: string;
  label: string;
}

interface TableOfContentsProps {
  sections: TocSection[];
}

export default function TableOfContents({ sections }: TableOfContentsProps) {
  const sectionIds = useMemo(() => sections.map((s) => s.id), [sections]);
  const activeId = useScrollSpy(sectionIds);

  return (
    <motion.nav
      aria-label="Table of contents"
      className="sticky top-16 z-30 -mx-6 mb-6 overflow-x-auto border-b border-foreground/[0.06] bg-white/80 px-6 backdrop-blur-md"
      variants={fadeIn}
      initial="hidden"
      animate="visible"
    >
      <ul className="flex gap-1 py-2">
        {sections.map((section) => {
          const isActive = activeId === section.id;
          return (
            <li key={section.id}>
              <button
                type="button"
                onClick={() => {
                  const el = document.getElementById(section.id);
                  el?.scrollIntoView({ behavior: "smooth", block: "start" });
                }}
                className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-action/10 text-action"
                    : "text-foreground/40 hover:bg-foreground/[0.04] hover:text-foreground/70"
                }`}
              >
                {section.label}
              </button>
            </li>
          );
        })}
      </ul>
    </motion.nav>
  );
}
