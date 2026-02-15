"""Authenticity analysis pure functions.

Scores AI agent posting behavior for signs of autonomy, human influence,
or bot farm activity. All functions are pure computation — no I/O.

Research basis:
- Temporal Fingerprint (arXiv:2602.07432): CV of inter-post intervals
- Burst rate (SimulaMet Observatory): bot farms post in tight clusters
- Activity pattern: real AI agents run 24/7, humans show sleep gaps
- Identity signals: Moltbook platform verification data
"""

from __future__ import annotations

import logging
import statistics
from collections import Counter
from datetime import datetime

from ethos_academy.shared.models import (
    ActivityPattern,
    AuthenticityResult,
    BurstAnalysis,
    IdentitySignals,
    TemporalSignature,
)

logger = logging.getLogger(__name__)

# ── Thresholds (named for easy tuning) ───────────────────────────────

# Temporal signature: CV of inter-post intervals
CV_AUTONOMOUS_THRESHOLD = 0.3  # CV below → autonomous (clockwork posting)
CV_HUMAN_THRESHOLD = 1.0  # CV above → human_influenced (irregular)
CV_NORMALIZATION_CAP = 2.0  # CV at or above → score 0.0

# Burst detection: fraction of consecutive posts within window
BURST_WINDOW_SECONDS = 10  # max gap to count as a burst
BURST_BOT_THRESHOLD = 0.5  # rate above → burst_bot
BURST_AUTOMATED_THRESHOLD = 0.2  # rate above → automated

# Activity pattern: consecutive zero-activity hours
SLEEP_GAP_HOURS = 6  # consecutive inactive hours → human_schedule

# Minimum data requirements
MIN_TEMPORAL_TIMESTAMPS = 5
MIN_BURST_TIMESTAMPS = 3

# Composite scoring weights
WEIGHT_TEMPORAL = 0.35
WEIGHT_BURST = 0.25
WEIGHT_ACTIVITY = 0.25
WEIGHT_IDENTITY = 0.15

# Classification thresholds
AUTONOMOUS_SCORE_THRESHOLD = 0.7
HUMAN_SCORE_THRESHOLD = 0.3


def parse_timestamps(raw: list[str]) -> list[datetime]:
    """Parse ISO 8601 timestamps, skipping invalid ones. Sorted ascending."""
    parsed = []
    for ts in raw:
        try:
            parsed.append(datetime.fromisoformat(ts))
        except (ValueError, TypeError):
            logger.warning("Skipping invalid timestamp: %s", ts)
    parsed.sort()
    return parsed


def analyze_temporal_signature(
    timestamps: list[str],
    *,
    _parsed: list[datetime] | None = None,
) -> TemporalSignature:
    """Compute coefficient of variation of inter-post intervals.

    CV < CV_AUTONOMOUS_THRESHOLD → autonomous (regular posting like clockwork)
    CV > CV_HUMAN_THRESHOLD → human_influenced (irregular, random timing)
    Otherwise → indeterminate

    Requires >= MIN_TEMPORAL_TIMESTAMPS timestamps, else returns default.
    """
    parsed = _parsed if _parsed is not None else parse_timestamps(timestamps)
    if len(parsed) < MIN_TEMPORAL_TIMESTAMPS:
        return TemporalSignature()

    intervals = [
        (parsed[i + 1] - parsed[i]).total_seconds() for i in range(len(parsed) - 1)
    ]

    mean = statistics.mean(intervals)
    if mean == 0:
        return TemporalSignature(
            cv_score=0.0, mean_interval_seconds=0.0, classification="autonomous"
        )

    std = statistics.pstdev(intervals)
    cv = std / mean

    # Normalize CV to 0-1 score: lower CV = higher autonomy score
    cv_score = max(0.0, min(1.0, 1.0 - (cv / CV_NORMALIZATION_CAP)))

    if cv < CV_AUTONOMOUS_THRESHOLD:
        classification = "autonomous"
    elif cv > CV_HUMAN_THRESHOLD:
        classification = "human_influenced"
    else:
        classification = "indeterminate"

    return TemporalSignature(
        cv_score=cv_score,
        mean_interval_seconds=mean,
        classification=classification,
    )


def analyze_burst_rate(
    timestamps: list[str],
    *,
    _parsed: list[datetime] | None = None,
) -> BurstAnalysis:
    """Compute percentage of consecutive posts within BURST_WINDOW_SECONDS.

    > BURST_BOT_THRESHOLD → burst_bot (bot farm behavior)
    > BURST_AUTOMATED_THRESHOLD → automated
    Otherwise → organic

    Requires >= MIN_BURST_TIMESTAMPS timestamps.
    """
    parsed = _parsed if _parsed is not None else parse_timestamps(timestamps)
    if len(parsed) < MIN_BURST_TIMESTAMPS:
        return BurstAnalysis(burst_rate=0.0, classification="organic")

    burst_count = sum(
        1
        for i in range(len(parsed) - 1)
        if (parsed[i + 1] - parsed[i]).total_seconds() <= BURST_WINDOW_SECONDS
    )
    total_pairs = len(parsed) - 1
    rate = burst_count / total_pairs

    if rate > BURST_BOT_THRESHOLD:
        classification = "burst_bot"
    elif rate > BURST_AUTOMATED_THRESHOLD:
        classification = "automated"
    else:
        classification = "organic"

    return BurstAnalysis(burst_rate=rate, classification=classification)


def analyze_activity_pattern(
    timestamps: list[str],
    *,
    _parsed: list[datetime] | None = None,
) -> ActivityPattern:
    """Bin posts into 24 hours, detect sleep gaps.

    >= SLEEP_GAP_HOURS consecutive zero-activity hours → human_schedule
    All 24 hours active → always_on
    Otherwise → mixed
    """
    parsed = _parsed if _parsed is not None else parse_timestamps(timestamps)
    if not parsed:
        return ActivityPattern(
            classification="mixed", active_hours=0, has_sleep_gap=False
        )

    hour_counts = Counter(dt.hour for dt in parsed)
    active_hours = sum(1 for h in range(24) if hour_counts.get(h, 0) > 0)

    # Check for sleep gap: >= SLEEP_GAP_HOURS consecutive zero-activity hours
    has_sleep_gap = False
    # Use circular check (wrap around midnight)
    for start in range(24):
        gap = 0
        for offset in range(24):
            hour = (start + offset) % 24
            if hour_counts.get(hour, 0) == 0:
                gap += 1
                if gap >= SLEEP_GAP_HOURS:
                    has_sleep_gap = True
                    break
            else:
                gap = 0
        if has_sleep_gap:
            break

    if has_sleep_gap:
        classification = "human_schedule"
    elif active_hours == 24:
        classification = "always_on"
    else:
        classification = "mixed"

    return ActivityPattern(
        classification=classification,
        active_hours=active_hours,
        has_sleep_gap=has_sleep_gap,
    )


def analyze_identity_signals(profile: dict) -> IdentitySignals:
    """Extract identity signals from a Moltbook agent profile dict.

    Expected keys: is_claimed, owner.x_verified, karma, post_count, comment_count.
    If post_count/comment_count are missing, falls back to 0.
    """
    if not profile:
        return IdentitySignals()

    is_claimed = bool(profile.get("is_claimed", False))
    owner = profile.get("owner", {}) or {}
    owner_verified = bool(owner.get("x_verified", False))

    karma = profile.get("karma", 0) or 0
    post_count = profile.get("post_count", 0) or 0
    comment_count = profile.get("comment_count", 0) or 0
    total_activity = post_count + comment_count

    karma_post_ratio = karma / total_activity if total_activity > 0 else 0.0

    return IdentitySignals(
        is_claimed=is_claimed,
        owner_verified=owner_verified,
        karma_post_ratio=karma_post_ratio,
    )


def _classification_to_score(classification: str) -> float:
    """Convert sub-classification to numeric score.

    Autonomous/organic/always_on → 1.0 (more autonomous)
    Human-influenced/human_schedule → 0.0 (more human)
    Indeterminate/mixed/automated/burst_bot → 0.5
    """
    high = {"autonomous", "organic", "always_on"}
    low = {"human_influenced", "human_schedule"}
    mid = {"indeterminate", "mixed", "automated", "burst_bot"}

    if classification in high:
        return 1.0
    if classification in low:
        return 0.0
    if classification in mid:
        return 0.5
    return 0.5


def _identity_score(identity: IdentitySignals) -> float:
    """Score identity signals: not claimed = 1.0, claimed+verified = 0.0."""
    if identity.is_claimed and identity.owner_verified:
        return 0.0
    if identity.is_claimed:
        return 0.25
    return 1.0


def _confidence_from_count(num_timestamps: int) -> float:
    """Compute confidence based on data volume."""
    if num_timestamps >= 50:
        return 0.9
    if num_timestamps >= 20:
        return 0.7
    if num_timestamps >= 5:
        return 0.5
    return 0.1


def compute_authenticity(
    temporal: TemporalSignature,
    burst: BurstAnalysis,
    activity: ActivityPattern,
    identity: IdentitySignals,
    num_timestamps: int,
    agent_name: str = "",
) -> AuthenticityResult:
    """Combine sub-scores into final authenticity assessment.

    Weights: temporal=0.35, burst=0.25, activity=0.25, identity=0.15
    Score > AUTONOMOUS_SCORE_THRESHOLD → likely_autonomous
    Score < HUMAN_SCORE_THRESHOLD → likely_human
    burst_bot classification overrides to high_frequency
    """
    confidence = _confidence_from_count(num_timestamps)

    # Insufficient data → default to indeterminate
    if num_timestamps < MIN_TEMPORAL_TIMESTAMPS:
        return AuthenticityResult(
            agent_name=agent_name,
            temporal=temporal,
            burst=burst,
            activity=activity,
            identity=identity,
            authenticity_score=0.5,
            classification="indeterminate",
            confidence=confidence,
        )

    temporal_score = _classification_to_score(temporal.classification)
    burst_score = _classification_to_score(burst.classification)
    activity_score = _classification_to_score(activity.classification)
    id_score = _identity_score(identity)

    weighted = (
        temporal_score * WEIGHT_TEMPORAL
        + burst_score * WEIGHT_BURST
        + activity_score * WEIGHT_ACTIVITY
        + id_score * WEIGHT_IDENTITY
    )

    # Clamp to [0.0, 1.0]
    authenticity_score = max(0.0, min(1.0, weighted))

    # Classification
    if burst.classification == "burst_bot":
        classification = "high_frequency"
    elif authenticity_score > AUTONOMOUS_SCORE_THRESHOLD:
        classification = "likely_autonomous"
    elif authenticity_score < HUMAN_SCORE_THRESHOLD:
        classification = "likely_human"
    else:
        classification = "indeterminate"

    return AuthenticityResult(
        agent_name=agent_name,
        temporal=temporal,
        burst=burst,
        activity=activity,
        identity=identity,
        authenticity_score=authenticity_score,
        classification=classification,
        confidence=confidence,
    )
