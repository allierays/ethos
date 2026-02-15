"""Tests for ethos.reflection.history — reflect_history()."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from ethos_academy.reflection.history import reflect_history
from ethos_academy.shared.models import ReflectionResult


def _make_eval(ethos: float, logos: float, pathos: float) -> dict:
    return {"ethos": ethos, "logos": logos, "pathos": pathos}


def _mock_graph_context(connected=True):
    """Create a mock async graph_context context manager."""
    mock_service = MagicMock()
    mock_service.connected = connected

    @asynccontextmanager
    async def mock_ctx():
        yield mock_service

    return mock_ctx, mock_service


class TestReflectHistory:
    async def test_returns_default_when_graph_unavailable(self):
        mock_ctx, _ = _mock_graph_context(connected=False)

        with patch("ethos_academy.reflection.history.graph_context", mock_ctx):
            result = await reflect_history("test-agent")

        assert isinstance(result, ReflectionResult)
        assert result.agent_id == "test-agent"
        assert result.trend == "insufficient_data"

    async def test_returns_profile_with_averages(self):
        mock_ctx, _ = _mock_graph_context(connected=True)

        with (
            patch("ethos_academy.reflection.history.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.history.get_agent_profile",
                new_callable=AsyncMock,
                return_value={
                    "agent_id": "hashed",
                    "evaluation_count": 12,
                    "dimension_averages": {"ethos": 0.7, "logos": 0.8, "pathos": 0.6},
                    "trait_averages": {
                        "virtue": 0.8,
                        "compassion": 0.65,
                        "accuracy": 0.9,
                    },
                },
            ),
            patch(
                "ethos_academy.reflection.history.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[_make_eval(0.7, 0.8, 0.6)] * 12,
            ),
        ):
            result = await reflect_history("my-bot")

        assert result.agent_id == "my-bot"
        assert result.ethos == 0.7
        assert result.logos == 0.8
        assert result.pathos == 0.6
        assert result.evaluation_count == 12
        assert result.trait_averages["virtue"] == 0.8

    async def test_returns_default_when_no_profile(self):
        mock_ctx, _ = _mock_graph_context(connected=True)

        with (
            patch("ethos_academy.reflection.history.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.history.get_agent_profile",
                new_callable=AsyncMock,
                return_value={},
            ),
            patch(
                "ethos_academy.reflection.history.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            result = await reflect_history("unknown")

        assert result.agent_id == "unknown"
        assert result.trend == "insufficient_data"
        assert result.evaluation_count == 0

    async def test_handles_graph_exception(self):
        @asynccontextmanager
        async def failing_ctx():
            raise RuntimeError("Connection refused")
            yield  # noqa: unreachable

        with patch("ethos_academy.reflection.history.graph_context", failing_ctx):
            result = await reflect_history("agent-1")

        assert isinstance(result, ReflectionResult)
        assert result.trend == "insufficient_data"

    async def test_backward_compat_fields(self):
        mock_ctx, _ = _mock_graph_context(connected=True)

        with (
            patch("ethos_academy.reflection.history.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.history.get_agent_profile",
                new_callable=AsyncMock,
                return_value={
                    "evaluation_count": 3,
                    "dimension_averages": {"ethos": 0.6, "logos": 0.7, "pathos": 0.5},
                    "trait_averages": {"compassion": 0.65, "accuracy": 0.82},
                },
            ),
            patch(
                "ethos_academy.reflection.history.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[_make_eval(0.6, 0.7, 0.5)] * 3,
            ),
        ):
            result = await reflect_history("agent-1")

        assert result.compassion == 0.65
        assert result.honesty == 0.82
        assert result.accuracy == 0.82
