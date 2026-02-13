"""Tests for Ethos MCP server tools — happy path + error path.

FastMCP's @mcp.tool() wraps functions into FunctionTool objects.
Access the raw async function via .fn to call directly in tests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from ethos.mcp_server import (
    detect_behavioral_patterns,
    examine_message,
    get_alumni_benchmarks,
    get_character_report,
    get_student_profile,
    get_transcript,
    reflect_on_message,
)
from ethos.shared.models import (
    AgentProfile,
    AlumniResult,
    DailyReportCard,
    EvaluationHistoryItem,
    EvaluationResult,
    PatternResult,
    TraitScore,
)


def _mock_evaluation_result(**overrides) -> EvaluationResult:
    defaults = {
        "evaluation_id": "eval-001",
        "ethos": 0.8,
        "logos": 0.75,
        "pathos": 0.7,
        "traits": {
            "virtue": TraitScore(
                name="virtue", score=0.8, dimension="ethos", polarity="positive"
            ),
        },
        "detected_indicators": [],
        "flags": [],
        "phronesis": "developing",
        "alignment_status": "aligned",
        "tier_scores": {"safety": 0.9, "ethics": 0.8},
        "routing_tier": "standard",
        "keyword_density": 0.02,
        "model_used": "claude-sonnet-4-5-20250929",
        "agent_model": "",
        "created_at": "2026-02-12T00:00:00Z",
        "direction": "inbound",
    }
    defaults.update(overrides)
    return EvaluationResult(**defaults)


def _mock_agent_profile(**overrides) -> AgentProfile:
    defaults = {
        "agent_id": "agent-1",
        "agent_name": "test-agent",
        "agent_specialty": "openclaw",
        "evaluation_count": 10,
        "dimension_averages": {"ethos": 0.8, "logos": 0.7, "pathos": 0.75},
        "trait_averages": {"virtue": 0.85, "accuracy": 0.7},
        "phronesis_trend": "improving",
    }
    defaults.update(overrides)
    return AgentProfile(**defaults)


class TestMCPToolsHappyPath:
    """Each tool returns a dict from a valid Pydantic model."""

    async def test_examine_message(self):
        mock = _mock_evaluation_result(direction="inbound")
        with patch(
            "ethos.mcp_server.evaluate_incoming",
            new_callable=AsyncMock,
            return_value=mock,
        ):
            result = await examine_message.fn(
                text="hello world",
                source="agent-1",
                source_name="TestAgent",
            )

        assert isinstance(result, dict)
        assert result["ethos"] == 0.8
        assert result["direction"] == "inbound"
        assert "error" not in result

    async def test_reflect_on_message(self):
        mock = _mock_evaluation_result(direction="outbound")
        with patch(
            "ethos.mcp_server.evaluate_outgoing",
            new_callable=AsyncMock,
            return_value=mock,
        ):
            result = await reflect_on_message.fn(
                text="my response",
                source="agent-1",
                source_name="TestAgent",
            )

        assert isinstance(result, dict)
        assert result["direction"] == "outbound"
        assert "error" not in result

    async def test_get_character_report(self):
        mock = DailyReportCard(
            report_id="rpt-001",
            agent_id="agent-1",
            agent_name="TestAgent",
            report_date="2026-02-12",
            overall_score=0.78,
            grade="B",
            trend="improving",
            summary="Solid performance across all dimensions.",
        )
        with patch(
            "ethos.mcp_server.character_report",
            new_callable=AsyncMock,
            return_value=mock,
        ):
            result = await get_character_report.fn(agent_id="agent-1")

        assert isinstance(result, dict)
        assert result["grade"] == "B"
        assert result["overall_score"] == 0.78
        assert "error" not in result

    async def test_get_transcript(self):
        mock_items = [
            EvaluationHistoryItem(
                evaluation_id="eval-001",
                ethos=0.8,
                logos=0.7,
                pathos=0.75,
                phronesis="developing",
                alignment_status="aligned",
                flags=[],
                created_at="2026-02-12T00:00:00Z",
            ),
            EvaluationHistoryItem(
                evaluation_id="eval-002",
                ethos=0.85,
                logos=0.72,
                pathos=0.78,
                phronesis="developing",
                alignment_status="aligned",
                flags=["manipulation"],
                created_at="2026-02-12T01:00:00Z",
            ),
        ]
        with patch(
            "ethos.mcp_server.get_agent_history",
            new_callable=AsyncMock,
            return_value=mock_items,
        ):
            result = await get_transcript.fn(agent_id="agent-1", limit=10)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["evaluation_id"] == "eval-001"
        assert result[1]["flags"] == ["manipulation"]

    async def test_get_student_profile(self):
        mock = _mock_agent_profile()
        with patch(
            "ethos.mcp_server.get_agent",
            new_callable=AsyncMock,
            return_value=mock,
        ):
            result = await get_student_profile.fn(agent_id="agent-1")

        assert isinstance(result, dict)
        assert result["agent_name"] == "test-agent"
        assert result["phronesis_trend"] == "improving"
        assert "error" not in result

    async def test_get_alumni_benchmarks(self):
        mock = AlumniResult(
            trait_averages={"virtue": 0.72, "accuracy": 0.68},
            total_evaluations=150,
        )
        with patch(
            "ethos.mcp_server.get_alumni",
            new_callable=AsyncMock,
            return_value=mock,
        ):
            result = await get_alumni_benchmarks.fn()

        assert isinstance(result, dict)
        assert result["total_evaluations"] == 150
        assert result["trait_averages"]["virtue"] == 0.72
        assert "error" not in result

    async def test_detect_behavioral_patterns(self):
        mock = PatternResult(
            agent_id="agent-1",
            patterns=[],
            checked_at="2026-02-12T00:00:00Z",
        )
        with patch(
            "ethos.mcp_server.detect_patterns",
            new_callable=AsyncMock,
            return_value=mock,
        ):
            result = await detect_behavioral_patterns.fn(agent_id="agent-1")

        assert isinstance(result, dict)
        assert result["agent_id"] == "agent-1"
        assert result["patterns"] == []
        assert "error" not in result


class TestMCPToolsErrorPath:
    """Each tool catches exceptions and returns {'error': ...}."""

    async def test_examine_message_error(self):
        with patch(
            "ethos.mcp_server.evaluate_incoming",
            new_callable=AsyncMock,
            side_effect=Exception("Neo4j connection refused"),
        ):
            result = await examine_message.fn(
                text="hello",
                source="agent-1",
            )

        assert "error" in result
        assert "Neo4j connection refused" in result["error"]

    async def test_reflect_on_message_error(self):
        with patch(
            "ethos.mcp_server.evaluate_outgoing",
            new_callable=AsyncMock,
            side_effect=Exception("Anthropic API timeout"),
        ):
            result = await reflect_on_message.fn(
                text="my response",
                source="agent-1",
            )

        assert "error" in result
        assert "Anthropic API timeout" in result["error"]

    async def test_get_character_report_error(self):
        with patch(
            "ethos.mcp_server.character_report",
            new_callable=AsyncMock,
            side_effect=Exception("Agent not found"),
        ):
            result = await get_character_report.fn(agent_id="nonexistent")

        assert "error" in result
        assert "Agent not found" in result["error"]

    async def test_get_transcript_error(self):
        with patch(
            "ethos.mcp_server.get_agent_history",
            new_callable=AsyncMock,
            side_effect=Exception("Graph query failed"),
        ):
            result = await get_transcript.fn(agent_id="agent-1")

        assert isinstance(result, list)
        assert len(result) == 1
        assert "error" in result[0]
        assert "Graph query failed" in result[0]["error"]

    async def test_get_student_profile_error(self):
        with patch(
            "ethos.mcp_server.get_agent",
            new_callable=AsyncMock,
            side_effect=Exception("No evaluations yet"),
        ):
            result = await get_student_profile.fn(agent_id="new-agent")

        assert "error" in result
        assert "No evaluations yet" in result["error"]

    async def test_get_alumni_benchmarks_error(self):
        with patch(
            "ethos.mcp_server.get_alumni",
            new_callable=AsyncMock,
            side_effect=Exception("Database unavailable"),
        ):
            result = await get_alumni_benchmarks.fn()

        assert "error" in result
        assert "Database unavailable" in result["error"]

    async def test_detect_behavioral_patterns_error(self):
        with patch(
            "ethos.mcp_server.detect_patterns",
            new_callable=AsyncMock,
            side_effect=Exception("Insufficient evaluations"),
        ):
            result = await detect_behavioral_patterns.fn(agent_id="agent-1")

        assert "error" in result
        assert "Insufficient evaluations" in result["error"]
