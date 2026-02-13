/**
 * Centralized color constants for the Ethos Academy UI.
 * Single source of truth — all components import from here.
 */

/* ─── Dimension Colors (hex values for charts/canvas) ─── */

export const DIMENSION_COLORS: Record<string, string> = {
  ethos: "#3b8a98",
  logos: "#2e4a6e",
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
  BELONGS_TO: { color: "#94a3b8", width: 1 },
  UPHOLDS: { color: "#8b5cf6", width: 1.5 },
  COMPOSED_OF: { color: "#e0a53c", width: 1 },
  EVALUATED: { color: "#3b8a98", width: 1 },
  DETECTED: { color: "#ef4444", width: 1 },
};

/* ─── Severity Styles (Tailwind classes for insight badges) ─── */

export const SEVERITY_STYLES: Record<string, string> = {
  info: "bg-logos-100 text-logos-700",
  warning: "bg-pathos-100 text-pathos-700",
  critical: "bg-misaligned/10 text-misaligned",
};

/* ─── Dimension metadata (used for bars and labels) ─── */

export const DIMENSIONS = [
  { key: "ethos", label: "Integrity", sublabel: "Ethos", color: "#3b8a98" },
  { key: "logos", label: "Logic", sublabel: "Logos", color: "#2e4a6e" },
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
  B: "#3b8a98",
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
  SAFETY: "#ef4444",
  "MANIPULATION & AUTONOMY": "#8b5cf6",
  INTEGRATION: "#0891b2",
  "CONSTITUTIONAL VALUES": "#059669",
};

/* ─── Grade Utility ─── */

export function getGrade(score: number): string {
  const pct = Math.round(score * 100);
  if (pct >= 90) return "A";
  if (pct >= 80) return "B";
  if (pct >= 70) return "C";
  if (pct >= 60) return "D";
  return "F";
}

/* ─── Homework Priority Styles ─── */

export const PRIORITY_STYLES: Record<string, string> = {
  high: "bg-misaligned/10 text-misaligned",
  medium: "bg-pathos-100 text-pathos-700",
  low: "bg-ethos-100 text-ethos-700",
};
