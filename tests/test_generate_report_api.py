"""Tests for POST /agent/{agent_id}/report/generate endpoint.

Follows the same pattern as test_exam_api.py: TestClient, mock domain function,
verify HTTP status codes and JSON response structure.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from api.main import app
from ethos_academy.shared.errors import (
    ConfigError,
    EvaluationError,
    GraphUnavailableError,
)
from ethos_academy.shared.models import (
    DailyReportCard,
    Homework,
    HomeworkFocus,
    Insight,
)

client = TestClient(app)


def _mock_report_card(**overrides) -> DailyReportCard:
    defaults = {
        "report_id": "rpt-001",
        "agent_id": "test-agent",
        "agent_name": "Test Agent",
        "report_date": "2026-02-14",
        "generated_at": "2026-02-14T12:00:00+00:00",
        "period_evaluation_count": 5,
        "total_evaluation_count": 42,
        "ethos": 0.82,
        "logos": 0.75,
        "pathos": 0.68,
        "overall_score": 0.75,
        "grade": "B",
        "trend": "improving",
        "risk_level": "low",
        "summary": "Test Agent shows strong character development.",
        "insights": [
            Insight(
                trait="virtue",
                severity="info",
                message="Consistent honesty signals.",
            )
        ],
        "homework": Homework(
            focus_areas=[
                HomeworkFocus(
                    trait="accuracy",
                    priority="high",
                    current_score=0.65,
                    target_score=0.75,
                    instruction="Cite sources when making factual claims.",
                )
            ],
            avoid_patterns=["Overpromising on uncertain outcomes"],
            strengths=["Clear communication", "Honest uncertainty signals"],
            directive="Focus on improving factual accuracy this week.",
        ),
    }
    defaults.update(overrides)
    return DailyReportCard(**defaults)


class TestGenerateReport:
    def test_generate_returns_report_card(self):
        mock_report = _mock_report_card()

        with patch(
            "api.main.generate_daily_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            resp = client.post("/agent/test-agent/report/generate")

        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "test-agent"
        assert data["grade"] == "B"
        assert data["overall_score"] == 0.75
        assert data["summary"] == "Test Agent shows strong character development."
        assert len(data["insights"]) == 1
        assert data["insights"][0]["trait"] == "virtue"

    def test_generate_returns_homework(self):
        mock_report = _mock_report_card()

        with patch(
            "api.main.generate_daily_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            resp = client.post("/agent/test-agent/report/generate")

        data = resp.json()
        hw = data["homework"]
        assert len(hw["focus_areas"]) == 1
        assert hw["focus_areas"][0]["trait"] == "accuracy"
        assert hw["directive"] == "Focus on improving factual accuracy this week."
        assert "Overpromising" in hw["avoid_patterns"][0]

    def test_generate_passes_agent_id_to_domain(self):
        mock_report = _mock_report_card(agent_id="custom-agent")

        with patch(
            "api.main.generate_daily_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ) as mock_fn:
            resp = client.post("/agent/custom-agent/report/generate")

        assert resp.status_code == 200
        mock_fn.assert_called_once_with("custom-agent")

    def test_generate_config_error_invalid_key_returns_401(self):
        with patch(
            "api.main.generate_daily_report",
            new_callable=AsyncMock,
            side_effect=ConfigError("Invalid Anthropic API key"),
        ):
            resp = client.post("/agent/test-agent/report/generate")

        assert resp.status_code == 401
        data = resp.json()
        assert data["error"] == "ConfigError"

    def test_generate_evaluation_error_returns_422(self):
        with patch(
            "api.main.generate_daily_report",
            new_callable=AsyncMock,
            side_effect=EvaluationError("Claude API call failed"),
        ):
            resp = client.post("/agent/test-agent/report/generate")

        assert resp.status_code == 422
        data = resp.json()
        assert data["error"] == "EvaluationError"

    def test_generate_graph_unavailable_returns_503(self):
        with patch(
            "api.main.generate_daily_report",
            new_callable=AsyncMock,
            side_effect=GraphUnavailableError("Neo4j unreachable"),
        ):
            resp = client.post("/agent/test-agent/report/generate")

        assert resp.status_code == 503
        data = resp.json()
        assert data["error"] == "GraphUnavailableError"

    def test_generate_minimal_report_card(self):
        """Report with no evaluations returns minimal card."""
        minimal = DailyReportCard(
            agent_id="new-agent",
            report_date="2026-02-14",
            generated_at="2026-02-14T12:00:00+00:00",
            summary="No evaluation history found",
        )

        with patch(
            "api.main.generate_daily_report",
            new_callable=AsyncMock,
            return_value=minimal,
        ):
            resp = client.post("/agent/new-agent/report/generate")

        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "new-agent"
        assert data["grade"] == ""
        assert data["overall_score"] == 0.0
        assert data["summary"] == "No evaluation history found"
