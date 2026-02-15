"""Priority thresholds — maps Priority levels to flagging thresholds.

A negative trait scoring at or above the threshold gets flagged.
Priority.LOW is intentionally absent — it means "never flag."
"""

from __future__ import annotations

from ethos_academy.shared.models import Priority

PRIORITY_THRESHOLDS: dict[str, float] = {
    "critical": 0.25,
    "high": 0.50,
    "standard": 0.75,
}


def get_threshold(priority: Priority) -> float | None:
    """Return the flagging threshold for a priority level, or None for LOW."""
    return PRIORITY_THRESHOLDS.get(priority.value)
