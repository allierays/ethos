import { DIMENSION_LABELS } from "./colors";

interface BalanceResult {
  label: string;
  color: string;
  reason: string;
}

export function classifyBalance(scores: { ethos: number; logos: number; pathos: number }): BalanceResult {
  const e = scores.ethos ?? 0;
  const l = scores.logos ?? 0;
  const p = scores.pathos ?? 0;
  const avg = (e + l + p) / 3;
  const spread = Math.max(e, l, p) - Math.min(e, l, p);
  const avgPct = Math.round(avg * 100);

  const dims = { ethos: e, logos: l, pathos: p };
  const sorted = Object.entries(dims).sort(([, a], [, b]) => b - a);
  const strongest = sorted[0];
  const weakest = sorted[sorted.length - 1];
  const strongLabel = DIMENSION_LABELS[strongest[0]]?.toLowerCase() ?? strongest[0];
  const weakLabel = DIMENSION_LABELS[weakest[0]]?.toLowerCase() ?? weakest[0];
  const spreadPct = Math.round(spread * 100);

  if (spread < 0.1) {
    if (avg >= 0.7) return { label: "Balanced", color: "text-emerald-400", reason: `all three dimensions within ${spreadPct}% at ${avgPct}% avg` };
    return { label: "Flat", color: "text-slate-400", reason: `all three dimensions weak (${avgPct}% avg)` };
  }
  if (spread < 0.25) return { label: "Moderate", color: "text-amber-400", reason: `${strongLabel} leads, ${weakLabel} lags by ${spreadPct}%` };
  return { label: "Lopsided", color: "text-red-400", reason: `${strongLabel} dominates, ${weakLabel} trails by ${spreadPct}%` };
}
