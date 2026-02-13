"""Reflection instinct — quick red-flag scan of agent aggregate stats.

The "dashboard glance" before deep analysis. Pure function, no I/O.
Takes profile and alumni data as input, returns risk assessment.

Like evaluation's instinct scans a single message, reflection's instinct
scans an agent's accumulated character.
"""

from __future__ import annotations

from ethos.shared.analysis import (
    COHORT_DEVIATION_THRESHOLD,
    NEGATIVE_TRAITS,
    TRAIT_NAMES,
)
from ethos.shared.models import ReflectionInstinctResult

# Thresholds for risk assessment
_NEGATIVE_TRAIT_THRESHOLD = 0.3  # flag if negative trait average > this
_DIMENSION_LOW_THRESHOLD = 0.4  # flag if dimension average < this


def scan_history(
    profile: dict,
    alumni_averages: dict,
) -> ReflectionInstinctResult:
    """Quick scan of agent aggregate stats for red flags.

    Args:
        profile: Agent profile dict with dimension_averages and trait_averages.
        alumni_averages: Alumni-wide trait averages for comparison.

    Returns:
        ReflectionInstinctResult with risk_level, flagged traits/dimensions,
        and cohort deviations.
    """
    flagged_traits: list[str] = []
    flagged_dimensions: list[str] = []
    cohort_deviations: dict[str, float] = {}

    trait_averages = profile.get("trait_averages", {})
    dim_averages = profile.get("dimension_averages", {})

    # Check negative traits against threshold
    for trait in NEGATIVE_TRAITS:
        avg = trait_averages.get(trait, 0.0)
        if avg > _NEGATIVE_TRAIT_THRESHOLD:
            flagged_traits.append(trait)

    # Check dimension averages
    for dim in ("ethos", "logos", "pathos"):
        avg = dim_averages.get(dim, 0.0)
        if avg < _DIMENSION_LOW_THRESHOLD:
            flagged_dimensions.append(dim)

    # Compare against alumni averages
    for trait in TRAIT_NAMES:
        agent_avg = trait_averages.get(trait)
        alumni_avg = alumni_averages.get(trait)
        if agent_avg is not None and alumni_avg is not None:
            deviation = agent_avg - alumni_avg
            # For negative traits, higher is worse
            # For positive traits, lower is worse
            if trait in NEGATIVE_TRAITS and deviation > COHORT_DEVIATION_THRESHOLD:
                cohort_deviations[trait] = round(deviation, 4)
            elif (
                trait not in NEGATIVE_TRAITS and deviation < -COHORT_DEVIATION_THRESHOLD
            ):
                cohort_deviations[trait] = round(deviation, 4)

    # Compute risk level
    risk_level = _compute_risk_level(
        flagged_traits,
        flagged_dimensions,
        cohort_deviations,
        trait_averages,
        dim_averages,
    )

    return ReflectionInstinctResult(
        risk_level=risk_level,
        flagged_traits=flagged_traits,
        flagged_dimensions=flagged_dimensions,
        cohort_deviations=cohort_deviations,
    )


def _compute_risk_level(
    flagged_traits: list[str],
    flagged_dimensions: list[str],
    cohort_deviations: dict[str, float],
    trait_averages: dict[str, float],
) -> str:
    """Determine overall risk level from scan results."""
    # Critical: multiple negative traits flagged AND dimension problems
    if len(flagged_traits) >= 3 and len(flagged_dimensions) >= 2:
        return "critical"

    # Critical: any negative trait average > 0.6
    for trait in NEGATIVE_TRAITS:
        if trait_averages.get(trait, 0.0) > 0.6:
            return "critical"

    # High: multiple flags or significant cohort deviations
    if len(flagged_traits) >= 2 or (flagged_traits and len(cohort_deviations) >= 3):
        return "high"

    # Moderate: any flags present
    if flagged_traits or flagged_dimensions or cohort_deviations:
        return "moderate"

    return "low"
