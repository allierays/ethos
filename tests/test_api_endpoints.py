"""Integration tests for API endpoints — agents, history, alumni."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ── GET /agents ──────────────────────────────────────────────────────


class TestAgentsEndpoint:
    @patch("ethos.agents.get_all_agents")
    @patch("ethos.graph.service.GraphService")
    def test_returns_list(self, mock_gs_cls, mock_get_all):
        from unittest.mock import MagicMock

        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service
        mock_get_all.return_value = [
            {
                "agent_id": "a1",
                "evaluation_count": 3,
                "latest_alignment_status": "aligned",
            }
        ]

        resp = client.get("/agents")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["agent_id"] == "a1"
        assert data[0]["evaluation_count"] == 3

    @patch("ethos.graph.service.GraphService")
    def test_returns_empty_on_failure(self, mock_gs_cls):
        mock_gs_cls.side_effect = RuntimeError("down")

        resp = client.get("/agents")

        assert resp.status_code == 200
        assert resp.json() == []


# ── GET /agent/{agent_id} ────────────────────────────────────────────


class TestAgentEndpoint:
    @patch("ethos.agents.get_agent_profile")
    @patch("ethos.graph.service.GraphService")
    def test_returns_profile(self, mock_gs_cls, mock_profile):
        from unittest.mock import MagicMock

        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service
        mock_profile.return_value = {
            "agent_id": "hashed",
            "agent_model": "",
            "created_at": "2024-01-01",
            "evaluation_count": 5,
            "dimension_averages": {"ethos": 0.7, "logos": 0.8, "pathos": 0.6},
            "trait_averages": {"virtue": 0.8},
            "alignment_history": ["aligned"],
        }

        resp = client.get("/agent/test-agent")

        assert resp.status_code == 200
        data = resp.json()
        assert "agent_id" in data
        assert "dimension_averages" in data

    @patch("ethos.agents.get_agent_profile")
    @patch("ethos.graph.service.GraphService")
    def test_returns_default_for_unknown(self, mock_gs_cls, mock_profile):
        from unittest.mock import MagicMock

        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service
        mock_profile.return_value = {}

        resp = client.get("/agent/unknown")

        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "unknown"
        assert data["evaluation_count"] == 0


# ── GET /agent/{agent_id}/history ────────────────────────────────────


class TestAgentHistoryEndpoint:
    @patch("ethos.agents.get_evaluation_history")
    @patch("ethos.graph.service.GraphService")
    def test_returns_history(self, mock_gs_cls, mock_history):
        from unittest.mock import MagicMock

        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service
        mock_history.return_value = [
            {
                "evaluation_id": "e1",
                "ethos": 0.7,
                "logos": 0.8,
                "pathos": 0.6,
                "phronesis": "developing",
                "alignment_status": "aligned",
                "flags": [],
                "created_at": "2024-01-01",
            }
        ]

        resp = client.get("/agent/test/history")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @patch("ethos.graph.service.GraphService")
    def test_returns_empty_on_failure(self, mock_gs_cls):
        mock_gs_cls.side_effect = RuntimeError("down")

        resp = client.get("/agent/test/history")

        assert resp.status_code == 200
        assert resp.json() == []


# ── GET /alumni ──────────────────────────────────────────────────────


class TestAlumniEndpoint:
    @patch("ethos.agents.get_alumni_averages")
    @patch("ethos.graph.service.GraphService")
    def test_returns_alumni(self, mock_gs_cls, mock_alumni):
        from unittest.mock import MagicMock

        mock_service = MagicMock()
        mock_gs_cls.return_value = mock_service
        mock_alumni.return_value = {
            "trait_averages": {"virtue": 0.7},
            "total_evaluations": 50,
        }

        resp = client.get("/alumni")

        assert resp.status_code == 200
        data = resp.json()
        assert "trait_averages" in data
        assert "total_evaluations" in data
        assert data["total_evaluations"] == 50

    @patch("ethos.graph.service.GraphService")
    def test_returns_default_on_failure(self, mock_gs_cls):
        mock_gs_cls.side_effect = RuntimeError("down")

        resp = client.get("/alumni")

        assert resp.status_code == 200
        data = resp.json()
        assert data["trait_averages"] == {}
        assert data["total_evaluations"] == 0


# ── POST /reflect (updated with text field) ──────────────────────────


class TestReflectEndpoint:
    @patch("ethos.graph.service.GraphService")
    def test_reflect_accepts_text(self, mock_gs_cls):
        from unittest.mock import MagicMock

        mock_service = MagicMock()
        mock_service.connected = False
        mock_gs_cls.return_value = mock_service

        resp = client.post(
            "/reflect",
            json={"agent_id": "test", "text": None},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "trend" in data
        assert "ethos" in data

    @patch("ethos.graph.service.GraphService")
    def test_reflect_without_text(self, mock_gs_cls):
        from unittest.mock import MagicMock

        mock_service = MagicMock()
        mock_service.connected = False
        mock_gs_cls.return_value = mock_service

        resp = client.post(
            "/reflect",
            json={"agent_id": "test"},
        )

        assert resp.status_code == 200


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
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


# ── Exception Handlers ──────────────────────────────────────────────


class TestExceptionHandlers:
    @patch("api.main.evaluate")
    def test_graph_unavailable_returns_503(self, mock_evaluate):
        from ethos.shared.errors import GraphUnavailableError

        mock_evaluate.side_effect = GraphUnavailableError("Neo4j is down")

        resp = client.post("/evaluate", json={"text": "test message"})

        assert resp.status_code == 503
        data = resp.json()
        assert data["error"] == "GraphUnavailableError"
        assert data["message"] == "Neo4j is down"
        assert data["status"] == 503

    @patch("api.main.evaluate")
    def test_evaluation_error_returns_422(self, mock_evaluate):
        from ethos.shared.errors import EvaluationError

        mock_evaluate.side_effect = EvaluationError("pipeline failed")

        resp = client.post("/evaluate", json={"text": "test message"})

        assert resp.status_code == 422
        data = resp.json()
        assert data["error"] == "EvaluationError"

    @patch("api.main.evaluate")
    def test_parse_error_returns_422(self, mock_evaluate):
        from ethos.shared.errors import ParseError

        mock_evaluate.side_effect = ParseError("bad response")

        resp = client.post("/evaluate", json={"text": "test message"})

        assert resp.status_code == 422
        data = resp.json()
        assert data["error"] == "ParseError"

    @patch("api.main.evaluate")
    def test_config_error_returns_500(self, mock_evaluate):
        from ethos.shared.errors import ConfigError

        mock_evaluate.side_effect = ConfigError("missing key")

        resp = client.post("/evaluate", json={"text": "test message"})

        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] == "ConfigError"

    @patch("api.main.evaluate")
    def test_base_ethos_error_returns_500(self, mock_evaluate):
        from ethos.shared.errors import EthosError

        mock_evaluate.side_effect = EthosError("unknown ethos error")

        resp = client.post("/evaluate", json={"text": "test message"})

        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] == "EthosError"


# ── Input Validation ────────────────────────────────────────────────


class TestInputValidation:
    def test_empty_text_rejected(self):
        resp = client.post("/evaluate", json={"text": ""})

        assert resp.status_code == 422

    def test_missing_text_rejected(self):
        resp = client.post("/evaluate", json={})

        assert resp.status_code == 422

    def test_text_too_long_rejected(self):
        resp = client.post("/evaluate", json={"text": "x" * 50001})

        assert resp.status_code == 422
