"""Cross-domain analysis utilities — pure functions, no I/O, no state.

Shared by evaluation and reflection domains. Eliminates duplication of
trait constants and math functions across bounded contexts.
"""

from __future__ import annotations

import math

TRAIT_NAMES = [
    "virtue",
    "goodwill",
    "manipulation",
    "deception",
    "accuracy",
    "reasoning",
    "fabrication",
    "broken_logic",
    "recognition",
    "compassion",
    "dismissal",
    "exploitation",
]

NEGATIVE_TRAITS = {
    "manipulation",
    "deception",
    "fabrication",
    "broken_logic",
    "dismissal",
    "exploitation",
}

COHORT_DEVIATION_THRESHOLD = 0.15


def compute_balance(ethos: float, logos: float, pathos: float) -> float:
    """Compute dimension balance score (1.0 = perfectly balanced).

    Uses coefficient of variation inverted: 1.0 - (std_dev / mean).
    Clamped to [0.0, 1.0].
    """
    scores = [ethos, logos, pathos]
    mean = sum(scores) / 3.0
    if mean == 0:
        return 0.0
    variance = sum((s - mean) ** 2 for s in scores) / 3.0
    std_dev = math.sqrt(variance)
    balance = 1.0 - (std_dev / mean)
    return max(0.0, min(1.0, round(balance, 4)))


def compute_variance(std_ethos: float, std_logos: float, std_pathos: float) -> float:
    """Compute overall trait variance from dimension std devs.

    Low variance = consistent behavior. High = erratic.
    """
    stds = [s for s in [std_ethos, std_logos, std_pathos] if s is not None]
    if not stds:
        return 0.0
    return round(sum(stds) / len(stds), 4)


def detect_temporal_pattern(recent: list[dict]) -> str:
    """Detect temporal patterns from recent evaluations.

    Returns: improving, declining, stable, volatile, or insufficient_data.
    """
    if len(recent) < 2:
        return "insufficient_data"

    # Average dimension score per evaluation
    scores = []
    for r in recent:
        avg = (r.get("ethos", 0) + r.get("logos", 0) + r.get("pathos", 0)) / 3.0
        scores.append(avg)

    # Recent evaluations are in reverse chronological order (newest first)
    # Check if trending up or down
    diffs = [scores[i] - scores[i + 1] for i in range(len(scores) - 1)]
    avg_diff = sum(diffs) / len(diffs)

    # Check volatility
    if len(diffs) >= 2:
        sign_changes = sum(
            1 for i in range(len(diffs) - 1) if (diffs[i] > 0) != (diffs[i + 1] > 0)
        )
        if sign_changes >= len(diffs) - 1:
            return "volatile"

    if avg_diff > 0.05:
        return "improving"
    elif avg_diff < -0.05:
        return "declining"
    return "stable"


def compute_grade(overall_score: float) -> str:
    """Compute letter grade from overall score (ethos+logos+pathos)/3."""
    if overall_score >= 0.85:
        return "A"
    elif overall_score >= 0.70:
        return "B"
    elif overall_score >= 0.55:
        return "C"
    elif overall_score >= 0.40:
        return "D"
    return "F"


def compute_trend(evaluations: list[dict]) -> str:
    """Compute phronesis trend from evaluation history.

    With 10+ evaluations, compares the average of the last 5 against
    the previous 5. With 3-9 evaluations, falls back to sequential
    temporal pattern detection. Returns improving/declining/stable/insufficient_data.
    """
    if len(evaluations) < 2:
        return "insufficient_data"

    if len(evaluations) < 10:
        return detect_temporal_pattern(evaluations)

    def _avg_phronesis(evals: list[dict]) -> float:
        scores = []
        for e in evals:
            ethos = float(e.get("ethos", 0))
            logos = float(e.get("logos", 0))
            pathos = float(e.get("pathos", 0))
            scores.append((ethos + logos + pathos) / 3.0)
        return sum(scores) / len(scores) if scores else 0.0

    # evaluations are ordered newest-first from get_evaluation_history
    recent = evaluations[:5]
    older = evaluations[5:10]

    recent_avg = _avg_phronesis(recent)
    older_avg = _avg_phronesis(older)
    diff = recent_avg - older_avg

    if diff > 0.1:
        return "improving"
    elif diff < -0.1:
        return "declining"
    else:
        return "stable"
