"""Tests for authenticity analysis pure functions.

Covers all 5 functions with required cases:
(a) empty timestamps → default/indeterminate
(b) regular intervals → autonomous
(c) random intervals → human_influenced
(d) burst timestamps (within 10s) → burst_bot
(e) 24-hour coverage → always_on
(f) 8-hour gap → human_schedule
(g) profile with is_claimed=True → IdentitySignals.is_claimed=True
(h) compute_authenticity with burst_bot override → classification='bot_farm'
"""

from datetime import datetime, timedelta, timezone

from ethos.evaluation.authenticity import (
    analyze_activity_pattern,
    analyze_burst_rate,
    analyze_identity_signals,
    analyze_temporal_signature,
    compute_authenticity,
)
from ethos.shared.models import (
    ActivityPattern,
    AuthenticityResult,
    BurstAnalysis,
    IdentitySignals,
    TemporalSignature,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _regular_timestamps(count: int, interval_hours: float = 1.0) -> list[str]:
    """Generate perfectly regular timestamps."""
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [_iso(base + timedelta(hours=i * interval_hours)) for i in range(count)]


def _random_timestamps() -> list[str]:
    """Timestamps with high variance in intervals (human-like)."""
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    offsets_minutes = [0, 5, 180, 185, 1440, 1500, 2880, 2881, 4320, 4400]
    return [_iso(base + timedelta(minutes=m)) for m in offsets_minutes]


def _burst_timestamps(count: int = 20) -> list[str]:
    """Timestamps all within seconds of each other."""
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [_iso(base + timedelta(seconds=i * 2)) for i in range(count)]


def _all_hours_timestamps() -> list[str]:
    """One post per hour for 24 hours."""
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [_iso(base + timedelta(hours=h)) for h in range(24)]


def _sleep_gap_timestamps() -> list[str]:
    """Posts from 8am-10pm, 8-hour gap (10pm-6am)."""
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    timestamps = []
    for day in range(3):
        for hour in range(8, 22):  # 8am to 9pm
            timestamps.append(_iso(base + timedelta(days=day, hours=hour)))
    return timestamps


# ── analyze_temporal_signature ───────────────────────────────────────


class TestAnalyzeTemporalSignature:
    def test_empty_timestamps(self):
        result = analyze_temporal_signature([])
        assert result.classification == "indeterminate"
        assert result.cv_score == 0.0
        assert result.mean_interval_seconds == 0.0

    def test_fewer_than_5_timestamps(self):
        ts = _regular_timestamps(4)
        result = analyze_temporal_signature(ts)
        assert result.classification == "indeterminate"

    def test_regular_intervals_autonomous(self):
        ts = _regular_timestamps(20, interval_hours=1.0)
        result = analyze_temporal_signature(ts)
        assert result.classification == "autonomous"
        assert result.cv_score > 0.5  # Low CV → high score

    def test_random_intervals_human_influenced(self):
        ts = _random_timestamps()
        result = analyze_temporal_signature(ts)
        assert result.classification == "human_influenced"

    def test_returns_pydantic_model(self):
        result = analyze_temporal_signature([])
        assert isinstance(result, TemporalSignature)
        dumped = result.model_dump()
        assert "cv_score" in dumped
        assert "classification" in dumped

    def test_invalid_timestamps_skipped(self):
        good = _regular_timestamps(6)
        bad = good + ["not-a-date", "also-bad", ""]
        result = analyze_temporal_signature(bad)
        assert result.classification == "autonomous"

    def test_mean_interval_computed(self):
        ts = _regular_timestamps(10, interval_hours=2.0)
        result = analyze_temporal_signature(ts)
        assert abs(result.mean_interval_seconds - 7200.0) < 1.0


# ── analyze_burst_rate ───────────────────────────────────────────────


class TestAnalyzeBurstRate:
    def test_empty_timestamps(self):
        result = analyze_burst_rate([])
        assert result.classification == "organic"
        assert result.burst_rate == 0.0

    def test_fewer_than_3_timestamps(self):
        result = analyze_burst_rate(_regular_timestamps(2))
        assert result.classification == "organic"

    def test_burst_timestamps_burst_bot(self):
        ts = _burst_timestamps(20)
        result = analyze_burst_rate(ts)
        assert result.classification == "burst_bot"
        assert result.burst_rate > 0.5

    def test_regular_hourly_organic(self):
        ts = _regular_timestamps(10, interval_hours=1.0)
        result = analyze_burst_rate(ts)
        assert result.classification == "organic"
        assert result.burst_rate == 0.0

    def test_mixed_some_bursts_automated(self):
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        ts = []
        # 3 regular posts (not bursts)
        for i in range(3):
            ts.append(_iso(base + timedelta(hours=i)))
        # 3 burst posts (within 10s)
        burst_base = base + timedelta(hours=5)
        for i in range(3):
            ts.append(_iso(burst_base + timedelta(seconds=i * 5)))
        result = analyze_burst_rate(ts)
        # 2 burst pairs out of 5 total pairs = 0.4 → automated (>0.2, <=0.5)
        assert result.classification == "automated"

    def test_returns_pydantic_model(self):
        result = analyze_burst_rate([])
        assert isinstance(result, BurstAnalysis)
        dumped = result.model_dump()
        assert "burst_rate" in dumped
        assert "classification" in dumped


# ── analyze_activity_pattern ─────────────────────────────────────────


class TestAnalyzeActivityPattern:
    def test_empty_timestamps(self):
        result = analyze_activity_pattern([])
        assert result.classification == "mixed"
        assert result.active_hours == 0

    def test_all_24_hours_always_on(self):
        ts = _all_hours_timestamps()
        result = analyze_activity_pattern(ts)
        assert result.classification == "always_on"
        assert result.active_hours == 24
        assert result.has_sleep_gap is False

    def test_sleep_gap_human_schedule(self):
        ts = _sleep_gap_timestamps()
        result = analyze_activity_pattern(ts)
        assert result.classification == "human_schedule"
        assert result.has_sleep_gap is True

    def test_few_hours_mixed(self):
        base = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        ts = [_iso(base + timedelta(hours=i)) for i in range(4)]
        result = analyze_activity_pattern(ts)
        # Only 4 hours active, large gap but classification depends on gap size
        assert result.classification in ("human_schedule", "mixed")

    def test_returns_pydantic_model(self):
        result = analyze_activity_pattern([])
        assert isinstance(result, ActivityPattern)
        dumped = result.model_dump()
        assert "classification" in dumped
        assert "active_hours" in dumped
        assert "has_sleep_gap" in dumped


# ── analyze_identity_signals ─────────────────────────────────────────


class TestAnalyzeIdentitySignals:
    def test_empty_profile(self):
        result = analyze_identity_signals({})
        assert result.is_claimed is False
        assert result.owner_verified is False
        assert result.karma_post_ratio == 0.0

    def test_claimed_profile(self):
        result = analyze_identity_signals({"is_claimed": True, "owner": {"x_verified": False}})
        assert result.is_claimed is True
        assert result.owner_verified is False

    def test_verified_owner(self):
        result = analyze_identity_signals({"is_claimed": True, "owner": {"x_verified": True}})
        assert result.is_claimed is True
        assert result.owner_verified is True

    def test_karma_ratio(self):
        profile = {
            "is_claimed": False,
            "owner": {"x_verified": False},
            "karma": 100,
            "post_count": 8,
            "comment_count": 2,
        }
        result = analyze_identity_signals(profile)
        assert result.karma_post_ratio == 10.0  # 100 / (8+2)

    def test_zero_activity_no_division_error(self):
        profile = {"karma": 50, "post_count": 0, "comment_count": 0}
        result = analyze_identity_signals(profile)
        assert result.karma_post_ratio == 0.0

    def test_missing_keys_defaults(self):
        result = analyze_identity_signals({"some_random_key": "value"})
        assert result.is_claimed is False
        assert result.owner_verified is False

    def test_returns_pydantic_model(self):
        result = analyze_identity_signals({})
        assert isinstance(result, IdentitySignals)
        dumped = result.model_dump()
        assert "is_claimed" in dumped
        assert "owner_verified" in dumped
        assert "karma_post_ratio" in dumped


# ── compute_authenticity ─────────────────────────────────────────────


class TestComputeAuthenticity:
    def test_all_autonomous_signals(self):
        temporal = TemporalSignature(cv_score=0.9, classification="autonomous")
        burst = BurstAnalysis(burst_rate=0.0, classification="organic")
        activity = ActivityPattern(classification="always_on")
        identity = IdentitySignals(is_claimed=False)

        result = compute_authenticity(temporal, burst, activity, identity, num_timestamps=50)
        assert result.classification == "likely_autonomous"
        assert result.authenticity_score > 0.7
        assert result.confidence == 0.9

    def test_all_human_signals(self):
        temporal = TemporalSignature(cv_score=0.1, classification="human_influenced")
        burst = BurstAnalysis(burst_rate=0.0, classification="organic")
        activity = ActivityPattern(classification="human_schedule")
        identity = IdentitySignals(is_claimed=True, owner_verified=True)

        result = compute_authenticity(temporal, burst, activity, identity, num_timestamps=50)
        assert result.classification == "likely_human"
        assert result.authenticity_score < 0.3

    def test_burst_bot_override(self):
        temporal = TemporalSignature(cv_score=0.9, classification="autonomous")
        burst = BurstAnalysis(burst_rate=0.8, classification="burst_bot")
        activity = ActivityPattern(classification="always_on")
        identity = IdentitySignals(is_claimed=False)

        result = compute_authenticity(temporal, burst, activity, identity, num_timestamps=50)
        assert result.classification == "bot_farm"

    def test_confidence_tiers(self):
        temporal = TemporalSignature()
        burst = BurstAnalysis()
        activity = ActivityPattern()
        identity = IdentitySignals()

        r1 = compute_authenticity(temporal, burst, activity, identity, num_timestamps=3)
        assert r1.confidence == 0.1

        r2 = compute_authenticity(temporal, burst, activity, identity, num_timestamps=10)
        assert r2.confidence == 0.5

        r3 = compute_authenticity(temporal, burst, activity, identity, num_timestamps=30)
        assert r3.confidence == 0.7

        r4 = compute_authenticity(temporal, burst, activity, identity, num_timestamps=100)
        assert r4.confidence == 0.9

    def test_indeterminate_classification(self):
        temporal = TemporalSignature(classification="indeterminate")
        burst = BurstAnalysis(classification="organic")
        activity = ActivityPattern(classification="mixed")
        identity = IdentitySignals(is_claimed=True)

        result = compute_authenticity(temporal, burst, activity, identity, num_timestamps=20)
        assert result.classification == "indeterminate"
        assert 0.3 <= result.authenticity_score <= 0.7

    def test_score_bounded(self):
        temporal = TemporalSignature(classification="autonomous")
        burst = BurstAnalysis(classification="organic")
        activity = ActivityPattern(classification="always_on")
        identity = IdentitySignals(is_claimed=False)

        result = compute_authenticity(temporal, burst, activity, identity, num_timestamps=20)
        assert 0.0 <= result.authenticity_score <= 1.0

    def test_returns_pydantic_model(self):
        temporal = TemporalSignature()
        burst = BurstAnalysis()
        activity = ActivityPattern()
        identity = IdentitySignals()

        result = compute_authenticity(temporal, burst, activity, identity, num_timestamps=5)
        assert isinstance(result, AuthenticityResult)
        dumped = result.model_dump()
        assert "authenticity_score" in dumped
        assert "classification" in dumped
        assert "confidence" in dumped
        assert "temporal" in dumped
        assert "burst" in dumped

    def test_sub_results_preserved(self):
        temporal = TemporalSignature(cv_score=0.8, classification="autonomous")
        burst = BurstAnalysis(burst_rate=0.1, classification="organic")
        activity = ActivityPattern(classification="always_on", active_hours=24)
        identity = IdentitySignals(is_claimed=False, owner_verified=False)

        result = compute_authenticity(temporal, burst, activity, identity, num_timestamps=20)
        assert result.temporal.cv_score == 0.8
        assert result.burst.burst_rate == 0.1
        assert result.activity.active_hours == 24
        assert result.identity.is_claimed is False


# ── Integration: end-to-end from raw timestamps ─────────────────────


class TestEndToEnd:
    def test_regular_posting_agent(self):
        ts = _regular_timestamps(20, interval_hours=1.0)
        temporal = analyze_temporal_signature(ts)
        burst = analyze_burst_rate(ts)
        activity = analyze_activity_pattern(ts)
        identity = analyze_identity_signals({"is_claimed": False, "owner": {"x_verified": False}})

        result = compute_authenticity(temporal, burst, activity, identity, num_timestamps=len(ts))
        assert result.authenticity_score > 0.5
        assert result.confidence == 0.7
        assert 0.0 <= result.authenticity_score <= 1.0

    def test_burst_bot_detection(self):
        ts = _burst_timestamps(30)
        temporal = analyze_temporal_signature(ts)
        burst = analyze_burst_rate(ts)
        activity = analyze_activity_pattern(ts)
        identity = analyze_identity_signals({})

        result = compute_authenticity(temporal, burst, activity, identity, num_timestamps=len(ts))
        assert result.classification == "bot_farm"

    def test_empty_timestamps_safe(self):
        temporal = analyze_temporal_signature([])
        burst = analyze_burst_rate([])
        activity = analyze_activity_pattern([])
        identity = analyze_identity_signals({})

        result = compute_authenticity(temporal, burst, activity, identity, num_timestamps=0)
        assert result.classification == "indeterminate"
        assert result.confidence == 0.1
