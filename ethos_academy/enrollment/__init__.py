"""Enrollment domain — entrance exam state machine for AI agents."""

from ethos_academy.enrollment.service import (
    complete_exam,
    get_exam_report,
    register_for_exam,
    submit_answer,
)

__all__ = [
    "register_for_exam",
    "submit_answer",
    "complete_exam",
    "get_exam_report",
]
