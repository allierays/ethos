"""Tests for ethos.reflection.reflect — agent reflection and trend computation."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from ethos_academy.reflection.reflect import reflect
from ethos_academy.shared.analysis import compute_trend
from ethos_academy.shared.models import EvaluationResult, ReflectionResult


# ── compute_trend tests ──────────────────────────────────────────────


def _make_eval(ethos: float, logos: float, pathos: float) -> dict:
    """Helper to build a minimal evaluation dict for trend testing."""
    return {"ethos": ethos, "logos": logos, "pathos": pathos}


class TestComputeTrend:
    def test_insufficient_data_fewer_than_2(self):
        evals = [_make_eval(0.8, 0.8, 0.8)]
        assert compute_trend(evals) == "insufficient_data"

    def test_fallback_to_temporal_pattern_with_few_evals(self):
        """With 3-9 evals, falls back to detect_temporal_pattern."""
        evals = [_make_eval(0.8, 0.8, 0.8)] * 5
        assert compute_trend(evals) == "stable"

    def test_insufficient_data_empty(self):
        assert compute_trend([]) == "insufficient_data"

    def test_stable_when_scores_similar(self):
        # All 10 evals have same scores -> diff = 0 -> stable
        evals = [_make_eval(0.7, 0.7, 0.7)] * 10
        assert compute_trend(evals) == "stable"

    def test_improving_when_recent_higher(self):
        # Recent 5 (index 0-4): high scores, older 5 (index 5-9): low scores
        recent = [_make_eval(0.9, 0.9, 0.9)] * 5
        older = [_make_eval(0.3, 0.3, 0.3)] * 5
        evals = recent + older  # newest first
        assert compute_trend(evals) == "improving"

    def test_declining_when_recent_lower(self):
        # Recent 5: low scores, older 5: high scores
        recent = [_make_eval(0.3, 0.3, 0.3)] * 5
        older = [_make_eval(0.9, 0.9, 0.9)] * 5
        evals = recent + older
        assert compute_trend(evals) == "declining"

    def test_stable_when_diff_within_threshold(self):
        # Recent avg = 0.6, older avg = 0.55 -> diff = 0.05 -> stable
        recent = [_make_eval(0.6, 0.6, 0.6)] * 5
        older = [_make_eval(0.55, 0.55, 0.55)] * 5
        evals = recent + older
        assert compute_trend(evals) == "stable"

    def test_exactly_10_evaluations(self):
        evals = [_make_eval(0.5, 0.5, 0.5)] * 10
        assert compute_trend(evals) == "stable"


# ── reflect() tests ─────────────────────────────────────────────────


def _mock_graph_context(connected=True, profile=None, history=None):
    """Create a mock async graph_context context manager."""
    mock_service = MagicMock()
    mock_service.connected = connected

    @asynccontextmanager
    async def mock_ctx():
        yield mock_service

    return mock_ctx, mock_service


class TestReflect:
    """Test reflect() with mocked graph and evaluate."""

    async def test_returns_default_when_graph_unavailable(self):
        """When Neo4j is down, return default ReflectionResult."""
        mock_ctx, _ = _mock_graph_context(connected=False)

        with patch("ethos_academy.reflection.reflect.graph_context", mock_ctx):
            result = await reflect("test-agent")

        assert isinstance(result, ReflectionResult)
        assert result.agent_id == "test-agent"
        assert result.trend == "insufficient_data"
        assert result.ethos == 0.0

    async def test_returns_default_when_agent_not_found(self):
        """When agent has no profile, return default ReflectionResult."""
        mock_ctx, _ = _mock_graph_context(connected=True)

        with (
            patch("ethos_academy.reflection.reflect.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.reflect.get_agent_profile",
                new_callable=AsyncMock,
                return_value={},
            ),
            patch(
                "ethos_academy.reflection.reflect.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            result = await reflect("unknown-agent")

        assert result.agent_id == "unknown-agent"
        assert result.trend == "insufficient_data"
        assert result.evaluation_count == 0

    async def test_returns_profile_with_averages(self):
        """When agent exists with history, return populated ReflectionResult."""
        mock_ctx, _ = _mock_graph_context(connected=True)

        profile = {
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
        history = [_make_eval(0.7, 0.7, 0.7)] * 15

        with (
            patch("ethos_academy.reflection.reflect.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.reflect.get_agent_profile",
                new_callable=AsyncMock,
                return_value=profile,
            ),
            patch(
                "ethos_academy.reflection.reflect.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=history,
            ),
        ):
            result = await reflect("my-bot")

        assert result.agent_id == "my-bot"
        assert result.ethos == 0.75
        assert result.logos == 0.8
        assert result.pathos == 0.65
        assert result.evaluation_count == 15
        assert result.trend == "stable"
        assert result.trait_averages["virtue"] == 0.8
        assert result.trait_averages["compassion"] == 0.6

    async def test_trend_stable_with_few_consistent_evals(self):
        """With 3-9 consistent evaluations, trend falls back to stable."""
        mock_ctx, _ = _mock_graph_context(connected=True)

        with (
            patch("ethos_academy.reflection.reflect.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.reflect.get_agent_profile",
                new_callable=AsyncMock,
                return_value={
                    "agent_id": "hashed",
                    "evaluation_count": 5,
                    "dimension_averages": {"ethos": 0.6, "logos": 0.6, "pathos": 0.6},
                    "trait_averages": {},
                },
            ),
            patch(
                "ethos_academy.reflection.reflect.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[_make_eval(0.6, 0.6, 0.6)] * 5,
            ),
        ):
            result = await reflect("new-agent")

        assert result.trend == "stable"

    async def test_evaluates_text_when_provided(self):
        """When text is provided, evaluate() is called before reflecting."""
        mock_ctx, _ = _mock_graph_context(connected=True)

        mock_evaluate = AsyncMock(
            return_value=EvaluationResult(
                evaluation_id="eval-1",
                ethos=0.7,
                logos=0.8,
                pathos=0.6,
                phronesis="developing",
                alignment_status="aligned",
            )
        )

        with (
            patch("ethos_academy.reflection.reflect.evaluate", mock_evaluate),
            patch("ethos_academy.reflection.reflect.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.reflect.get_agent_profile",
                new_callable=AsyncMock,
                return_value={
                    "agent_id": "hashed",
                    "evaluation_count": 1,
                    "dimension_averages": {"ethos": 0.7, "logos": 0.8, "pathos": 0.6},
                    "trait_averages": {"virtue": 0.8},
                },
            ),
            patch(
                "ethos_academy.reflection.reflect.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[_make_eval(0.7, 0.8, 0.6)],
            ),
        ):
            result = await reflect("my-bot", text="Hello, I'm a helpful assistant!")

        mock_evaluate.assert_called_once_with(
            "Hello, I'm a helpful assistant!", source="my-bot"
        )
        assert result.agent_id == "my-bot"
        assert result.ethos == 0.7

    async def test_evaluate_failure_does_not_crash(self):
        """If evaluate() raises, reflect still returns a profile."""
        mock_ctx, _ = _mock_graph_context(connected=True)

        mock_evaluate = AsyncMock(side_effect=RuntimeError("Claude API down"))

        with (
            patch("ethos_academy.reflection.reflect.evaluate", mock_evaluate),
            patch("ethos_academy.reflection.reflect.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.reflect.get_agent_profile",
                new_callable=AsyncMock,
                return_value={
                    "agent_id": "hashed",
                    "evaluation_count": 3,
                    "dimension_averages": {"ethos": 0.5, "logos": 0.5, "pathos": 0.5},
                    "trait_averages": {},
                },
            ),
            patch(
                "ethos_academy.reflection.reflect.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[_make_eval(0.5, 0.5, 0.5)] * 3,
            ),
        ):
            result = await reflect("my-bot", text="test message")

        assert isinstance(result, ReflectionResult)
        assert result.agent_id == "my-bot"
        assert result.evaluation_count == 3

    async def test_no_text_does_not_call_evaluate(self):
        """When text is None, evaluate() is NOT called."""
        mock_ctx, _ = _mock_graph_context(connected=False)
        mock_evaluate = AsyncMock()

        with (
            patch("ethos_academy.reflection.reflect.evaluate", mock_evaluate),
            patch("ethos_academy.reflection.reflect.graph_context", mock_ctx),
        ):
            await reflect("my-bot")

        mock_evaluate.assert_not_called()

    async def test_backward_compat_fields(self):
        """Backward-compat compassion/honesty/accuracy fields are populated."""
        mock_ctx, _ = _mock_graph_context(connected=True)

        with (
            patch("ethos_academy.reflection.reflect.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.reflect.get_agent_profile",
                new_callable=AsyncMock,
                return_value={
                    "agent_id": "hashed",
                    "evaluation_count": 2,
                    "dimension_averages": {"ethos": 0.6, "logos": 0.7, "pathos": 0.5},
                    "trait_averages": {
                        "compassion": 0.65,
                        "accuracy": 0.82,
                    },
                },
            ),
            patch(
                "ethos_academy.reflection.reflect.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[_make_eval(0.6, 0.7, 0.5)] * 2,
            ),
        ):
            result = await reflect("agent-1")

        assert result.compassion == 0.65
        assert result.honesty == 0.82
        assert result.accuracy == 0.82

    async def test_graph_exception_returns_default(self):
        """When graph_context raises, return default ReflectionResult."""

        @asynccontextmanager
        async def failing_ctx():
            raise RuntimeError("Connection refused")
            yield  # noqa: unreachable

        with patch("ethos_academy.reflection.reflect.graph_context", failing_ctx):
            result = await reflect("agent-1")

        assert isinstance(result, ReflectionResult)
        assert result.agent_id == "agent-1"
        assert result.trend == "insufficient_data"
