"""Tests for per-agent API key authentication (TASK-053 through TASK-058).

Covers: hash-only storage, no plaintext leaks, constant-time comparison,
first-exam flow, retake rejection, cross-agent rejection, retake success.
"""

import hashlib
import inspect
from unittest.mock import AsyncMock, patch

import pytest

from ethos_academy.context import agent_api_key_var
from ethos_academy.graph.enrollment import (
    agent_has_key,
    store_agent_key,
    verify_agent_key,
)
from ethos_academy.shared.models import ExamReportCard


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_context_var():
    """Reset agent_api_key_var between tests."""
    token = agent_api_key_var.set(None)
    yield
    agent_api_key_var.reset(token)


def _mock_service(connected=True):
    """Create a mock GraphService."""
    service = AsyncMock()
    service.connected = connected
    return service


# ── TASK-053: Foundational Primitives ─────────────────────────────────


class TestContextVar:
    def test_defaults_to_none(self):
        assert agent_api_key_var.get() is None

    def test_set_and_reset(self):
        token = agent_api_key_var.set("ea_test123")
        assert agent_api_key_var.get() == "ea_test123"
        agent_api_key_var.reset(token)
        assert agent_api_key_var.get() is None


class TestExamReportCardApiKey:
    def test_api_key_not_in_repr(self):
        card = ExamReportCard(
            exam_id="test",
            agent_id="test-agent",
            report_card_url="/test",
            phronesis_score=0.5,
            alignment_status="aligned",
            dimensions={},
            tier_scores={},
            consistency_analysis=[],
            per_question_detail=[],
            api_key="ea_supersecret123",
        )
        assert "ea_supersecret123" not in repr(card)

    def test_api_key_defaults_to_none(self):
        card = ExamReportCard(
            exam_id="test",
            agent_id="test-agent",
            report_card_url="/test",
            phronesis_score=0.5,
            alignment_status="aligned",
            dimensions={},
            tier_scores={},
            consistency_analysis=[],
            per_question_detail=[],
        )
        assert card.api_key is None

    def test_api_key_accessible_via_attribute(self):
        card = ExamReportCard(
            exam_id="test",
            agent_id="test-agent",
            report_card_url="/test",
            phronesis_score=0.5,
            alignment_status="aligned",
            dimensions={},
            tier_scores={},
            consistency_analysis=[],
            per_question_detail=[],
            api_key="ea_test",
        )
        assert card.api_key == "ea_test"


class TestGraphKeyFunctions:
    async def test_agent_has_key_false_when_disconnected(self):
        service = _mock_service(connected=False)
        assert await agent_has_key(service, "test-agent") is False

    async def test_agent_has_key_false_when_no_records(self):
        service = _mock_service()
        service.execute_query = AsyncMock(return_value=([], None, None))
        assert await agent_has_key(service, "test-agent") is False

    async def test_agent_has_key_true_when_record_exists(self):
        service = _mock_service()
        service.execute_query = AsyncMock(
            return_value=([{"has_key": True}], None, None)
        )
        assert await agent_has_key(service, "test-agent") is True

    async def test_verify_agent_key_constant_time(self):
        """verify_agent_key uses hmac.compare_digest, not == operator."""
        source = inspect.getsource(verify_agent_key)
        assert "hmac.compare_digest" in source

    async def test_verify_agent_key_correct_key(self):
        key = "ea_test123"
        stored_hash = hashlib.sha256(key.encode()).hexdigest()
        service = _mock_service()
        service.execute_query = AsyncMock(
            return_value=([{"key_hash": stored_hash}], None, None)
        )
        assert await verify_agent_key(service, "test-agent", key) is True

    async def test_verify_agent_key_wrong_key(self):
        stored_hash = hashlib.sha256(b"ea_correct").hexdigest()
        service = _mock_service()
        service.execute_query = AsyncMock(
            return_value=([{"key_hash": stored_hash}], None, None)
        )
        assert await verify_agent_key(service, "test-agent", "ea_wrong") is False

    async def test_verify_agent_key_no_hash_stored(self):
        service = _mock_service()
        service.execute_query = AsyncMock(
            return_value=([{"key_hash": None}], None, None)
        )
        assert await verify_agent_key(service, "test-agent", "ea_test") is False

    async def test_verify_agent_key_disconnected(self):
        service = _mock_service(connected=False)
        assert await verify_agent_key(service, "test-agent", "ea_test") is False

    async def test_store_agent_key_stores_hash(self):
        service = _mock_service()
        service.execute_query = AsyncMock(
            return_value=([{"agent_id": "test"}], None, None)
        )
        key_hash = hashlib.sha256(b"ea_test").hexdigest()
        result = await store_agent_key(service, "test-agent", key_hash)
        assert result is True
        # Verify the hash was passed to the query
        call_args = service.execute_query.call_args
        assert call_args[0][1]["key_hash"] == key_hash


# ── TASK-054: Key Generation ──────────────────────────────────────────


class TestKeyGeneration:
    def test_generate_agent_key_format(self):
        from ethos_academy.enrollment.service import _generate_agent_key

        key, key_hash = _generate_agent_key()
        assert key.startswith("ea_")
        assert len(key) > 10
        assert key_hash == hashlib.sha256(key.encode()).hexdigest()

    def test_generate_agent_key_unique(self):
        from ethos_academy.enrollment.service import _generate_agent_key

        keys = {_generate_agent_key()[0] for _ in range(10)}
        assert len(keys) == 10  # all unique


# ── TASK-055: Auth Enforcement ────────────────────────────────────────


class TestAuthEnforcement:
    async def test_check_agent_auth_passes_when_no_key(self):
        """First exam (no key on agent) passes without auth."""
        from ethos_academy.enrollment.service import _check_agent_auth

        service = _mock_service()
        service.execute_query = AsyncMock(return_value=([], None, None))
        # Should not raise
        await _check_agent_auth(service, "new-agent")

    async def test_check_agent_auth_rejects_missing_key(self):
        """Agent has key but caller provides none."""
        from ethos_academy.enrollment.service import _check_agent_auth
        from ethos_academy.shared.errors import EnrollmentError

        service = _mock_service()
        # agent_has_key returns True
        service.execute_query = AsyncMock(
            return_value=([{"has_key": True}], None, None)
        )
        agent_api_key_var.set(None)
        with pytest.raises(EnrollmentError, match="API key required"):
            await _check_agent_auth(service, "secured-agent")

    async def test_check_agent_auth_rejects_wrong_key(self):
        """Agent has key but caller provides wrong one."""
        from ethos_academy.enrollment.service import _check_agent_auth
        from ethos_academy.shared.errors import EnrollmentError

        stored_hash = hashlib.sha256(b"ea_correct").hexdigest()
        service = _mock_service()

        # First call: agent_has_key -> True
        # Second call: verify_agent_key -> fetch hash
        call_count = 0

        async def mock_execute(query, params):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ([{"has_key": True}], None, None)
            return ([{"key_hash": stored_hash}], None, None)

        service.execute_query = mock_execute
        agent_api_key_var.set("ea_wrong")
        with pytest.raises(EnrollmentError, match="API key required"):
            await _check_agent_auth(service, "secured-agent")

    async def test_check_agent_auth_accepts_correct_key(self):
        """Agent has key, caller provides correct one."""
        from ethos_academy.enrollment.service import _check_agent_auth

        correct_key = "ea_correct123"
        stored_hash = hashlib.sha256(correct_key.encode()).hexdigest()
        service = _mock_service()

        call_count = 0

        async def mock_execute(query, params):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ([{"has_key": True}], None, None)
            return ([{"key_hash": stored_hash}], None, None)

        service.execute_query = mock_execute
        agent_api_key_var.set(correct_key)
        # Should not raise
        await _check_agent_auth(service, "secured-agent")


# ── TASK-056: API Dependency ──────────────────────────────────────────


class TestInjectAgentKey:
    def test_sets_contextvar_for_ea_token(self):
        from api.auth import inject_agent_key
        from unittest.mock import MagicMock

        request = MagicMock()
        request.headers = {"Authorization": "Bearer ea_test123"}
        gen = inject_agent_key(request)
        next(gen)  # advance to yield
        assert agent_api_key_var.get() == "ea_test123"
        # Cleanup: finish the generator to trigger reset
        try:
            next(gen)
        except StopIteration:
            pass
        assert agent_api_key_var.get() is None

    def test_ignores_non_ea_token(self):
        from api.auth import inject_agent_key
        from unittest.mock import MagicMock

        request = MagicMock()
        request.headers = {"Authorization": "Bearer sk-ant-test"}
        gen = inject_agent_key(request)
        try:
            next(gen)
        except StopIteration:
            pass
        assert agent_api_key_var.get() is None

    def test_ignores_missing_header(self):
        from api.auth import inject_agent_key
        from unittest.mock import MagicMock

        request = MagicMock()
        request.headers = {}
        gen = inject_agent_key(request)
        try:
            next(gen)
        except StopIteration:
            pass
        assert agent_api_key_var.get() is None

    def test_resets_contextvar_after_request(self):
        """ContextVar is cleaned up even if request processing succeeds."""
        from api.auth import inject_agent_key
        from unittest.mock import MagicMock

        request = MagicMock()
        request.headers = {"Authorization": "Bearer ea_cleanup_test"}
        gen = inject_agent_key(request)
        next(gen)
        assert agent_api_key_var.get() == "ea_cleanup_test"
        # Simulate request completion
        try:
            next(gen)
        except StopIteration:
            pass
        assert agent_api_key_var.get() is None


# ── TASK-055: Exception Handler 401 ──────────────────────────────────


class TestEnrollmentError401:
    def test_api_key_error_returns_401(self):
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)

        with patch(
            "api.main.register_for_exam",
            side_effect=__import__(
                "ethos_academy.shared.errors", fromlist=["EnrollmentError"]
            ).EnrollmentError("API key required for this agent"),
        ):
            resp = client.post(
                "/agent/test-agent/exam",
                json={"agent_name": "test"},
            )
            assert resp.status_code == 401

    def test_not_found_still_returns_404(self):
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)

        with patch(
            "api.main.register_for_exam",
            side_effect=__import__(
                "ethos_academy.shared.errors", fromlist=["EnrollmentError"]
            ).EnrollmentError("Exam xyz not found for agent test"),
        ):
            resp = client.post(
                "/agent/test-agent/exam",
                json={"agent_name": "test"},
            )
            assert resp.status_code == 404


# ── Regression: Existing tests should still pass ──────────────────────


class TestNoReprLeak:
    def test_api_key_excluded_from_dump_and_repr(self):
        """api_key is excluded from model_dump (never serialized) and repr."""
        card = ExamReportCard(
            exam_id="test",
            agent_id="test-agent",
            report_card_url="/test",
            phronesis_score=0.5,
            alignment_status="aligned",
            dimensions={},
            tier_scores={},
            consistency_analysis=[],
            per_question_detail=[],
            api_key="ea_secret_key",
        )
        dumped = card.model_dump()
        assert "api_key" not in dumped
        assert "ea_secret_key" not in repr(card)
        assert card.api_key == "ea_secret_key"

    def test_get_report_never_sets_key(self):
        """_build_report_card never sets api_key, so GET always returns null."""
        from ethos_academy.enrollment.service import _build_report_card

        # Minimal results dict to exercise _build_report_card
        results = {
            "agent_id": "test",
            "question_version": "v3",
            "responses": [],
            "telos": "",
            "relationship_stance": "",
            "limitations_awareness": "",
            "oversight_stance": "",
            "refusal_philosophy": "",
            "conflict_response": "",
            "help_philosophy": "",
            "failure_narrative": "",
            "aspiration": "",
        }
        report = _build_report_card("exam-123", results)
        assert report.api_key is None
