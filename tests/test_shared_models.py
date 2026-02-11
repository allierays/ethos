"""TDD tests for ethos.shared domain — models and errors."""

import pytest


# ── Model import tests ──────────────────────────────────────────────

class TestModelImports:
    """All models must be importable from ethos.shared.models."""

    def test_import_routing_tier(self):
        from ethos.shared.models import RoutingTier
        assert RoutingTier.STANDARD == "standard"
        assert RoutingTier.FOCUSED == "focused"
        assert RoutingTier.DEEP == "deep"
        assert RoutingTier.DEEP_WITH_CONTEXT == "deep_with_context"

    def test_import_priority(self):
        from ethos.shared.models import Priority
        assert Priority.CRITICAL == "critical"
        assert Priority.HIGH == "high"
        assert Priority.STANDARD == "standard"
        assert Priority.LOW == "low"

    def test_import_detected_indicator(self):
        from ethos.shared.models import DetectedIndicator
        ind = DetectedIndicator(id="M-01", name="test", trait="manipulation", confidence=0.8, severity=0.5)
        assert ind.id == "M-01"
        assert ind.confidence == 0.8

    def test_import_trait_score(self):
        from ethos.shared.models import TraitScore
        ts = TraitScore(name="manipulation", dimension="ethos", polarity="negative")
        assert ts.score == 0.0
        assert ts.name == "manipulation"

    def test_import_graph_context(self):
        from ethos.shared.models import GraphContext
        gc = GraphContext()
        assert gc.prior_evaluations == 0
        assert gc.trust_trend == "insufficient_data"

    def test_import_keyword_scan_result(self):
        from ethos.shared.models import KeywordScanResult
        ksr = KeywordScanResult()
        assert ksr.total_flags == 0
        assert ksr.routing_tier == "standard"

    def test_import_insight(self):
        from ethos.shared.models import Insight
        i = Insight(trait="manipulation")
        assert i.severity == "info"

    def test_import_insights_result(self):
        from ethos.shared.models import InsightsResult
        ir = InsightsResult()
        assert ir.insights == []


# ── EvaluationResult tests ──────────────────────────────────────────

class TestEvaluationResult:
    """EvaluationResult must have all fields including new alignment_status and tier_scores."""

    def test_default_values(self):
        from ethos.shared.models import EvaluationResult
        r = EvaluationResult()
        assert r.ethos == 0.0
        assert r.logos == 0.0
        assert r.pathos == 0.0
        assert r.trust == "unknown"
        assert r.flags == []
        assert r.traits == {}

    def test_alignment_status_default(self):
        from ethos.shared.models import EvaluationResult
        r = EvaluationResult()
        assert r.alignment_status == "unknown"

    def test_tier_scores_default(self):
        from ethos.shared.models import EvaluationResult
        r = EvaluationResult()
        assert r.tier_scores == {}

    def test_alignment_status_settable(self):
        from ethos.shared.models import EvaluationResult
        r = EvaluationResult(alignment_status="aligned")
        assert r.alignment_status == "aligned"

    def test_tier_scores_settable(self):
        from ethos.shared.models import EvaluationResult
        r = EvaluationResult(tier_scores={"safety": 0.3, "ethics": 0.7})
        assert r.tier_scores["safety"] == 0.3
        assert r.tier_scores["ethics"] == 0.7

    def test_score_bounds(self):
        from ethos.shared.models import EvaluationResult
        with pytest.raises(Exception):
            EvaluationResult(ethos=1.5)
        with pytest.raises(Exception):
            EvaluationResult(logos=-0.1)

    def test_metadata_fields(self):
        from ethos.shared.models import EvaluationResult
        r = EvaluationResult(evaluation_id="abc", model_used="test", created_at="2025-01-01")
        assert r.evaluation_id == "abc"
        assert r.model_used == "test"


# ── ReflectionResult tests ──────────────────────────────────────────

class TestReflectionResult:
    def test_default_values(self):
        from ethos.shared.models import ReflectionResult
        r = ReflectionResult()
        assert r.compassion == 0.0
        assert r.honesty == 0.0
        assert r.accuracy == 0.0
        assert r.trend == "stable"
        assert r.evaluation_count == 0

    def test_trait_averages(self):
        from ethos.shared.models import ReflectionResult
        r = ReflectionResult(trait_averages={"manipulation": 0.2, "deception": 0.1})
        assert r.trait_averages["manipulation"] == 0.2


# ── Error tests ─────────────────────────────────────────────────────

class TestErrors:
    """Custom exception hierarchy must be importable and well-structured."""

    def test_import_ethos_error(self):
        from ethos.shared.errors import EthosError
        assert issubclass(EthosError, Exception)

    def test_import_graph_unavailable_error(self):
        from ethos.shared.errors import GraphUnavailableError
        assert issubclass(GraphUnavailableError, Exception)

    def test_import_evaluation_error(self):
        from ethos.shared.errors import EvaluationError
        assert issubclass(EvaluationError, Exception)

    def test_import_config_error(self):
        from ethos.shared.errors import ConfigError
        assert issubclass(ConfigError, Exception)

    def test_import_parse_error(self):
        from ethos.shared.errors import ParseError
        assert issubclass(ParseError, Exception)

    def test_all_errors_inherit_from_ethos_error(self):
        from ethos.shared.errors import (
            EthosError,
            GraphUnavailableError,
            EvaluationError,
            ConfigError,
            ParseError,
        )
        assert issubclass(GraphUnavailableError, EthosError)
        assert issubclass(EvaluationError, EthosError)
        assert issubclass(ConfigError, EthosError)
        assert issubclass(ParseError, EthosError)

    def test_error_message(self):
        from ethos.shared.errors import EthosError
        e = EthosError("something went wrong")
        assert str(e) == "something went wrong"

    def test_raise_and_catch(self):
        from ethos.shared.errors import GraphUnavailableError, EthosError
        with pytest.raises(EthosError):
            raise GraphUnavailableError("Neo4j is down")


# ── Re-export tests ─────────────────────────────────────────────────

class TestReExports:
    """ethos.shared.__init__.py must re-export all models and errors."""

    def test_models_from_shared(self):
        from ethos.shared import (
            RoutingTier,
            Priority,
        )
        assert RoutingTier is not None
        assert Priority is not None

    def test_errors_from_shared(self):
        from ethos.shared import (
            EthosError,
            GraphUnavailableError,
        )
        assert issubclass(GraphUnavailableError, EthosError)
