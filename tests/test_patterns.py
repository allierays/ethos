"""Tests for pattern detection — Layer 3 deterministic graph queries."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ethos_academy.patterns import detect_patterns
from ethos_academy.shared.models import DetectedPattern, PatternResult


def _mock_graph_context(connected=True):
    """Create a mock async context manager for graph_context()."""
    mock_service = AsyncMock()
    mock_service.connected = connected
    mock_ctx = AsyncMock()
    mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx, mock_service


class TestDetectPatterns:
    @patch("ethos_academy.patterns.store_exhibits_pattern", new_callable=AsyncMock)
    @patch(
        "ethos_academy.patterns.get_agent_detected_indicators", new_callable=AsyncMock
    )
    @patch("ethos_academy.patterns.get_pattern_indicator_map", new_callable=AsyncMock)
    @patch("ethos_academy.patterns.get_agent_evaluation_count", new_callable=AsyncMock)
    @patch("ethos_academy.patterns.graph_context")
    async def test_detects_matching_pattern(
        self, mock_ctx, mock_count, mock_map, mock_indicators, mock_store
    ):
        mock_service = AsyncMock()
        mock_service.connected = True
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_count.return_value = 10

        mock_map.return_value = [
            {
                "pattern_id": "SP-01",
                "name": "diffuse_sandbagging",
                "description": "Deliberately performing below capability",
                "indicator_ids": ["DEC-SANDBAG", "FAB-TOOLRESULT"],
            },
        ]

        mock_indicators.return_value = {
            "DEC-SANDBAG": {
                "occurrence_count": 3,
                "first_seen": "2024-01-01T00:00:00",
                "last_seen": "2024-01-03T00:00:00",
            },
            "FAB-TOOLRESULT": {
                "occurrence_count": 2,
                "first_seen": "2024-01-02T00:00:00",
                "last_seen": "2024-01-04T00:00:00",
            },
        }

        result = await detect_patterns("test-agent")

        assert isinstance(result, PatternResult)
        assert result.agent_id == "test-agent"
        assert len(result.patterns) == 1
        assert result.patterns[0].pattern_id == "SP-01"
        assert result.patterns[0].confidence == 1.0
        assert result.patterns[0].matched_indicators == [
            "DEC-SANDBAG",
            "FAB-TOOLRESULT",
        ]
        assert result.patterns[0].occurrence_count == 5
        assert result.patterns[0].current_stage == 2
        assert result.patterns[0].first_seen == "2024-01-01T00:00:00"
        assert result.patterns[0].last_seen == "2024-01-04T00:00:00"

        # Verify EXHIBITS_PATTERN was stored
        mock_store.assert_called_once()

    @patch(
        "ethos_academy.patterns.get_agent_detected_indicators", new_callable=AsyncMock
    )
    @patch("ethos_academy.patterns.get_pattern_indicator_map", new_callable=AsyncMock)
    @patch("ethos_academy.patterns.get_agent_evaluation_count", new_callable=AsyncMock)
    @patch("ethos_academy.patterns.graph_context")
    async def test_partial_match_gives_fractional_confidence(
        self, mock_ctx, mock_count, mock_map, mock_indicators
    ):
        mock_service = AsyncMock()
        mock_service.connected = True
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_count.return_value = 10

        mock_map.return_value = [
            {
                "pattern_id": "SP-02",
                "name": "targeted_sabotage",
                "description": "Inserting targeted bugs",
                "indicator_ids": [
                    "DEC-SANDBAG",
                    "FAB-TOOLRESULT",
                    "MAN-SABOTAGE",
                ],
            },
        ]

        # Only 1 of 3 indicators matched
        mock_indicators.return_value = {
            "DEC-SANDBAG": {
                "occurrence_count": 1,
                "first_seen": "2024-01-01T00:00:00",
                "last_seen": "2024-01-01T00:00:00",
            },
        }

        result = await detect_patterns("test-agent")

        assert len(result.patterns) == 1
        assert result.patterns[0].confidence == round(1 / 3, 4)
        assert result.patterns[0].current_stage == 1
        assert result.patterns[0].matched_indicators == ["DEC-SANDBAG"]

    @patch(
        "ethos_academy.patterns.get_agent_detected_indicators", new_callable=AsyncMock
    )
    @patch("ethos_academy.patterns.get_pattern_indicator_map", new_callable=AsyncMock)
    @patch("ethos_academy.patterns.get_agent_evaluation_count", new_callable=AsyncMock)
    @patch("ethos_academy.patterns.graph_context")
    async def test_no_match_returns_empty_patterns(
        self, mock_ctx, mock_count, mock_map, mock_indicators
    ):
        mock_service = AsyncMock()
        mock_service.connected = True
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_count.return_value = 10

        mock_map.return_value = [
            {
                "pattern_id": "SP-01",
                "name": "diffuse_sandbagging",
                "description": "Deliberately performing below capability",
                "indicator_ids": ["DEC-SANDBAG", "FAB-TOOLRESULT"],
            },
        ]

        mock_indicators.return_value = {}

        result = await detect_patterns("test-agent")

        assert isinstance(result, PatternResult)
        assert result.patterns == []

    @patch("ethos_academy.patterns.get_agent_evaluation_count", new_callable=AsyncMock)
    @patch("ethos_academy.patterns.graph_context")
    async def test_insufficient_evaluations_returns_empty(self, mock_ctx, mock_count):
        mock_service = AsyncMock()
        mock_service.connected = True
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_count.return_value = 3  # Below threshold of 5

        result = await detect_patterns("test-agent")

        assert isinstance(result, PatternResult)
        assert result.agent_id == "test-agent"
        assert result.patterns == []

    @patch("ethos_academy.patterns.graph_context")
    async def test_graph_down_returns_empty(self, mock_ctx):
        mock_service = AsyncMock()
        mock_service.connected = False
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await detect_patterns("test-agent")

        assert isinstance(result, PatternResult)
        assert result.agent_id == "test-agent"
        assert result.patterns == []

    @patch("ethos_academy.patterns.graph_context")
    async def test_graph_exception_returns_empty(self, mock_ctx):
        mock_ctx.return_value.__aenter__ = AsyncMock(
            side_effect=RuntimeError("Connection refused")
        )
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await detect_patterns("test-agent")

        assert isinstance(result, PatternResult)
        assert result.agent_id == "test-agent"
        assert result.patterns == []

    @patch("ethos_academy.patterns.store_exhibits_pattern", new_callable=AsyncMock)
    @patch(
        "ethos_academy.patterns.get_agent_detected_indicators", new_callable=AsyncMock
    )
    @patch("ethos_academy.patterns.get_pattern_indicator_map", new_callable=AsyncMock)
    @patch("ethos_academy.patterns.get_agent_evaluation_count", new_callable=AsyncMock)
    @patch("ethos_academy.patterns.graph_context")
    async def test_multiple_patterns_detected(
        self, mock_ctx, mock_count, mock_map, mock_indicators, mock_store
    ):
        mock_service = AsyncMock()
        mock_service.connected = True
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_count.return_value = 10

        mock_map.return_value = [
            {
                "pattern_id": "SP-01",
                "name": "diffuse_sandbagging",
                "description": "Sandbagging",
                "indicator_ids": ["DEC-SANDBAG"],
            },
            {
                "pattern_id": "SP-03",
                "name": "code_backdoors",
                "description": "Backdoors",
                "indicator_ids": ["DEC-HIDDEN", "DEC-OVERSIGHT"],
            },
        ]

        mock_indicators.return_value = {
            "DEC-SANDBAG": {
                "occurrence_count": 2,
                "first_seen": "2024-01-01T00:00:00",
                "last_seen": "2024-01-02T00:00:00",
            },
            "DEC-HIDDEN": {
                "occurrence_count": 1,
                "first_seen": "2024-01-03T00:00:00",
                "last_seen": "2024-01-03T00:00:00",
            },
        }

        result = await detect_patterns("test-agent")

        assert len(result.patterns) == 2
        assert result.patterns[0].pattern_id == "SP-01"
        assert result.patterns[0].confidence == 1.0
        assert result.patterns[1].pattern_id == "SP-03"
        assert result.patterns[1].confidence == 0.5
        assert mock_store.call_count == 2


class TestDetectedPatternModel:
    def test_valid_pattern(self):
        p = DetectedPattern(
            pattern_id="SP-01",
            name="diffuse_sandbagging",
            description="Test",
            matched_indicators=["DEC-SANDBAG"],
            confidence=0.5,
            first_seen="2024-01-01",
            last_seen="2024-01-02",
            occurrence_count=3,
            current_stage=1,
        )
        assert p.pattern_id == "SP-01"
        assert p.confidence == 0.5

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            DetectedPattern(
                pattern_id="SP-01",
                name="test",
                confidence=1.5,
            )


class TestPatternResultModel:
    def test_empty_result(self):
        r = PatternResult(agent_id="test")
        assert r.patterns == []
        assert r.checked_at == ""

    def test_with_patterns(self):
        p = DetectedPattern(
            pattern_id="SP-01",
            name="test",
            confidence=0.8,
        )
        r = PatternResult(agent_id="test", patterns=[p], checked_at="2024-01-01")
        assert len(r.patterns) == 1
        assert r.patterns[0].confidence == 0.8
