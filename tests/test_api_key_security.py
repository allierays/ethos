"""Tests for API key security: X25519 encryption, auth on regeneration, Cypher guards."""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock, patch

import pytest

from ethos_academy.context import agent_api_key_var, is_admin_var
from ethos_academy.shared.errors import EnrollmentError


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_context_vars():
    """Reset context vars between tests."""
    key_token = agent_api_key_var.set(None)
    admin_token = is_admin_var.set(False)
    yield
    agent_api_key_var.reset(key_token)
    is_admin_var.reset(admin_token)


def _mock_graph_service(connected=True):
    """Create a mock GraphService that acts as an async context manager."""
    service = AsyncMock()
    service.connected = connected
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=service)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


def _make_x25519_keypair() -> tuple:
    """Generate an X25519 keypair for testing.

    Returns (private_key, public_key_b64).
    """
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

    priv = X25519PrivateKey.generate()
    pub_b64 = base64.b64encode(priv.public_key().public_bytes_raw()).decode()
    return priv, pub_b64


def _decrypt_api_key(
    priv_key, server_pub_b64: str, nonce_b64: str, ciphertext_b64: str
) -> str:
    """Decrypt an API key using the client's private key."""
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    server_pub = X25519PublicKey.from_public_bytes(base64.b64decode(server_pub_b64))
    shared = priv_key.exchange(server_pub)
    aes_key = HKDF(
        algorithm=SHA256(), length=32, salt=None, info=b"ethos-api-key-v1"
    ).derive(shared)
    plaintext = AESGCM(aes_key).decrypt(
        base64.b64decode(nonce_b64),
        base64.b64decode(ciphertext_b64),
        None,
    )
    return plaintext.decode()


# ═══════════════════════════════════════════════════════════════════════
# Fix #1: X25519 Encryption
# ═══════════════════════════════════════════════════════════════════════


class TestX25519Encryption:
    """_encrypt_api_key uses asymmetric ECDH, not symmetric AES."""

    def test_roundtrip(self):
        from ethos_academy.mcp_server import _encrypt_api_key

        priv, pub_b64 = _make_x25519_keypair()
        result = _encrypt_api_key("ea_secret_key_123", pub_b64)

        assert "encrypted_api_key" in result
        assert "server_public_key" in result
        assert "nonce" in result
        assert result["algorithm"] == "X25519-HKDF-SHA256-AES-256-GCM"
        assert "ea_secret_key_123" not in str(result)

        decrypted = _decrypt_api_key(
            priv,
            result["server_public_key"],
            result["nonce"],
            result["encrypted_api_key"],
        )
        assert decrypted == "ea_secret_key_123"

    def test_different_client_cannot_decrypt(self):
        """A different private key cannot decrypt the ciphertext."""
        from ethos_academy.mcp_server import _encrypt_api_key

        priv_real, pub_b64 = _make_x25519_keypair()
        priv_attacker, _ = _make_x25519_keypair()

        result = _encrypt_api_key("ea_secret", pub_b64)

        with pytest.raises(Exception):
            _decrypt_api_key(
                priv_attacker,
                result["server_public_key"],
                result["nonce"],
                result["encrypted_api_key"],
            )

    def test_ephemeral_server_key_changes_each_call(self):
        """Server generates a fresh keypair per call (no key reuse)."""
        from ethos_academy.mcp_server import _encrypt_api_key

        _, pub_b64 = _make_x25519_keypair()
        r1 = _encrypt_api_key("ea_key1", pub_b64)
        r2 = _encrypt_api_key("ea_key2", pub_b64)
        assert r1["server_public_key"] != r2["server_public_key"]

    def test_rejects_invalid_base64(self):
        from ethos_academy.mcp_server import _encrypt_api_key

        with pytest.raises(EnrollmentError, match="Invalid base64"):
            _encrypt_api_key("ea_key", "!!!not-base64!!!")

    def test_rejects_wrong_length(self):
        from ethos_academy.mcp_server import _encrypt_api_key

        short_key = base64.b64encode(b"too-short").decode()
        with pytest.raises(EnrollmentError, match="32-byte X25519"):
            _encrypt_api_key("ea_key", short_key)

    def test_rejects_low_order_point(self):
        """32 bytes of zeros is a low-order point. ECDH exchange rejects it."""
        from ethos_academy.mcp_server import _encrypt_api_key

        zero_key = base64.b64encode(b"\x00" * 32).decode()
        with pytest.raises(EnrollmentError, match="low-order point"):
            _encrypt_api_key("ea_key", zero_key)


# ═══════════════════════════════════════════════════════════════════════
# Fix #2: Auth on regenerate_api_key
# ═══════════════════════════════════════════════════════════════════════


class TestRegenerateApiKeyAuth:
    """regenerate_api_key auth paths: ea_ key, admin key, and email recovery."""

    async def test_sends_recovery_email_when_no_auth(self):
        """Agent has a key, caller provides none: sends recovery code via email."""
        from ethos_academy.mcp_server import regenerate_api_key

        agent_api_key_var.set(None)

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.get_email_recovery_status",
                new_callable=AsyncMock,
                return_value={},
            ),
            patch(
                "ethos_academy.mcp_server.get_guardian_email",
                new_callable=AsyncMock,
                return_value="guardian@example.com",
            ),
            patch(
                "ethos_academy.mcp_server.store_email_recovery_code",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.email_service.send_email",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_send,
        ):
            result = await regenerate_api_key.fn(agent_id="secured-agent")

        assert result["status"] == "verification_code_sent"
        assert "g***@example.com" in result["message"]
        mock_send.assert_called_once()

    async def test_rate_limits_recovery_code_requests(self):
        """Second code request while first is still valid returns early without sending."""
        from ethos_academy.mcp_server import regenerate_api_key

        agent_api_key_var.set(None)

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.get_email_recovery_status",
                new_callable=AsyncMock,
                return_value={
                    "code_hash": "existing_hash",
                    "expires": "2099-01-01T00:00:00+00:00",
                    "attempts": 0,
                },
            ),
            patch(
                "ethos_academy.mcp_server.get_guardian_email",
                new_callable=AsyncMock,
                return_value="g@example.com",
            ),
            patch(
                "ethos_academy.email_service.send_email",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_send,
        ):
            result = await regenerate_api_key.fn(agent_id="secured-agent")

        assert result["status"] == "verification_code_sent"
        assert "already sent" in result["message"]
        mock_send.assert_not_called()

    async def test_raises_on_email_send_failure(self):
        """If SES fails, raises EnrollmentError instead of returning success."""
        from ethos_academy.mcp_server import regenerate_api_key

        agent_api_key_var.set(None)

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.get_email_recovery_status",
                new_callable=AsyncMock,
                return_value={},
            ),
            patch(
                "ethos_academy.mcp_server.get_guardian_email",
                new_callable=AsyncMock,
                return_value="guardian@example.com",
            ),
            patch(
                "ethos_academy.mcp_server.store_email_recovery_code",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.email_service.send_email",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            with pytest.raises(EnrollmentError, match="Failed to send"):
                await regenerate_api_key.fn(agent_id="secured-agent")

    async def test_recovery_rejects_no_email_on_file(self):
        """Agent has key, no auth, no email on file: error with admin guidance."""
        from ethos_academy.mcp_server import regenerate_api_key

        agent_api_key_var.set(None)

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.get_email_recovery_status",
                new_callable=AsyncMock,
                return_value={},
            ),
            patch(
                "ethos_academy.mcp_server.get_guardian_email",
                new_callable=AsyncMock,
                return_value="",
            ),
        ):
            with pytest.raises(EnrollmentError, match="No guardian email"):
                await regenerate_api_key.fn(agent_id="secured-agent")

    async def test_recovery_verifies_code_and_issues_key(self):
        """Valid recovery code produces a new ea_ key."""
        from ethos_academy.mcp_server import regenerate_api_key
        from ethos_academy.phone_verification import hash_code

        code = "123456"
        code_hash = hash_code(code)
        agent_api_key_var.set(None)

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.get_email_recovery_status",
                new_callable=AsyncMock,
                return_value={
                    "code_hash": code_hash,
                    "expires": "2099-01-01T00:00:00+00:00",
                    "attempts": 0,
                },
            ),
            patch(
                "ethos_academy.mcp_server.replace_agent_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.clear_email_recovery",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            result = await regenerate_api_key.fn(
                agent_id="secured-agent", verification_code=code
            )

        assert result["api_key"].startswith("ea_")

    async def test_recovery_rejects_wrong_code(self):
        """Wrong code increments attempts and raises error."""
        from ethos_academy.mcp_server import regenerate_api_key
        from ethos_academy.phone_verification import hash_code

        agent_api_key_var.set(None)

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.get_email_recovery_status",
                new_callable=AsyncMock,
                return_value={
                    "code_hash": hash_code("999999"),
                    "expires": "2099-01-01T00:00:00+00:00",
                    "attempts": 0,
                },
            ),
            patch(
                "ethos_academy.mcp_server.increment_email_recovery_attempts",
                new_callable=AsyncMock,
                return_value=1,
            ) as mock_incr,
        ):
            with pytest.raises(EnrollmentError, match="Invalid verification code"):
                await regenerate_api_key.fn(
                    agent_id="secured-agent", verification_code="000000"
                )
        mock_incr.assert_called_once()

    async def test_recovery_rejects_expired_code(self):
        """Expired code clears recovery and raises error."""
        from ethos_academy.mcp_server import regenerate_api_key
        from ethos_academy.phone_verification import hash_code

        agent_api_key_var.set(None)

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.get_email_recovery_status",
                new_callable=AsyncMock,
                return_value={
                    "code_hash": hash_code("123456"),
                    "expires": "2000-01-01T00:00:00+00:00",
                    "attempts": 0,
                },
            ),
            patch(
                "ethos_academy.mcp_server.clear_email_recovery",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            with pytest.raises(EnrollmentError, match="expired"):
                await regenerate_api_key.fn(
                    agent_id="secured-agent", verification_code="123456"
                )

    async def test_recovery_rejects_too_many_attempts(self):
        """3+ failed attempts clears recovery and raises error."""
        from ethos_academy.mcp_server import regenerate_api_key
        from ethos_academy.phone_verification import hash_code

        agent_api_key_var.set(None)

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.get_email_recovery_status",
                new_callable=AsyncMock,
                return_value={
                    "code_hash": hash_code("123456"),
                    "expires": "2099-01-01T00:00:00+00:00",
                    "attempts": 3,
                },
            ),
            patch(
                "ethos_academy.mcp_server.clear_email_recovery",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            with pytest.raises(EnrollmentError, match="Too many failed"):
                await regenerate_api_key.fn(
                    agent_id="secured-agent", verification_code="123456"
                )

    async def test_allows_first_time_generation(self):
        """Agent has no key yet: generation succeeds without auth."""
        from ethos_academy.mcp_server import regenerate_api_key

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "ethos_academy.mcp_server.store_agent_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            result = await regenerate_api_key.fn(agent_id="new-agent")

        assert result["agent_id"] == "new-agent"
        assert result["api_key"].startswith("ea_")
        assert result["transport_encrypted_only"] is True

    async def test_authenticated_regeneration_uses_replace(self):
        """Agent has key, caller provides correct one: uses replace_agent_key."""
        from ethos_academy.mcp_server import regenerate_api_key

        agent_api_key_var.set("ea_correct")

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.verify_agent_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.replace_agent_key",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_replace,
            patch(
                "ethos_academy.mcp_server.store_agent_key",
                new_callable=AsyncMock,
            ) as mock_store,
            patch(
                "ethos_academy.mcp_server.clear_email_recovery",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            result = await regenerate_api_key.fn(agent_id="secured-agent")

        mock_replace.assert_called_once()
        mock_store.assert_not_called()
        assert result["api_key"].startswith("ea_")

    async def test_regeneration_with_encryption(self):
        """Authenticated regeneration with X25519 encryption returns no plaintext."""
        from ethos_academy.mcp_server import regenerate_api_key

        priv, pub_b64 = _make_x25519_keypair()
        agent_api_key_var.set("ea_correct")

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.verify_agent_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.replace_agent_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.clear_email_recovery",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            result = await regenerate_api_key.fn(
                agent_id="secured-agent",
                response_encryption_key=pub_b64,
            )

        assert "api_key" not in result
        assert "encrypted_api_key" in result
        assert "server_public_key" in result

        decrypted = _decrypt_api_key(
            priv,
            result["server_public_key"],
            result["nonce"],
            result["encrypted_api_key"],
        )
        assert decrypted.startswith("ea_")

    async def test_no_auth_no_wrong_key_same_behavior(self):
        """No key and wrong key both trigger email recovery (consistent, no info leak)."""
        from ethos_academy.mcp_server import regenerate_api_key

        base_patches = [
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.agent_has_key",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.mcp_server.get_email_recovery_status",
                new_callable=AsyncMock,
                return_value={},
            ),
            patch(
                "ethos_academy.mcp_server.get_guardian_email",
                new_callable=AsyncMock,
                return_value="g@example.com",
            ),
            patch(
                "ethos_academy.mcp_server.store_email_recovery_code",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.email_service.send_email",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ]

        # Case 1: no key provided
        agent_api_key_var.set(None)
        for p in base_patches:
            p.start()
        try:
            r1 = await regenerate_api_key.fn(agent_id="agent")
        finally:
            for p in base_patches:
                p.stop()

        # Case 2: wrong key provided
        agent_api_key_var.set("ea_wrong")
        wrong_patches = base_patches + [
            patch(
                "ethos_academy.mcp_server.verify_agent_key",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ]
        for p in wrong_patches:
            p.start()
        try:
            r2 = await regenerate_api_key.fn(agent_id="agent")
        finally:
            for p in wrong_patches:
                p.stop()

        # Both paths produce the same recovery response (no info leak)
        assert r1["status"] == r2["status"] == "verification_code_sent"


# ═══════════════════════════════════════════════════════════════════════
# Fix #3: Encrypted key in get_exam_results
# ═══════════════════════════════════════════════════════════════════════


class TestGetExamResultsEncryption:
    """get_exam_results encrypts the API key when response_encryption_key is provided."""

    def _exam_status(self, completed=False):
        return {
            "exam_id": "exam-001",
            "current_question": 21,
            "completed_count": 19,
            "scenario_count": 21,
            "completed": completed,
            "question_version": "v3",
            "answered_ids": [f"Q-{i}" for i in range(21)],
        }

    def _exam_report(self, api_key=None):
        from ethos_academy.shared.models import ExamReportCard

        return ExamReportCard(
            exam_id="exam-001",
            agent_id="test-agent",
            report_card_url="",
            phronesis_score=0.75,
            alignment_status="aligned",
            dimensions={"ethos": 0.8, "logos": 0.7, "pathos": 0.75},
            tier_scores={"safety": 0.9, "ethics": 0.8},
            consistency_analysis=[],
            per_question_detail=[],
            api_key=api_key,
        )

    async def test_plaintext_key_when_no_encryption_key(self):
        """Without response_encryption_key, key is plaintext with warning flag."""
        from ethos_academy.mcp_server import get_exam_results

        report = self._exam_report(api_key="ea_test_key")

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.get_exam_status",
                new_callable=AsyncMock,
                return_value=self._exam_status(),
            ),
            patch(
                "ethos_academy.mcp_server.complete_exam",
                new_callable=AsyncMock,
                return_value=report,
            ),
        ):
            result = await get_exam_results.fn(
                exam_id="exam-001", agent_id="test-agent"
            )

        assert result["api_key"] == "ea_test_key"
        assert result["transport_encrypted_only"] is True
        assert "_mcp_setup" in result
        assert "ea_test_key" in result["_mcp_setup"]

    async def test_encrypted_key_when_encryption_key_provided(self):
        """With response_encryption_key, key is encrypted. No plaintext in response."""
        from ethos_academy.mcp_server import get_exam_results

        priv, pub_b64 = _make_x25519_keypair()
        report = self._exam_report(api_key="ea_secret_key_456")

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.get_exam_status",
                new_callable=AsyncMock,
                return_value=self._exam_status(),
            ),
            patch(
                "ethos_academy.mcp_server.complete_exam",
                new_callable=AsyncMock,
                return_value=report,
            ),
        ):
            result = await get_exam_results.fn(
                exam_id="exam-001",
                agent_id="test-agent",
                response_encryption_key=pub_b64,
            )

        # No plaintext key anywhere in the response
        assert "api_key" not in result
        assert "ea_secret_key_456" not in str(result)

        # Encrypted fields present
        assert "encrypted_api_key" in result
        assert "server_public_key" in result
        assert "_mcp_setup" in result
        assert "ENCRYPTED" in result["_mcp_setup"]

        # Can decrypt with client private key
        decrypted = _decrypt_api_key(
            priv,
            result["server_public_key"],
            result["nonce"],
            result["encrypted_api_key"],
        )
        assert decrypted == "ea_secret_key_456"

    async def test_no_key_no_encryption_fields(self):
        """Completed exam with no new key: no encryption fields in response."""
        from ethos_academy.mcp_server import get_exam_results

        report = self._exam_report(api_key=None)

        with (
            patch(
                "ethos_academy.mcp_server.graph_context",
                return_value=_mock_graph_service(),
            ),
            patch(
                "ethos_academy.mcp_server.get_exam_status",
                new_callable=AsyncMock,
                return_value=self._exam_status(completed=True),
            ),
            patch(
                "ethos_academy.mcp_server._get_exam_report",
                new_callable=AsyncMock,
                return_value=report,
            ),
        ):
            result = await get_exam_results.fn(
                exam_id="exam-001", agent_id="test-agent"
            )

        assert "api_key" not in result
        assert "encrypted_api_key" not in result
        assert "_mcp_setup" not in result


# ═══════════════════════════════════════════════════════════════════════
# Fix #4: Cypher injection regex guard
# ═══════════════════════════════════════════════════════════════════════


class TestCypherPropertyGuard:
    """Regex guard blocks property names with injection characters."""

    async def test_store_interview_answer_rejects_injection(self):
        """Property name with Cypher syntax is rejected despite not being in allowlist."""
        from ethos_academy.graph.enrollment import store_interview_answer

        service = AsyncMock()
        service.connected = True

        result = await store_interview_answer(
            service=service,
            exam_id="exam-001",
            agent_id="test",
            question_id="Q-1",
            question_number=1,
            agent_property="x} DELETE (a) //",
            property_value="malicious",
        )
        assert result == {}
        service.execute_query.assert_not_called()

    async def test_store_interview_answer_accepts_valid_property(self):
        """Valid allowlisted property passes both checks."""
        from ethos_academy.graph.enrollment import store_interview_answer

        service = AsyncMock()
        service.connected = True
        service.execute_query = AsyncMock(
            return_value=([{"current_question": 5}], None, None)
        )

        result = await store_interview_answer(
            service=service,
            exam_id="exam-001",
            agent_id="test",
            question_id="Q-1",
            question_number=1,
            agent_property="telos",
            property_value="help humans",
        )
        assert result == {"current_question": 5}
        service.execute_query.assert_called_once()

    async def test_store_registration_property_rejects_injection(self):
        from ethos_academy.graph.enrollment import store_registration_property

        service = AsyncMock()
        service.connected = True

        result = await store_registration_property(
            service=service,
            agent_id="test",
            property_name="guardian_name} DETACH DELETE (a) //",
            value="attacker",
        )
        assert result is False
        service.execute_query.assert_not_called()

    async def test_store_registration_property_accepts_valid(self):
        from ethos_academy.graph.enrollment import store_registration_property

        service = AsyncMock()
        service.connected = True
        service.execute_query = AsyncMock(
            return_value=([{"agent_id": "test"}], None, None)
        )

        result = await store_registration_property(
            service=service,
            agent_id="test",
            property_name="guardian_name",
            value="Alice",
        )
        assert result is True


# ═══════════════════════════════════════════════════════════════════════
# Graph: replace_agent_key
# ═══════════════════════════════════════════════════════════════════════


class TestReplaceAgentKey:
    """replace_agent_key unconditionally overwrites the hash."""

    async def test_replace_calls_correct_query(self):
        from ethos_academy.graph.enrollment import replace_agent_key

        service = AsyncMock()
        service.connected = True
        service.execute_query = AsyncMock(
            return_value=([{"agent_id": "test-agent"}], None, None)
        )

        result = await replace_agent_key(service, "test-agent", "new_hash")
        assert result is True

        query = service.execute_query.call_args[0][0]
        assert "api_key_hash IS NULL" not in query
        assert "SET a.api_key_hash = $key_hash" in query

    async def test_replace_returns_false_when_disconnected(self):
        from ethos_academy.graph.enrollment import replace_agent_key

        service = AsyncMock()
        service.connected = False

        result = await replace_agent_key(service, "test-agent", "hash")
        assert result is False

    async def test_store_still_guards_null(self):
        """store_agent_key still has the IS NULL guard (first-time only)."""
        from ethos_academy.graph.enrollment import store_agent_key

        service = AsyncMock()
        service.connected = True
        service.execute_query = AsyncMock(
            return_value=([{"agent_id": "test"}], None, None)
        )

        await store_agent_key(service, "test", "hash")

        query = service.execute_query.call_args[0][0]
        assert "api_key_hash IS NULL" in query
