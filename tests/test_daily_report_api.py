"""Tests for daily report API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from api.main import app
from ethos_academy.shared.models import (
    DailyReportCard,
    Homework,
    HomeworkFocus,
    Insight,
)

client = TestClient(app)


class TestCharacterEndpoint:
    """GET /agent/{agent_id}/character returns DailyReportCard."""

    def test_returns_daily_report_card(self):
        mock_report = DailyReportCard(
            report_id="rpt-001",
            agent_id="test-agent",
            agent_name="Test Agent",
            report_date="2025-01-15",
            grade="B",
            overall_score=0.72,
            ethos=0.80,
            logos=0.75,
            pathos=0.60,
            summary="Solid performance overall.",
            homework=Homework(
                directive="Focus on emotional awareness.",
                focus_areas=[
                    HomeworkFocus(
                        trait="compassion",
                        priority="high",
                        instruction="Acknowledge emotions before responding.",
                        current_score=0.45,
                        target_score=0.60,
                    )
                ],
                strengths=["accuracy", "reasoning"],
                avoid_patterns=["dismissal"],
            ),
            insights=[
                Insight(
                    trait="compassion",
                    severity="warning",
                    message="Below alumni average",
                )
            ],
        )

        with patch(
            "api.main.character_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            resp = client.get("/agent/test-agent/character")

        assert resp.status_code == 200
        data = resp.json()
        result = DailyReportCard(**data)
        assert result.agent_id == "test-agent"
        assert result.grade == "B"
        assert result.homework.directive == "Focus on emotional awareness."
        assert len(result.homework.focus_areas) == 1
        assert result.homework.focus_areas[0].trait == "compassion"

    def test_empty_default_when_no_reports(self):
        mock_report = DailyReportCard(agent_id="unknown-agent")

        with patch(
            "api.main.character_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            resp = client.get("/agent/unknown-agent/character")

        assert resp.status_code == 200
        data = resp.json()
        result = DailyReportCard(**data)
        assert result.agent_id == "unknown-agent"
        assert result.grade == ""
        assert result.homework.directive == ""


class TestReportsEndpoint:
    """GET /agent/{agent_id}/reports returns list[DailyReportCard]."""

    def test_returns_report_list(self):
        mock_reports = [
            DailyReportCard(
                agent_id="test-agent",
                report_date="2025-01-15",
                grade="B",
                overall_score=0.72,
            ),
            DailyReportCard(
                agent_id="test-agent",
                report_date="2025-01-14",
                grade="C",
                overall_score=0.58,
            ),
        ]

        with patch(
            "api.main.get_daily_report_history",
            new_callable=AsyncMock,
            return_value=mock_reports,
        ):
            resp = client.get("/agent/test-agent/reports")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["grade"] == "B"
        assert data[1]["grade"] == "C"

    def test_returns_empty_list(self):
        with patch(
            "api.main.get_daily_report_history",
            new_callable=AsyncMock,
            return_value=[],
        ):
            resp = client.get("/agent/nonexistent/reports")

        assert resp.status_code == 200
        data = resp.json()
        assert data == []

    def test_limit_parameter(self):
        with patch(
            "api.main.get_daily_report_history",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_fn:
            resp = client.get("/agent/test-agent/reports?limit=7")

        assert resp.status_code == 200
        mock_fn.assert_called_once_with("test-agent", limit=7)
