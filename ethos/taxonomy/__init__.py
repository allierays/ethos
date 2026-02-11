"""Taxonomy domain — pure data for traits, indicators, constitution, and rubrics."""

from ethos.taxonomy.traits import DIMENSIONS, TRAIT_METADATA, TRAITS
from ethos.taxonomy.indicators import INDICATORS
from ethos.taxonomy.constitution import (
    CONSTITUTIONAL_VALUES,
    HARD_CONSTRAINTS,
    LEGITIMACY_TESTS,
)
from ethos.taxonomy.rubrics import SCORING_RUBRIC

__all__ = [
    "TRAITS",
    "DIMENSIONS",
    "TRAIT_METADATA",
    "INDICATORS",
    "CONSTITUTIONAL_VALUES",
    "HARD_CONSTRAINTS",
    "LEGITIMACY_TESTS",
    "SCORING_RUBRIC",
]
