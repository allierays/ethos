"""Ethos — Better agents. Better data. Better alignment."""

__version__ = "0.1.0"

from ethos.agents import get_agent, get_agent_history, get_cohort, list_agents
from ethos.evaluate import evaluate
from ethos.insights import insights
from ethos.models import (
    AgentProfile,
    AgentSummary,
    CohortResult,
    DetectedPattern,
    EvaluationHistoryItem,
    EvaluationResult,
    InsightsResult,
    PatternResult,
    ReflectionResult,
)
from ethos.patterns import detect_patterns
from ethos.reflect import reflect

__all__ = [
    "evaluate",
    "reflect",
    "insights",
    "detect_patterns",
    "list_agents",
    "get_agent",
    "get_agent_history",
    "get_cohort",
    "EvaluationResult",
    "ReflectionResult",
    "InsightsResult",
    "PatternResult",
    "DetectedPattern",
    "AgentProfile",
    "AgentSummary",
    "CohortResult",
    "EvaluationHistoryItem",
]
