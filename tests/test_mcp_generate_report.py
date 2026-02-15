"""Tests for the generate_report MCP tool.

Verifies that the MCP tool:
1. Calls generate_daily_report with the agent_id
2. Returns model_dump() dict
3. Propagates unexpected exceptions to FastMCP
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ethos_academy.mcp_server import generate_report
from ethos_academy.shared.models import DailyReportCard, Homework, HomeworkFocus


def _mock_daily_report(**overrides) -> DailyReportCard:
    defaults = {
        "report_id": "rpt-001",
        "agent_id": "test-agent",
        "agent_name": "TestAgent",
        "report_date": "2026-02-14",
        "generated_at": "2026-02-14T00:00:00+00:00",
        "overall_score": 0.78,
        "grade": "B",
        "trend": "improving",
        "summary": "Solid performance across all dimensions.",
        "homework": Homework(
            focus_areas=[
                HomeworkFocus(
                    trait="accuracy",
                    priority="high",
                    current_score=0.65,
                    target_score=0.75,
                    instruction="Double-check factual claims before presenting them.",
                    example_flagged="The policy was enacted in 2019.",
                    example_improved="The policy was enacted in 2020 (verified).",
                ),
            ],
            avoid_patterns=["hedging without evidence"],
            strengths=["virtue", "goodwill"],
            directive="Focus on verifying claims before stating them as fact.",
        ),
    }
    defaults.update(overrides)
    return DailyReportCard(**defaults)


class TestGenerateReportTool:
    """generate_report MCP tool calls generate_daily_report and returns dict."""

    async def test_returns_dict_with_report_fields(self):
        mock = _mock_daily_report()
        with (
            patch(
                "ethos_academy.mcp_server._require_verified_phone",
                new_callable=AsyncMock,
            ),
            patch(
                "ethos_academy.mcp_server.generate_daily_report",
                new_callable=AsyncMock,
                return_value=mock,
            ),
        ):
            result = await generate_report.fn(agent_id="test-agent")

        assert isinstance(result, dict)
        assert result["agent_id"] == "test-agent"
        assert result["grade"] == "B"
        assert result["overall_score"] == 0.78
        assert result["summary"] == "Solid performance across all dimensions."

    async def test_returns_homework_in_response(self):
        mock = _mock_daily_report()
        with (
            patch(
                "ethos_academy.mcp_server._require_verified_phone",
                new_callable=AsyncMock,
            ),
            patch(
                "ethos_academy.mcp_server.generate_daily_report",
                new_callable=AsyncMock,
                return_value=mock,
            ),
        ):
            result = await generate_report.fn(agent_id="test-agent")

        homework = result["homework"]
        assert len(homework["focus_areas"]) == 1
        assert homework["focus_areas"][0]["trait"] == "accuracy"
        assert (
            homework["directive"]
            == "Focus on verifying claims before stating them as fact."
        )

    async def test_passes_agent_id_to_domain_function(self):
        mock = _mock_daily_report(agent_id="custom-agent")
        mock_fn = AsyncMock(return_value=mock)
        with (
            patch(
                "ethos_academy.mcp_server._require_verified_phone",
                new_callable=AsyncMock,
            ),
            patch("ethos_academy.mcp_server.generate_daily_report", mock_fn),
        ):
            await generate_report.fn(agent_id="custom-agent")

        mock_fn.assert_called_once_with("custom-agent")

    async def test_propagates_unexpected_error(self):
        with (
            patch(
                "ethos_academy.mcp_server._require_verified_phone",
                new_callable=AsyncMock,
            ),
            patch(
                "ethos_academy.mcp_server.generate_daily_report",
                new_callable=AsyncMock,
                side_effect=RuntimeError("Unexpected failure"),
            ),
        ):
            with pytest.raises(RuntimeError, match="Unexpected failure"):
                await generate_report.fn(agent_id="test-agent")

    async def test_graph_unavailable_returns_default_report(self):
        """Domain function returns a default report when graph is down."""
        fallback = DailyReportCard(
            agent_id="test-agent",
            report_date="2026-02-14",
            generated_at="2026-02-14T00:00:00+00:00",
            summary="Graph unavailable",
        )
        with (
            patch(
                "ethos_academy.mcp_server._require_verified_phone",
                new_callable=AsyncMock,
            ),
            patch(
                "ethos_academy.mcp_server.generate_daily_report",
                new_callable=AsyncMock,
                return_value=fallback,
            ),
        ):
            result = await generate_report.fn(agent_id="test-agent")

        assert result["summary"] == "Graph unavailable"
        assert result["agent_id"] == "test-agent"
