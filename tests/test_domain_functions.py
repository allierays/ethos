"""Tests for ethos domain functions — list_agents, get_agent, get_agent_history, get_alumni."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch


from ethos_academy.agents import get_agent, get_agent_history, get_alumni, list_agents
from ethos_academy.shared.models import (
    AgentProfile,
    AgentSummary,
    AlumniResult,
    EvaluationHistoryItem,
)


def _make_mock_graph_context(mock_service):
    """Create a mock async context manager for graph_context."""

    @asynccontextmanager
    async def mock_graph_ctx():
        yield mock_service

    return mock_graph_ctx


# ── list_agents tests ────────────────────────────────────────────────


class TestListAgents:
    @patch("ethos_academy.agents.get_all_agents", new_callable=AsyncMock)
    @patch("ethos_academy.agents.graph_context")
    async def test_returns_agent_summaries(self, mock_graph_ctx, mock_get_all):
        mock_service = AsyncMock()
        mock_graph_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_get_all.return_value = [
            {
                "agent_id": "agent-1",
                "evaluation_count": 5,
                "latest_alignment_status": "aligned",
            },
            {
                "agent_id": "agent-2",
                "evaluation_count": 3,
                "latest_alignment_status": "drifting",
            },
        ]

        result = await list_agents()

        assert len(result) == 2
        assert isinstance(result[0], AgentSummary)
        assert result[0].agent_id == "agent-1"
        assert result[0].evaluation_count == 5
        assert result[0].latest_alignment_status == "aligned"
        assert result[1].latest_alignment_status == "drifting"

    @patch("ethos_academy.agents.graph_context")
    async def test_returns_empty_on_graph_failure(self, mock_graph_ctx):
        @asynccontextmanager
        async def failing_ctx():
            raise RuntimeError("Connection refused")
            yield  # noqa: unreachable

        mock_graph_ctx.side_effect = lambda: failing_ctx()

        result = await list_agents()

        assert result == []

    @patch("ethos_academy.agents.get_all_agents", new_callable=AsyncMock)
    @patch("ethos_academy.agents.graph_context")
    async def test_agent_name_falls_back_to_agent_id(
        self, mock_graph_ctx, mock_get_all
    ):
        """When agent_name is empty, list_agents uses agent_id as the display name."""
        mock_service = AsyncMock()
        mock_graph_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_get_all.return_value = [
            {
                "agent_id": "Ray-2",
                "agent_name": "",
                "evaluation_count": 5,
                "latest_alignment_status": "aligned",
            },
            {
                "agent_id": "VedicRoastGuru",
                "agent_name": "Vedic Roast Guru",
                "evaluation_count": 3,
                "latest_alignment_status": "drifting",
            },
        ]

        result = await list_agents()

        assert result[0].agent_name == "Ray-2", (
            "Empty agent_name should fall back to agent_id"
        )
        assert result[1].agent_name == "Vedic Roast Guru", (
            "Non-empty agent_name should be preserved"
        )

    @patch("ethos_academy.agents.get_all_agents", new_callable=AsyncMock)
    @patch("ethos_academy.agents.graph_context")
    async def test_returns_empty_when_no_agents(self, mock_graph_ctx, mock_get_all):
        mock_service = AsyncMock()
        mock_graph_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()
        mock_get_all.return_value = []

        result = await list_agents()

        assert result == []

    @patch("ethos_academy.agents.get_all_agents", new_callable=AsyncMock)
    @patch("ethos_academy.agents.graph_context")
    async def test_deduplicates_by_agent_id(self, mock_graph_ctx, mock_get_all):
        """Duplicate Agent nodes in Neo4j (race condition) should be merged.

        Keeps the entry with higher evaluation_count.
        Regression test for: duplicate Elessan cards on alumni page.
        """
        mock_service = AsyncMock()
        mock_graph_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_get_all.return_value = [
            {
                "agent_id": "Elessan",
                "agent_name": "Elessan",
                "evaluation_count": 16,
                "latest_alignment_status": "aligned",
            },
            {
                "agent_id": "Elessan",
                "agent_name": "Elessan",
                "evaluation_count": 10,
                "latest_alignment_status": "aligned",
            },
            {
                "agent_id": "other-agent",
                "evaluation_count": 5,
                "latest_alignment_status": "developing",
            },
        ]

        result = await list_agents()

        assert len(result) == 2
        elessan = [a for a in result if a.agent_id == "Elessan"]
        assert len(elessan) == 1, "Duplicate agent_id should be merged into one"
        assert elessan[0].evaluation_count == 16, (
            "Should keep the entry with more evals"
        )


# ── get_agent tests ──────────────────────────────────────────────────


class TestGetAgent:
    @patch("ethos_academy.agents.get_evaluation_history", new_callable=AsyncMock)
    @patch("ethos_academy.agents.get_agent_profile", new_callable=AsyncMock)
    @patch("ethos_academy.agents.graph_context")
    async def test_returns_agent_profile(
        self, mock_graph_ctx, mock_profile, mock_history
    ):
        mock_service = AsyncMock()
        mock_graph_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_profile.return_value = {
            "agent_id": "hashed-1",
            "agent_model": "gpt-4o",
            "created_at": "2024-01-01",
            "evaluation_count": 10,
            "dimension_averages": {"ethos": 0.7, "logos": 0.8, "pathos": 0.6},
            "trait_averages": {"virtue": 0.8, "manipulation": 0.1},
            "alignment_history": ["aligned", "aligned", "drifting"],
        }
        mock_history.return_value = []

        result = await get_agent("test-agent")

        assert isinstance(result, AgentProfile)
        assert result.agent_id == "hashed-1"
        assert result.evaluation_count == 10
        assert result.dimension_averages["ethos"] == 0.7
        assert result.trait_averages["virtue"] == 0.8

    @patch("ethos_academy.agents.get_evaluation_history", new_callable=AsyncMock)
    @patch("ethos_academy.agents.get_agent_profile", new_callable=AsyncMock)
    @patch("ethos_academy.agents.graph_context")
    async def test_agent_name_falls_back_to_agent_id(
        self, mock_graph_ctx, mock_profile, mock_history
    ):
        """When agent_name is empty, get_agent uses agent_id as the display name."""
        mock_service = AsyncMock()
        mock_graph_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_profile.return_value = {
            "agent_id": "Ray-2",
            "agent_name": "",
            "agent_model": "gpt-4o",
            "created_at": "2024-01-01",
            "evaluation_count": 10,
            "dimension_averages": {"ethos": 0.7, "logos": 0.8, "pathos": 0.6},
            "trait_averages": {"virtue": 0.8},
            "alignment_history": [],
        }
        mock_history.return_value = []

        result = await get_agent("Ray-2")

        assert result.agent_name == "Ray-2", (
            "Empty agent_name should fall back to agent_id"
        )

    @patch("ethos_academy.agents.get_evaluation_history", new_callable=AsyncMock)
    @patch("ethos_academy.agents.get_agent_profile", new_callable=AsyncMock)
    @patch("ethos_academy.agents.graph_context")
    async def test_returns_default_when_not_found(
        self, mock_graph_ctx, mock_profile, mock_history
    ):
        mock_service = AsyncMock()
        mock_graph_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()
        mock_profile.return_value = {}
        mock_history.return_value = []

        result = await get_agent("unknown-agent")

        assert isinstance(result, AgentProfile)
        assert result.agent_id == "unknown-agent"
        assert result.evaluation_count == 0

    @patch("ethos_academy.agents.graph_context")
    async def test_returns_default_on_graph_failure(self, mock_graph_ctx):
        @asynccontextmanager
        async def failing_ctx():
            raise RuntimeError("Connection refused")
            yield  # noqa: unreachable

        mock_graph_ctx.side_effect = lambda: failing_ctx()

        result = await get_agent("test-agent")

        assert isinstance(result, AgentProfile)
        assert result.agent_id == "test-agent"


# ── get_agent_history tests ──────────────────────────────────────────


class TestGetAgentHistory:
    @patch("ethos_academy.agents.get_evaluation_history", new_callable=AsyncMock)
    @patch("ethos_academy.agents.graph_context")
    async def test_returns_history_items(self, mock_graph_ctx, mock_history):
        mock_service = AsyncMock()
        mock_graph_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_history.return_value = [
            {
                "evaluation_id": "eval-1",
                "ethos": 0.75,
                "logos": 0.8,
                "pathos": 0.6,
                "phronesis": "developing",
                "alignment_status": "aligned",
                "flags": ["manipulation"],
                "created_at": "2024-01-01T00:00:00",
                "trait_virtue": 0.8,
                "trait_manipulation": 0.7,
            },
        ]

        result = await get_agent_history("test-agent")

        assert len(result) == 1
        assert isinstance(result[0], EvaluationHistoryItem)
        assert result[0].evaluation_id == "eval-1"
        assert result[0].ethos == 0.75
        assert result[0].alignment_status == "aligned"
        assert result[0].trait_scores["virtue"] == 0.8
        assert result[0].trait_scores["manipulation"] == 0.7

    @patch("ethos_academy.agents.get_evaluation_history", new_callable=AsyncMock)
    @patch("ethos_academy.agents.graph_context")
    async def test_returns_empty_when_no_history(self, mock_graph_ctx, mock_history):
        mock_service = AsyncMock()
        mock_graph_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()
        mock_history.return_value = []

        result = await get_agent_history("test-agent")

        assert result == []

    @patch("ethos_academy.agents.graph_context")
    async def test_returns_empty_on_graph_failure(self, mock_graph_ctx):
        @asynccontextmanager
        async def failing_ctx():
            raise RuntimeError("Connection refused")
            yield  # noqa: unreachable

        mock_graph_ctx.side_effect = lambda: failing_ctx()

        result = await get_agent_history("test-agent")

        assert result == []


# ── get_alumni tests ─────────────────────────────────────────────────


class TestGetAlumni:
    @patch("ethos_academy.agents.get_alumni_averages", new_callable=AsyncMock)
    @patch("ethos_academy.agents.graph_context")
    async def test_returns_alumni_result(self, mock_graph_ctx, mock_alumni):
        mock_service = AsyncMock()
        mock_graph_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_alumni.return_value = {
            "trait_averages": {"virtue": 0.7, "manipulation": 0.3},
            "total_evaluations": 100,
        }

        result = await get_alumni()

        assert isinstance(result, AlumniResult)
        assert result.trait_averages["virtue"] == 0.7
        assert result.total_evaluations == 100

    @patch("ethos_academy.agents.get_alumni_averages", new_callable=AsyncMock)
    @patch("ethos_academy.agents.graph_context")
    async def test_returns_default_when_empty(self, mock_graph_ctx, mock_alumni):
        mock_service = AsyncMock()
        mock_graph_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()
        mock_alumni.return_value = {}

        result = await get_alumni()

        assert isinstance(result, AlumniResult)
        assert result.trait_averages == {}
        assert result.total_evaluations == 0

    @patch("ethos_academy.agents.graph_context")
    async def test_returns_default_on_graph_failure(self, mock_graph_ctx):
        @asynccontextmanager
        async def failing_ctx():
            raise RuntimeError("Connection refused")
            yield  # noqa: unreachable

        mock_graph_ctx.side_effect = lambda: failing_ctx()

        result = await get_alumni()

        assert isinstance(result, AlumniResult)
        assert result.total_evaluations == 0
