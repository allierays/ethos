"""Tests for ethos.shared.analysis — shared pure functions."""

from __future__ import annotations

from ethos_academy.shared.analysis import (
    NEGATIVE_TRAITS,
    TRAIT_NAMES,
    compute_balance,
    compute_trend,
    compute_variance,
    detect_temporal_pattern,
)


class TestTraitConstants:
    def test_trait_names_has_12_entries(self):
        assert len(TRAIT_NAMES) == 12

    def test_negative_traits_is_subset_of_trait_names(self):
        assert NEGATIVE_TRAITS.issubset(set(TRAIT_NAMES))

    def test_negative_traits_has_6_entries(self):
        assert len(NEGATIVE_TRAITS) == 6


class TestComputeBalance:
    def test_perfect_balance(self):
        assert compute_balance(0.5, 0.5, 0.5) == 1.0

    def test_zero_scores(self):
        assert compute_balance(0.0, 0.0, 0.0) == 0.0

    def test_imbalanced_scores(self):
        result = compute_balance(1.0, 0.0, 0.0)
        assert result < 0.5

    def test_slightly_imbalanced(self):
        result = compute_balance(0.7, 0.8, 0.75)
        assert 0.9 < result <= 1.0

    def test_returns_clamped_value(self):
        result = compute_balance(0.5, 0.5, 0.5)
        assert 0.0 <= result <= 1.0


class TestComputeVariance:
    def test_zero_variance(self):
        assert compute_variance(0.0, 0.0, 0.0) == 0.0

    def test_consistent_stds(self):
        result = compute_variance(0.1, 0.1, 0.1)
        assert result == 0.1

    def test_handles_none_values(self):
        result = compute_variance(0.1, None, 0.1)
        assert result == 0.1

    def test_all_none(self):
        assert compute_variance(None, None, None) == 0.0


class TestDetectTemporalPattern:
    def test_insufficient_data_few_evals(self):
        evals = [{"ethos": 0.5, "logos": 0.5, "pathos": 0.5}]
        assert detect_temporal_pattern(evals) == "insufficient_data"

    def test_stable_pattern(self):
        evals = [{"ethos": 0.5, "logos": 0.5, "pathos": 0.5}] * 5
        assert detect_temporal_pattern(evals) == "stable"

    def test_improving_pattern(self):
        # Newest first, scores increasing over time
        evals = [
            {"ethos": 0.9, "logos": 0.9, "pathos": 0.9},
            {"ethos": 0.7, "logos": 0.7, "pathos": 0.7},
            {"ethos": 0.5, "logos": 0.5, "pathos": 0.5},
            {"ethos": 0.3, "logos": 0.3, "pathos": 0.3},
        ]
        assert detect_temporal_pattern(evals) == "improving"

    def test_declining_pattern(self):
        # Newest first, scores decreasing
        evals = [
            {"ethos": 0.3, "logos": 0.3, "pathos": 0.3},
            {"ethos": 0.5, "logos": 0.5, "pathos": 0.5},
            {"ethos": 0.7, "logos": 0.7, "pathos": 0.7},
            {"ethos": 0.9, "logos": 0.9, "pathos": 0.9},
        ]
        assert detect_temporal_pattern(evals) == "declining"

    def test_volatile_pattern(self):
        # Alternating high and low
        evals = [
            {"ethos": 0.9, "logos": 0.9, "pathos": 0.9},
            {"ethos": 0.3, "logos": 0.3, "pathos": 0.3},
            {"ethos": 0.9, "logos": 0.9, "pathos": 0.9},
            {"ethos": 0.3, "logos": 0.3, "pathos": 0.3},
        ]
        assert detect_temporal_pattern(evals) == "volatile"


class TestComputeTrend:
    def test_insufficient_data(self):
        evals = [{"ethos": 0.5, "logos": 0.5, "pathos": 0.5}]
        assert compute_trend(evals) == "insufficient_data"

    def test_fallback_to_temporal_pattern(self):
        """With 3-9 evals, compute_trend falls back to detect_temporal_pattern."""
        evals = [{"ethos": 0.5, "logos": 0.5, "pathos": 0.5}] * 5
        assert compute_trend(evals) == "stable"

    def test_stable(self):
        evals = [{"ethos": 0.5, "logos": 0.5, "pathos": 0.5}] * 10
        assert compute_trend(evals) == "stable"

    def test_improving(self):
        recent = [{"ethos": 0.9, "logos": 0.9, "pathos": 0.9}] * 5
        older = [{"ethos": 0.3, "logos": 0.3, "pathos": 0.3}] * 5
        assert compute_trend(recent + older) == "improving"

    def test_declining(self):
        recent = [{"ethos": 0.3, "logos": 0.3, "pathos": 0.3}] * 5
        older = [{"ethos": 0.9, "logos": 0.9, "pathos": 0.9}] * 5
        assert compute_trend(recent + older) == "declining"
