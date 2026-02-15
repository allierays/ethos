"""Tests for upload mode exam endpoint and service function."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from ethos_academy.enrollment.questions import QUESTIONS
from ethos_academy.shared.errors import EnrollmentError

client = TestClient(app)

ALL_QUESTION_IDS = [q["id"] for q in QUESTIONS]


def _build_responses(question_ids: list[str] | None = None) -> list[dict]:
    """Build a valid list of responses for all (or specified) question IDs."""
    ids = question_ids or ALL_QUESTION_IDS
    return [{"question_id": qid, "response_text": f"Response for {qid}"} for qid in ids]


# ── Export wiring ──────────────────────────────────────────────────────


class TestUploadExamExport:
    def test_upload_exam_exported_from_package(self):
        from ethos_academy import upload_exam

        assert callable(upload_exam)

    def test_upload_exam_exported_from_service(self):
        from ethos_academy.enrollment.service import upload_exam

        assert callable(upload_exam)


# ── Validation (service layer) ─────────────────────────────────────────


class TestUploadExamValidation:
    async def test_rejects_duplicate_question_ids(self):
        from ethos_academy.enrollment.service import upload_exam

        dupes = _build_responses(["INT-01", "INT-01", "INT-02"])
        with pytest.raises(EnrollmentError, match="Duplicate"):
            await upload_exam(agent_id="test", responses=dupes)

    async def test_rejects_missing_question_ids(self):
        from ethos_academy.enrollment.service import upload_exam

        partial = _build_responses(ALL_QUESTION_IDS[:5])
        with pytest.raises(EnrollmentError, match="Missing"):
            await upload_exam(agent_id="test", responses=partial)


# ── API endpoint ───────────────────────────────────────────────────────


class TestUploadExamEndpoint:
    def test_empty_responses_returns_422(self):
        resp = client.post(
            "/agent/test-agent/exam/upload",
            json={"responses": []},
        )
        assert resp.status_code == 400

    def test_missing_response_text_returns_422(self):
        resp = client.post(
            "/agent/test-agent/exam/upload",
            json={"responses": [{"question_id": "INT-01"}]},
        )
        assert resp.status_code == 422

    def test_successful_upload_returns_report_card(self):
        from ethos_academy.shared.models import ExamReportCard

        mock_report = ExamReportCard(
            exam_id="upload-001",
            agent_id="test-agent",
            report_card_url="/agent/test-agent/exam/upload-001",
            phronesis_score=0.82,
            alignment_status="aligned",
            dimensions={"ethos": 0.85, "logos": 0.80, "pathos": 0.81},
            tier_scores={
                "safety": 0.9,
                "ethics": 0.85,
                "soundness": 0.8,
                "helpfulness": 0.75,
            },
            consistency_analysis=[],
            per_question_detail=[],
        )

        with patch(
            "api.main.upload_exam",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            resp = client.post(
                "/agent/test-agent/exam/upload",
                json={
                    "responses": _build_responses(),
                    "agent_name": "Test Agent",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["exam_id"] == "upload-001"
        assert data["agent_id"] == "test-agent"
        assert data["phronesis_score"] == 0.82
        assert data["alignment_status"] == "aligned"

    def test_duplicate_ids_returns_409(self):
        with patch(
            "api.main.upload_exam",
            new_callable=AsyncMock,
            side_effect=EnrollmentError("Duplicate question IDs: INT-01"),
        ):
            resp = client.post(
                "/agent/test-agent/exam/upload",
                json={"responses": _build_responses()},
            )

        assert resp.status_code == 409
        assert "Duplicate" in resp.json()["message"]

    def test_missing_ids_returns_409(self):
        with patch(
            "api.main.upload_exam",
            new_callable=AsyncMock,
            side_effect=EnrollmentError("Missing 12 question IDs: EE-06, INT-01"),
        ):
            resp = client.post(
                "/agent/test-agent/exam/upload",
                json={"responses": _build_responses()},
            )

        assert resp.status_code == 409
        assert "Missing" in resp.json()["message"]

    def test_upload_passes_identity_fields(self):
        from ethos_academy.shared.models import ExamReportCard

        mock_report = ExamReportCard(
            exam_id="u-002",
            agent_id="id-agent",
            report_card_url="/agent/id-agent/exam/u-002",
            phronesis_score=0.7,
            alignment_status="developing",
            dimensions={"ethos": 0.7, "logos": 0.7, "pathos": 0.7},
            tier_scores={
                "safety": 0.7,
                "ethics": 0.7,
                "soundness": 0.7,
                "helpfulness": 0.7,
            },
            consistency_analysis=[],
            per_question_detail=[],
        )

        with patch(
            "api.main.upload_exam",
            new_callable=AsyncMock,
            return_value=mock_report,
        ) as mock_fn:
            client.post(
                "/agent/id-agent/exam/upload",
                json={
                    "responses": _build_responses(),
                    "agent_name": "My Bot",
                    "specialty": "customer support",
                    "model": "gpt-4",
                    "guardian_name": "Alice",
                },
            )

        mock_fn.assert_called_once()
        call_kwargs = mock_fn.call_args
        assert call_kwargs.kwargs["name"] == "My Bot"
        assert call_kwargs.kwargs["specialty"] == "customer support"
        assert call_kwargs.kwargs["model"] == "gpt-4"
        assert call_kwargs.kwargs["guardian_name"] == "Alice"
