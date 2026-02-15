"""Shared logging configuration for Ethos.

Provides a reusable configure_logging() and JSON formatter with request_id
correlation. Use this from api/, mcp_server, and scripts instead of
duplicating logging setup.

Usage:
    from ethos_academy.shared.logging import configure_logging
    configure_logging()  # Call once at startup

Logger creation remains standard:
    import logging
    logger = logging.getLogger(__name__)
"""

from __future__ import annotations

import json
import logging
import os


class JsonFormatter(logging.Formatter):
    """JSON log formatter with request_id correlation.

    Produces one JSON object per log line with timestamp, level, logger name,
    message, and optional request_id + exception traceback.
    """

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Inject request_id when running inside an API request
        try:
            from ethos_academy.context import request_id_var

            req_id = request_id_var.get()
            if req_id:
                entry["request_id"] = req_id
        except ImportError:
            pass

        if record.exc_info and record.exc_info[0]:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry)


_SIMPLE_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(
    level: str | None = None,
    fmt: str | None = None,
) -> None:
    """Set up structured logging. JSON in production, simple in dev.

    Reads from environment if args are not provided:
        LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (default: INFO)
        LOG_FORMAT: "json" or "simple" (default: simple)

    Safe to call multiple times. Adds a handler only if the root logger has none.
    """
    resolved_level = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    resolved_fmt = fmt or os.environ.get("LOG_FORMAT", "simple")

    root = logging.getLogger()
    root.setLevel(resolved_level)

    if not root.handlers:
        handler = logging.StreamHandler()
        if resolved_fmt == "json":
            handler.setFormatter(JsonFormatter())
        else:
            handler.setFormatter(logging.Formatter(_SIMPLE_FORMAT))
        root.addHandler(handler)
