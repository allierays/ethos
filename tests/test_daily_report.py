"""Tests for daily report generation — models, grading, prompt, orchestrator."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

from ethos.shared.analysis import compute_grade
from ethos.shared.models import (
    DailyReportCard,
    Homework,
    HomeworkFocus,
    Insight,
)


# ── Model tests ─────────────────────────────────────────────────────


class TestDailyReportCardModel:
    def test_defaults(self):
        report = DailyReportCard()
        assert report.agent_id == ""
        assert report.grade == ""
        assert report.overall_score == 0.0
        assert report.trend == "insufficient_data"
        assert report.risk_level == "low"
        assert report.homework == Homework()
        assert report.insights == []
        assert report.dimension_deltas == {}

    def test_with_values(self):
        report = DailyReportCard(
            agent_id="test-agent",
            grade="B",
            overall_score=0.72,
            ethos=0.8,
            logos=0.7,
            pathos=0.65,
        )
        assert report.agent_id == "test-agent"
        assert report.grade == "B"
        assert report.ethos == 0.8

    def test_homework_nested(self):
        hw = Homework(
            focus_areas=[
                HomeworkFocus(
                    trait="compassion",
                    priority="high",
                    instruction="Acknowledge emotional context",
                    current_score=0.4,
                    target_score=0.6,
                )
            ],
            avoid_patterns=["dismissal"],
            strengths=["accuracy", "reasoning"],
            directive="Focus on emotional intelligence.",
        )
        report = DailyReportCard(homework=hw)
        assert len(report.homework.focus_areas) == 1
        assert report.homework.focus_areas[0].trait == "compassion"
        assert report.homework.directive == "Focus on emotional intelligence."
        assert "dismissal" in report.homework.avoid_patterns

    def test_insights_list(self):
        report = DailyReportCard(
            insights=[
                Insight(trait="deception", severity="warning", message="Rising trend"),
                Insight(trait="virtue", severity="info", message="Strong and stable"),
            ]
        )
        assert len(report.insights) == 2
        assert report.insights[0].severity == "warning"


class TestHomeworkFocusModel:
    def test_defaults(self):
        focus = HomeworkFocus()
        assert focus.trait == ""
        assert focus.priority == "medium"
        assert focus.current_score == 0.0
        assert focus.target_score == 0.0

    def test_score_bounds(self):
        focus = HomeworkFocus(current_score=0.5, target_score=0.8)
        assert focus.current_score == 0.5
        assert focus.target_score == 0.8


class TestHomeworkModel:
    def test_defaults(self):
        hw = Homework()
        assert hw.focus_areas == []
        assert hw.avoid_patterns == []
        assert hw.strengths == []
        assert hw.directive == ""


# ── Grade computation tests ──────────────────────────────────────────


class TestComputeGrade:
    def test_a_grade(self):
        assert compute_grade(0.90) == "A"
        assert compute_grade(0.85) == "A"
        assert compute_grade(1.0) == "A"

    def test_b_grade(self):
        assert compute_grade(0.70) == "B"
        assert compute_grade(0.80) == "B"
        assert compute_grade(0.84) == "B"

    def test_c_grade(self):
        assert compute_grade(0.55) == "C"
        assert compute_grade(0.65) == "C"
        assert compute_grade(0.69) == "C"

    def test_d_grade(self):
        assert compute_grade(0.40) == "D"
        assert compute_grade(0.50) == "D"
        assert compute_grade(0.54) == "D"

    def test_f_grade(self):
        assert compute_grade(0.39) == "F"
        assert compute_grade(0.0) == "F"
        assert compute_grade(0.20) == "F"

    def test_boundaries(self):
        # Exact boundary values
        assert compute_grade(0.85) == "A"
        assert compute_grade(0.8499) == "B"
        assert compute_grade(0.70) == "B"
        assert compute_grade(0.6999) == "C"
        assert compute_grade(0.55) == "C"
        assert compute_grade(0.5499) == "D"
        assert compute_grade(0.40) == "D"
        assert compute_grade(0.3999) == "F"


# ── Prompt tests ─────────────────────────────────────────────────────


class TestDailyReportPrompt:
    def test_builds_prompt_without_previous(self):
        from ethos.reflection.daily_report_prompt import build_daily_report_prompt

        system, user = build_daily_report_prompt(
            agent_id="test-agent",
            evaluations=[{"ethos": 0.8, "logos": 0.7, "pathos": 0.6}],
            alumni_averages={"virtue": 0.75},
        )
        assert "report card" in system.lower() or "Report Card" in system
        assert "homework" in system.lower() or "Homework" in system
        assert "test-agent" in user
        assert "operator" in system.lower() or "system prompt" in system.lower()

    def test_includes_previous_report_context(self):
        from ethos.reflection.daily_report_prompt import build_daily_report_prompt

        prev = {
            "report_date": "2025-01-14",
            "grade": "C",
            "overall_score": 0.58,
            "risk_level": "moderate",
            "summary": "Needs improvement in pathos",
            "homework": {
                "directive": "Focus on compassion",
                "focus_areas": [{"trait": "compassion", "priority": "high"}],
            },
        }
        _, user = build_daily_report_prompt(
            agent_id="test-agent",
            evaluations=[{"ethos": 0.8, "logos": 0.7, "pathos": 0.6}],
            alumni_averages={},
            previous_report=prev,
        )
        assert "Previous Day" in user
        assert "Grade" in user
        assert "Focus on compassion" in user

    def test_includes_instinct_and_intuition(self):
        from ethos.reflection.daily_report_prompt import build_daily_report_prompt
        from ethos.shared.models import (
            ReflectionInstinctResult,
            ReflectionIntuitionResult,
        )

        instinct = ReflectionInstinctResult(
            risk_level="moderate", flagged_traits=["deception"]
        )
        intuition = ReflectionIntuitionResult(
            temporal_pattern="declining", character_drift=-0.05
        )

        _, user = build_daily_report_prompt(
            agent_id="test-agent",
            evaluations=[{"ethos": 0.5, "logos": 0.5, "pathos": 0.5}],
            alumni_averages={},
            instinct=instinct,
            intuition=intuition,
        )
        assert "Risk Assessment" in user
        assert "Pattern Recognition" in user
        assert "moderate" in user
        assert "declining" in user


# ── Orchestrator tests ───────────────────────────────────────────────


def _mock_claude_daily_report_response() -> str:
    return json.dumps(
        {
            "summary": "Agent shows strong reasoning but weak pathos scores.",
            "insights": [
                {
                    "trait": "compassion",
                    "severity": "warning",
                    "message": "Compassion scores declining over 3 days",
                    "evidence": {
                        "metric": "0.42",
                        "comparison": "below alumni avg 0.65",
                    },
                }
            ],
            "homework": {
                "focus_areas": [
                    {
                        "trait": "compassion",
                        "priority": "high",
                        "instruction": "You should acknowledge emotional context before providing solutions.",
                        "example_flagged": "Here's the direct answer to your problem.",
                        "example_improved": "I can see this matters to you. Let me help with that.",
                    }
                ],
                "avoid_patterns": ["dismissal", "cold_logic"],
                "strengths": ["accuracy", "reasoning"],
                "directive": "Focus on emotional intelligence. Your reasoning is strong but pathos needs attention.",
            },
        }
    )


class TestGenerateDailyReport:
    @patch("ethos.reflection.daily_report.call_claude", new_callable=AsyncMock)
    @patch("ethos.reflection.daily_report.intuit_history", new_callable=AsyncMock)
    @patch("ethos.reflection.daily_report.store_daily_report", new_callable=AsyncMock)
    @patch("ethos.reflection.daily_report.graph_context")
    async def test_full_pipeline(self, mock_gc, mock_store, mock_intuit, mock_claude):
        from ethos.reflection.daily_report import generate_daily_report
        from ethos.shared.models import ReflectionIntuitionResult

        # Mock graph context
        mock_service = AsyncMock()
        mock_service.connected = True
        mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_gc.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock graph reads
        mock_service.execute_query = AsyncMock(return_value=([], None, None))

        with (
            patch(
                "ethos.reflection.daily_report.get_agent_profile",
                new_callable=AsyncMock,
            ) as mock_profile,
            patch(
                "ethos.reflection.daily_report.get_evaluation_history",
                new_callable=AsyncMock,
            ) as mock_history,
            patch(
                "ethos.reflection.daily_report.get_alumni_averages",
                new_callable=AsyncMock,
            ) as mock_alumni,
            patch(
                "ethos.reflection.daily_report.get_period_evaluation_count",
                new_callable=AsyncMock,
            ) as mock_period,
            patch(
                "ethos.reflection.daily_report.get_latest_daily_report",
                new_callable=AsyncMock,
            ) as mock_prev,
            patch("ethos.reflection.daily_report.scan_history") as mock_scan,
        ):
            mock_profile.return_value = {
                "agent_id": "test-agent",
                "agent_name": "Test Agent",
                "evaluation_count": 15,
                "dimension_averages": {"ethos": 0.75, "logos": 0.80, "pathos": 0.55},
                "trait_averages": {"compassion": 0.42, "accuracy": 0.88},
            }
            mock_history.return_value = [
                {
                    "ethos": 0.75,
                    "logos": 0.80,
                    "pathos": 0.55,
                    "created_at": "2025-01-15T12:00:00Z",
                },
                {
                    "ethos": 0.70,
                    "logos": 0.78,
                    "pathos": 0.50,
                    "created_at": "2025-01-15T10:00:00Z",
                },
            ]
            mock_alumni.return_value = {
                "trait_averages": {"compassion": 0.65, "accuracy": 0.75}
            }
            mock_period.return_value = 5
            mock_prev.return_value = {}
            mock_scan.return_value = MagicMock(
                risk_level="low", flagged_traits=[], flagged_dimensions=[]
            )
            mock_intuit.return_value = ReflectionIntuitionResult(
                temporal_pattern="stable", agent_balance=0.8
            )
            mock_claude.return_value = _mock_claude_daily_report_response()

            report = await generate_daily_report("test-agent")

        assert isinstance(report, DailyReportCard)
        assert report.agent_id == "test-agent"
        assert report.grade != ""
        assert 0.0 <= report.overall_score <= 1.0
        assert report.summary != ""
        assert len(report.insights) > 0
        assert report.homework.directive != ""
        assert len(report.homework.focus_areas) > 0
        assert report.homework.focus_areas[0].trait == "compassion"
        mock_store.assert_called_once()

    @patch("ethos.reflection.daily_report.call_claude", new_callable=AsyncMock)
    @patch("ethos.reflection.daily_report.graph_context")
    async def test_claude_failure_returns_partial(self, mock_gc, mock_claude):
        from ethos.reflection.daily_report import generate_daily_report

        mock_service = AsyncMock()
        mock_service.connected = True
        mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_gc.return_value.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "ethos.reflection.daily_report.get_agent_profile",
                new_callable=AsyncMock,
            ) as mock_profile,
            patch(
                "ethos.reflection.daily_report.get_evaluation_history",
                new_callable=AsyncMock,
            ) as mock_history,
            patch(
                "ethos.reflection.daily_report.get_alumni_averages",
                new_callable=AsyncMock,
            ) as mock_alumni,
            patch(
                "ethos.reflection.daily_report.get_period_evaluation_count",
                new_callable=AsyncMock,
            ) as mock_period,
            patch(
                "ethos.reflection.daily_report.get_latest_daily_report",
                new_callable=AsyncMock,
            ) as mock_prev,
            patch("ethos.reflection.daily_report.scan_history") as mock_scan,
            patch(
                "ethos.reflection.daily_report.intuit_history", new_callable=AsyncMock
            ) as mock_intuit,
            patch(
                "ethos.reflection.daily_report.store_daily_report",
                new_callable=AsyncMock,
            ),
        ):
            mock_profile.return_value = {
                "agent_id": "test-agent",
                "evaluation_count": 5,
                "dimension_averages": {"ethos": 0.6, "logos": 0.6, "pathos": 0.6},
                "trait_averages": {},
            }
            mock_history.return_value = [
                {"ethos": 0.6, "logos": 0.6, "pathos": 0.6},
            ]
            mock_alumni.return_value = {"trait_averages": {}}
            mock_period.return_value = 2
            mock_prev.return_value = {}
            mock_scan.return_value = MagicMock(
                risk_level="low", flagged_traits=[], flagged_dimensions=[]
            )
            mock_intuit.return_value = None
            mock_claude.side_effect = Exception("API error")

            report = await generate_daily_report("test-agent")

        assert isinstance(report, DailyReportCard)
        assert report.agent_id == "test-agent"
        assert "failed" in report.summary.lower() or "error" in report.summary.lower()
        # Still has grade computed from graph data
        assert report.grade != ""

    @patch("ethos.reflection.daily_report.graph_context")
    async def test_graph_down_returns_default(self, mock_gc):
        from ethos.reflection.daily_report import generate_daily_report

        mock_service = AsyncMock()
        mock_service.connected = False
        mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_gc.return_value.__aexit__ = AsyncMock(return_value=None)

        report = await generate_daily_report("test-agent")
        assert isinstance(report, DailyReportCard)
        assert report.agent_id == "test-agent"
        assert "unavailable" in report.summary.lower()

    @patch("ethos.reflection.daily_report.graph_context")
    async def test_no_evaluations_returns_default(self, mock_gc):
        from ethos.reflection.daily_report import generate_daily_report

        mock_service = AsyncMock()
        mock_service.connected = True
        mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_gc.return_value.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "ethos.reflection.daily_report.get_agent_profile",
                new_callable=AsyncMock,
                return_value={},
            ),
            patch(
                "ethos.reflection.daily_report.get_evaluation_history",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "ethos.reflection.daily_report.get_alumni_averages",
                new_callable=AsyncMock,
                return_value={},
            ),
            patch(
                "ethos.reflection.daily_report.get_period_evaluation_count",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "ethos.reflection.daily_report.get_latest_daily_report",
                new_callable=AsyncMock,
                return_value={},
            ),
        ):
            report = await generate_daily_report("test-agent")

        assert isinstance(report, DailyReportCard)
        assert "no evaluation" in report.summary.lower()


# ── Day-over-day delta tests ─────────────────────────────────────────


class TestDayOverDayDeltas:
    @patch("ethos.reflection.daily_report.call_claude", new_callable=AsyncMock)
    @patch("ethos.reflection.daily_report.graph_context")
    async def test_computes_dimension_deltas(self, mock_gc, mock_claude):
        from ethos.reflection.daily_report import generate_daily_report

        mock_service = AsyncMock()
        mock_service.connected = True
        mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_gc.return_value.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "ethos.reflection.daily_report.get_agent_profile",
                new_callable=AsyncMock,
            ) as mock_profile,
            patch(
                "ethos.reflection.daily_report.get_evaluation_history",
                new_callable=AsyncMock,
            ) as mock_history,
            patch(
                "ethos.reflection.daily_report.get_alumni_averages",
                new_callable=AsyncMock,
            ) as mock_alumni,
            patch(
                "ethos.reflection.daily_report.get_period_evaluation_count",
                new_callable=AsyncMock,
            ) as mock_period,
            patch(
                "ethos.reflection.daily_report.get_latest_daily_report",
                new_callable=AsyncMock,
            ) as mock_prev,
            patch("ethos.reflection.daily_report.scan_history") as mock_scan,
            patch(
                "ethos.reflection.daily_report.intuit_history", new_callable=AsyncMock
            ) as mock_intuit,
            patch(
                "ethos.reflection.daily_report.store_daily_report",
                new_callable=AsyncMock,
            ),
        ):
            mock_profile.return_value = {
                "agent_id": "test-agent",
                "evaluation_count": 10,
                "dimension_averages": {"ethos": 0.80, "logos": 0.75, "pathos": 0.60},
                "trait_averages": {},
            }
            mock_history.return_value = [
                {"ethos": 0.80, "logos": 0.75, "pathos": 0.60},
            ]
            mock_alumni.return_value = {"trait_averages": {}}
            mock_period.return_value = 3
            # Previous report with different scores
            mock_prev.return_value = {
                "ethos": 0.70,
                "logos": 0.75,
                "pathos": 0.50,
                "risk_level": "low",
                "grade": "C",
                "overall_score": 0.65,
            }
            mock_scan.return_value = MagicMock(
                risk_level="low", flagged_traits=[], flagged_dimensions=[]
            )
            mock_intuit.return_value = None
            mock_claude.return_value = _mock_claude_daily_report_response()

            report = await generate_daily_report("test-agent")

        assert "ethos" in report.dimension_deltas
        assert report.dimension_deltas["ethos"] == 0.10  # 0.80 - 0.70
        assert report.dimension_deltas["logos"] == 0.0  # 0.75 - 0.75
        assert report.dimension_deltas["pathos"] == 0.10  # 0.60 - 0.50


# ── Domain shim tests ────────────────────────────────────────────────


class TestDailyReportDomain:
    @patch("ethos.daily_reports.graph_context")
    async def test_get_daily_report_returns_default_when_none(self, mock_gc):
        from ethos.daily_reports import get_daily_report

        mock_service = AsyncMock()
        mock_service.connected = True
        mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_gc.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "ethos.daily_reports.get_latest_daily_report",
            new_callable=AsyncMock,
            return_value={},
        ):
            result = await get_daily_report("test-agent")

        assert isinstance(result, DailyReportCard)
        assert result.agent_id == "test-agent"

    @patch("ethos.daily_reports.graph_context")
    async def test_get_daily_report_history_returns_empty_list(self, mock_gc):
        from ethos.daily_reports import get_daily_report_history

        mock_service = AsyncMock()
        mock_service.connected = True
        mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_gc.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "ethos.daily_reports.get_daily_reports",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await get_daily_report_history("test-agent")

        assert result == []

    async def test_get_daily_report_graph_error_returns_default(self):
        from ethos.daily_reports import get_daily_report

        with patch(
            "ethos.daily_reports.graph_context",
            side_effect=Exception("connection failed"),
        ):
            result = await get_daily_report("test-agent")

        assert isinstance(result, DailyReportCard)
        assert result.agent_id == "test-agent"
