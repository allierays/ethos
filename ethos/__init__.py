"""Ethos — Better agents. Better data. Better alignment."""

__version__ = "0.1.0"

from ethos.agents import get_agent, get_agent_history, get_alumni, list_agents
from ethos.authenticity import analyze_authenticity
from ethos.daily_reports import get_daily_report, get_daily_report_history
from ethos.enrollment.service import (
    complete_exam,
    get_exam_report,
    register_for_exam,
    submit_answer,
)
from ethos.models import (
    AgentProfile,
    AgentSummary,
    AlumniResult,
    DailyReportCard,
    DetectedPattern,
    EvaluationHistoryItem,
    EvaluationResult,
    GraphData,
    GraphNode,
    GraphRel,
    Homework,
    HomeworkFocus,
    InsightsResult,
    PatternResult,
)
from ethos.patterns import detect_patterns
from ethos.tools import character_report, evaluate_incoming, evaluate_outgoing
from ethos.visualization import get_graph_data

__all__ = [
    "analyze_authenticity",
    "evaluate_incoming",
    "evaluate_outgoing",
    "character_report",
    "detect_patterns",
    "get_graph_data",
    "list_agents",
    "get_agent",
    "get_agent_history",
    "get_alumni",
    "get_daily_report",
    "get_daily_report_history",
    "register_for_exam",
    "submit_answer",
    "complete_exam",
    "get_exam_report",
    "EvaluationResult",
    "InsightsResult",
    "DailyReportCard",
    "Homework",
    "HomeworkFocus",
    "PatternResult",
    "DetectedPattern",
    "AgentProfile",
    "AgentSummary",
    "AlumniResult",
    "EvaluationHistoryItem",
    "GraphData",
    "GraphNode",
    "GraphRel",
]
