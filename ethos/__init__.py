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
    GraphData,
    GraphNode,
    GraphRel,
    InsightsResult,
    PatternResult,
    ReflectionResult,
)
from ethos.patterns import detect_patterns
from ethos.reflect import reflect
from ethos.visualization import get_graph_data

__all__ = [
    "evaluate",
    "reflect",
    "insights",
    "detect_patterns",
    "get_graph_data",
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
    "GraphData",
    "GraphNode",
    "GraphRel",
]
