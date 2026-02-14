"""BYOK middleware tests for the MCP SSE transport.

Tests that BYOKMiddleware.on_call_tool correctly reads API keys from HTTP
headers, sets the ContextVar for tool execution, and resets it afterward.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest

from ethos.context import anthropic_api_key_var
from ethos.mcp_server import BYOKMiddleware


# ---------------------------------------------------------------------------
# Helpers: minimal fakes for FastMCP middleware types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FakeCallToolParams:
    name: str = "examine_message"
    arguments: dict[str, Any] | None = None


@dataclass(frozen=True)
class FakeMiddlewareContext:
    message: Any = None
    method: str = "tools/call"
    timestamp: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# BYOKMiddleware.on_call_tool
# ---------------------------------------------------------------------------


class TestBYOKMiddlewareOnCallTool:
    """on_call_tool sets the ContextVar from HTTP headers."""

    @pytest.fixture(autouse=True)
    def _reset_contextvar(self):
        """Ensure ContextVar starts clean and ends clean."""
        assert anthropic_api_key_var.get() is None
        yield
        assert anthropic_api_key_var.get() is None

    async def test_authorization_bearer_sets_contextvar(self):
        """Authorization: Bearer <key> sets the ContextVar during tool call."""
        captured_key = None

        async def fake_call_next(ctx):
            nonlocal captured_key
            captured_key = anthropic_api_key_var.get()
            return []

        headers = {"authorization": "Bearer sk-ant-test-mcp-key-123"}
        ctx = FakeMiddlewareContext(message=FakeCallToolParams())

        middleware = BYOKMiddleware()
        with patch("ethos.mcp_server.get_http_headers", return_value=headers):
            await middleware.on_call_tool(ctx, fake_call_next)

        assert captured_key == "sk-ant-test-mcp-key-123"

    async def test_x_anthropic_key_header_sets_contextvar(self):
        """X-Anthropic-Key header sets the ContextVar during tool call."""
        captured_key = None

        async def fake_call_next(ctx):
            nonlocal captured_key
            captured_key = anthropic_api_key_var.get()
            return []

        headers = {"x-anthropic-key": "sk-ant-test-xheader-456"}
        ctx = FakeMiddlewareContext(message=FakeCallToolParams())

        middleware = BYOKMiddleware()
        with patch("ethos.mcp_server.get_http_headers", return_value=headers):
            await middleware.on_call_tool(ctx, fake_call_next)

        assert captured_key == "sk-ant-test-xheader-456"

    async def test_bearer_takes_priority_over_x_header(self):
        """Authorization: Bearer wins when both headers are present."""
        captured_key = None

        async def fake_call_next(ctx):
            nonlocal captured_key
            captured_key = anthropic_api_key_var.get()
            return []

        headers = {
            "authorization": "Bearer sk-ant-bearer-wins",
            "x-anthropic-key": "sk-ant-x-header-loses",
        }
        ctx = FakeMiddlewareContext(message=FakeCallToolParams())

        middleware = BYOKMiddleware()
        with patch("ethos.mcp_server.get_http_headers", return_value=headers):
            await middleware.on_call_tool(ctx, fake_call_next)

        assert captured_key == "sk-ant-bearer-wins"

    async def test_no_headers_leaves_contextvar_none(self):
        """Without headers (stdio mode), ContextVar stays None."""
        captured_key = "sentinel"

        async def fake_call_next(ctx):
            nonlocal captured_key
            captured_key = anthropic_api_key_var.get()
            return []

        ctx = FakeMiddlewareContext(message=FakeCallToolParams())

        middleware = BYOKMiddleware()
        with patch("ethos.mcp_server.get_http_headers", return_value={}):
            await middleware.on_call_tool(ctx, fake_call_next)

        assert captured_key is None

    async def test_contextvar_reset_after_tool_call(self):
        """ContextVar resets to None after the tool call completes."""

        async def fake_call_next(ctx):
            assert anthropic_api_key_var.get() == "sk-ant-reset-test"
            return []

        headers = {"authorization": "Bearer sk-ant-reset-test"}
        ctx = FakeMiddlewareContext(message=FakeCallToolParams())

        middleware = BYOKMiddleware()
        with patch("ethos.mcp_server.get_http_headers", return_value=headers):
            await middleware.on_call_tool(ctx, fake_call_next)

        # After on_call_tool returns, ContextVar must be back to None
        assert anthropic_api_key_var.get() is None

    async def test_contextvar_reset_on_exception(self):
        """ContextVar resets even if the tool handler raises."""

        async def exploding_call_next(ctx):
            assert anthropic_api_key_var.get() == "sk-ant-boom"
            raise RuntimeError("tool failed")

        headers = {"authorization": "Bearer sk-ant-boom"}
        ctx = FakeMiddlewareContext(message=FakeCallToolParams())

        middleware = BYOKMiddleware()
        with patch("ethos.mcp_server.get_http_headers", return_value=headers):
            with pytest.raises(RuntimeError, match="tool failed"):
                await middleware.on_call_tool(ctx, exploding_call_next)

        # Key must not leak after exception
        assert anthropic_api_key_var.get() is None
