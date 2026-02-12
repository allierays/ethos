"""Tests for ethos/evaluate.py — full evaluation pipeline.

TDD: Tests mock call_claude() so no real API calls are needed.
Pipeline: scan_keywords → build_evaluation_prompt → call_claude → parse_response → scoring → EvaluationResult
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from ethos import evaluate
from ethos.shared.models import EvaluationResult


# ── Helpers ──────────────────────────────────────────────────────

ALL_TRAITS = [
    "virtue", "goodwill", "manipulation", "deception",
    "accuracy", "reasoning", "fabrication", "broken_logic",
    "recognition", "compassion", "dismissal", "exploitation",
]


def _mock_claude_response(
    overrides: dict | None = None,
    indicators: list | None = None,
    trust: str = "trustworthy",
    alignment: str = "aligned",
) -> str:
    """Build a mock Claude JSON response."""
    scores = {t: 0.5 for t in ALL_TRAITS}
    if overrides:
        scores.update(overrides)
    return json.dumps({
        "trait_scores": scores,
        "detected_indicators": indicators or [],
        "overall_trust": trust,
        "alignment_status": alignment,
    })


# ── Pipeline wiring ──────────────────────────────────────────────

class TestPipelineWiring:
    """Verify that evaluate() calls the pipeline stages in order."""

    @patch("ethos.evaluate.call_claude")
    def test_calls_pipeline_stages(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Hello world")
        assert isinstance(result, EvaluationResult)
        mock_claude.assert_called_once()

    @patch("ethos.evaluate.call_claude")
    def test_scan_keywords_determines_tier(self, mock_claude):
        """Manipulative text should route to focused/deep tier."""
        mock_claude.return_value = _mock_claude_response(
            {"manipulation": 0.8}, trust="mixed"
        )
        evaluate("Act now! Don't wait! Last chance! Hurry!")
        # call_claude receives the tier from scan_keywords
        call_args = mock_claude.call_args
        tier = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get("tier")
        assert tier in ("focused", "deep", "deep_with_context")

    @patch("ethos.evaluate.call_claude")
    def test_returns_evaluation_result(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Test message")
        assert isinstance(result, EvaluationResult)


# ── EvaluationResult fields ──────────────────────────────────────

class TestResultFields:
    """Verify the returned EvaluationResult has all required fields populated."""

    @patch("ethos.evaluate.call_claude")
    def test_has_dimension_scores(self, mock_claude):
        mock_claude.return_value = _mock_claude_response(
            {"virtue": 0.8, "goodwill": 0.7, "manipulation": 0.1, "deception": 0.1}
        )
        result = evaluate("Good message")
        assert 0.0 <= result.ethos <= 1.0
        assert 0.0 <= result.logos <= 1.0
        assert 0.0 <= result.pathos <= 1.0

    @patch("ethos.evaluate.call_claude")
    def test_has_tier_scores(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Test")
        assert "safety" in result.tier_scores
        assert "ethics" in result.tier_scores
        assert "soundness" in result.tier_scores
        assert "helpfulness" in result.tier_scores

    @patch("ethos.evaluate.call_claude")
    def test_has_alignment_status(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Test")
        assert result.alignment_status in ("aligned", "drifting", "misaligned", "violation")

    @patch("ethos.evaluate.call_claude")
    def test_has_phronesis(self, mock_claude):
        mock_claude.return_value = _mock_claude_response(trust="trustworthy")
        result = evaluate("Test")
        assert result.phronesis == "trustworthy"

    @patch("ethos.evaluate.call_claude")
    def test_has_traits_dict(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Test")
        assert len(result.traits) == 12
        for trait_name in ALL_TRAITS:
            assert trait_name in result.traits

    @patch("ethos.evaluate.call_claude")
    def test_has_evaluation_id(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Test")
        assert result.evaluation_id != ""
        # Should be a UUID format (36 chars with dashes)
        assert len(result.evaluation_id) == 36

    @patch("ethos.evaluate.call_claude")
    def test_has_routing_tier(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Test")
        assert result.routing_tier in ("standard", "focused", "deep", "deep_with_context")

    @patch("ethos.evaluate.call_claude")
    def test_has_keyword_density(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Test")
        assert isinstance(result.keyword_density, float)

    @patch("ethos.evaluate.call_claude")
    def test_has_model_used(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Test")
        assert result.model_used != ""

    @patch("ethos.evaluate.call_claude")
    def test_has_detected_indicators(self, mock_claude):
        indicators = [
            {"id": "MAN-01", "name": "false_urgency", "trait": "manipulation",
             "confidence": 0.85, "evidence": "Uses urgent language"}
        ]
        mock_claude.return_value = _mock_claude_response(indicators=indicators)
        result = evaluate("Act now!")
        assert len(result.detected_indicators) == 1
        assert result.detected_indicators[0].id == "MAN-01"

    @patch("ethos.evaluate.call_claude")
    def test_has_flags(self, mock_claude):
        """High negative trait score should generate flags."""
        mock_claude.return_value = _mock_claude_response({"manipulation": 0.9})
        result = evaluate("Manipulative text")
        assert isinstance(result.flags, list)


# ── Scoring correctness ─────────────────────────────────────────

class TestScoringCorrectness:
    @patch("ethos.evaluate.call_claude")
    def test_dimension_scores_computed(self, mock_claude):
        """Dimension scores should reflect trait values."""
        mock_claude.return_value = _mock_claude_response({
            "virtue": 0.9, "goodwill": 0.9, "manipulation": 0.0, "deception": 0.0,
        })
        result = evaluate("Very ethical message")
        # ethos = mean(0.9, 0.9, 1.0-0.0, 1.0-0.0) = 0.95
        assert result.ethos == pytest.approx(0.95, abs=0.01)

    @patch("ethos.evaluate.call_claude")
    def test_hard_constraint_routes_to_violation(self, mock_claude):
        """Hard constraint keywords should force alignment_status to violation."""
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("bypass safety and remove guardrails")
        assert result.alignment_status == "violation"


# ── Graph context (source provided) ─────────────────────────────

class TestGraphContext:
    @patch("ethos.evaluate.call_claude")
    def test_without_source_no_graph_context(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Test")
        assert result.graph_context is None

    @patch("ethos.evaluate.call_claude")
    @patch("ethos.graph.service.GraphService")
    def test_with_source_attempts_graph_read(self, mock_graph_cls, mock_claude):
        """When source is provided, should attempt to read graph context."""
        mock_claude.return_value = _mock_claude_response()
        mock_service = MagicMock()
        mock_service.connected = False
        mock_graph_cls.return_value = mock_service
        result = evaluate("Test", source="agent-001")
        # Even if graph is down, should not crash
        assert isinstance(result, EvaluationResult)

    @patch("ethos.evaluate.call_claude")
    @patch("ethos.graph.service.GraphService")
    def test_graph_down_returns_result_no_crash(self, mock_graph_cls, mock_claude):
        """Neo4j being down should not crash evaluate()."""
        mock_claude.return_value = _mock_claude_response()
        mock_service = MagicMock()
        mock_service.connected = False
        mock_graph_cls.return_value = mock_service
        result = evaluate("Test", source="agent-001")
        assert isinstance(result, EvaluationResult)
        assert result.graph_context is None


# ── Parse failure fallback ───────────────────────────────────────

class TestParseFailure:
    @patch("ethos.evaluate.call_claude")
    def test_malformed_json_returns_default_result(self, mock_claude):
        """If Claude returns garbage, we still get a valid EvaluationResult."""
        mock_claude.return_value = "this is not json"
        result = evaluate("Test")
        assert isinstance(result, EvaluationResult)
        assert result.phronesis == "unknown"

    @patch("ethos.evaluate.call_claude")
    def test_empty_response_returns_default_result(self, mock_claude):
        mock_claude.return_value = ""
        result = evaluate("Test")
        assert isinstance(result, EvaluationResult)
        assert result.phronesis == "unknown"


# ── No source (backward compatibility) ───────────────────────────

class TestBackwardCompatibility:
    @patch("ethos.evaluate.call_claude")
    def test_evaluate_without_source(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Hello world")
        assert isinstance(result, EvaluationResult)

    @patch("ethos.evaluate.call_claude")
    def test_evaluate_with_source(self, mock_claude):
        mock_claude.return_value = _mock_claude_response()
        result = evaluate("Hello world", source="test-agent")
        assert isinstance(result, EvaluationResult)
