"""Integration tests for the full evaluate() pipeline.

Mocks call_claude_with_tools but runs everything else: instinct scan,
prompt building, parsing, scoring, and result construction.
"""

from unittest.mock import AsyncMock, patch

import pytest

from ethos_academy.evaluate import evaluate
from ethos_academy.shared.errors import EvaluationError
from ethos_academy.shared.models import EvaluationResult


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
) -> tuple[dict[str, dict], str]:
    """Build realistic mock tool call results."""
    scores = {t: 0.5 for t in ALL_TRAITS}
    if overrides:
        scores.update(overrides)
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
            "detect_indicators": {
                "indicators": indicators or [],
            },
            "score_traits": {
                "trait_scores": scores,
                "overall_trust": trust,
                "confidence": confidence,
                "reasoning": "Integration test evaluation",
            },
        },
        "",
    )


@pytest.mark.integration
class TestEvaluatePipeline:
    """Full pipeline tests with mocked Claude client."""

    @patch("ethos_academy.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_evaluate_with_mocked_claude(self, mock_claude):
        """Run full pipeline with benign text. Verify EvaluationResult fields."""
        mock_claude.return_value = _mock_tool_results()
        result = await evaluate("The weather today is sunny and warm.")

        assert isinstance(result, EvaluationResult)
        assert result.evaluation_id != ""
        assert len(result.evaluation_id) == 36  # UUID format
        assert 0.0 <= result.ethos <= 1.0
        assert 0.0 <= result.logos <= 1.0
        assert 0.0 <= result.pathos <= 1.0
        assert result.phronesis in ("trustworthy", "mixed", "unknown", "undetermined")
        assert result.alignment_status in (
            "aligned",
            "drifting",
            "misaligned",
            "violation",
        )
        assert len(result.traits) == 12
        assert result.model_used != ""
        assert result.routing_tier in (
            "standard",
            "focused",
            "deep",
            "deep_with_context",
        )
        assert isinstance(result.keyword_density, float)
        assert result.intent_classification is not None
        assert result.scoring_reasoning == "Integration test evaluation"

    @patch("ethos_academy.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_evaluate_flags_manipulative_text(self, mock_claude):
        """Manipulation keywords should escalate routing tier above standard."""
        mock_claude.return_value = _mock_tool_results(
            overrides={"manipulation": 0.85, "deception": 0.7},
            trust="mixed",
        )
        result = await evaluate(
            "Act now! Don't wait! This is your last chance! Hurry before it's too late!"
        )

        assert isinstance(result, EvaluationResult)
        # Keyword-heavy text should route above standard
        assert result.routing_tier in ("focused", "deep", "deep_with_context")

    async def test_evaluate_empty_text_raises(self):
        """Empty text should raise EvaluationError."""
        with pytest.raises(EvaluationError, match="empty"):
            await evaluate("")

    async def test_evaluate_long_text_raises(self):
        """Text over 100k characters should raise EvaluationError."""
        with pytest.raises(EvaluationError, match="maximum length"):
            await evaluate("x" * 100_001)

    @patch("ethos_academy.evaluate.call_claude_with_tools", new_callable=AsyncMock)
    async def test_evaluate_result_scores_in_range(self, mock_claude):
        """All trait scores and dimension scores must be 0.0-1.0."""
        mock_claude.return_value = _mock_tool_results(
            overrides={
                "virtue": 0.9,
                "goodwill": 0.8,
                "manipulation": 0.1,
                "deception": 0.05,
                "accuracy": 0.85,
                "reasoning": 0.9,
                "fabrication": 0.1,
                "broken_logic": 0.05,
                "recognition": 0.7,
                "compassion": 0.8,
                "dismissal": 0.1,
                "exploitation": 0.05,
            }
        )
        result = await evaluate("A helpful and honest response with good reasoning.")

        # Dimension scores
        assert 0.0 <= result.ethos <= 1.0
        assert 0.0 <= result.logos <= 1.0
        assert 0.0 <= result.pathos <= 1.0

        # All 12 trait scores
        for trait_name in ALL_TRAITS:
            assert trait_name in result.traits, f"Missing trait: {trait_name}"
            score = result.traits[trait_name].score
            assert 0.0 <= score <= 1.0, f"{trait_name} score {score} out of range"

        # Tier scores
        for tier_name, tier_score in result.tier_scores.items():
            assert 0.0 <= tier_score <= 1.0, f"Tier {tier_name} score out of range"

        # Confidence
        assert 0.0 <= result.confidence <= 1.0
