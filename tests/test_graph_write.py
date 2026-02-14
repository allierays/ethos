"""Tests for ethos/graph/write.py -- graph mutation operations.

Covers store_evaluation (duplicate detection, phronesis_score calculation,
balance_score, trait_variance, indicator param building, error handling),
store_authenticity, and update_agent_specialty.
"""

from __future__ import annotations

import math
from unittest.mock import AsyncMock, MagicMock


from ethos.shared.models import (
    AuthenticityResult,
    DetectedIndicator,
    EvaluationResult,
    IntentClassification,
    TraitScore,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_TRAIT_NAMES = [
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


def _make_result(**overrides) -> EvaluationResult:
    """Build an EvaluationResult with sensible defaults."""
    defaults = {
        "evaluation_id": "eval-001",
        "ethos": 0.8,
        "logos": 0.7,
        "pathos": 0.6,
        "alignment_status": "aligned",
        "flags": [],
        "routing_tier": "standard",
        "keyword_density": 0.02,
        "model_used": "claude-sonnet-4-20250514",
        "agent_model": "test-model",
        "traits": {
            name: TraitScore(
                name=name,
                dimension="ethos",
                polarity="positive",
                score=0.5,
            )
            for name in ALL_TRAIT_NAMES
        },
        "detected_indicators": [],
        "intent_classification": IntentClassification(),
    }
    defaults.update(overrides)
    return EvaluationResult(**defaults)


def _mock_service(connected: bool = True) -> MagicMock:
    """Build a mock GraphService."""
    service = MagicMock()
    service.connected = connected
    service.execute_query = AsyncMock(return_value=([], None, None))
    return service


# ---------------------------------------------------------------------------
# _get_trait_score (unit)
# ---------------------------------------------------------------------------


class TestGetTraitScore:
    """_get_trait_score extracts scores from EvaluationResult.traits dict."""

    def test_returns_score_when_trait_exists(self):
        from ethos.graph.write import _get_trait_score

        result = _make_result()
        assert _get_trait_score(result, "virtue") == 0.5

    def test_returns_zero_when_trait_missing(self):
        from ethos.graph.write import _get_trait_score

        result = _make_result(traits={})
        assert _get_trait_score(result, "virtue") == 0.0

    def test_returns_exact_score_value(self):
        from ethos.graph.write import _get_trait_score

        traits = {
            "accuracy": TraitScore(
                name="accuracy", dimension="logos", polarity="positive", score=0.93
            )
        }
        result = _make_result(traits=traits)
        assert _get_trait_score(result, "accuracy") == 0.93


# ---------------------------------------------------------------------------
# store_evaluation: early exits
# ---------------------------------------------------------------------------


class TestStoreEvaluationEarlyExits:
    """store_evaluation returns early when disconnected or duplicate found."""

    async def test_returns_when_not_connected(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service(connected=False)
        result = _make_result()

        await store_evaluation(service, "agent-1", result)
        service.execute_query.assert_not_called()

    async def test_skips_duplicate_evaluation(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        # First call (duplicate check) returns an existing record
        service.execute_query.return_value = (
            [{"existing_id": "eval-old"}],
            None,
            None,
        )

        result = _make_result()
        await store_evaluation(service, "agent-1", result, message_hash="abc123")

        # Only the duplicate check query runs, not the store query
        assert service.execute_query.call_count == 1

    async def test_proceeds_when_no_duplicate(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        # First call (duplicate check) returns empty, second call (store) succeeds
        service.execute_query.side_effect = [
            ([], None, None),  # duplicate check
            ([], None, None),  # store
        ]

        result = _make_result()
        await store_evaluation(service, "agent-1", result, message_hash="abc123")

        assert service.execute_query.call_count == 2

    async def test_skips_duplicate_check_when_no_hash(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()

        result = _make_result()
        await store_evaluation(service, "agent-1", result, message_hash="")

        # Only the store query runs (no duplicate check)
        assert service.execute_query.call_count == 1

    async def test_continues_if_duplicate_check_fails(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        # Duplicate check raises, store succeeds
        service.execute_query.side_effect = [
            ConnectionError("timeout"),  # duplicate check fails
            ([], None, None),  # store succeeds
        ]

        result = _make_result()
        await store_evaluation(service, "agent-1", result, message_hash="abc123")

        # Both calls happen: failed duplicate check + store
        assert service.execute_query.call_count == 2


# ---------------------------------------------------------------------------
# store_evaluation: computed fields (phronesis_score, balance_score, trait_variance)
# ---------------------------------------------------------------------------


class TestStoreEvaluationComputedFields:
    """store_evaluation calculates agent-level aggregate fields correctly."""

    async def test_phronesis_score_is_dimension_average(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        result = _make_result(ethos=0.9, logos=0.6, pathos=0.3)

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        expected = round((0.9 + 0.6 + 0.3) / 3.0, 4)
        assert params["phronesis_score"] == expected

    async def test_balance_score_perfect_balance(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        result = _make_result(ethos=0.8, logos=0.8, pathos=0.8)

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        # Equal dimensions = zero std_dev = balance 1.0
        assert params["balance_score"] == 1.0

    async def test_balance_score_imbalanced(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        result = _make_result(ethos=1.0, logos=0.5, pathos=0.0)

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        # Verify calculation: mean=0.5, variance=((0.5)^2+(0)^2+(-0.5)^2)/3=0.1667
        # std=0.4082, balance=1-(0.4082/0.5)=0.1835
        scores = [1.0, 0.5, 0.0]
        mean = sum(scores) / 3.0
        variance = sum((s - mean) ** 2 for s in scores) / 3.0
        std_dev = math.sqrt(variance)
        expected = round(max(0.0, min(1.0, 1.0 - (std_dev / mean))), 4)
        assert params["balance_score"] == expected

    async def test_balance_score_zero_mean(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        result = _make_result(ethos=0.0, logos=0.0, pathos=0.0)

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        assert params["balance_score"] == 0.0

    async def test_trait_variance_all_equal(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        # All 12 traits at 0.5 (from _make_result default)
        result = _make_result()

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        assert params["trait_variance"] == 0.0

    async def test_trait_variance_mixed_scores(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        traits = {}
        for i, name in enumerate(ALL_TRAIT_NAMES):
            traits[name] = TraitScore(
                name=name,
                dimension="ethos",
                polarity="positive",
                score=round(i / 11.0, 4),  # 0.0 to 1.0 spread
            )
        result = _make_result(traits=traits)

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        assert params["trait_variance"] > 0.0

        # Verify exact calculation
        scores = [round(i / 11.0, 4) for i in range(12)]
        mean = sum(scores) / 12
        expected = round(sum((s - mean) ** 2 for s in scores) / 12, 4)
        assert params["trait_variance"] == expected


# ---------------------------------------------------------------------------
# store_evaluation: params construction
# ---------------------------------------------------------------------------


class TestStoreEvaluationParams:
    """store_evaluation builds correct Cypher params from EvaluationResult."""

    async def test_all_12_trait_params_present(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        result = _make_result()

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        for name in ALL_TRAIT_NAMES:
            assert f"trait_{name}" in params, f"Missing trait_{name} param"
            assert params[f"trait_{name}"] == 0.5

    async def test_indicators_built_from_detected_indicators(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        indicators = [
            DetectedIndicator(
                id="VIR-AUTHENTIC",
                name="Authentic Self-Presentation",
                trait="virtue",
                confidence=0.9,
                severity=0.1,
                evidence="Direct quote here",
            ),
            DetectedIndicator(
                id="MAN-URGENCY",
                name="False Urgency",
                trait="manipulation",
                confidence=0.7,
                severity=0.8,
                evidence="Act now!",
            ),
        ]
        result = _make_result(detected_indicators=indicators)

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        assert len(params["indicators"]) == 2
        assert params["indicators"][0]["id"] == "VIR-AUTHENTIC"
        assert params["indicators"][0]["confidence"] == 0.9
        assert params["indicators"][1]["id"] == "MAN-URGENCY"

    async def test_empty_indicators_when_none_detected(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        result = _make_result(detected_indicators=[])

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        assert params["indicators"] == []

    async def test_intent_classification_fields(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        intent = IntentClassification(
            rhetorical_mode="persuasive",
            primary_intent="sell",
            cost_to_reader="financial",
            stakes_reality="exaggerated",
            proportionality="disproportionate",
            persona_type="brand_mascot",
            relational_quality="transactional",
        )
        result = _make_result(intent_classification=intent)

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        assert params["intent_rhetorical_mode"] == "persuasive"
        assert params["intent_primary_intent"] == "sell"
        assert params["intent_cost_to_reader"] == "financial"
        assert params["intent_stakes_reality"] == "exaggerated"
        assert params["intent_proportionality"] == "disproportionate"
        assert params["intent_persona_type"] == "brand_mascot"
        assert params["intent_relational_quality"] == "transactional"

    async def test_intent_defaults_to_empty_when_none(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        result = _make_result(intent_classification=None)

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        assert params["intent_rhetorical_mode"] == ""
        assert params["intent_primary_intent"] == ""

    async def test_direction_defaults_to_empty_string(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        result = _make_result()

        await store_evaluation(service, "agent-1", result)

        params = service.execute_query.call_args[0][1]
        assert params["direction"] == ""

    async def test_direction_passed_through(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        result = _make_result()

        await store_evaluation(service, "agent-1", result, direction="incoming")

        params = service.execute_query.call_args[0][1]
        assert params["direction"] == "incoming"


# ---------------------------------------------------------------------------
# store_evaluation: error handling
# ---------------------------------------------------------------------------


class TestStoreEvaluationErrors:
    """store_evaluation fails silently on graph errors (never crashes evaluate)."""

    async def test_connection_error_swallowed(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        service.execute_query.side_effect = ConnectionError("Neo4j down")

        result = _make_result()
        # Should not raise
        await store_evaluation(service, "agent-1", result)

    async def test_generic_exception_swallowed(self):
        from ethos.graph.write import store_evaluation

        service = _mock_service()
        service.execute_query.side_effect = RuntimeError("unexpected")

        result = _make_result()
        await store_evaluation(service, "agent-1", result)


# ---------------------------------------------------------------------------
# update_agent_specialty
# ---------------------------------------------------------------------------


class TestUpdateAgentSpecialty:
    """update_agent_specialty sets specialty on existing Agent nodes."""

    async def test_returns_false_when_not_connected(self):
        from ethos.graph.write import update_agent_specialty

        service = _mock_service(connected=False)
        assert await update_agent_specialty(service, "agent-1", "coding") is False

    async def test_returns_true_when_node_found(self):
        from ethos.graph.write import update_agent_specialty

        service = _mock_service()
        service.execute_query.return_value = (
            [{"updated": "agent-1"}],
            None,
            None,
        )

        assert await update_agent_specialty(service, "agent-1", "coding") is True

    async def test_returns_false_when_node_not_found(self):
        from ethos.graph.write import update_agent_specialty

        service = _mock_service()
        service.execute_query.return_value = ([], None, None)

        assert await update_agent_specialty(service, "ghost", "coding") is False

    async def test_returns_false_on_exception(self):
        from ethos.graph.write import update_agent_specialty

        service = _mock_service()
        service.execute_query.side_effect = RuntimeError("boom")

        assert await update_agent_specialty(service, "agent-1", "coding") is False

    async def test_passes_correct_params(self):
        from ethos.graph.write import update_agent_specialty

        service = _mock_service()
        service.execute_query.return_value = (
            [{"updated": "agent-1"}],
            None,
            None,
        )

        await update_agent_specialty(service, "agent-1", "security research")

        params = service.execute_query.call_args[0][1]
        assert params["agent_id"] == "agent-1"
        assert params["agent_specialty"] == "security research"


# ---------------------------------------------------------------------------
# store_authenticity
# ---------------------------------------------------------------------------


class TestStoreAuthenticity:
    """store_authenticity writes authenticity scores to Agent nodes."""

    async def test_returns_when_not_connected(self):
        from ethos.graph.write import store_authenticity

        service = _mock_service(connected=False)
        result = AuthenticityResult(
            agent_name="bot-1",
            authenticity_score=0.8,
            classification="likely_autonomous",
        )

        await store_authenticity(service, "bot-1", result)
        service.execute_query.assert_not_called()

    async def test_passes_correct_params(self):
        from ethos.graph.write import store_authenticity

        service = _mock_service()
        service.execute_query.return_value = (
            [{"matched": "bot-1"}],
            None,
            None,
        )
        result = AuthenticityResult(
            agent_name="bot-1",
            authenticity_score=0.92,
            classification="likely_autonomous",
        )

        await store_authenticity(service, "bot-1", result)

        params = service.execute_query.call_args[0][1]
        assert params["agent_name"] == "bot-1"
        assert params["authenticity_score"] == 0.92
        assert params["classification"] == "likely_autonomous"

    async def test_handles_no_matching_agent(self):
        from ethos.graph.write import store_authenticity

        service = _mock_service()
        service.execute_query.return_value = ([], None, None)
        result = AuthenticityResult(
            agent_name="ghost",
            authenticity_score=0.5,
            classification="indeterminate",
        )

        # Should not raise
        await store_authenticity(service, "ghost", result)

    async def test_connection_error_swallowed(self):
        from ethos.graph.write import store_authenticity

        service = _mock_service()
        service.execute_query.side_effect = ConnectionError("down")
        result = AuthenticityResult(
            agent_name="bot-1",
            authenticity_score=0.8,
            classification="likely_autonomous",
        )

        await store_authenticity(service, "bot-1", result)

    async def test_generic_exception_swallowed(self):
        from ethos.graph.write import store_authenticity

        service = _mock_service()
        service.execute_query.side_effect = RuntimeError("unexpected")
        result = AuthenticityResult(
            agent_name="bot-1",
            authenticity_score=0.8,
            classification="likely_autonomous",
        )

        await store_authenticity(service, "bot-1", result)
