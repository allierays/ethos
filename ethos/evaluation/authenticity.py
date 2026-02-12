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

from ethos.shared.models import (
    ActivityPattern,
    AuthenticityResult,
    BurstAnalysis,
    IdentitySignals,
    TemporalSignature,
)

logger = logging.getLogger(__name__)


def _parse_timestamps(raw: list[str]) -> list[datetime]:
    """Parse ISO 8601 timestamps, skipping invalid ones."""
    parsed = []
    for ts in raw:
        try:
            parsed.append(datetime.fromisoformat(ts))
        except (ValueError, TypeError):
            logger.warning("Skipping invalid timestamp: %s", ts)
    parsed.sort()
    return parsed


def analyze_temporal_signature(timestamps: list[str]) -> TemporalSignature:
    """Compute coefficient of variation of inter-post intervals.

    CV < 0.3 → autonomous (regular posting like clockwork)
    CV > 1.0 → human_influenced (irregular, random timing)
    Otherwise → indeterminate

    Requires >= 5 timestamps, else returns default.
    """
    parsed = _parse_timestamps(timestamps)
    if len(parsed) < 5:
        return TemporalSignature()

    intervals = [
        (parsed[i + 1] - parsed[i]).total_seconds()
        for i in range(len(parsed) - 1)
    ]

    mean = statistics.mean(intervals)
    if mean == 0:
        return TemporalSignature(cv_score=0.0, mean_interval_seconds=0.0, classification="autonomous")

    std = statistics.stdev(intervals)
    cv = std / mean

    # Normalize CV to 0-1 score: lower CV = higher autonomy score
    # CV 0 → score 1.0, CV >= 2 → score 0.0
    cv_score = max(0.0, min(1.0, 1.0 - (cv / 2.0)))

    if cv < 0.3:
        classification = "autonomous"
    elif cv > 1.0:
        classification = "human_influenced"
    else:
        classification = "indeterminate"

    return TemporalSignature(
        cv_score=cv_score,
        mean_interval_seconds=mean,
        classification=classification,
    )


def analyze_burst_rate(timestamps: list[str]) -> BurstAnalysis:
    """Compute percentage of consecutive posts within 10-second windows.

    > 50% → burst_bot (bot farm behavior)
    > 20% → automated
    Otherwise → organic

    Requires >= 3 timestamps.
    """
    parsed = _parse_timestamps(timestamps)
    if len(parsed) < 3:
        return BurstAnalysis(burst_rate=0.0, classification="organic")

    burst_count = sum(
        1
        for i in range(len(parsed) - 1)
        if (parsed[i + 1] - parsed[i]).total_seconds() <= 10
    )
    total_pairs = len(parsed) - 1
    rate = burst_count / total_pairs

    if rate > 0.5:
        classification = "burst_bot"
    elif rate > 0.2:
        classification = "automated"
    else:
        classification = "organic"

    return BurstAnalysis(burst_rate=rate, classification=classification)


def analyze_activity_pattern(timestamps: list[str]) -> ActivityPattern:
    """Bin posts into 24 hours, detect sleep gaps.

    >= 6 consecutive zero-activity hours → human_schedule
    All 24 hours active → always_on
    Otherwise → mixed
    """
    parsed = _parse_timestamps(timestamps)
    if not parsed:
        return ActivityPattern(classification="mixed", active_hours=0, has_sleep_gap=False)

    hour_counts = Counter(dt.hour for dt in parsed)
    active_hours = sum(1 for h in range(24) if hour_counts.get(h, 0) > 0)

    # Check for sleep gap: >= 6 consecutive zero-activity hours
    has_sleep_gap = False
    # Use circular check (wrap around midnight)
    for start in range(24):
        gap = 0
        for offset in range(24):
            hour = (start + offset) % 24
            if hour_counts.get(hour, 0) == 0:
                gap += 1
                if gap >= 6:
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

    Autonomous/organic/always_on/not_claimed → 1.0 (more autonomous)
    Human-influenced/human_schedule/claimed+verified → 0.0 (more human)
    Indeterminate/mixed → 0.5
    """
    high = {"autonomous", "organic", "always_on"}
    low = {"human_influenced", "human_schedule"}
    mid = {"indeterminate", "mixed", "automated"}

    if classification in high:
        return 1.0
    if classification in low:
        return 0.0
    if classification in mid:
        return 0.5
    # burst_bot maps to automated score
    if classification == "burst_bot":
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
) -> AuthenticityResult:
    """Combine sub-scores into final authenticity assessment.

    Weights: temporal=0.35, burst=0.25, activity=0.25, identity=0.15
    Score > 0.7 → likely_autonomous
    Score < 0.3 → likely_human
    burst_bot classification overrides to bot_farm
    """
    confidence = _confidence_from_count(num_timestamps)

    # Insufficient data → default to indeterminate
    if num_timestamps < 5:
        return AuthenticityResult(
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
        temporal_score * 0.35
        + burst_score * 0.25
        + activity_score * 0.25
        + id_score * 0.15
    )

    # Clamp to [0.0, 1.0]
    authenticity_score = max(0.0, min(1.0, weighted))

    # Classification
    if burst.classification == "burst_bot":
        classification = "bot_farm"
    elif authenticity_score > 0.7:
        classification = "likely_autonomous"
    elif authenticity_score < 0.3:
        classification = "likely_human"
    else:
        classification = "indeterminate"

    return AuthenticityResult(
        temporal=temporal,
        burst=burst,
        activity=activity,
        identity=identity,
        authenticity_score=authenticity_score,
        classification=classification,
        confidence=confidence,
    )
