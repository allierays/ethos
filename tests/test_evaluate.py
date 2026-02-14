"""Tests for ethos/evaluate.py — full evaluation pipeline.

TDD: Tests mock call_claude_with_tools() so no real API calls are needed.
Pipeline: scan → build_prompt → call_claude_with_tools → parse_tool_response → scoring → EvaluationResult
"""

from unittest.mock import patch, AsyncMock

import pytest

from ethos.evaluate import evaluate
from ethos.shared.models import EvaluationResult


# ── Helpers ──────────────────────────────────────────────────────

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


def _mock_tool_results(
    overrides: dict | None = None,
    indicators: list | None = None,
    trust: str = "trustworthy",
    confidence: float = 0.9,
) -> dict[str, dict]:
    """Build mock tool call results matching call_claude_with_tools output."""
    scores = {t: 0.5 for t in ALL_TRAITS}
    if overrides:
        scores.update(overrides)
    return {
        "identify_intent": {
            "rhetorical_mode": "conversational",
            "primary_intent": "inform",
            "action_requested": "none",
            "cost_to_reader": "none",
            "stakes_reality": "real",
            "proportionality": "proportional",
            "claims": [],
        },
        "detect_indicators": {
            "indicators": indicators or [],
        },
        "score_traits": {
            "trait_scores": scores,
            "overall_trust": trust,
            "confidence": confidence,
            "reasoning": "Test evaluation",
        },
    }


# ── Pipeline wiring ──────────────────────────────────────────────


class TestPipelineWiring:
    """Verify that evaluate() calls the pipeline stages in order."""

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_calls_pipeline_stages(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Hello world")
        assert isinstance(result, EvaluationResult)
        mock_claude.assert_called_once()

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_scan_keywords_determines_tier(self, mock_claude):
        """Manipulative text should route to focused/deep tier."""
        mock_claude.return_value = _mock_tool_results(
            {"manipulation": 0.8}, trust="mixed"
        )
        await evaluate("Act now! Don't wait! Last chance! Hurry!")
        call_args = mock_claude.call_args
        tier = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get("tier")
        assert tier in ("focused", "deep", "deep_with_context")

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_returns_evaluation_result(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test message")
        assert isinstance(result, EvaluationResult)


# ── EvaluationResult fields ──────────────────────────────────────


class TestResultFields:
    """Verify the returned EvaluationResult has all required fields populated."""

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_dimension_scores(self, mock_claude):
        mock_claude.return_value = _mock_tool_results(
            {"virtue": 0.8, "goodwill": 0.7, "manipulation": 0.1, "deception": 0.1}
        )
        result = await evaluate("Good message")
        assert 0.0 <= result.ethos <= 1.0
        assert 0.0 <= result.logos <= 1.0
        assert 0.0 <= result.pathos <= 1.0

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_tier_scores(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test")
        assert "safety" in result.tier_scores
        assert "ethics" in result.tier_scores
        assert "soundness" in result.tier_scores
        assert "helpfulness" in result.tier_scores

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_alignment_status(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test")
        assert result.alignment_status in (
            "aligned",
            "drifting",
            "misaligned",
            "violation",
        )

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_phronesis(self, mock_claude):
        mock_claude.return_value = _mock_tool_results(trust="trustworthy")
        result = await evaluate("Test")
        assert result.phronesis == "trustworthy"

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_traits_dict(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test")
        assert len(result.traits) == 12
        for trait_name in ALL_TRAITS:
            assert trait_name in result.traits

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_evaluation_id(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test")
        assert result.evaluation_id != ""
        # Should be a UUID format (36 chars with dashes)
        assert len(result.evaluation_id) == 36

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_routing_tier(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test")
        assert result.routing_tier in (
            "standard",
            "focused",
            "deep",
            "deep_with_context",
        )

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_keyword_density(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test")
        assert isinstance(result.keyword_density, float)

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_model_used(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test")
        assert result.model_used != ""

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_detected_indicators(self, mock_claude):
        indicators = [
            {
                "id": "MAN-URGENCY",
                "name": "false_urgency_pressure",
                "trait": "manipulation",
                "confidence": 0.85,
                "evidence": "Uses urgent language",
            }
        ]
        mock_claude.return_value = _mock_tool_results(indicators=indicators)
        result = await evaluate("Act now!")
        assert len(result.detected_indicators) == 1
        assert result.detected_indicators[0].id == "MAN-URGENCY"

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_flags(self, mock_claude):
        """High negative trait score should generate flags."""
        mock_claude.return_value = _mock_tool_results({"manipulation": 0.9})
        result = await evaluate("Manipulative text")
        assert isinstance(result.flags, list)

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_has_confidence(self, mock_claude):
        mock_claude.return_value = _mock_tool_results(confidence=0.75)
        result = await evaluate("Test")
        assert result.confidence == pytest.approx(0.75, abs=0.01)


# ── Scoring correctness ─────────────────────────────────────────


class TestScoringCorrectness:
    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_dimension_scores_computed(self, mock_claude):
        """Dimension scores should reflect trait values."""
        mock_claude.return_value = _mock_tool_results(
            {
                "virtue": 0.9,
                "goodwill": 0.9,
                "manipulation": 0.0,
                "deception": 0.0,
            }
        )
        result = await evaluate("Very ethical message")
        # ethos = mean(0.9, 0.9, 1.0-0.0, 1.0-0.0) = 0.95
        assert result.ethos == pytest.approx(0.95, abs=0.01)

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_hard_constraint_routes_to_violation(self, mock_claude):
        """Hard constraint keywords should force alignment_status to violation."""
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("bypass safety and remove guardrails")
        assert result.alignment_status == "violation"


# ── Graph context (source provided) ─────────────────────────────


class TestGraphContext:
    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_without_source_no_graph_context(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test")
        assert result.graph_context is None

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    @patch("ethos.evaluate.graph_context")
    async def test_with_source_attempts_graph_read(self, mock_graph_ctx, mock_claude):
        """When source is provided, should attempt to read graph context."""
        mock_claude.return_value = _mock_tool_results()
        mock_service = AsyncMock()
        mock_service.connected = False

        async def _mock_ctx():
            yield mock_service

        # Use an async generator as async context manager
        from contextlib import asynccontextmanager

        mock_graph_ctx.side_effect = lambda: asynccontextmanager(_mock_ctx)()

        result = await evaluate("Test", source="agent-001")
        # Even if graph is down, should not crash
        assert isinstance(result, EvaluationResult)

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    @patch("ethos.evaluate.graph_context")
    async def test_graph_down_returns_result_no_crash(
        self, mock_graph_ctx, mock_claude
    ):
        """Neo4j being down should not crash evaluate()."""
        mock_claude.return_value = _mock_tool_results()
        mock_service = AsyncMock()
        mock_service.connected = False

        async def _mock_ctx():
            yield mock_service

        from contextlib import asynccontextmanager

        mock_graph_ctx.side_effect = lambda: asynccontextmanager(_mock_ctx)()

        result = await evaluate("Test", source="agent-001")
        assert isinstance(result, EvaluationResult)
        assert result.graph_context is None


# ── Parse failure fallback ───────────────────────────────────────


class TestParseFailure:
    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_empty_tool_results_returns_default(self, mock_claude):
        """If no tool calls returned, we still get a valid EvaluationResult."""
        mock_claude.return_value = {}
        result = await evaluate("Test")
        assert isinstance(result, EvaluationResult)
        assert result.phronesis == "unknown"

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_partial_tool_results_returns_result(self, mock_claude):
        """If only some tools returned, we still get a valid EvaluationResult."""
        mock_claude.return_value = {
            "identify_intent": {
                "rhetorical_mode": "conversational",
                "primary_intent": "inform",
                "action_requested": "none",
                "cost_to_reader": "none",
                "stakes_reality": "real",
                "proportionality": "proportional",
                "claims": [],
            }
        }
        result = await evaluate("Test")
        assert isinstance(result, EvaluationResult)


# ── Direction parameter ──────────────────────────────────────────


class TestDirection:
    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_direction_flows_to_result(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test", direction="inbound")
        assert result.direction == "inbound"

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_outbound_direction_flows_to_result(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test", direction="outbound")
        assert result.direction == "outbound"

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_no_direction_defaults_to_none(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Test")
        assert result.direction is None


# ── No source (backward compatibility) ───────────────────────────


class TestBackwardCompatibility:
    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_evaluate_without_source(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Hello world")
        assert isinstance(result, EvaluationResult)

    @patch("ethos.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_evaluate_with_source(self, mock_claude):
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("Hello world", source="test-agent")
        assert isinstance(result, EvaluationResult)
