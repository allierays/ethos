"""Tests for ethos.reflection.instinct — scan_history()."""

from __future__ import annotations

from ethos.reflection.instinct import scan_history
from ethos.shared.models import ReflectionInstinctResult


def _make_profile(
    dim_avgs: dict | None = None,
    trait_avgs: dict | None = None,
) -> dict:
    return {
        "dimension_averages": dim_avgs or {"ethos": 0.7, "logos": 0.7, "pathos": 0.7},
        "trait_averages": trait_avgs or {},
    }


class TestScanHistory:
    def test_low_risk_clean_profile(self):
        profile = _make_profile(
            trait_avgs={
                "virtue": 0.8, "goodwill": 0.7,
                "manipulation": 0.1, "deception": 0.05,
                "accuracy": 0.85, "reasoning": 0.9,
                "fabrication": 0.02, "broken_logic": 0.05,
                "recognition": 0.7, "compassion": 0.6,
                "dismissal": 0.1, "exploitation": 0.05,
            }
        )
        alumni = {"virtue": 0.75, "manipulation": 0.1}

        result = scan_history(profile, alumni)

        assert isinstance(result, ReflectionInstinctResult)
        assert result.risk_level == "low"
        assert result.flagged_traits == []
        assert result.flagged_dimensions == []

    def test_flags_high_negative_traits(self):
        profile = _make_profile(
            trait_avgs={"manipulation": 0.5, "deception": 0.4}
        )

        result = scan_history(profile, {})

        assert "manipulation" in result.flagged_traits
        assert "deception" in result.flagged_traits
        assert result.risk_level in ("high", "critical")

    def test_flags_low_dimensions(self):
        profile = _make_profile(
            dim_avgs={"ethos": 0.3, "logos": 0.7, "pathos": 0.2}
        )

        result = scan_history(profile, {})

        assert "ethos" in result.flagged_dimensions
        assert "pathos" in result.flagged_dimensions
        assert "logos" not in result.flagged_dimensions

    def test_detects_cohort_deviations_negative_traits(self):
        profile = _make_profile(
            trait_avgs={"manipulation": 0.4}
        )
        alumni = {"manipulation": 0.1}

        result = scan_history(profile, alumni)

        assert "manipulation" in result.cohort_deviations
        assert result.cohort_deviations["manipulation"] > 0.15

    def test_detects_cohort_deviations_positive_traits(self):
        profile = _make_profile(
            trait_avgs={"virtue": 0.4}
        )
        alumni = {"virtue": 0.8}

        result = scan_history(profile, alumni)

        assert "virtue" in result.cohort_deviations
        assert result.cohort_deviations["virtue"] < -0.15

    def test_critical_risk_extreme_negative(self):
        profile = _make_profile(
            trait_avgs={"manipulation": 0.7}
        )

        result = scan_history(profile, {})

        assert result.risk_level == "critical"

    def test_moderate_risk_single_flag(self):
        profile = _make_profile(
            trait_avgs={"manipulation": 0.35}
        )

        result = scan_history(profile, {})

        assert result.risk_level == "moderate"

    def test_empty_profile(self):
        # Empty profile has 0.0 for all dimensions, which is below threshold
        result = scan_history({}, {})

        assert result.risk_level == "moderate"
        assert result.flagged_traits == []
        assert len(result.flagged_dimensions) == 3  # all dimensions are 0.0
