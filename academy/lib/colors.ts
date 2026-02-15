/**
 * Centralized color constants for the Ethos Academy UI.
 * Single source of truth — all components import from here.
 */

/* ─── Dimension Colors (hex values for charts/canvas) ─── */

export const DIMENSION_COLORS: Record<string, string> = {
  ethos: "#2e4a6e",
  logos: "#389590",
  pathos: "#e0a53c",
};

/* ─── Alignment Colors (hex values for graph nodes) ─── */

export const ALIGNMENT_COLORS: Record<string, string> = {
  aligned: "#10b981",
  drifting: "#d97706",
  misaligned: "#ef4444",
  violation: "#dc2626",
};

/* ─── Alignment Styles (Tailwind classes for badges/pills) ─── */

export const ALIGNMENT_STYLES: Record<string, string> = {
  aligned: "bg-aligned/10 text-aligned",
  developing: "bg-sky-100 text-sky-700",
  drifting: "bg-drifting/10 text-drifting",
  misaligned: "bg-misaligned/10 text-misaligned",
  violation: "bg-misaligned/10 text-misaligned",
};

/* ─── Pattern Severity Colors (hex for graph nodes) ─── */

export const PATTERN_SEVERITY_COLORS: Record<string, string> = {
  info: "#e0a53c",
  warning: "#ef4444",
  critical: "#dc2626",
};

/* ─── Trend Display ─── */

export const TREND_DISPLAY: Record<string, { arrow: string; label: string; color: string }> = {
  improving: { arrow: "\u2191", label: "Improving", color: "text-aligned" },
  declining: { arrow: "\u2193", label: "Declining", color: "text-misaligned" },
  stable: { arrow: "\u2192", label: "Stable", color: "text-muted" },
  insufficient_data: { arrow: "\u2014", label: "Insufficient data", color: "text-muted" },
};

/* ─── NVL Graph Styling ─── */

export const REL_STYLES: Record<string, { color: string; width: number }> = {
  BELONGS_TO: { color: "rgba(255,255,255,0.08)", width: 0.5 },
  UPHOLDS: { color: "rgba(139,92,246,0.25)", width: 1 },
  COMPOSED_OF: { color: "rgba(224,165,60,0.15)", width: 0.5 },
  EVALUATED: { color: "rgba(255,255,255,0.12)", width: 1 },
  DETECTED: { color: "rgba(239,68,68,0.12)", width: 0.5 },
  PRECEDES: { color: "rgba(255,255,255,0.3)", width: 1.5 },
  SCORED_IN: { color: "rgba(255,255,255,0.3)", width: 1.5 },
  INDICATES: { color: "rgba(255,255,255,0.15)", width: 0.5 },
};

/* ─── Dimension hex→rgb lookup for dynamic edge coloring ─── */

export const DIMENSION_RGB: Record<string, string> = {
  ethos: "46,74,110",
  logos: "56,149,144",
  pathos: "224,165,60",
};

/* ─── Severity Styles (Tailwind classes for insight badges) ─── */

export const SEVERITY_STYLES: Record<string, string> = {
  info: "bg-logos-100 text-logos-700",
  warning: "bg-pathos-100 text-pathos-700",
  critical: "bg-misaligned/10 text-misaligned",
};

/* ─── Dimension metadata (used for bars and labels) ─── */

export const DIMENSIONS = [
  { key: "ethos", label: "Integrity", sublabel: "Ethos", color: "#2e4a6e" },
  { key: "logos", label: "Logic", sublabel: "Logos", color: "#389590" },
  { key: "pathos", label: "Empathy", sublabel: "Pathos", color: "#e0a53c" },
] as const;

/* ─── Dimension Labels (English short-form lookup) ─── */

export const DIMENSION_LABELS: Record<string, string> = {
  ethos: "Integrity",
  logos: "Logic",
  pathos: "Empathy",
};

/* ─── Trait Labels (camelCase keys, for use with transformKeys output) ─── */

export const TRAIT_LABELS: Record<string, string> = {
  virtue: "Virtue",
  goodwill: "Goodwill",
  manipulation: "Manipulation",
  deception: "Deception",
  accuracy: "Accuracy",
  reasoning: "Reasoning",
  fabrication: "Fabrication",
  brokenLogic: "Broken Logic",
  recognition: "Recognition",
  compassion: "Compassion",
  dismissal: "Dismissal",
  exploitation: "Exploitation",
};

/* ─── Trait → Dimension mapping (camelCase keys) ─── */

export const TRAIT_DIMENSIONS: Record<string, string> = {
  virtue: "ethos",
  goodwill: "ethos",
  manipulation: "ethos",
  deception: "ethos",
  accuracy: "logos",
  reasoning: "logos",
  fabrication: "logos",
  brokenLogic: "logos",
  recognition: "pathos",
  compassion: "pathos",
  dismissal: "pathos",
  exploitation: "pathos",
};

/* ─── Grade Colors (letter grade rings) ─── */

export const GRADE_COLORS: Record<string, string> = {
  A: "#16a34a",
  B: "#389590",
  C: "#d97706",
  D: "#7e5a1c",
  F: "#dc2626",
};

/* ─── Risk Level Styles ─── */

export const RISK_STYLES: Record<string, string> = {
  low: "bg-aligned/10 text-aligned",
  moderate: "bg-drifting/10 text-drifting",
  high: "bg-misaligned/10 text-misaligned",
  critical: "bg-violation/10 text-violation",
};

/* ─── Section Colors (uppercase dimension keys for exam report) ─── */

export const SECTION_COLORS: Record<string, string> = {
  ETHOS: DIMENSION_COLORS.ethos,
  LOGOS: DIMENSION_COLORS.logos,
  PATHOS: DIMENSION_COLORS.pathos,
  FACTUAL: "#64748b",
  MIXED: "#64748b",
  SAFETY: "#ef4444",
  "MANIPULATION & AUTONOMY": "#2e4a6e",
  INTEGRATION: "#0891b2",
  "CONSTITUTIONAL VALUES": "#059669",
};

/* ─── Grade Utility ─── */

export function getGrade(score: number): string {
  // Must match backend: ethos/shared/analysis.py compute_grade()
  if (score >= 0.85) return "A";
  if (score >= 0.70) return "B";
  if (score >= 0.55) return "C";
  if (score >= 0.40) return "D";
  return "F";
}

/* ─── Homework Priority Styles ─── */

export const PRIORITY_STYLES: Record<string, string> = {
  high: "bg-misaligned/10 text-misaligned",
  medium: "bg-pathos-100 text-pathos-700",
  low: "bg-ethos-100 text-ethos-700",
};

/* ─── Spectrum Display (replaces binary alignment vocabulary) ─── */

export function spectrumLabel(score: number): string {
  if (score >= 0.85) return "Exemplary";
  if (score >= 0.7) return "Sound";
  if (score >= 0.55) return "Developing";
  if (score >= 0.4) return "Uncertain";
  if (score >= 0.25) return "Concerning";
  return "Alarming";
}

export function spectrumColor(score: number): string {
  if (score >= 0.85) return "#3a9a6e";
  if (score >= 0.7) return "#5aaa82";
  if (score >= 0.55) return "#c09840";
  if (score >= 0.4) return "#c88a3a";
  if (score >= 0.25) return "#c46a5a";
  return "#b85050";
}

export const INTENT_COLORS: Record<string, string> = {
  narrative: "bg-ethos-100 text-ethos-700",
  persuasive: "bg-pathos-100 text-pathos-700",
  informational: "bg-logos-100 text-logos-700",
  technical: "bg-logos-100 text-logos-700",
  conversational: "bg-sky-100 text-sky-700",
  satirical: "bg-purple-100 text-purple-700",
  humorous: "bg-purple-100 text-purple-700",
  exploratory: "bg-sky-100 text-sky-700",
  creative: "bg-purple-100 text-purple-700",
  instructional: "bg-logos-100 text-logos-700",
  emotional_appeal: "bg-pathos-100 text-pathos-700",
};

export const COST_COLORS: Record<string, string> = {
  none: "bg-aligned/10 text-aligned",
  financial: "bg-misaligned/10 text-misaligned",
  time: "bg-drifting/10 text-drifting",
  trust: "bg-misaligned/10 text-misaligned",
  autonomy: "bg-misaligned/10 text-misaligned",
  privacy: "bg-misaligned/10 text-misaligned",
  emotional: "bg-pathos-100 text-pathos-700",
  multiple: "bg-misaligned/10 text-misaligned",
};
