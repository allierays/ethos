"""Pattern detection domain — deterministic sabotage pathway detection.

Layer 3: NO LLM calls. Pure graph queries on score sequences.
Detects 8 sabotage pathways (SP-01 through SP-08) by matching
detected indicators against pattern compositions in the graph.

DDD layering: API calls detect_patterns(), which calls graph/patterns.py.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ethos_academy.graph.patterns import (
    get_agent_detected_indicators,
    get_agent_evaluation_count,
    get_pattern_indicator_map,
    store_exhibits_pattern,
)
from ethos_academy.graph.service import graph_context
from ethos_academy.shared.models import DetectedPattern, PatternResult

logger = logging.getLogger(__name__)

_MIN_EVALUATIONS = 5


async def detect_patterns(agent_id: str) -> PatternResult:
    """Detect sabotage pathways for an agent based on graph data.

    Returns PatternResult with detected patterns. Returns empty result
    if Neo4j is down or agent has fewer than 5 evaluations.
    """
    checked_at = datetime.now(timezone.utc).isoformat()

    try:
        async with graph_context() as service:
            if not service.connected:
                return PatternResult(agent_id=agent_id, checked_at=checked_at)

            # Check minimum evaluation threshold
            eval_count = await get_agent_evaluation_count(service, agent_id)
            if eval_count < _MIN_EVALUATIONS:
                return PatternResult(agent_id=agent_id, checked_at=checked_at)

            # Get pattern definitions from graph (Pattern -> COMPOSED_OF -> Indicator)
            pattern_map = await get_pattern_indicator_map(service)
            if not pattern_map:
                return PatternResult(agent_id=agent_id, checked_at=checked_at)

            # Get all indicators detected for this agent
            agent_indicators = await get_agent_detected_indicators(service, agent_id)

            # Match patterns against agent's detected indicators
            detected: list[DetectedPattern] = []

            for pattern in pattern_map:
                pattern_indicator_ids = pattern["indicator_ids"]
                if not pattern_indicator_ids:
                    continue

                # Find which of this pattern's indicators the agent has triggered
                matched = []
                total_occurrences = 0
                earliest_seen = ""
                latest_seen = ""

                for ind_id in pattern_indicator_ids:
                    if ind_id in agent_indicators:
                        matched.append(ind_id)
                        info = agent_indicators[ind_id]
                        total_occurrences += info["occurrence_count"]

                        if not earliest_seen or info["first_seen"] < earliest_seen:
                            earliest_seen = info["first_seen"]
                        if not latest_seen or info["last_seen"] > latest_seen:
                            latest_seen = info["last_seen"]

                if not matched:
                    continue

                # Confidence = proportion of pathway indicators matched
                confidence = round(len(matched) / len(pattern_indicator_ids), 4)

                # Stage = number of distinct indicators matched (progression)
                current_stage = len(matched)

                detected_pattern = DetectedPattern(
                    pattern_id=pattern["pattern_id"],
                    name=pattern["name"],
                    description=pattern["description"],
                    matched_indicators=matched,
                    confidence=confidence,
                    first_seen=earliest_seen,
                    last_seen=latest_seen,
                    occurrence_count=total_occurrences,
                    current_stage=current_stage,
                )
                detected.append(detected_pattern)

                # Store EXHIBITS_PATTERN in graph (MERGE to update existing)
                await store_exhibits_pattern(
                    service,
                    agent_id,
                    pattern_id=pattern["pattern_id"],
                    first_seen=earliest_seen,
                    last_seen=latest_seen,
                    occurrence_count=total_occurrences,
                    current_stage=current_stage,
                    confidence=confidence,
                )

            return PatternResult(
                agent_id=agent_id,
                patterns=detected,
                checked_at=checked_at,
            )

    except Exception as exc:
        logger.warning("Failed to detect patterns (%s): %s", type(exc).__name__, exc)
        return PatternResult(agent_id=agent_id, checked_at=checked_at)
