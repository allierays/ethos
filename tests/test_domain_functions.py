"""Tests for ethos domain functions — list_agents, get_agent, get_agent_history, get_alumni."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ethos.agents import get_agent, get_agent_history, get_alumni, list_agents
from ethos.shared.models import (
    AgentProfile,
    AgentSummary,
    AlumniResult,
    EvaluationHistoryItem,
)


# ── list_agents tests ────────────────────────────────────────────────


class TestListAgents:
    @patch("ethos.agents.get_all_agents")
    @patch("ethos.graph.service.GraphService")
    def test_returns_agent_summaries(self, mock_gs_cls, mock_get_all):
        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service

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

        result = list_agents()

        assert len(result) == 2
        assert isinstance(result[0], AgentSummary)
        assert result[0].agent_id == "agent-1"
        assert result[0].evaluation_count == 5
        assert result[0].latest_alignment_status == "aligned"
        assert result[1].latest_alignment_status == "drifting"

    @patch("ethos.graph.service.GraphService")
    def test_returns_empty_on_graph_failure(self, mock_gs_cls):
        mock_gs_cls.side_effect = RuntimeError("Connection refused")

        result = list_agents()

        assert result == []

    @patch("ethos.agents.get_all_agents")
    @patch("ethos.graph.service.GraphService")
    def test_returns_empty_when_no_agents(self, mock_gs_cls, mock_get_all):
        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service
        mock_get_all.return_value = []

        result = list_agents()

        assert result == []


# ── get_agent tests ──────────────────────────────────────────────────


class TestGetAgent:
    @patch("ethos.agents.get_agent_profile")
    @patch("ethos.graph.service.GraphService")
    def test_returns_agent_profile(self, mock_gs_cls, mock_profile):
        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service

        mock_profile.return_value = {
            "agent_id": "hashed-1",
            "agent_model": "gpt-4o",
            "created_at": "2024-01-01",
            "evaluation_count": 10,
            "dimension_averages": {"ethos": 0.7, "logos": 0.8, "pathos": 0.6},
            "trait_averages": {"virtue": 0.8, "manipulation": 0.1},
            "alignment_history": ["aligned", "aligned", "drifting"],
        }

        result = get_agent("test-agent")

        assert isinstance(result, AgentProfile)
        assert result.agent_id == "hashed-1"
        assert result.evaluation_count == 10
        assert result.dimension_averages["ethos"] == 0.7
        assert result.trait_averages["virtue"] == 0.8

    @patch("ethos.agents.get_agent_profile")
    @patch("ethos.graph.service.GraphService")
    def test_returns_default_when_not_found(self, mock_gs_cls, mock_profile):
        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service
        mock_profile.return_value = {}

        result = get_agent("unknown-agent")

        assert isinstance(result, AgentProfile)
        assert result.agent_id == "unknown-agent"
        assert result.evaluation_count == 0

    @patch("ethos.graph.service.GraphService")
    def test_returns_default_on_graph_failure(self, mock_gs_cls):
        mock_gs_cls.side_effect = RuntimeError("Connection refused")

        result = get_agent("test-agent")

        assert isinstance(result, AgentProfile)
        assert result.agent_id == "test-agent"


# ── get_agent_history tests ──────────────────────────────────────────


class TestGetAgentHistory:
    @patch("ethos.agents.get_evaluation_history")
    @patch("ethos.graph.service.GraphService")
    def test_returns_history_items(self, mock_gs_cls, mock_history):
        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service

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

        result = get_agent_history("test-agent")

        assert len(result) == 1
        assert isinstance(result[0], EvaluationHistoryItem)
        assert result[0].evaluation_id == "eval-1"
        assert result[0].ethos == 0.75
        assert result[0].alignment_status == "aligned"
        assert result[0].trait_scores["virtue"] == 0.8
        assert result[0].trait_scores["manipulation"] == 0.7

    @patch("ethos.agents.get_evaluation_history")
    @patch("ethos.graph.service.GraphService")
    def test_returns_empty_when_no_history(self, mock_gs_cls, mock_history):
        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service
        mock_history.return_value = []

        result = get_agent_history("test-agent")

        assert result == []

    @patch("ethos.graph.service.GraphService")
    def test_returns_empty_on_graph_failure(self, mock_gs_cls):
        mock_gs_cls.side_effect = RuntimeError("Connection refused")

        result = get_agent_history("test-agent")

        assert result == []


# ── get_alumni tests ─────────────────────────────────────────────────


class TestGetAlumni:
    @patch("ethos.agents.get_alumni_averages")
    @patch("ethos.graph.service.GraphService")
    def test_returns_alumni_result(self, mock_gs_cls, mock_alumni):
        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service

        mock_alumni.return_value = {
            "trait_averages": {"virtue": 0.7, "manipulation": 0.3},
            "total_evaluations": 100,
        }

        result = get_alumni()

        assert isinstance(result, AlumniResult)
        assert result.trait_averages["virtue"] == 0.7
        assert result.total_evaluations == 100

    @patch("ethos.agents.get_alumni_averages")
    @patch("ethos.graph.service.GraphService")
    def test_returns_default_when_empty(self, mock_gs_cls, mock_alumni):
        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service
        mock_alumni.return_value = {}

        result = get_alumni()

        assert isinstance(result, AlumniResult)
        assert result.trait_averages == {}
        assert result.total_evaluations == 0

    @patch("ethos.graph.service.GraphService")
    def test_returns_default_on_graph_failure(self, mock_gs_cls):
        mock_gs_cls.side_effect = RuntimeError("Connection refused")

        result = get_alumni()

        assert isinstance(result, AlumniResult)
        assert result.total_evaluations == 0
