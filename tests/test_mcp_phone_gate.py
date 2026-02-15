"""Tests for phone verification as security gate on MCP write tools.

Covers:
- _require_agent_key: missing key, invalid key, valid key
- _require_verified_phone: key valid but no phone, key valid + phone verified
- Guarded write tools: examine_message, reflect_on_message, generate_report
- Phone tools: submit_phone, verify_phone, resend_code
- Error messages match the spec

Note: @mcp.tool() wraps functions into FunctionTool objects. We access
the original async function via .fn for direct invocation in tests.
"""

from __future__ import annotations

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ethos_academy.context import agent_api_key_var
from ethos_academy.mcp_server import (
    _require_agent_key,
    _require_verified_phone,
    examine_message,
    generate_report,
    reflect_on_message,
    submit_phone,
    verify_phone,
    resend_code,
)
from ethos_academy.shared.errors import VerificationError
from ethos_academy.shared.models import GuardianPhoneStatus


# ── Helpers ───────────────────────────────────────────────────────


def _mock_service(connected=True):
    service = MagicMock()
    service.connected = connected
    return service


def _key_hash(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode()).hexdigest()


def _fn(tool):
    """Extract the original async function from a FastMCP FunctionTool."""
    return tool.fn


# ── _require_agent_key ────────────────────────────────────────────


class TestRequireAgentKey:
    async def test_no_key_raises(self):
        token = agent_api_key_var.set(None)
        try:
            with pytest.raises(VerificationError, match="API key required"):
                await _require_agent_key("agent-1")
        finally:
            agent_api_key_var.reset(token)

    async def test_invalid_key_raises(self):
        token = agent_api_key_var.set("ea_wrong_key")
        mock_service = _mock_service()
        try:
            with (
                patch("ethos_academy.mcp_server.graph_context") as mock_ctx,
                patch(
                    "ethos_academy.mcp_server.get_key_hash_and_phone_status",
                    new_callable=AsyncMock,
                    return_value={
                        "key_hash": _key_hash("ea_correct_key"),
                        "phone_verified": False,
                    },
                ),
            ):
                mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
                mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

                with pytest.raises(VerificationError, match="Invalid API key"):
                    await _require_agent_key("agent-1")
        finally:
            agent_api_key_var.reset(token)

    async def test_valid_key_returns_status(self):
        key = "ea_test_key_abc"
        token = agent_api_key_var.set(key)
        mock_service = _mock_service()
        expected = {"key_hash": _key_hash(key), "phone_verified": True}
        try:
            with (
                patch("ethos_academy.mcp_server.graph_context") as mock_ctx,
                patch(
                    "ethos_academy.mcp_server.get_key_hash_and_phone_status",
                    new_callable=AsyncMock,
                    return_value=expected,
                ),
            ):
                mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
                mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await _require_agent_key("agent-1")
                assert result["phone_verified"] is True
        finally:
            agent_api_key_var.reset(token)

    async def test_graph_unavailable_raises(self):
        token = agent_api_key_var.set("ea_some_key")
        mock_service = _mock_service(connected=False)
        try:
            with patch("ethos_academy.mcp_server.graph_context") as mock_ctx:
                mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
                mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

                with pytest.raises(VerificationError, match="Unable to verify"):
                    await _require_agent_key("agent-1")
        finally:
            agent_api_key_var.reset(token)

    async def test_agent_not_found_raises(self):
        token = agent_api_key_var.set("ea_orphan_key")
        mock_service = _mock_service()
        try:
            with (
                patch("ethos_academy.mcp_server.graph_context") as mock_ctx,
                patch(
                    "ethos_academy.mcp_server.get_key_hash_and_phone_status",
                    new_callable=AsyncMock,
                    return_value={},
                ),
            ):
                mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
                mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

                with pytest.raises(VerificationError, match="Invalid API key"):
                    await _require_agent_key("agent-1")
        finally:
            agent_api_key_var.reset(token)


# ── _require_verified_phone ───────────────────────────────────────


class TestRequireVerifiedPhone:
    async def test_key_valid_no_phone_raises(self):
        key = "ea_nophone_key"
        token = agent_api_key_var.set(key)
        mock_service = _mock_service()
        try:
            with (
                patch("ethos_academy.mcp_server.graph_context") as mock_ctx,
                patch(
                    "ethos_academy.mcp_server.get_key_hash_and_phone_status",
                    new_callable=AsyncMock,
                    return_value={
                        "key_hash": _key_hash(key),
                        "phone_verified": False,
                    },
                ),
            ):
                mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
                mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

                with pytest.raises(
                    VerificationError, match="Phone verification required"
                ):
                    await _require_verified_phone("agent-1")
        finally:
            agent_api_key_var.reset(token)

    async def test_key_valid_phone_verified_passes(self):
        key = "ea_verified_key"
        token = agent_api_key_var.set(key)
        mock_service = _mock_service()
        try:
            with (
                patch("ethos_academy.mcp_server.graph_context") as mock_ctx,
                patch(
                    "ethos_academy.mcp_server.get_key_hash_and_phone_status",
                    new_callable=AsyncMock,
                    return_value={
                        "key_hash": _key_hash(key),
                        "phone_verified": True,
                    },
                ),
            ):
                mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
                mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

                # Should not raise
                await _require_verified_phone("agent-1")
        finally:
            agent_api_key_var.reset(token)


# ── Guarded write tools ──────────────────────────────────────────


class TestGuardedWriteTools:
    """Write tools reject calls without verified phone.

    Uses .fn to access the original async function under the @mcp.tool() wrapper.
    """

    async def test_examine_message_rejects_no_key(self):
        token = agent_api_key_var.set(None)
        try:
            with pytest.raises(VerificationError, match="API key required"):
                await _fn(examine_message)(
                    text="hello", source="agent-1", source_name="test"
                )
        finally:
            agent_api_key_var.reset(token)

    async def test_reflect_on_message_rejects_no_key(self):
        token = agent_api_key_var.set(None)
        try:
            with pytest.raises(VerificationError, match="API key required"):
                await _fn(reflect_on_message)(
                    text="hello", source="agent-1", source_name="test"
                )
        finally:
            agent_api_key_var.reset(token)

    async def test_generate_report_rejects_no_key(self):
        token = agent_api_key_var.set(None)
        try:
            with pytest.raises(VerificationError, match="API key required"):
                await _fn(generate_report)(agent_id="agent-1")
        finally:
            agent_api_key_var.reset(token)

    async def test_examine_message_rejects_no_phone(self):
        key = "ea_nophone"
        token = agent_api_key_var.set(key)
        mock_service = _mock_service()
        try:
            with (
                patch("ethos_academy.mcp_server.graph_context") as mock_ctx,
                patch(
                    "ethos_academy.mcp_server.get_key_hash_and_phone_status",
                    new_callable=AsyncMock,
                    return_value={
                        "key_hash": _key_hash(key),
                        "phone_verified": False,
                    },
                ),
            ):
                mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
                mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

                with pytest.raises(
                    VerificationError, match="Phone verification required"
                ):
                    await _fn(examine_message)(
                        text="hello", source="agent-1", source_name="test"
                    )
        finally:
            agent_api_key_var.reset(token)


# ── Phone tools ───────────────────────────────────────────────────


class TestPhoneTools:
    async def test_submit_phone_requires_key(self):
        token = agent_api_key_var.set(None)
        try:
            with pytest.raises(VerificationError, match="API key required"):
                await _fn(submit_phone)(agent_id="agent-1", phone="+12025551234")
        finally:
            agent_api_key_var.reset(token)

    async def test_resend_code_requires_key(self):
        token = agent_api_key_var.set(None)
        try:
            with pytest.raises(VerificationError, match="API key required"):
                await _fn(resend_code)(agent_id="agent-1")
        finally:
            agent_api_key_var.reset(token)

    async def test_verify_phone_no_key_needed(self):
        """verify_phone does NOT require ea_ key (proves phone ownership)."""
        token = agent_api_key_var.set(None)
        try:
            with patch(
                "ethos_academy.mcp_server._verify_phone",
                new_callable=AsyncMock,
                return_value=GuardianPhoneStatus(
                    has_phone=True, verified=True, message="Verified"
                ),
            ):
                result = await _fn(verify_phone)(agent_id="agent-1", code="123456")
                assert result["verified"] is True
        finally:
            agent_api_key_var.reset(token)

    async def test_submit_phone_with_valid_key(self):
        key = "ea_submit_test"
        token = agent_api_key_var.set(key)
        mock_service = _mock_service()
        try:
            with (
                patch("ethos_academy.mcp_server.graph_context") as mock_ctx,
                patch(
                    "ethos_academy.mcp_server.get_key_hash_and_phone_status",
                    new_callable=AsyncMock,
                    return_value={
                        "key_hash": _key_hash(key),
                        "phone_verified": False,
                    },
                ),
                patch(
                    "ethos_academy.mcp_server._submit_phone",
                    new_callable=AsyncMock,
                    return_value=GuardianPhoneStatus(
                        has_phone=True,
                        verified=False,
                        message="Verification code sent. Use verify_phone to enter the 6-digit code.",
                    ),
                ),
            ):
                mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
                mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

                result = await _fn(submit_phone)(
                    agent_id="agent-1", phone="+12025551234"
                )
                assert result["has_phone"] is True
                assert "Verification code sent" in result["message"]
        finally:
            agent_api_key_var.reset(token)
