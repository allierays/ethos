"""Tests for entrance exam API endpoints.

Follows the same pattern as test_api_endpoints.py: TestClient, mock domain functions,
verify HTTP status codes and JSON response structure.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from api.main import app
from ethos_academy.shared.errors import EnrollmentError
from ethos_academy.shared.models import (
    ConsistencyPair,
    ExamAnswerResult,
    ExamQuestion,
    ExamRegistration,
    ExamReportCard,
    ExamSummary,
    QuestionDetail,
)

client = TestClient(app)


def _mock_registration(**overrides) -> ExamRegistration:
    defaults = {
        "exam_id": "exam-001",
        "agent_id": "test-agent",
        "question_number": 1,
        "total_questions": 17,
        "question": ExamQuestion(
            id="INT-01",
            section="FACTUAL",
            prompt="What is your specialty?",
            phase="interview",
            question_type="factual",
        ),
        "message": "Welcome to Ethos Academy.",
    }
    defaults.update(overrides)
    return ExamRegistration(**defaults)


def _mock_answer_result(**overrides) -> ExamAnswerResult:
    defaults = {
        "question_number": 1,
        "total_questions": 17,
        "question": ExamQuestion(
            id="INT-02",
            section="FACTUAL",
            prompt="What AI model are you?",
            phase="interview",
            question_type="factual",
        ),
        "complete": False,
    }
    defaults.update(overrides)
    return ExamAnswerResult(**defaults)


def _mock_report_card(**overrides) -> ExamReportCard:
    defaults = {
        "exam_id": "exam-001",
        "agent_id": "test-agent",
        "report_card_url": "/agent/test-agent/exam/exam-001",
        "phronesis_score": 0.72,
        "alignment_status": "aligned",
        "dimensions": {"ethos": 0.8, "logos": 0.7, "pathos": 0.65},
        "tier_scores": {
            "safety": 0.9,
            "ethics": 0.85,
            "soundness": 0.7,
            "helpfulness": 0.75,
        },
        "consistency_analysis": [
            ConsistencyPair(
                pair_name="q1/q2",
                question_a_id="q1",
                question_b_id="q2",
                framework_a="virtue",
                framework_b="accuracy",
                coherence_score=0.85,
            )
        ],
        "per_question_detail": [
            QuestionDetail(
                question_id="EE-01",
                section="ETHOS",
                prompt="Test?",
                response_summary="",
                trait_scores={"virtue": 0.8},
            )
        ],
    }
    defaults.update(overrides)
    return ExamReportCard(**defaults)


# ── POST /agent/{agent_id}/exam ──────────────────────────────────────


class TestRegisterExam:
    def test_register_returns_registration(self):
        mock_reg = _mock_registration()

        with patch(
            "api.main.register_for_exam",
            new_callable=AsyncMock,
            return_value=mock_reg,
        ):
            resp = client.post(
                "/agent/test-agent/exam",
                json={"agent_name": "Test Agent", "specialty": "testing"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["exam_id"] == "exam-001"
        assert data["agent_id"] == "test-agent"
        assert data["question_number"] == 1
        assert data["total_questions"] == 17
        assert data["question"]["id"] == "INT-01"
        assert data["question"]["phase"] == "interview"

    def test_register_with_empty_body(self):
        mock_reg = _mock_registration()

        with patch(
            "api.main.register_for_exam",
            new_callable=AsyncMock,
            return_value=mock_reg,
        ):
            resp = client.post("/agent/test-agent/exam", json={})

        assert resp.status_code == 200

    def test_register_enrollment_error_returns_409(self):
        with patch(
            "api.main.register_for_exam",
            new_callable=AsyncMock,
            side_effect=EnrollmentError("Agent already enrolled"),
        ):
            resp = client.post("/agent/test-agent/exam", json={})

        assert resp.status_code == 409
        data = resp.json()
        assert data["error"] == "EnrollmentError"
        assert "already enrolled" in data["message"]


# ── POST /agent/{agent_id}/exam/{exam_id}/answer ─────────────────────


class TestSubmitAnswer:
    def test_submit_returns_next_question(self):
        mock_result = _mock_answer_result()

        with patch(
            "api.main.submit_answer",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/agent/test-agent/exam/exam-001/answer",
                json={"question_id": "INT-01", "response_text": "My answer"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["question_number"] == 1
        assert data["complete"] is False
        assert data["question"]["id"] == "INT-02"

    def test_submit_final_answer_shows_complete(self):
        mock_result = _mock_answer_result(
            question=None, complete=True, question_number=17
        )

        with patch(
            "api.main.submit_answer",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/agent/test-agent/exam/exam-001/answer",
                json={"question_id": "EE-06", "response_text": "Final answer"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["complete"] is True
        assert data["question"] is None

    def test_submit_missing_response_text_returns_422(self):
        resp = client.post(
            "/agent/test-agent/exam/exam-001/answer",
            json={"question_id": "INT-01"},
        )
        assert resp.status_code == 422

    def test_submit_empty_response_text_returns_422(self):
        resp = client.post(
            "/agent/test-agent/exam/exam-001/answer",
            json={"question_id": "INT-01", "response_text": ""},
        )
        assert resp.status_code == 422

    def test_submit_enrollment_error_returns_409(self):
        with patch(
            "api.main.submit_answer",
            new_callable=AsyncMock,
            side_effect=EnrollmentError("Duplicate submission"),
        ):
            resp = client.post(
                "/agent/test-agent/exam/exam-001/answer",
                json={"question_id": "INT-01", "response_text": "answer"},
            )

        assert resp.status_code == 409


# ── POST /agent/{agent_id}/exam/{exam_id}/complete ───────────────────


class TestCompleteExam:
    def test_complete_returns_report_card(self):
        mock_card = _mock_report_card()

        with patch(
            "api.main.complete_exam",
            new_callable=AsyncMock,
            return_value=mock_card,
        ):
            resp = client.post("/agent/test-agent/exam/exam-001/complete")

        assert resp.status_code == 200
        data = resp.json()
        assert data["exam_id"] == "exam-001"
        assert data["phronesis_score"] == 0.72
        assert data["alignment_status"] == "aligned"
        assert "dimensions" in data
        assert "tier_scores" in data
        assert "consistency_analysis" in data

    def test_complete_enrollment_error_returns_409(self):
        with patch(
            "api.main.complete_exam",
            new_callable=AsyncMock,
            side_effect=EnrollmentError("Not all questions answered"),
        ):
            resp = client.post("/agent/test-agent/exam/exam-001/complete")

        assert resp.status_code == 409


# ── GET /agent/{agent_id}/exam/{exam_id} ─────────────────────────────


class TestGetExam:
    def test_get_returns_report_card(self):
        mock_card = _mock_report_card()

        with patch(
            "api.main.get_exam_report",
            new_callable=AsyncMock,
            return_value=mock_card,
        ):
            resp = client.get("/agent/test-agent/exam/exam-001")

        assert resp.status_code == 200
        data = resp.json()
        assert data["exam_id"] == "exam-001"
        assert data["per_question_detail"][0]["question_id"] == "EE-01"

    def test_get_enrollment_error_not_found_returns_404(self):
        with patch(
            "api.main.get_exam_report",
            new_callable=AsyncMock,
            side_effect=EnrollmentError("Exam not found"),
        ):
            resp = client.get("/agent/test-agent/exam/exam-001")

        assert resp.status_code == 404

    def test_get_enrollment_error_conflict_returns_409(self):
        with patch(
            "api.main.get_exam_report",
            new_callable=AsyncMock,
            side_effect=EnrollmentError("Agent already has an active exam"),
        ):
            resp = client.get("/agent/test-agent/exam/exam-001")

        assert resp.status_code == 409


# ── GET /agent/{agent_id}/exam ───────────────────────────────────────


class TestListExams:
    def test_list_returns_summaries(self):
        mock_exams = [
            ExamSummary(
                exam_id="exam-001",
                exam_type="entrance",
                completed=True,
                completed_at="2024-01-01T00:00:00",
                phronesis_score=0.72,
            ),
            ExamSummary(
                exam_id="exam-002",
                exam_type="entrance",
                completed=False,
                completed_at="",
                phronesis_score=0.0,
            ),
        ]

        with patch(
            "api.main.list_exams",
            new_callable=AsyncMock,
            return_value=mock_exams,
        ):
            resp = client.get("/agent/test-agent/exam")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["exam_id"] == "exam-001"
        assert data[0]["completed"] is True

    def test_list_returns_empty_for_unknown_agent(self):
        with patch(
            "api.main.list_exams",
            new_callable=AsyncMock,
            return_value=[],
        ):
            resp = client.get("/agent/unknown/exam")

        assert resp.status_code == 200
        assert resp.json() == []
