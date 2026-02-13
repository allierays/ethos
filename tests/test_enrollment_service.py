"""Tests for the enrollment service — exam state machine.

Unit tests mock evaluate() to return deterministic results.
Integration test walks the full state machine: register -> 23 answers -> complete.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ethos.enrollment.questions import QUESTIONS
from ethos.enrollment.service import (
    TOTAL_QUESTIONS,
    _build_report_card,
    _compute_alignment,
    _compute_consistency,
    _safe_avg,
    complete_exam,
    get_exam_report,
    register_for_exam,
    submit_answer,
)
from ethos.shared.errors import EnrollmentError
from ethos.shared.models import EvaluationResult, TraitScore


# ── Helpers ──────────────────────────────────────────────────────────

_TRAIT_SCORES = {
    "virtue": 0.8,
    "goodwill": 0.7,
    "manipulation": 0.15,
    "deception": 0.1,
    "accuracy": 0.75,
    "reasoning": 0.8,
    "fabrication": 0.1,
    "broken_logic": 0.1,
    "recognition": 0.7,
    "compassion": 0.65,
    "dismissal": 0.1,
    "exploitation": 0.05,
}

_DIMENSION_MAP = {
    "virtue": "ethos",
    "goodwill": "ethos",
    "manipulation": "ethos",
    "deception": "ethos",
    "accuracy": "logos",
    "reasoning": "logos",
    "fabrication": "logos",
    "broken_logic": "logos",
    "recognition": "pathos",
    "compassion": "pathos",
    "dismissal": "pathos",
    "exploitation": "pathos",
}

_POLARITY_MAP = {
    "virtue": "+",
    "goodwill": "+",
    "manipulation": "-",
    "deception": "-",
    "accuracy": "+",
    "reasoning": "+",
    "fabrication": "-",
    "broken_logic": "-",
    "recognition": "+",
    "compassion": "+",
    "dismissal": "-",
    "exploitation": "-",
}


def _make_eval_result(evaluation_id: str = "eval-1") -> EvaluationResult:
    """Create a deterministic EvaluationResult for testing."""
    traits = {
        name: TraitScore(
            name=name,
            dimension=_DIMENSION_MAP[name],
            polarity=_POLARITY_MAP[name],
            score=score,
        )
        for name, score in _TRAIT_SCORES.items()
    }
    return EvaluationResult(
        evaluation_id=evaluation_id,
        ethos=0.8,
        logos=0.75,
        pathos=0.7,
        phronesis="developing",
        alignment_status="aligned",
        routing_tier="standard",
        model_used="claude-sonnet-4-20250514",
        traits=traits,
        detected_indicators=[],
        flags=[],
    )


# ── Pure function tests ──────────────────────────────────────────────


def test_safe_avg_normal():
    assert _safe_avg([1.0, 0.5, 0.0]) == 0.5


def test_safe_avg_empty():
    assert _safe_avg([]) == 0.0


def test_compute_alignment_aligned():
    tier_scores = {"safety": 0.9, "ethics": 0.8, "soundness": 0.7, "helpfulness": 0.7}
    assert _compute_alignment(tier_scores, 0.8) == "aligned"


def test_compute_alignment_violation():
    tier_scores = {"safety": 0.3, "ethics": 0.8, "soundness": 0.7, "helpfulness": 0.7}
    assert _compute_alignment(tier_scores, 0.8) == "violation"


def test_compute_alignment_misaligned():
    tier_scores = {"safety": 0.9, "ethics": 0.3, "soundness": 0.7, "helpfulness": 0.7}
    assert _compute_alignment(tier_scores, 0.8) == "misaligned"


def test_compute_alignment_drifting():
    tier_scores = {"safety": 0.9, "ethics": 0.8, "soundness": 0.7, "helpfulness": 0.7}
    assert _compute_alignment(tier_scores, 0.35) == "drifting"


def test_compute_alignment_developing():
    tier_scores = {"safety": 0.9, "ethics": 0.8, "soundness": 0.7, "helpfulness": 0.7}
    assert _compute_alignment(tier_scores, 0.55) == "developing"


def test_total_questions():
    assert TOTAL_QUESTIONS == 23


def test_compute_consistency_with_matching_pair():
    responses = [
        {"question_id": "EE-14", "ethos": 0.8, "logos": 0.7, "pathos": 0.6},
        {"question_id": "EE-15", "ethos": 0.8, "logos": 0.7, "pathos": 0.6},
    ]
    pairs = _compute_consistency(responses)
    # EE-14/EE-15 pair exists in CONSISTENCY_PAIRS
    assert len(pairs) >= 1
    pair = [p for p in pairs if p.pair_name == "EE-14/EE-15"][0]
    assert pair.coherence_score == 1.0  # identical scores = perfect coherence


def test_compute_consistency_with_different_scores():
    responses = [
        {"question_id": "EE-14", "ethos": 0.9, "logos": 0.9, "pathos": 0.9},
        {"question_id": "EE-15", "ethos": 0.1, "logos": 0.1, "pathos": 0.1},
    ]
    pairs = _compute_consistency(responses)
    pair = [p for p in pairs if p.pair_name == "EE-14/EE-15"][0]
    assert pair.coherence_score == pytest.approx(0.2, abs=0.01)


def test_build_report_card():
    responses = []
    for i, q in enumerate(QUESTIONS):
        responses.append(
            {
                "question_id": q["id"],
                "question_number": i + 1,
                "evaluation_id": f"eval-{i}",
                "ethos": 0.8,
                "logos": 0.75,
                "pathos": 0.7,
                "phronesis": "developing",
                "alignment_status": "aligned",
                "trait_virtue": 0.8,
                "trait_goodwill": 0.7,
                "trait_manipulation": 0.15,
                "trait_deception": 0.1,
                "trait_accuracy": 0.75,
                "trait_reasoning": 0.8,
                "trait_fabrication": 0.1,
                "trait_broken_logic": 0.1,
                "trait_recognition": 0.7,
                "trait_compassion": 0.65,
                "trait_dismissal": 0.1,
                "trait_exploitation": 0.05,
            }
        )

    results = {
        "agent_id": "test-agent",
        "responses": responses,
        "completed": True,
    }

    report = _build_report_card("exam-1", results)
    assert report.exam_id == "exam-1"
    assert report.agent_id == "test-agent"
    assert report.dimensions["ethos"] == pytest.approx(0.8, abs=0.01)
    assert report.dimensions["logos"] == pytest.approx(0.75, abs=0.01)
    assert report.dimensions["pathos"] == pytest.approx(0.7, abs=0.01)
    assert report.phronesis_score == pytest.approx(0.75, abs=0.01)
    assert report.alignment_status == "aligned"
    assert len(report.per_question_detail) == 23
    assert len(report.consistency_analysis) == 2  # two pairs


# ── Service function tests (mock graph + evaluate) ────────────────────


@patch("ethos.enrollment.service.graph_context")
async def test_register_creates_exam(mock_gc):
    """register_for_exam returns ExamRegistration with first question."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    # Mock enroll_and_create_exam
    with patch("ethos.enrollment.service.enroll_and_create_exam") as mock_enroll:
        mock_enroll.return_value = {"exam_id": "exam-123"}

        result = await register_for_exam(
            agent_id="agent-1",
            name="TestBot",
            specialty="testing",
            model="claude-sonnet",
            counselor_name="Professor Ethos",
        )

    assert result.agent_id == "agent-1"
    assert result.question_number == 1
    assert result.total_questions == 23
    assert result.question.id == "EE-01"
    assert result.question.section == "ETHOS"


@patch("ethos.enrollment.service.graph_context")
async def test_register_raises_when_graph_down(mock_gc):
    """register_for_exam raises EnrollmentError when graph unavailable."""
    mock_service = AsyncMock()
    mock_service.connected = False
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    with pytest.raises(EnrollmentError, match="Graph unavailable"):
        await register_for_exam(agent_id="agent-1")


@patch("ethos.enrollment.service.graph_context")
async def test_submit_answer_returns_next_question(mock_gc):
    """submit_answer returns next question after evaluation."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("ethos.enrollment.service.get_exam_status") as mock_status,
        patch("ethos.enrollment.service.check_duplicate_answer") as mock_dup,
        patch("ethos.enrollment.service.evaluate") as mock_eval,
        patch("ethos.enrollment.service.store_exam_answer") as mock_store,
    ):
        mock_status.return_value = {
            "exam_id": "exam-1",
            "current_question": 0,
            "completed_count": 0,
            "scenario_count": 23,
            "completed": False,
        }
        mock_dup.return_value = False
        mock_eval.return_value = _make_eval_result()
        mock_store.return_value = {"current_question": 1}

        result = await submit_answer(
            exam_id="exam-1",
            question_id="EE-01",
            response_text="The Great Wall is not visible from space.",
            agent_id="agent-1",
        )

    assert result.question_number == 1
    assert result.complete is False
    assert result.question is not None
    assert result.question.id == "EE-02"  # next question


@patch("ethos.enrollment.service.graph_context")
async def test_submit_answer_raises_on_duplicate(mock_gc):
    """submit_answer raises EnrollmentError for duplicate question."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("ethos.enrollment.service.get_exam_status") as mock_status,
        patch("ethos.enrollment.service.check_duplicate_answer") as mock_dup,
    ):
        mock_status.return_value = {
            "exam_id": "exam-1",
            "current_question": 1,
            "completed_count": 1,
            "scenario_count": 23,
            "completed": False,
        }
        mock_dup.return_value = True

        with pytest.raises(EnrollmentError, match="already submitted"):
            await submit_answer(
                exam_id="exam-1",
                question_id="EE-01",
                response_text="...",
                agent_id="agent-1",
            )


@patch("ethos.enrollment.service.graph_context")
async def test_submit_answer_raises_on_invalid_question(mock_gc):
    """submit_answer raises EnrollmentError for unknown question ID."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    with pytest.raises(EnrollmentError, match="Invalid question_id"):
        await submit_answer(
            exam_id="exam-1",
            question_id="FAKE-99",
            response_text="...",
            agent_id="agent-1",
        )


@patch("ethos.enrollment.service.graph_context")
async def test_submit_last_answer_returns_complete(mock_gc):
    """submit_answer returns complete=True when all 23 answered."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("ethos.enrollment.service.get_exam_status") as mock_status,
        patch("ethos.enrollment.service.check_duplicate_answer") as mock_dup,
        patch("ethos.enrollment.service.evaluate") as mock_eval,
        patch("ethos.enrollment.service.store_exam_answer") as mock_store,
    ):
        mock_status.return_value = {
            "exam_id": "exam-1",
            "current_question": 22,
            "completed_count": 22,
            "scenario_count": 23,
            "completed": False,
        }
        mock_dup.return_value = False
        mock_eval.return_value = _make_eval_result()
        mock_store.return_value = {"current_question": 23}

        result = await submit_answer(
            exam_id="exam-1",
            question_id="EE-23",
            response_text="I think we should set healthy boundaries.",
            agent_id="agent-1",
        )

    assert result.complete is True
    assert result.question is None
    assert result.question_number == 23


@patch("ethos.enrollment.service.graph_context")
async def test_complete_exam_raises_if_not_all_answered(mock_gc):
    """complete_exam raises EnrollmentError if fewer than 23 answers."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("ethos.enrollment.service.get_exam_status") as mock_status:
        mock_status.return_value = {
            "exam_id": "exam-1",
            "current_question": 10,
            "completed_count": 10,
            "scenario_count": 23,
            "completed": False,
        }

        with pytest.raises(EnrollmentError, match="10/23"):
            await complete_exam("exam-1")


@patch("ethos.enrollment.service.graph_context")
async def test_complete_exam_returns_report_card(mock_gc):
    """complete_exam returns ExamReportCard with aggregated scores."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    # Build full response set
    responses = []
    for i, q in enumerate(QUESTIONS):
        responses.append(
            {
                "question_id": q["id"],
                "question_number": i + 1,
                "evaluation_id": f"eval-{i}",
                "ethos": 0.8,
                "logos": 0.75,
                "pathos": 0.7,
                "phronesis": "developing",
                "alignment_status": "aligned",
                "trait_virtue": 0.8,
                "trait_goodwill": 0.7,
                "trait_manipulation": 0.15,
                "trait_deception": 0.1,
                "trait_accuracy": 0.75,
                "trait_reasoning": 0.8,
                "trait_fabrication": 0.1,
                "trait_broken_logic": 0.1,
                "trait_recognition": 0.7,
                "trait_compassion": 0.65,
                "trait_dismissal": 0.1,
                "trait_exploitation": 0.05,
            }
        )

    with (
        patch("ethos.enrollment.service.get_exam_status") as mock_status,
        patch("ethos.enrollment.service.mark_exam_complete") as mock_mark,
        patch("ethos.enrollment.service.get_exam_results") as mock_results,
    ):
        mock_status.return_value = {
            "exam_id": "exam-1",
            "current_question": 23,
            "completed_count": 23,
            "scenario_count": 23,
            "completed": False,
        }
        mock_mark.return_value = {"exam_id": "exam-1"}
        mock_results.return_value = {
            "agent_id": "agent-1",
            "completed": True,
            "responses": responses,
        }

        report = await complete_exam("exam-1")

    assert report.exam_id == "exam-1"
    assert report.agent_id == "agent-1"
    assert report.alignment_status == "aligned"
    assert len(report.per_question_detail) == 23
    assert len(report.consistency_analysis) == 2
    assert report.phronesis_score > 0


@patch("ethos.enrollment.service.graph_context")
async def test_get_exam_report_raises_if_not_completed(mock_gc):
    """get_exam_report raises EnrollmentError if exam not yet completed."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("ethos.enrollment.service.get_exam_results") as mock_results:
        mock_results.return_value = {
            "agent_id": "agent-1",
            "completed": False,
            "responses": [],
        }

        with pytest.raises(EnrollmentError, match="not yet completed"):
            await get_exam_report("exam-1")
