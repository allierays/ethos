"""Tests for API key authentication."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from ethos.shared.models import EvaluationResult, ReflectionResult


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_api_key(monkeypatch):
    """Ensure ETHOS_API_KEY is unset by default."""
    monkeypatch.delenv("ETHOS_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _mock_domain():
    """Mock domain functions so tests don't need Claude or Neo4j."""
    with (
        patch("api.main.evaluate", return_value=EvaluationResult()),
        patch("api.main.reflect", return_value=ReflectionResult()),
    ):
        yield


class TestDevMode:
    """When ETHOS_API_KEY is not set, all requests pass (dev mode)."""

    def test_evaluate_no_key_configured(self, client):
        resp = client.post("/evaluate", json={"text": "hello"})
        assert resp.status_code == 200

    def test_reflect_no_key_configured(self, client):
        resp = client.post("/reflect", json={"agent_id": "test"})
        assert resp.status_code == 200


class TestAuthEnabled:
    """When ETHOS_API_KEY is set, write endpoints require Bearer token."""

    @pytest.fixture(autouse=True)
    def _set_api_key(self, monkeypatch):
        monkeypatch.setenv("ETHOS_API_KEY", "test-secret-key")

    def test_evaluate_missing_header(self, client):
        resp = client.post("/evaluate", json={"text": "hello"})
        assert resp.status_code == 401
        assert "Invalid or missing API key" in resp.json()["detail"]

    def test_evaluate_wrong_key(self, client):
        resp = client.post(
            "/evaluate",
            json={"text": "hello"},
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert resp.status_code == 401

    def test_evaluate_correct_key(self, client):
        resp = client.post(
            "/evaluate",
            json={"text": "hello"},
            headers={"Authorization": "Bearer test-secret-key"},
        )
        assert resp.status_code == 200

    def test_reflect_missing_header(self, client):
        resp = client.post("/reflect", json={"agent_id": "test"})
        assert resp.status_code == 401

    def test_reflect_correct_key(self, client):
        resp = client.post(
            "/reflect",
            json={"agent_id": "test"},
            headers={"Authorization": "Bearer test-secret-key"},
        )
        assert resp.status_code == 200


class TestGetEndpointsPublic:
    """GET endpoints remain public regardless of auth config."""

    @pytest.fixture(autouse=True)
    def _set_api_key(self, monkeypatch):
        monkeypatch.setenv("ETHOS_API_KEY", "test-secret-key")

    def test_root(self, client):
        assert client.get("/").status_code == 200

    def test_health(self, client):
        assert client.get("/health").status_code == 200

    def test_agents(self, client):
        resp = client.get("/agents")
        assert resp.status_code != 401
