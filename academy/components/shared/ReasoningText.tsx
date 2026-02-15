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

/**
 * Parse a text string and return React nodes with:
 * - Indicator codes wrapped in GlossaryTerm (clickable, dotted underline)
 * - Dimension names highlighted in their dimension color
 */
function parseSegment(text: string): ReactNode[] {
  // Indicator codes are always UPPERCASE (VIR-HONESTY, not vir-honesty).
  // Dimension names can be any case. Using a single regex with separate
  // case handling: indicator group is case-sensitive via [A-Z], dimension
  // group uses alternation for both cases.
  const combined = new RegExp(
    `(\\b[A-Z]{2,4}-[A-Z]{2,}\\b)|(\\b[Ee]thos\\b|\\b[Ll]ogos\\b|\\b[Pp]athos\\b)`,
    "g"
  );

  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = combined.exec(text)) !== null) {
    // Add text before this match
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index));
    }

    const fullMatch = match[0];

    if (match[1]) {
      // Indicator code match
      const slug = codeToSlug(fullMatch);
      nodes.push(
        <GlossaryTerm key={`${match.index}-${fullMatch}`} slug={slug}>
          {fullMatch}
        </GlossaryTerm>
      );
    } else if (match[2]) {
      // Dimension name match
      const dimKey = fullMatch.toLowerCase();
      const color = DIMENSION_COLORS[dimKey];
      nodes.push(
        <span
          key={`${match.index}-${fullMatch}`}
          className="font-bold"
          style={{ color }}
        >
          {fullMatch}
        </span>
      );
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
