"""Request-scoped ContextVars for per-request state threading.

ContextVars provide async-safe per-coroutine values without thread/task
leakage. Two vars live here:

    anthropic_api_key_var: BYOK (Bring Your Own Key) override for the
        server default Anthropic API key.
    request_id_var: UUID per API request for log correlation.

Pattern follows graph_context() in ethos/graph/service.py -- runtime
concerns live at ethos/ package root, not in shared/ (pure data only).
"""

from __future__ import annotations

from contextvars import ContextVar

# Default None means "use server key from EthosConfig"
anthropic_api_key_var: ContextVar[str | None] = ContextVar(
    "anthropic_api_key", default=None
)

# Request ID for structured logging and trace correlation
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Per-agent API key for write operations (ea_ prefix).
# Set by API/MCP middleware, verified by enrollment service.
agent_api_key_var: ContextVar[str | None] = ContextVar("agent_api_key", default=None)
