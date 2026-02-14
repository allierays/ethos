"use client";

import type { ReactNode, KeyboardEvent } from "react";
import { useGlossary } from "../../lib/GlossaryContext";
import { getGlossaryEntry } from "../../lib/glossary";

interface GlossaryTermProps {
  slug: string;
  children: ReactNode;
}

export default function GlossaryTerm({ slug, children }: GlossaryTermProps) {
  const { selectTerm } = useGlossary();
  const entry = getGlossaryEntry(slug);
  if (!entry) return <>{children}</>;

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      selectTerm(slug);
    }
  };

  return (
    <span
      role="button"
      tabIndex={0}
      aria-label={`Learn about ${entry.term}`}
      onClick={() => selectTerm(slug)}
      onKeyDown={handleKeyDown}
      className="cursor-pointer text-accent border-b border-dotted border-accent/40 hover:border-accent transition-colors"
    >
      {children}
    </span>
  );
}
