"""Request-scoped ContextVar for BYOK (Bring Your Own Key) API key threading.

The ContextVar allows callers to set a per-request Anthropic API key that
overrides the server default. Async-safe: each coroutine/task gets its own
value without thread/task leakage.

Pattern follows graph_context() in ethos/graph/service.py -- runtime
concerns live at ethos/ package root, not in shared/ (pure data only).
"""

from __future__ import annotations

from contextvars import ContextVar

# Default None means "use server key from EthosConfig"
anthropic_api_key_var: ContextVar[str | None] = ContextVar(
    "anthropic_api_key", default=None
)
