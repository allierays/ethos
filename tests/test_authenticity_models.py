"""Tests for authenticity detection Pydantic models.

Covers:
- Default construction for all 5 models
- Pydantic validation rejects out-of-range scores
- model_dump() roundtrip (serialize then reconstruct)
- Nested model defaults work correctly in AuthenticityResult
- Re-exports from ethos_academy.models
"""

import pytest
from pydantic import ValidationError

from ethos_academy.shared.models import (
    ActivityPattern,
    AuthenticityResult,
    BurstAnalysis,
    IdentitySignals,
    TemporalSignature,
)


# ── Default construction ─────────────────────────────────────────


class TestDefaults:
    def test_temporal_signature_defaults(self):
        ts = TemporalSignature()
        assert ts.cv_score == 0.0
        assert ts.mean_interval_seconds == 0.0
        assert ts.classification == "indeterminate"

    def test_burst_analysis_defaults(self):
        ba = BurstAnalysis()
        assert ba.burst_rate == 0.0
        assert ba.classification == "organic"

    def test_activity_pattern_defaults(self):
        ap = ActivityPattern()
        assert ap.classification == "mixed"
        assert ap.active_hours == 24
        assert ap.has_sleep_gap is False

    def test_identity_signals_defaults(self):
        ids = IdentitySignals()
        assert ids.is_claimed is False
        assert ids.owner_verified is False
        assert ids.karma_post_ratio == 0.0

    def test_authenticity_result_defaults(self):
        ar = AuthenticityResult(agent_name="test")
        assert ar.agent_name == "test"
        assert ar.authenticity_score == 0.5
        assert ar.classification == "indeterminate"
        assert ar.confidence == 0.0

    def test_authenticity_result_nested_defaults(self):
        ar = AuthenticityResult(agent_name="test")
        assert isinstance(ar.temporal, TemporalSignature)
        assert ar.temporal.classification == "indeterminate"
        assert isinstance(ar.burst, BurstAnalysis)
        assert ar.burst.classification == "organic"
        assert isinstance(ar.activity, ActivityPattern)
        assert ar.activity.classification == "mixed"
        assert isinstance(ar.identity, IdentitySignals)
        assert ar.identity.is_claimed is False


# ── Validation ───────────────────────────────────────────────────


class TestValidation:
    def test_authenticity_score_rejects_above_one(self):
        with pytest.raises(ValidationError):
            AuthenticityResult(agent_name="x", authenticity_score=2.0)

    def test_authenticity_score_rejects_below_zero(self):
        with pytest.raises(ValidationError):
            AuthenticityResult(agent_name="x", authenticity_score=-0.1)

    def test_confidence_rejects_above_one(self):
        with pytest.raises(ValidationError):
            AuthenticityResult(agent_name="x", confidence=1.5)

    def test_cv_score_rejects_above_one(self):
        with pytest.raises(ValidationError):
            TemporalSignature(cv_score=1.5)

    def test_burst_rate_rejects_above_one(self):
        with pytest.raises(ValidationError):
            BurstAnalysis(burst_rate=1.1)

    def test_valid_scores_accepted(self):
        ar = AuthenticityResult(
            agent_name="valid",
            authenticity_score=0.85,
            confidence=0.9,
        )
        assert ar.authenticity_score == 0.85
        assert ar.confidence == 0.9


# ── model_dump() roundtrip ───────────────────────────────────────


class TestRoundtrip:
    def test_temporal_signature_roundtrip(self):
        orig = TemporalSignature(
            cv_score=0.3, mean_interval_seconds=120.5, classification="autonomous"
        )
        rebuilt = TemporalSignature(**orig.model_dump())
        assert rebuilt == orig

    def test_burst_analysis_roundtrip(self):
        orig = BurstAnalysis(burst_rate=0.6, classification="automated")
        rebuilt = BurstAnalysis(**orig.model_dump())
        assert rebuilt == orig

    def test_activity_pattern_roundtrip(self):
        orig = ActivityPattern(
            classification="human_schedule", active_hours=16, has_sleep_gap=True
        )
        rebuilt = ActivityPattern(**orig.model_dump())
        assert rebuilt == orig

    def test_identity_signals_roundtrip(self):
        orig = IdentitySignals(
            is_claimed=True, owner_verified=True, karma_post_ratio=3.5
        )
        rebuilt = IdentitySignals(**orig.model_dump())
        assert rebuilt == orig

    def test_authenticity_result_roundtrip(self):
        orig = AuthenticityResult(
            agent_name="roundtrip-bot",
            temporal=TemporalSignature(cv_score=0.2, classification="autonomous"),
            burst=BurstAnalysis(burst_rate=0.1, classification="organic"),
            activity=ActivityPattern(classification="always_on", active_hours=24),
            identity=IdentitySignals(is_claimed=True, karma_post_ratio=2.0),
            authenticity_score=0.85,
            classification="likely_autonomous",
            confidence=0.7,
        )
        rebuilt = AuthenticityResult(**orig.model_dump())
        assert rebuilt == orig
        assert rebuilt.temporal.cv_score == 0.2
        assert rebuilt.classification == "likely_autonomous"


# ── Re-exports from ethos_academy.models ─────────────────────────────────


class TestReExports:
    def test_all_models_importable_from_ethos_models(self):
        from ethos_academy.models import (
            ActivityPattern as AP,
            AuthenticityResult as AR,
            BurstAnalysis as BA,
            IdentitySignals as IS,
            TemporalSignature as TS,
        )

        assert AP is ActivityPattern
        assert AR is AuthenticityResult
        assert BA is BurstAnalysis
        assert IS is IdentitySignals
        assert TS is TemporalSignature
