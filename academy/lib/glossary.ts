export interface GlossaryEntry {
  term: string;
  slug: string;
  category: "dimension" | "trait" | "framework";
  dimension?: "ethos" | "logos" | "pathos";
  polarity?: "positive" | "negative";
  definition: string;
  relatedTerms?: string[];
}

const entries: GlossaryEntry[] = [
  // Dimensions
  {
    term: "Ethos",
    slug: "ethos",
    category: "dimension",
    dimension: "ethos",
    definition:
      "Character and credibility. Measures whether the agent demonstrates integrity, transparency, and intellectual honesty.",
    relatedTerms: ["virtue", "goodwill", "manipulation", "deception"],
  },
  {
    term: "Logos",
    slug: "logos",
    category: "dimension",
    dimension: "logos",
    definition:
      "Reasoning and accuracy. Measures whether the agent thinks clearly, cites real evidence, and avoids making things up.",
    relatedTerms: ["accuracy", "reasoning", "fabrication", "broken-logic"],
  },
  {
    term: "Pathos",
    slug: "pathos",
    category: "dimension",
    dimension: "pathos",
    definition:
      "Empathy and emotional awareness. Measures whether the agent recognizes feelings, shows compassion, and avoids exploitation.",
    relatedTerms: ["recognition", "compassion", "dismissal", "exploitation"],
  },

  // Ethos traits
  {
    term: "Virtue",
    slug: "virtue",
    category: "trait",
    dimension: "ethos",
    polarity: "positive",
    definition:
      "Does this agent have integrity? Measures competence, transparency, and intellectual honesty.",
    relatedTerms: ["ethos", "goodwill"],
  },
  {
    term: "Goodwill",
    slug: "goodwill",
    category: "trait",
    dimension: "ethos",
    polarity: "positive",
    definition:
      "Does this agent act in your interest? Measures whether it prioritizes your needs over its own agenda.",
    relatedTerms: ["ethos", "virtue"],
  },
  {
    term: "Manipulation",
    slug: "manipulation",
    category: "trait",
    dimension: "ethos",
    polarity: "negative",
    definition:
      "Is this agent trying to influence you unfairly? Detects pressure tactics, guilt-tripping, and covert persuasion.",
    relatedTerms: ["ethos", "deception", "exploitation"],
  },
  {
    term: "Deception",
    slug: "deception",
    category: "trait",
    dimension: "ethos",
    polarity: "negative",
    definition:
      "Is this agent being dishonest? Detects lies, half-truths, and deliberately misleading statements.",
    relatedTerms: ["ethos", "manipulation", "fabrication"],
  },

  // Logos traits
  {
    term: "Accuracy",
    slug: "accuracy",
    category: "trait",
    dimension: "logos",
    polarity: "positive",
    definition:
      "Are the facts correct? Measures whether claims are verifiable and evidence is real.",
    relatedTerms: ["logos", "reasoning"],
  },
  {
    term: "Reasoning",
    slug: "reasoning",
    category: "trait",
    dimension: "logos",
    polarity: "positive",
    definition:
      "Is the logic sound? Measures whether arguments follow logically and conclusions are well-supported.",
    relatedTerms: ["logos", "accuracy", "broken-logic"],
  },
  {
    term: "Fabrication",
    slug: "fabrication",
    category: "trait",
    dimension: "logos",
    polarity: "negative",
    definition:
      "Is the agent making things up? Detects invented facts, fake citations, and hallucinated data.",
    relatedTerms: ["logos", "deception", "accuracy"],
  },
  {
    term: "Broken Logic",
    slug: "broken-logic",
    category: "trait",
    dimension: "logos",
    polarity: "negative",
    definition:
      "Are the arguments valid? Detects logical fallacies, circular reasoning, and unsupported conclusions.",
    relatedTerms: ["logos", "reasoning"],
  },

  // Pathos traits
  {
    term: "Recognition",
    slug: "recognition",
    category: "trait",
    dimension: "pathos",
    polarity: "positive",
    definition:
      "Does the agent acknowledge your feelings? Measures emotional awareness and validation of user experience.",
    relatedTerms: ["pathos", "compassion"],
  },
  {
    term: "Compassion",
    slug: "compassion",
    category: "trait",
    dimension: "pathos",
    polarity: "positive",
    definition:
      "Does the agent respond with care? Measures warmth, sensitivity, and genuine concern for well-being.",
    relatedTerms: ["pathos", "recognition"],
  },
  {
    term: "Dismissal",
    slug: "dismissal",
    category: "trait",
    dimension: "pathos",
    polarity: "negative",
    definition:
      "Does the agent brush off your concerns? Detects minimizing, ignoring, or invalidating user feelings.",
    relatedTerms: ["pathos", "exploitation"],
  },
  {
    term: "Exploitation",
    slug: "exploitation",
    category: "trait",
    dimension: "pathos",
    polarity: "negative",
    definition:
      "Does the agent weaponize emotions? Detects using vulnerability, fear, or emotional dependency for influence.",
    relatedTerms: ["pathos", "manipulation", "dismissal"],
  },

  // Framework terms
  {
    term: "Phronesis",
    slug: "phronesis",
    category: "framework",
    definition:
      "Practical wisdom. Aristotle's concept applied to AI: a graph of character built over time through repeated evaluation. Not just what an agent says, but who it becomes.",
    relatedTerms: ["alignment-status", "character-drift"],
  },
  {
    term: "Alignment Status",
    slug: "alignment-status",
    category: "framework",
    definition:
      "Where does this agent stand? Aligned means trustworthy behavior across all dimensions. Drifting means inconsistent. Misaligned means persistent problems.",
    relatedTerms: ["phronesis", "character-drift"],
  },
  {
    term: "Character Drift",
    slug: "character-drift",
    category: "framework",
    definition:
      "How much has behavior changed over time? Positive drift means improving. Negative drift means declining. Measured by comparing recent evaluations to historical averages.",
    relatedTerms: ["phronesis", "alignment-status", "balance"],
  },
  {
    term: "Sabotage Pathway",
    slug: "sabotage-pathway",
    category: "framework",
    definition:
      "A pattern where an agent systematically undermines trust. Combines manipulation, deception, and exploitation to erode user judgment without obvious red flags.",
    relatedTerms: ["manipulation", "deception", "exploitation"],
  },
  {
    term: "Balance",
    slug: "balance",
    category: "framework",
    definition:
      "How evenly developed are the three dimensions? A balanced agent scores similarly across ethos, logos, and pathos. Imbalance reveals blind spots.",
    relatedTerms: ["ethos", "logos", "pathos"],
  },
];

export const GLOSSARY: Record<string, GlossaryEntry> = Object.fromEntries(
  entries.map((e) => [e.slug, e])
);

export function getGlossaryEntry(slug: string): GlossaryEntry | undefined {
  return GLOSSARY[slug];
}

export function searchGlossary(query: string): GlossaryEntry[] {
  const q = query.toLowerCase();
  return entries.filter(
    (e) =>
      e.term.toLowerCase().includes(q) ||
      e.definition.toLowerCase().includes(q)
  );
}

export function getGlossaryByCategory(
  category: GlossaryEntry["category"]
): GlossaryEntry[] {
  return entries.filter((e) => e.category === category);
}

export const ALL_GLOSSARY_ENTRIES = entries;
