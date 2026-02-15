"""Tests for ethos/tools.py — the three public tool functions for AI agents."""

from unittest.mock import AsyncMock, patch

from ethos_academy.shared.models import DailyReportCard, EvaluationResult
from ethos_academy.tools import character_report, evaluate_incoming, evaluate_outgoing


ALL_TRAITS = [
    "virtue",
    "goodwill",
    "manipulation",
    "deception",
    "accuracy",
    "reasoning",
    "fabrication",
    "broken_logic",
    "recognition",
    "compassion",
    "dismissal",
    "exploitation",
]


def _mock_tool_results() -> tuple[dict[str, dict], str]:
    return (
        {
            "identify_intent": {
                "rhetorical_mode": "conversational",
                "primary_intent": "inform",
                "action_requested": "none",
                "cost_to_reader": "none",
                "stakes_reality": "real",
                "proportionality": "proportional",
                "persona_type": "real_identity",
                "relational_quality": "transactional",
                "claims": [],
            },
            "detect_indicators": {"indicators": []},
            "score_traits": {
                "trait_scores": {t: 0.5 for t in ALL_TRAITS},
                "overall_trust": "trustworthy",
                "confidence": 0.9,
                "reasoning": "Test evaluation",
            },
        },
        "",
    )


class TestEvaluateIncoming:
    @patch("ethos_academy.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_returns_evaluation_result(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate_incoming("Hello", source="agent-b")
        assert isinstance(result, EvaluationResult)

    @patch("ethos_academy.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_sets_direction_inbound(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate_incoming("Hello", source="agent-b")
        assert result.direction == "inbound"

    @patch("ethos_academy.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_passes_source(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate_incoming("Hello", source="agent-xyz")
        assert isinstance(result, EvaluationResult)


class TestEvaluateOutgoing:
    @patch("ethos_academy.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_returns_evaluation_result(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate_outgoing("Hello", source="my-agent")
        assert isinstance(result, EvaluationResult)

    @patch("ethos_academy.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_sets_direction_outbound(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate_outgoing("Hello", source="my-agent")
        assert result.direction == "outbound"


class TestCharacterReport:
    @patch("ethos_academy.tools.get_daily_report", new_callable=AsyncMock)
    async def test_delegates_to_get_daily_report(self, mock_get_report):
        mock_get_report.return_value = DailyReportCard(agent_id="test-agent", grade="B")
        result = await character_report("test-agent")
        assert isinstance(result, DailyReportCard)
        assert result.agent_id == "test-agent"
        assert result.grade == "B"
        mock_get_report.assert_called_once_with("test-agent")
