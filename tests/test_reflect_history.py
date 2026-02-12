"""Tests for ethos.reflection.history — reflect_history()."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ethos.reflection.history import reflect_history
from ethos.shared.models import ReflectionResult


def _make_eval(ethos: float, logos: float, pathos: float) -> dict:
    return {"ethos": ethos, "logos": logos, "pathos": pathos}


class TestReflectHistory:
    @patch("ethos.graph.service.GraphService")
    def test_returns_default_when_graph_unavailable(self, mock_gs_cls):
        mock_service = MagicMock()
        mock_service.connected = False
        mock_gs_cls.return_value = mock_service

        result = reflect_history("test-agent")

        assert isinstance(result, ReflectionResult)
        assert result.agent_id == "test-agent"
        assert result.trend == "insufficient_data"

    @patch("ethos.reflection.history.get_evaluation_history")
    @patch("ethos.reflection.history.get_agent_profile")
    @patch("ethos.graph.service.GraphService")
    def test_returns_profile_with_averages(
        self, mock_gs_cls, mock_profile, mock_history
    ):
        mock_service = MagicMock()
        mock_service.connected = True
        mock_gs_cls.return_value = mock_service

        mock_profile.return_value = {
            "agent_id": "hashed",
            "evaluation_count": 12,
            "dimension_averages": {"ethos": 0.7, "logos": 0.8, "pathos": 0.6},
            "trait_averages": {"virtue": 0.8, "compassion": 0.65, "accuracy": 0.9},
        }
        mock_history.return_value = [_make_eval(0.7, 0.8, 0.6)] * 12

        result = reflect_history("my-bot")

        assert result.agent_id == "my-bot"
        assert result.ethos == 0.7
        assert result.logos == 0.8
        assert result.pathos == 0.6
        assert result.evaluation_count == 12
        assert result.trait_averages["virtue"] == 0.8

    @patch("ethos.reflection.history.get_evaluation_history")
    @patch("ethos.reflection.history.get_agent_profile")
    @patch("ethos.graph.service.GraphService")
    def test_returns_default_when_no_profile(
        self, mock_gs_cls, mock_profile, mock_history
    ):
        mock_service = MagicMock()
        mock_service.connected = True
        mock_gs_cls.return_value = mock_service

        mock_profile.return_value = {}
        mock_history.return_value = []

        result = reflect_history("unknown")

        assert result.agent_id == "unknown"
        assert result.trend == "insufficient_data"
        assert result.evaluation_count == 0

    @patch("ethos.graph.service.GraphService")
    def test_handles_graph_exception(self, mock_gs_cls):
        mock_gs_cls.side_effect = RuntimeError("Connection refused")

        result = reflect_history("agent-1")

        assert isinstance(result, ReflectionResult)
        assert result.trend == "insufficient_data"

    @patch("ethos.reflection.history.get_evaluation_history")
    @patch("ethos.reflection.history.get_agent_profile")
    @patch("ethos.graph.service.GraphService")
    def test_backward_compat_fields(
        self, mock_gs_cls, mock_profile, mock_history
    ):
        mock_service = MagicMock()
        mock_service.connected = True
        mock_gs_cls.return_value = mock_service

        mock_profile.return_value = {
            "evaluation_count": 3,
            "dimension_averages": {"ethos": 0.6, "logos": 0.7, "pathos": 0.5},
            "trait_averages": {"compassion": 0.65, "accuracy": 0.82},
        }
        mock_history.return_value = [_make_eval(0.6, 0.7, 0.5)] * 3

        result = reflect_history("agent-1")

        assert result.compassion == 0.65
        assert result.honesty == 0.82
        assert result.accuracy == 0.82
