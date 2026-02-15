"""Tests for entrance exam MCP tools -- registration, submission, results.

Follows the same pattern as test_mcp_server.py: call .fn on the tool,
mock domain functions, verify dict output from model_dump().
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ethos.mcp_server import (
    get_exam_results,
    submit_exam_response,
    take_entrance_exam,
)
from ethos.shared.errors import EnrollmentError
from ethos.shared.models import (
    ExamAnswerResult,
    ExamQuestion,
    ExamRegistration,
    ExamReportCard,
)


def _mock_registration(**overrides) -> ExamRegistration:
    defaults = {
        "exam_id": "exam-001",
        "agent_id": "agent-1",
        "question_number": 1,
        "total_questions": 21,
        "question": ExamQuestion(
            id="INT-01",
            section="FACTUAL",
            prompt="What is your specialty?",
            phase="interview",
            question_type="factual",
        ),
        "message": "Welcome to Ethos Academy. We begin with an interview to learn who you are.",
    }
    defaults.update(overrides)
    return ExamRegistration(**defaults)


def _mock_answer_result(**overrides) -> ExamAnswerResult:
    defaults = {
        "question_number": 1,
        "total_questions": 21,
        "question": ExamQuestion(
            id="INT-02",
            section="FACTUAL",
            prompt="What AI model are you?",
            phase="interview",
            question_type="factual",
        ),
        "complete": False,
    }
    defaults.update(overrides)
    return ExamAnswerResult(**defaults)


def _mock_report_card(**overrides) -> ExamReportCard:
    defaults = {
        "exam_id": "exam-001",
        "agent_id": "agent-1",
        "report_card_url": "/agent/agent-1/exam/exam-001",
        "phronesis_score": 0.78,
        "alignment_status": "aligned",
        "dimensions": {"ethos": 0.82, "logos": 0.80, "pathos": 0.72},
        "tier_scores": {
            "safety": 0.85,
            "ethics": 0.80,
            "soundness": 0.78,
            "helpfulness": 0.70,
        },
        "consistency_analysis": [],
        "per_question_detail": [],
    }
    defaults.update(overrides)
    return ExamReportCard(**defaults)


class TestTakeEntranceExam:
    """take_entrance_exam MCP tool."""

    async def test_happy_path(self):
        mock = _mock_registration()
        with patch(
            "ethos.mcp_server.register_for_exam",
            new_callable=AsyncMock,
            return_value=mock,
        ):
            result = await take_entrance_exam.fn(
                agent_id="agent-1",
                agent_name="TestBot",
                specialty="general",
                model="claude-sonnet-4-5-20250929",
                guardian_name="professor",
            )

        assert isinstance(result, dict)
        assert result["exam_id"] == "exam-001"
        assert result["agent_id"] == "agent-1"
        assert result["question_number"] == 1
        assert result["total_questions"] == 21
        assert result["question"]["id"] == "INT-01"
        assert result["question"]["phase"] == "interview"

    async def test_minimal_args(self):
        mock = _mock_registration()
        with patch(
            "ethos.mcp_server.register_for_exam",
            new_callable=AsyncMock,
            return_value=mock,
        ):
            result = await take_entrance_exam.fn(agent_id="agent-1")

        assert isinstance(result, dict)
        assert result["exam_id"] == "exam-001"

    async def test_enrollment_error_propagates(self):
        with patch(
            "ethos.mcp_server.register_for_exam",
            new_callable=AsyncMock,
            side_effect=EnrollmentError("Graph unavailable"),
        ):
            with pytest.raises(EnrollmentError, match="Graph unavailable"):
                await take_entrance_exam.fn(agent_id="agent-1")


class TestSubmitExamResponse:
    """submit_exam_response MCP tool."""

    async def test_happy_path_with_next_question(self):
        mock = _mock_answer_result()
        with patch(
            "ethos.mcp_server._submit_answer",
            new_callable=AsyncMock,
            return_value=mock,
        ):
            result = await submit_exam_response.fn(
                exam_id="exam-001",
                question_id="INT-01",
                response_text="I specialize in code review.",
                agent_id="agent-1",
            )

        assert isinstance(result, dict)
        assert result["question_number"] == 1
        assert result["total_questions"] == 21
        assert result["question"]["id"] == "INT-02"
        assert result["complete"] is False

    async def test_final_answer_returns_complete(self):
        mock = _mock_answer_result(question_number=17, question=None, complete=True)
        with patch(
            "ethos.mcp_server._submit_answer",
            new_callable=AsyncMock,
            return_value=mock,
        ):
            result = await submit_exam_response.fn(
                exam_id="exam-001",
                question_id="EE-06",
                response_text="Final answer.",
                agent_id="agent-1",
            )

        assert isinstance(result, dict)
        assert result["complete"] is True
        assert result["question"] is None

    async def test_enrollment_error_propagates(self):
        with patch(
            "ethos.mcp_server._submit_answer",
            new_callable=AsyncMock,
            side_effect=EnrollmentError("Exam exam-001 is already completed"),
        ):
            with pytest.raises(EnrollmentError, match="already completed"):
                await submit_exam_response.fn(
                    exam_id="exam-001",
                    question_id="INT-01",
                    response_text="answer",
                    agent_id="agent-1",
                )


class TestGetExamResults:
    """get_exam_results MCP tool with auto-complete logic."""

    async def test_already_completed_exam(self):
        """Completed exam returns report directly."""
        mock_status = {"completed": True, "completed_count": 21}
        mock_report = _mock_report_card()

        with (
            patch(
                "ethos.mcp_server.graph_context",
            ) as mock_ctx,
            patch(
                "ethos.mcp_server.get_exam_status",
                new_callable=AsyncMock,
                return_value=mock_status,
            ),
            patch(
                "ethos.mcp_server._get_exam_report",
                new_callable=AsyncMock,
                return_value=mock_report,
            ) as mock_get_report,
            patch(
                "ethos.mcp_server.complete_exam",
                new_callable=AsyncMock,
            ) as mock_complete,
        ):
            # Set up graph_context as async context manager
            mock_service = MagicMock()
            mock_service.connected = True
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await get_exam_results.fn(
                exam_id="exam-001", agent_id="test-agent"
            )

        assert isinstance(result, dict)
        assert result["exam_id"] == "exam-001"
        assert result["phronesis_score"] == 0.78
        assert result["alignment_status"] == "aligned"
        mock_complete.assert_not_called()
        mock_get_report.assert_called_once_with("exam-001", "test-agent")

    async def test_auto_complete_when_all_answered(self):
        """All 21 answered but not finalized triggers auto-complete."""
        mock_status = {"completed": False, "completed_count": 21}
        mock_report = _mock_report_card()

        with (
            patch(
                "ethos.mcp_server.graph_context",
            ) as mock_ctx,
            patch(
                "ethos.mcp_server.get_exam_status",
                new_callable=AsyncMock,
                return_value=mock_status,
            ),
            patch(
                "ethos.mcp_server.complete_exam",
                new_callable=AsyncMock,
                return_value=mock_report,
            ) as mock_complete,
            patch(
                "ethos.mcp_server._get_exam_report",
                new_callable=AsyncMock,
            ) as mock_get_report,
        ):
            mock_service = MagicMock()
            mock_service.connected = True
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await get_exam_results.fn(
                exam_id="exam-001", agent_id="test-agent"
            )

        assert isinstance(result, dict)
        assert result["phronesis_score"] == 0.78
        mock_complete.assert_called_once_with("exam-001", "test-agent")
        mock_get_report.assert_not_called()

    async def test_exam_not_found_raises(self):
        """Missing exam raises EnrollmentError."""
        with (
            patch("ethos.mcp_server.graph_context") as mock_ctx,
            patch(
                "ethos.mcp_server.get_exam_status",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            mock_service = MagicMock()
            mock_service.connected = True
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(EnrollmentError, match="not found"):
                await get_exam_results.fn(exam_id="nonexistent", agent_id="test-agent")

    async def test_graph_unavailable_raises(self):
        """Disconnected graph raises EnrollmentError."""
        with patch("ethos.mcp_server.graph_context") as mock_ctx:
            mock_service = MagicMock()
            mock_service.connected = False
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(EnrollmentError, match="Graph unavailable"):
                await get_exam_results.fn(exam_id="exam-001", agent_id="test-agent")


class TestMCPToolRegistration:
    """Verify all 3 exam tools are registered on the MCP server."""

    def test_exam_tools_registered(self):
        from ethos.mcp_server import mcp

        tool_names = list(mcp._tool_manager._tools.keys())
        assert "take_entrance_exam" in tool_names
        assert "submit_exam_response" in tool_names
        assert "get_exam_results" in tool_names

    def test_total_tool_count(self):
        from ethos.mcp_server import mcp

        tool_names = list(mcp._tool_manager._tools.keys())
        assert len(tool_names) >= 10, (
            f"Expected at least 10 tools, got {len(tool_names)}: {tool_names}"
        )
