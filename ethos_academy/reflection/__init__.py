"""Reflection domain — behavioral analysis over time.

Three cognitive faculties:
  - Instinct: scan_history() — quick red-flag scan of aggregate stats
  - Intuition: intuit_history() — graph-based pattern recognition + extensions
  - Deliberation: insights() — Opus-powered temporal analysis

Plus:
  - reflect() — evaluate + profile in one call
  - reflect_history() — profile-only read (no evaluation)
  - generate_daily_report() — nightly report card + homework
"""

from ethos_academy.reflection.daily_report import generate_daily_report
from ethos_academy.reflection.history import reflect_history
from ethos_academy.reflection.insights import insights
from ethos_academy.reflection.instinct import scan_history
from ethos_academy.reflection.intuition import intuit_history
from ethos_academy.reflection.reflect import reflect

__all__ = [
    "reflect",
    "reflect_history",
    "insights",
    "scan_history",
    "intuit_history",
    "generate_daily_report",
]
