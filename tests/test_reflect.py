"""Tests for ethos.reflect — agent reflection and trend computation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ethos.reflect import _compute_trend, reflect
from ethos.shared.models import EvaluationResult, ReflectionResult


# ── _compute_trend tests ─────────────────────────────────────────────


def _make_eval(ethos: float, logos: float, pathos: float) -> dict:
    """Helper to build a minimal evaluation dict for trend testing."""
    return {"ethos": ethos, "logos": logos, "pathos": pathos}


class TestComputeTrend:
    def test_insufficient_data_fewer_than_10(self):
        evals = [_make_eval(0.8, 0.8, 0.8)] * 9
        assert _compute_trend(evals) == "insufficient_data"

    def test_insufficient_data_empty(self):
        assert _compute_trend([]) == "insufficient_data"

    def test_stable_when_scores_similar(self):
        # All 10 evals have same scores → diff = 0 → stable
        evals = [_make_eval(0.7, 0.7, 0.7)] * 10
        assert _compute_trend(evals) == "stable"

    def test_improving_when_recent_higher(self):
        # Recent 5 (index 0-4): high scores, older 5 (index 5-9): low scores
        recent = [_make_eval(0.9, 0.9, 0.9)] * 5
        older = [_make_eval(0.3, 0.3, 0.3)] * 5
        evals = recent + older  # newest first
        assert _compute_trend(evals) == "improving"

    def test_declining_when_recent_lower(self):
        # Recent 5: low scores, older 5: high scores
        recent = [_make_eval(0.3, 0.3, 0.3)] * 5
        older = [_make_eval(0.9, 0.9, 0.9)] * 5
        evals = recent + older
        assert _compute_trend(evals) == "declining"

    def test_stable_when_diff_within_threshold(self):
        # Recent avg = 0.6, older avg = 0.55 → diff = 0.05 → stable
        recent = [_make_eval(0.6, 0.6, 0.6)] * 5
        older = [_make_eval(0.55, 0.55, 0.55)] * 5
        evals = recent + older
        assert _compute_trend(evals) == "stable"

    def test_exactly_10_evaluations(self):
        evals = [_make_eval(0.5, 0.5, 0.5)] * 10
        assert _compute_trend(evals) == "stable"


# ── reflect() tests ──────────────────────────────────────────────────


class TestReflect:
    """Test reflect() with mocked graph and evaluate."""

    @patch("ethos.reflect.GraphService")
    def test_returns_default_when_graph_unavailable(self, mock_gs_cls):
        """When Neo4j is down, return default ReflectionResult."""
        mock_service = MagicMock()
        mock_service.connected = False
        mock_gs_cls.return_value = mock_service

        result = reflect("test-agent")

        assert isinstance(result, ReflectionResult)
        assert result.agent_id == "test-agent"
        assert result.trend == "insufficient_data"
        assert result.ethos == 0.0

    @patch("ethos.reflect.get_evaluation_history")
    @patch("ethos.reflect.get_agent_profile")
    @patch("ethos.reflect.GraphService")
    def test_returns_default_when_agent_not_found(
        self, mock_gs_cls, mock_profile, mock_history
    ):
        """When agent has no profile, return default ReflectionResult."""
        mock_service = MagicMock()
        mock_service.connected = True
        mock_gs_cls.return_value = mock_service
        mock_profile.return_value = {}
        mock_history.return_value = []

        result = reflect("unknown-agent")

        assert result.agent_id == "unknown-agent"
        assert result.trend == "insufficient_data"
        assert result.evaluation_count == 0

    @patch("ethos.reflect.get_evaluation_history")
    @patch("ethos.reflect.get_agent_profile")
    @patch("ethos.reflect.GraphService")
    def test_returns_profile_with_averages(
        self, mock_gs_cls, mock_profile, mock_history
    ):
        """When agent exists with history, return populated ReflectionResult."""
        mock_service = MagicMock()
        mock_service.connected = True
        mock_gs_cls.return_value = mock_service

        mock_profile.return_value = {
            "agent_id": "hashed-id",
            "evaluation_count": 15,
            "dimension_averages": {
                "ethos": 0.75,
                "logos": 0.8,
                "pathos": 0.65,
            },
            "trait_averages": {
                "virtue": 0.8,
                "goodwill": 0.7,
                "manipulation": 0.2,
                "deception": 0.1,
                "accuracy": 0.85,
                "reasoning": 0.9,
                "fabrication": 0.05,
                "broken_logic": 0.1,
                "recognition": 0.7,
                "compassion": 0.6,
                "dismissal": 0.15,
                "exploitation": 0.1,
            },
            "alignment_history": ["aligned", "aligned", "drifting"],
        }

        # 15 evals, all with similar scores → stable
        mock_history.return_value = [_make_eval(0.7, 0.7, 0.7)] * 15

        result = reflect("my-bot")

        assert result.agent_id == "my-bot"
        assert result.ethos == 0.75
        assert result.logos == 0.8
        assert result.pathos == 0.65
        assert result.evaluation_count == 15
        assert result.trend == "stable"
        assert result.trait_averages["virtue"] == 0.8
        assert result.trait_averages["compassion"] == 0.6

    @patch("ethos.reflect.get_evaluation_history")
    @patch("ethos.reflect.get_agent_profile")
    @patch("ethos.reflect.GraphService")
    def test_trend_insufficient_data_with_few_evals(
        self, mock_gs_cls, mock_profile, mock_history
    ):
        """With fewer than 10 evaluations, trend is insufficient_data."""
        mock_service = MagicMock()
        mock_service.connected = True
        mock_gs_cls.return_value = mock_service

        mock_profile.return_value = {
            "agent_id": "hashed",
            "evaluation_count": 5,
            "dimension_averages": {"ethos": 0.6, "logos": 0.6, "pathos": 0.6},
            "trait_averages": {},
        }
        mock_history.return_value = [_make_eval(0.6, 0.6, 0.6)] * 5

        result = reflect("new-agent")
        assert result.trend == "insufficient_data"

    @patch("ethos.reflect.evaluate")
    @patch("ethos.reflect.get_evaluation_history")
    @patch("ethos.reflect.get_agent_profile")
    @patch("ethos.reflect.GraphService")
    def test_evaluates_text_when_provided(
        self, mock_gs_cls, mock_profile, mock_history, mock_evaluate
    ):
        """When text is provided, evaluate() is called before reflecting."""
        mock_service = MagicMock()
        mock_service.connected = True
        mock_gs_cls.return_value = mock_service

        mock_evaluate.return_value = EvaluationResult(
            evaluation_id="eval-1",
            ethos=0.7,
            logos=0.8,
            pathos=0.6,
            trust="developing",
            alignment_status="aligned",
        )

        mock_profile.return_value = {
            "agent_id": "hashed",
            "evaluation_count": 1,
            "dimension_averages": {"ethos": 0.7, "logos": 0.8, "pathos": 0.6},
            "trait_averages": {"virtue": 0.8},
        }
        mock_history.return_value = [_make_eval(0.7, 0.8, 0.6)]

        result = reflect("my-bot", text="Hello, I'm a helpful assistant!")

        mock_evaluate.assert_called_once_with(
            "Hello, I'm a helpful assistant!", source="my-bot"
        )
        assert result.agent_id == "my-bot"
        assert result.ethos == 0.7

    @patch("ethos.reflect.evaluate")
    @patch("ethos.reflect.get_evaluation_history")
    @patch("ethos.reflect.get_agent_profile")
    @patch("ethos.reflect.GraphService")
    def test_evaluate_failure_does_not_crash(
        self, mock_gs_cls, mock_profile, mock_history, mock_evaluate
    ):
        """If evaluate() raises, reflect still returns a profile."""
        mock_service = MagicMock()
        mock_service.connected = True
        mock_gs_cls.return_value = mock_service

        mock_evaluate.side_effect = RuntimeError("Claude API down")

        mock_profile.return_value = {
            "agent_id": "hashed",
            "evaluation_count": 3,
            "dimension_averages": {"ethos": 0.5, "logos": 0.5, "pathos": 0.5},
            "trait_averages": {},
        }
        mock_history.return_value = [_make_eval(0.5, 0.5, 0.5)] * 3

        result = reflect("my-bot", text="test message")

        assert isinstance(result, ReflectionResult)
        assert result.agent_id == "my-bot"
        assert result.evaluation_count == 3

    @patch("ethos.reflect.evaluate")
    @patch("ethos.reflect.GraphService")
    def test_no_text_does_not_call_evaluate(self, mock_gs_cls, mock_evaluate):
        """When text is None, evaluate() is NOT called."""
        mock_service = MagicMock()
        mock_service.connected = False
        mock_gs_cls.return_value = mock_service

        reflect("my-bot")

        mock_evaluate.assert_not_called()

    @patch("ethos.reflect.get_evaluation_history")
    @patch("ethos.reflect.get_agent_profile")
    @patch("ethos.reflect.GraphService")
    def test_backward_compat_fields(
        self, mock_gs_cls, mock_profile, mock_history
    ):
        """Backward-compat compassion/honesty/accuracy fields are populated."""
        mock_service = MagicMock()
        mock_service.connected = True
        mock_gs_cls.return_value = mock_service

        mock_profile.return_value = {
            "agent_id": "hashed",
            "evaluation_count": 2,
            "dimension_averages": {"ethos": 0.6, "logos": 0.7, "pathos": 0.5},
            "trait_averages": {
                "compassion": 0.65,
                "accuracy": 0.82,
            },
        }
        mock_history.return_value = [_make_eval(0.6, 0.7, 0.5)] * 2

        result = reflect("agent-1")

        assert result.compassion == 0.65
        assert result.honesty == 0.82
        assert result.accuracy == 0.82

    @patch("ethos.reflect.GraphService")
    def test_graph_exception_returns_default(self, mock_gs_cls):
        """When GraphService raises, return default ReflectionResult."""
        mock_gs_cls.side_effect = RuntimeError("Connection refused")

        result = reflect("agent-1")

        assert isinstance(result, ReflectionResult)
        assert result.agent_id == "agent-1"
        assert result.trend == "insufficient_data"
