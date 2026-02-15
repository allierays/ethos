"""Integration tests for API endpoints — agents, history, alumni."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _mock_graph_context(connected=True):
    """Create a mock async graph_context context manager."""
    mock_service = MagicMock()
    mock_service.connected = connected

    @asynccontextmanager
    async def mock_ctx():
        yield mock_service

    return mock_ctx, mock_service


# ── GET /agents ──────────────────────────────────────────────────────


class TestAgentsEndpoint:
    def test_returns_list(self):
        from ethos_academy.shared.models import AgentSummary

        mock_agents = [
            AgentSummary(
                agent_id="a1",
                evaluation_count=3,
                latest_alignment_status="aligned",
            )
        ]

        with patch(
            "api.main.list_agents", new_callable=AsyncMock, return_value=mock_agents
        ):
            resp = client.get("/agents")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["agent_id"] == "a1"
        assert data[0]["evaluation_count"] == 3

    def test_returns_empty_on_failure(self):
        with patch("api.main.list_agents", new_callable=AsyncMock, return_value=[]):
            resp = client.get("/agents")

        assert resp.status_code == 200
        assert resp.json() == []


# ── GET /agent/{agent_id} ────────────────────────────────────────────


class TestAgentEndpoint:
    def test_returns_profile(self):
        from ethos_academy.shared.models import AgentProfile

        mock_profile = AgentProfile(
            agent_id="hashed",
            agent_model="",
            created_at="2024-01-01",
            evaluation_count=5,
            dimension_averages={"ethos": 0.7, "logos": 0.8, "pathos": 0.6},
            trait_averages={"virtue": 0.8},
            alignment_history=["aligned"],
        )

        with patch(
            "api.main.get_agent", new_callable=AsyncMock, return_value=mock_profile
        ):
            resp = client.get("/agent/test-agent")

        assert resp.status_code == 200
        data = resp.json()
        assert "agent_id" in data
        assert "dimension_averages" in data

    def test_returns_default_for_unknown(self):
        from ethos_academy.shared.models import AgentProfile

        mock_profile = AgentProfile(agent_id="unknown", evaluation_count=0)

        with patch(
            "api.main.get_agent", new_callable=AsyncMock, return_value=mock_profile
        ):
            resp = client.get("/agent/unknown")

        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "unknown"
        assert data["evaluation_count"] == 0


# ── GET /agent/{agent_id}/history ────────────────────────────────────


class TestAgentHistoryEndpoint:
    def test_returns_history(self):
        from ethos_academy.shared.models import EvaluationHistoryItem

        mock_history = [
            EvaluationHistoryItem(
                evaluation_id="e1",
                ethos=0.7,
                logos=0.8,
                pathos=0.6,
                phronesis="developing",
                alignment_status="aligned",
                flags=[],
                created_at="2024-01-01",
            )
        ]

        with patch(
            "api.main.get_agent_history",
            new_callable=AsyncMock,
            return_value=mock_history,
        ):
            resp = client.get("/agent/test/history")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_returns_empty_on_failure(self):
        with patch(
            "api.main.get_agent_history",
            new_callable=AsyncMock,
            return_value=[],
        ):
            resp = client.get("/agent/test/history")

        assert resp.status_code == 200
        assert resp.json() == []


# ── GET /alumni ──────────────────────────────────────────────────────


class TestAlumniEndpoint:
    def test_returns_alumni(self):
        from ethos_academy.shared.models import AlumniResult

        mock_alumni = AlumniResult(
            trait_averages={"virtue": 0.7},
            total_evaluations=50,
        )

        with patch(
            "api.main.get_alumni", new_callable=AsyncMock, return_value=mock_alumni
        ):
            resp = client.get("/alumni")

        assert resp.status_code == 200
        data = resp.json()
        assert "trait_averages" in data
        assert "total_evaluations" in data
        assert data["total_evaluations"] == 50

    def test_returns_default_on_failure(self):
        from ethos_academy.shared.models import AlumniResult

        mock_alumni = AlumniResult(trait_averages={}, total_evaluations=0)

        with patch(
            "api.main.get_alumni", new_callable=AsyncMock, return_value=mock_alumni
        ):
            resp = client.get("/alumni")

        assert resp.status_code == 200
        data = resp.json()
        assert data["trait_averages"] == {}
        assert data["total_evaluations"] == 0


# ── CORS ─────────────────────────────────────────────────────────────


class TestCORS:
    def test_cors_headers_for_localhost_3000(self):
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert (
            resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
        )


# ── Exception Handlers ──────────────────────────────────────────────


_EVAL_PAYLOAD = {"text": "test message", "source": "test-agent"}


class TestExceptionHandlers:
    def setup_method(self):
        from api.rate_limit import _requests

        _requests.clear()

    def test_graph_unavailable_returns_503(self):
        from ethos_academy.shared.errors import GraphUnavailableError

        with patch(
            "api.main.evaluate_incoming",
            new_callable=AsyncMock,
            side_effect=GraphUnavailableError("Neo4j is down"),
        ):
            resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)

        assert resp.status_code == 503
        data = resp.json()
        assert data["error"] == "GraphUnavailableError"
        assert data["message"] == "Neo4j is down"
        assert data["status"] == 503

    def test_evaluation_error_returns_422(self):
        from ethos_academy.shared.errors import EvaluationError

        with patch(
            "api.main.evaluate_incoming",
            new_callable=AsyncMock,
            side_effect=EvaluationError("pipeline failed"),
        ):
            resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)

        assert resp.status_code == 422
        data = resp.json()
        assert data["error"] == "EvaluationError"

    def test_parse_error_returns_422(self):
        from ethos_academy.shared.errors import ParseError

        with patch(
            "api.main.evaluate_incoming",
            new_callable=AsyncMock,
            side_effect=ParseError("bad response"),
        ):
            resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)

        assert resp.status_code == 422
        data = resp.json()
        assert data["error"] == "ParseError"

    def test_config_error_returns_500(self):
        from ethos_academy.shared.errors import ConfigError

        with patch(
            "api.main.evaluate_incoming",
            new_callable=AsyncMock,
            side_effect=ConfigError("missing key"),
        ):
            resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)

        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] == "ConfigError"

    def test_base_ethos_error_returns_500(self):
        from ethos_academy.shared.errors import EthosError

        with patch(
            "api.main.evaluate_incoming",
            new_callable=AsyncMock,
            side_effect=EthosError("unknown ethos error"),
        ):
            resp = client.post("/evaluate/incoming", json=_EVAL_PAYLOAD)

        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] == "EthosError"


# ── Input Validation ────────────────────────────────────────────────


class TestInputValidation:
    def setup_method(self):
        from api.rate_limit import _requests

        _requests.clear()

    def test_empty_text_rejected(self):
        resp = client.post("/evaluate/incoming", json={"text": "", "source": "a"})
        assert resp.status_code == 422

    def test_missing_text_rejected(self):
        resp = client.post("/evaluate/incoming", json={"source": "a"})
        assert resp.status_code == 422

    def test_missing_source_rejected(self):
        resp = client.post("/evaluate/incoming", json={"text": "hello"})
        assert resp.status_code == 422

    def test_text_too_long_rejected(self):
        resp = client.post(
            "/evaluate/incoming", json={"text": "x" * 50001, "source": "a"}
        )
        assert resp.status_code == 422
