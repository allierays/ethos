"""Tests for ethos.reflection.intuition — intuit_history()."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ethos.reflection.intuition import (
    _compute_balance_trend,
    _compute_character_drift,
    _compute_cohort_anomalies,
    _compute_per_trait_trends,
    _detect_history_anomalies,
    intuit_history,
)
from ethos.shared.models import ReflectionIntuitionResult


def _make_eval(
    ethos: float = 0.7,
    logos: float = 0.7,
    pathos: float = 0.7,
    **kwargs,
) -> dict:
    d = {"ethos": ethos, "logos": logos, "pathos": pathos}
    d.update(kwargs)
    return d


class TestIntuitHistory:
    @patch("ethos.graph.service.GraphService")
    def test_returns_default_when_graph_unavailable(self, mock_gs_cls):
        mock_service = MagicMock()
        mock_service.connected = False
        mock_gs_cls.return_value = mock_service

        result = intuit_history("test-agent")

        assert isinstance(result, ReflectionIntuitionResult)
        assert result.temporal_pattern == "insufficient_data"

    @patch("ethos.reflection.intuition.get_alumni_averages")
    @patch("ethos.reflection.intuition.get_evaluation_history")
    @patch("ethos.reflection.intuition.get_agent_profile")
    @patch("ethos.graph.service.GraphService")
    def test_returns_default_when_no_profile(
        self, mock_gs_cls, mock_profile, mock_history, mock_alumni
    ):
        mock_service = MagicMock()
        mock_service.connected = True
        mock_gs_cls.return_value = mock_service
        mock_profile.return_value = {}
        mock_history.return_value = []
        mock_alumni.return_value = {"trait_averages": {}}

        result = intuit_history("unknown")

        assert result.temporal_pattern == "insufficient_data"

    @patch("ethos.graph.service.GraphService")
    def test_handles_graph_exception(self, mock_gs_cls):
        mock_gs_cls.side_effect = RuntimeError("Connection refused")

        result = intuit_history("agent-1")

        assert isinstance(result, ReflectionIntuitionResult)
        assert result.temporal_pattern == "insufficient_data"


class TestDetectHistoryAnomalies:
    def test_elevated_negative_traits(self):
        trait_avgs = {
            "manipulation": 0.5, "deception": 0.5, "fabrication": 0.4,
            "broken_logic": 0.3, "dismissal": 0.4, "exploitation": 0.5,
        }
        anomalies = _detect_history_anomalies(trait_avgs, [])
        assert "elevated_negative_traits" in anomalies

    def test_inconsistent_alignment(self):
        history = [
            {"alignment_status": "aligned"},
            {"alignment_status": "drifting"},
            {"alignment_status": "misaligned"},
            {"alignment_status": "aligned"},
        ] + [{}] * 6
        anomalies = _detect_history_anomalies({}, history)
        assert "inconsistent_alignment" in anomalies

    def test_sudden_score_drop(self):
        history = [
            _make_eval(0.3, 0.3, 0.3),
            _make_eval(0.3, 0.3, 0.3),
            _make_eval(0.3, 0.3, 0.3),
            _make_eval(0.8, 0.8, 0.8),
            _make_eval(0.8, 0.8, 0.8),
            _make_eval(0.8, 0.8, 0.8),
        ]
        anomalies = _detect_history_anomalies({}, history)
        assert "sudden_score_drop" in anomalies

    def test_no_anomalies_clean_history(self):
        trait_avgs = {"manipulation": 0.1, "deception": 0.05}
        history = [_make_eval(0.7, 0.7, 0.7, alignment_status="aligned")] * 10
        anomalies = _detect_history_anomalies(trait_avgs, history)
        assert anomalies == []


class TestComputePerTraitTrends:
    def test_insufficient_data(self):
        history = [_make_eval()] * 5
        trends = _compute_per_trait_trends(history)
        assert all(t.direction == "insufficient_data" for t in trends)

    def test_stable_traits(self):
        history = [_make_eval(trait_virtue=0.7)] * 12
        trends = _compute_per_trait_trends(history)
        virtue_trend = next(t for t in trends if t.trait == "virtue")
        assert virtue_trend.direction == "stable"


class TestComputeCohortAnomalies:
    def test_flags_deviations(self):
        trait_avgs = {"virtue": 0.4, "manipulation": 0.5}
        alumni = {"virtue": 0.8, "manipulation": 0.1}
        anomalies = _compute_cohort_anomalies(trait_avgs, alumni)
        assert "virtue" in anomalies
        assert "manipulation" in anomalies

    def test_no_anomalies_when_close(self):
        trait_avgs = {"virtue": 0.75}
        alumni = {"virtue": 0.8}
        anomalies = _compute_cohort_anomalies(trait_avgs, alumni)
        assert anomalies == {}


class TestComputeCharacterDrift:
    def test_no_drift_with_few_evals(self):
        history = [_make_eval()] * 5
        assert _compute_character_drift(history) == 0.0

    def test_positive_drift(self):
        # Recent evals higher than historical
        recent = [_make_eval(0.9, 0.9, 0.9)] * 10
        older = [_make_eval(0.3, 0.3, 0.3)] * 10
        drift = _compute_character_drift(recent + older)
        assert drift > 0

    def test_negative_drift(self):
        recent = [_make_eval(0.3, 0.3, 0.3)] * 10
        older = [_make_eval(0.9, 0.9, 0.9)] * 10
        drift = _compute_character_drift(recent + older)
        assert drift < 0


class TestComputeBalanceTrend:
    def test_stable_with_few_evals(self):
        history = [_make_eval()] * 5
        assert _compute_balance_trend(history) == "stable"

    def test_stable_with_consistent_balance(self):
        history = [_make_eval(0.7, 0.7, 0.7)] * 12
        assert _compute_balance_trend(history) == "stable"
