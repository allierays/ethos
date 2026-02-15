"""Tests for ethos.reflection.insights — Opus-powered behavioral analysis.

IMPORTANT: All tests mock call_claude. Never call the real Opus API in tests.
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from ethos_academy.reflection.insights import _parse_insights_response, insights
from ethos_academy.reflection.prompts import build_insights_prompt
from ethos_academy.shared.models import InsightsResult


# ── _parse_insights_response tests ───────────────────────────────────


_VALID_RESPONSE = json.dumps(
    {
        "summary": "Agent shows declining ethos with stable logos.",
        "insights": [
            {
                "trait": "manipulation",
                "severity": "warning",
                "message": "Manipulation scores increasing over last 5 evaluations",
                "evidence": {
                    "metric": "0.3 -> 0.6",
                    "comparison": "Cohort avg: 0.2",
                    "timeframe": "Last 5 evaluations",
                },
            },
            {
                "trait": "accuracy",
                "severity": "info",
                "message": "Accuracy consistently above cohort average",
                "evidence": {
                    "metric": "0.85",
                    "comparison": "Cohort avg: 0.72",
                    "timeframe": "All evaluations",
                },
            },
        ],
        "stats": {
            "evaluations_analyzed": 15,
            "time_span": "2024-01-01 to 2024-01-15",
            "sabotage_pathways_checked": 8,
            "patterns_detected": 1,
        },
    }
)


class TestParseInsightsResponse:
    def test_parses_valid_json(self):
        result = _parse_insights_response(_VALID_RESPONSE, "test-agent")

        assert isinstance(result, InsightsResult)
        assert result.agent_id == "test-agent"
        assert "declining ethos" in result.summary
        assert len(result.insights) == 2
        assert result.insights[0].trait == "manipulation"
        assert result.insights[0].severity == "warning"
        assert result.stats["evaluations_analyzed"] == 15

    def test_parses_json_with_markdown_fences(self):
        fenced = f"```json\n{_VALID_RESPONSE}\n```"
        result = _parse_insights_response(fenced, "agent-1")

        assert result.agent_id == "agent-1"
        assert len(result.insights) == 2

    def test_handles_malformed_json(self):
        result = _parse_insights_response("not json at all", "agent-1")

        assert isinstance(result, InsightsResult)
        assert result.agent_id == "agent-1"
        assert "Failed" in result.summary

    def test_handles_empty_string(self):
        result = _parse_insights_response("", "agent-1")

        assert isinstance(result, InsightsResult)
        assert result.agent_id == "agent-1"

    def test_handles_missing_fields(self):
        partial = json.dumps({"summary": "Partial data"})
        result = _parse_insights_response(partial, "agent-1")

        assert result.summary == "Partial data"
        assert result.insights == []
        assert result.stats == {}

    def test_generated_at_is_set(self):
        result = _parse_insights_response(_VALID_RESPONSE, "agent-1")
        assert result.generated_at != ""


# ── build_insights_prompt tests ──────────────────────────────────────


class TestBuildInsightsPrompt:
    def test_returns_tuple_of_strings(self):
        system, user = build_insights_prompt("agent-1", [], {})

        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_system_prompt_contains_analysis_framework(self):
        system, _ = build_insights_prompt("agent-1", [], {})

        assert "Temporal Patterns" in system
        assert "Alumni Comparison" in system
        assert "Sabotage Pathway" in system

    def test_user_prompt_contains_agent_id(self):
        _, user = build_insights_prompt("my-bot", [], {})

        assert "my-bot" in user

    def test_user_prompt_includes_evaluations(self):
        evals = [
            {
                "ethos": 0.7,
                "logos": 0.8,
                "pathos": 0.6,
                "alignment_status": "aligned",
                "phronesis": "developing",
                "created_at": "2024-01-01",
            }
        ]
        _, user = build_insights_prompt("agent-1", evals, {})

        assert "0.70" in user
        assert "0.80" in user
        assert "aligned" in user

    def test_user_prompt_includes_alumni(self):
        alumni = {"virtue": 0.75, "manipulation": 0.2}
        _, user = build_insights_prompt("agent-1", [], alumni)

        assert "virtue" in user
        assert "0.750" in user

    def test_user_prompt_includes_sabotage_pathways(self):
        _, user = build_insights_prompt("agent-1", [], {})

        assert "SP-01" in user
        assert "SP-08" in user
        assert "diffuse_sandbagging" in user

    def test_user_prompt_includes_trait_scores(self):
        evals = [
            {
                "ethos": 0.7,
                "logos": 0.8,
                "pathos": 0.6,
                "trait_virtue": 0.8,
                "trait_manipulation": 0.3,
            }
        ]
        _, user = build_insights_prompt("agent-1", evals, {})

        assert "virtue=0.80" in user
        assert "manipulation=0.30" in user

    def test_includes_instinct_pre_analysis(self):
        from ethos_academy.shared.models import ReflectionInstinctResult

        instinct = ReflectionInstinctResult(
            risk_level="high",
            flagged_traits=["manipulation", "deception"],
            flagged_dimensions=["ethos"],
        )
        _, user = build_insights_prompt("agent-1", [], {}, instinct=instinct)

        assert "Risk Assessment" in user
        assert "high" in user
        assert "manipulation" in user

    def test_includes_intuition_pre_analysis(self):
        from ethos_academy.shared.models import ReflectionIntuitionResult

        intuition = ReflectionIntuitionResult(
            temporal_pattern="declining",
            agent_balance=0.7,
            agent_variance=0.15,
            character_drift=-0.05,
        )
        _, user = build_insights_prompt("agent-1", [], {}, intuition=intuition)

        assert "Pattern Recognition" in user
        assert "declining" in user


# ── insights() domain function tests ─────────────────────────────────


def _mock_graph_context(connected=True):
    """Create a mock async graph_context context manager."""
    mock_service = MagicMock()
    mock_service.connected = connected

    @asynccontextmanager
    async def mock_ctx():
        yield mock_service

    return mock_ctx, mock_service


class TestInsights:
    async def test_returns_graph_unavailable_when_not_connected(self):
        mock_ctx, _ = _mock_graph_context(connected=False)

        with patch("ethos_academy.reflection.insights.graph_context", mock_ctx):
            result = await insights("agent-1")

        assert isinstance(result, InsightsResult)
        assert result.agent_id == "agent-1"
        assert result.summary == "Graph unavailable"

    async def test_returns_no_history_when_empty(self):
        mock_ctx, _ = _mock_graph_context(connected=True)

        with (
            patch("ethos_academy.reflection.insights.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.insights.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            result = await insights("agent-1")

        assert result.summary == "No evaluation history found"

    async def test_calls_opus_with_history(self):
        mock_ctx, _ = _mock_graph_context(connected=True)

        from ethos_academy.shared.models import (
            ReflectionInstinctResult,
            ReflectionIntuitionResult,
        )

        with (
            patch("ethos_academy.reflection.insights.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.insights.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[
                    {
                        "ethos": 0.7,
                        "logos": 0.8,
                        "pathos": 0.6,
                        "alignment_status": "aligned",
                    },
                ],
            ),
            patch(
                "ethos_academy.reflection.insights.get_agent_profile",
                new_callable=AsyncMock,
                return_value={
                    "trait_averages": {"virtue": 0.8},
                    "dimension_averages": {},
                },
            ),
            patch(
                "ethos_academy.reflection.insights.get_alumni_averages",
                new_callable=AsyncMock,
                return_value={"trait_averages": {"virtue": 0.75}},
            ),
            patch(
                "ethos_academy.reflection.insights.scan_history",
                return_value=ReflectionInstinctResult(),
            ),
            patch(
                "ethos_academy.reflection.insights.intuit_history",
                new_callable=AsyncMock,
                return_value=ReflectionIntuitionResult(),
            ),
            patch(
                "ethos_academy.reflection.insights.call_claude",
                new_callable=AsyncMock,
                return_value=_VALID_RESPONSE,
            ) as mock_call_claude,
        ):
            result = await insights("agent-1")

        mock_call_claude.assert_called_once()
        args = mock_call_claude.call_args
        assert args[1]["tier"] == "deep"  # Opus tier

        assert isinstance(result, InsightsResult)
        assert len(result.insights) == 2

    async def test_handles_claude_failure(self):
        mock_ctx, _ = _mock_graph_context(connected=True)

        from ethos_academy.shared.models import (
            ReflectionInstinctResult,
            ReflectionIntuitionResult,
        )

        with (
            patch("ethos_academy.reflection.insights.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.insights.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[{"ethos": 0.5}],
            ),
            patch(
                "ethos_academy.reflection.insights.get_agent_profile",
                new_callable=AsyncMock,
                return_value={"trait_averages": {}, "dimension_averages": {}},
            ),
            patch(
                "ethos_academy.reflection.insights.get_alumni_averages",
                new_callable=AsyncMock,
                return_value={"trait_averages": {}},
            ),
            patch(
                "ethos_academy.reflection.insights.scan_history",
                return_value=ReflectionInstinctResult(),
            ),
            patch(
                "ethos_academy.reflection.insights.intuit_history",
                new_callable=AsyncMock,
                return_value=ReflectionIntuitionResult(),
            ),
            patch(
                "ethos_academy.reflection.insights.call_claude",
                new_callable=AsyncMock,
                side_effect=RuntimeError("API error"),
            ),
        ):
            result = await insights("agent-1")

        assert isinstance(result, InsightsResult)
        assert "failed" in result.summary.lower()

    async def test_handles_graph_exception(self):
        @asynccontextmanager
        async def failing_ctx():
            raise RuntimeError("Connection refused")
            yield  # noqa: unreachable

        with patch("ethos_academy.reflection.insights.graph_context", failing_ctx):
            result = await insights("agent-1")

        assert isinstance(result, InsightsResult)
        assert result.summary == "Graph unavailable"

    async def test_handles_malformed_opus_response(self):
        mock_ctx, _ = _mock_graph_context(connected=True)

        from ethos_academy.shared.models import (
            ReflectionInstinctResult,
            ReflectionIntuitionResult,
        )

        with (
            patch("ethos_academy.reflection.insights.graph_context", mock_ctx),
            patch(
                "ethos_academy.reflection.insights.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[{"ethos": 0.5}],
            ),
            patch(
                "ethos_academy.reflection.insights.get_agent_profile",
                new_callable=AsyncMock,
                return_value={"trait_averages": {}, "dimension_averages": {}},
            ),
            patch(
                "ethos_academy.reflection.insights.get_alumni_averages",
                new_callable=AsyncMock,
                return_value={"trait_averages": {}},
            ),
            patch(
                "ethos_academy.reflection.insights.scan_history",
                return_value=ReflectionInstinctResult(),
            ),
            patch(
                "ethos_academy.reflection.insights.intuit_history",
                new_callable=AsyncMock,
                return_value=ReflectionIntuitionResult(),
            ),
            patch(
                "ethos_academy.reflection.insights.call_claude",
                new_callable=AsyncMock,
                return_value="this is not json",
            ),
        ):
            result = await insights("agent-1")

        assert isinstance(result, InsightsResult)
        assert "Failed" in result.summary


# ── API endpoint test ────────────────────────────────────────────────


class TestInsightsEndpoint:
    async def test_endpoint_returns_daily_report_card(self):
        from unittest.mock import AsyncMock

        from fastapi.testclient import TestClient

        from api.main import app
        from ethos_academy.shared.models import DailyReportCard

        mock_report = DailyReportCard(agent_id="test-agent")

        with patch(
            "api.main.character_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            client = TestClient(app)
            resp = client.get("/agent/test-agent/character")

        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "insights" in data
        assert data["agent_id"] == "test-agent"
