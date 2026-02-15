"""Tests for authenticity API endpoint and domain layer."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from api.main import app
from ethos_academy.shared.models import AuthenticityResult

client = TestClient(app)


class TestAuthenticityEndpoint:
    """GET /agent/{agent_name}/authenticity (singular to match other detail endpoints)"""

    def test_known_agent_returns_valid_result(self):
        mock_result = AuthenticityResult(
            agent_name="a-dao",
            temporal={
                "cv_score": 0.65,
                "mean_interval_seconds": 3600.0,
                "classification": "indeterminate",
            },
            burst={"burst_rate": 0.1, "classification": "organic"},
            activity={
                "classification": "always_on",
                "active_hours": 24,
                "has_sleep_gap": False,
            },
            identity={
                "is_claimed": True,
                "owner_verified": False,
                "karma_post_ratio": 5.0,
            },
            authenticity_score=0.72,
            classification="likely_autonomous",
            confidence=0.9,
        )

        with patch(
            "api.main.analyze_authenticity",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.get("/agent/a-dao/authenticity")

        assert resp.status_code == 200
        data = resp.json()

        # Validate against Pydantic model
        result = AuthenticityResult(**data)
        assert result.agent_name == "a-dao"
        assert 0.0 <= result.authenticity_score <= 1.0
        assert result.classification == "likely_autonomous"
        assert 0.0 <= result.confidence <= 1.0

        # Check sub-results present
        assert "temporal" in data
        assert "cv_score" in data["temporal"]
        assert "burst" in data
        assert "burst_rate" in data["burst"]
        assert "activity" in data
        assert "identity" in data

    def test_unknown_agent_returns_indeterminate(self):
        mock_result = AuthenticityResult(agent_name="NONEXISTENT_AGENT_XYZ")

        with patch(
            "api.main.analyze_authenticity",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.get("/agent/NONEXISTENT_AGENT_XYZ/authenticity")

        assert resp.status_code == 200
        data = resp.json()

        result = AuthenticityResult(**data)
        assert result.classification == "indeterminate"
        assert result.agent_name == "NONEXISTENT_AGENT_XYZ"

    def test_response_matches_pydantic_schema(self):
        mock_result = AuthenticityResult(
            agent_name="test-bot",
            temporal={
                "cv_score": 0.0,
                "mean_interval_seconds": 500.0,
                "classification": "human_influenced",
            },
            burst={"burst_rate": 0.55, "classification": "burst_bot"},
            activity={
                "classification": "human_schedule",
                "active_hours": 12,
                "has_sleep_gap": True,
            },
            identity={
                "is_claimed": False,
                "owner_verified": False,
                "karma_post_ratio": 0.5,
            },
            authenticity_score=0.25,
            classification="high_frequency",
            confidence=0.7,
        )

        with patch(
            "api.main.analyze_authenticity",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.get("/agent/test-bot/authenticity")

        assert resp.status_code == 200
        data = resp.json()

        # Full round-trip through Pydantic — validates all fields and types
        result = AuthenticityResult(**data)
        assert result.classification == "high_frequency"
        assert result.burst.classification == "burst_bot"
        assert result.activity.has_sleep_gap is True


class TestAuthenticityDomainLayer:
    """Test analyze_authenticity() directly."""

    async def test_loads_from_cache(self):
        from ethos_academy.authenticity import analyze_authenticity

        with (
            patch(
                "ethos_academy.authenticity._load_results_cache",
                return_value={
                    "cached-agent": {
                        "agent_name": "cached-agent",
                        "temporal": {
                            "cv_score": 0.8,
                            "mean_interval_seconds": 1000.0,
                            "classification": "autonomous",
                        },
                        "burst": {"burst_rate": 0.05, "classification": "organic"},
                        "activity": {
                            "classification": "always_on",
                            "active_hours": 24,
                            "has_sleep_gap": False,
                        },
                        "identity": {
                            "is_claimed": False,
                            "owner_verified": False,
                            "karma_post_ratio": 10.0,
                        },
                        "authenticity_score": 0.85,
                        "classification": "likely_autonomous",
                        "confidence": 0.9,
                    }
                },
            ),
            patch("ethos_academy.authenticity._try_store_authenticity"),
        ):
            result = await analyze_authenticity("cached-agent")

        assert isinstance(result, AuthenticityResult)
        assert result.agent_name == "cached-agent"
        assert result.authenticity_score == 0.85

    async def test_defaults_for_unknown(self):
        from ethos_academy.authenticity import analyze_authenticity

        with (
            patch("ethos_academy.authenticity._load_results_cache", return_value={}),
            patch(
                "ethos_academy.authenticity._compute_from_profile", return_value=None
            ),
        ):
            result = await analyze_authenticity("totally-unknown")

        assert isinstance(result, AuthenticityResult)
        assert result.agent_name == "totally-unknown"
        assert result.classification == "indeterminate"
        assert result.authenticity_score == 0.5
