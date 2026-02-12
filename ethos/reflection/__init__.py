"""Reflection domain — behavioral analysis over time.

Three cognitive faculties:
  - Instinct: scan_history() — quick red-flag scan of aggregate stats
  - Intuition: intuit_history() — graph-based pattern recognition + extensions
  - Deliberation: insights() — Opus-powered temporal analysis

Plus:
  - reflect() — evaluate + profile in one call
  - reflect_history() — profile-only read (no evaluation)
"""

from ethos.reflection.history import reflect_history
from ethos.reflection.insights import insights
from ethos.reflection.instinct import scan_history
from ethos.reflection.intuition import intuit_history
from ethos.reflection.reflect import reflect

__all__ = [
    "reflect",
    "reflect_history",
    "insights",
    "scan_history",
    "intuit_history",
]
