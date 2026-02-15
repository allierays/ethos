"use client";

import type { ReactNode } from "react";
import GlossaryTerm from "./GlossaryTerm";
import { DIMENSION_COLORS } from "../../lib/colors";

/**
 * Convert an indicator code like "VIR-HONESTY" to its glossary slug.
 * Uses lowercase with the dash preserved: "vir-honesty"
 */
function codeToSlug(code: string): string {
  return code.toLowerCase();
}

/** Map trait names (as they appear in reasoning text) to glossary slugs. */
const TRAIT_SLUG_MAP: Record<string, string> = {
  virtue: "virtue",
  goodwill: "goodwill",
  manipulation: "manipulation",
  deception: "deception",
  accuracy: "accuracy",
  reasoning: "reasoning",
  fabrication: "fabrication",
  recognition: "recognition",
  compassion: "compassion",
  dismissal: "dismissal",
  exploitation: "exploitation",
};

/** Trait names to match in text (case-insensitive via regex flag). */
const TRAIT_NAMES = Object.keys(TRAIT_SLUG_MAP).join("|");

/**
 * Parse a text string and return React nodes with:
 * - Indicator codes wrapped in GlossaryTerm (clickable, dotted underline)
 * - Dimension names highlighted in their dimension color and clickable
 * - Trait names wrapped in GlossaryTerm (clickable)
 */
function parseSegment(text: string): ReactNode[] {
  // Group 1: Indicator codes (UPPERCASE only)
  // Group 2: Dimension names (any case)
  // Group 3: Trait names (any case, word boundaries)
  const combined = new RegExp(
    `(\\b[A-Z]{2,4}-[A-Z]{2,}\\b)|(\\b[Ee]thos\\b|\\b[Ll]ogos\\b|\\b[Pp]athos\\b)|(\\b(?:${TRAIT_NAMES})\\b)`,
    "gi"
  );

  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = combined.exec(text)) !== null) {
    const fullMatch = match[0];

    // Skip trait matches that are actually part of indicator codes (already matched)
    // or common English words in wrong context
    if (match[3]) {
      // Only match trait names that start with uppercase (proper noun usage)
      // to avoid matching "reasoning" in "the reasoning is sound"
      if (fullMatch[0] !== fullMatch[0].toUpperCase()) {
        continue;
      }
    }

    // Skip indicator code matches that aren't all uppercase
    if (match[1] && fullMatch !== fullMatch.toUpperCase()) {
      continue;
    }

    // Add text before this match
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index));
    }

    if (match[1]) {
      // Indicator code match
      const slug = codeToSlug(fullMatch);
      nodes.push(
        <GlossaryTerm key={`${match.index}-${fullMatch}`} slug={slug}>
          {fullMatch}
        </GlossaryTerm>
      );
    } else if (match[2]) {
      // Dimension name match - colored and clickable
      const dimKey = fullMatch.toLowerCase();
      const color = DIMENSION_COLORS[dimKey];
      nodes.push(
        <GlossaryTerm key={`${match.index}-${fullMatch}`} slug={dimKey}>
          <span className="font-bold" style={{ color }}>
            {fullMatch}
          </span>
        </GlossaryTerm>
      );
    } else if (match[3]) {
      // Trait name match
      const slug = TRAIT_SLUG_MAP[fullMatch.toLowerCase()];
      if (slug) {
        nodes.push(
          <GlossaryTerm key={`${match.index}-${fullMatch}`} slug={slug}>
            {fullMatch}
          </GlossaryTerm>
        );
      } else {
        nodes.push(fullMatch);
      }
    }

    lastIndex = match.index + fullMatch.length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }

  return nodes;
}

interface ReasoningTextProps {
  text: string;
  /** Split into paragraphs by sentence boundaries (default: true) */
  splitSentences?: boolean;
  className?: string;
}

/**
 * Renders scoring reasoning text with interactive indicator codes
 * and highlighted dimension names. Indicator codes open the glossary
 * sidebar with their definition.
 */
export default function ReasoningText({
  text,
  splitSentences = true,
  className,
}: ReasoningTextProps) {
  if (!text) return null;

  if (splitSentences) {
    const sentences = text.split(/(?<=\.)\s+(?=[A-Z])/);
    return (
      <div className={className}>
        {sentences.map((sentence, i) => (
          <p key={i} className={i < sentences.length - 1 ? "mb-2.5" : ""}>
            {parseSegment(sentence)}
          </p>
        ))}
      </div>
    );
  }

  return <span className={className}>{parseSegment(text)}</span>;
}
