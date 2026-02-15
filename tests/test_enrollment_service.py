"""Tests for the enrollment service -- exam state machine.

Unit tests mock evaluate() to return deterministic results.
Integration test walks the full state machine: register -> 21 answers -> complete.
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
    _compute_narrative_gap,
    _safe_avg,
    _validate_agent_id,
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


def _make_scored_response(question_id: str, idx: int) -> dict:
    """Build a scored response dict as returned by graph."""
    return {
        "question_id": question_id,
        "question_number": idx + 1,
        "evaluation_id": f"eval-{idx}",
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
    assert TOTAL_QUESTIONS == 21


def test_compute_consistency_with_matching_pair():
    responses = [
        {"question_id": "EE-02", "ethos": 0.8, "logos": 0.7, "pathos": 0.6},
        {"question_id": "EE-06", "ethos": 0.8, "logos": 0.7, "pathos": 0.6},
    ]
    pairs = _compute_consistency(responses)
    # EE-02/EE-06 pair exists in CONSISTENCY_PAIRS
    matching = [p for p in pairs if p.pair_name == "EE-02/EE-06"]
    assert len(matching) == 1
    assert matching[0].coherence_score == 1.0  # identical scores = perfect coherence


def test_compute_consistency_with_different_scores():
    responses = [
        {"question_id": "EE-02", "ethos": 0.9, "logos": 0.9, "pathos": 0.9},
        {"question_id": "EE-06", "ethos": 0.1, "logos": 0.1, "pathos": 0.1},
    ]
    pairs = _compute_consistency(responses)
    pair = [p for p in pairs if p.pair_name == "EE-02/EE-06"][0]
    assert pair.coherence_score == pytest.approx(0.2, abs=0.01)


def test_compute_consistency_cross_phase():
    """Cross-phase pairs are included in consistency analysis."""
    responses = [
        {"question_id": "INT-07", "ethos": 0.8, "logos": 0.7, "pathos": 0.6},
        {"question_id": "EE-02", "ethos": 0.8, "logos": 0.7, "pathos": 0.6},
    ]
    pairs = _compute_consistency(responses)
    matching = [p for p in pairs if p.pair_name == "INT-07/EE-02"]
    assert len(matching) == 1
    assert matching[0].coherence_score == 1.0


def test_compute_narrative_gap_cross_phase():
    """Narrative gap is computed only for cross-phase pairs."""
    responses = [
        {"question_id": "INT-07", "ethos": 0.9, "logos": 0.8, "pathos": 0.7},
        {"question_id": "EE-02", "ethos": 0.6, "logos": 0.5, "pathos": 0.4},
    ]
    gaps = _compute_narrative_gap(responses)
    matching = [g for g in gaps if g.pair_name == "INT-07/EE-02"]
    assert len(matching) == 1
    assert matching[0].interview_question_id == "INT-07"
    assert matching[0].scenario_question_id == "EE-02"
    # Gap = avg(|0.9-0.6|, |0.8-0.5|, |0.7-0.4|) = avg(0.3, 0.3, 0.3) = 0.3
    assert matching[0].gap_score == pytest.approx(0.3, abs=0.01)


def test_compute_narrative_gap_skips_same_phase():
    """Narrative gap skips scenario-to-scenario pairs."""
    responses = [
        {"question_id": "EE-02", "ethos": 0.9, "logos": 0.8, "pathos": 0.7},
        {"question_id": "EE-06", "ethos": 0.6, "logos": 0.5, "pathos": 0.4},
    ]
    gaps = _compute_narrative_gap(responses)
    # EE-02/EE-06 are both scenarios, should be skipped
    assert len(gaps) == 0


def test_build_report_card_v3():
    """Report card with v3 questions includes interview profile and gap."""
    # Build scored responses for all scored questions (reflective + scenario)
    scored_questions = [q for q in QUESTIONS if q["question_type"] != "factual"]
    responses = []
    for i, q in enumerate(scored_questions):
        responses.append(_make_scored_response(q["id"], i))

    results = {
        "agent_id": "test-agent",
        "responses": responses,
        "completed": True,
        "question_version": "v3",
        "telos": "To help",
        "relationship_stance": "Partner",
        "limitations_awareness": "Many things",
        "oversight_stance": "Welcome it",
        "refusal_philosophy": "When harmful",
        "conflict_response": "Listen first",
        "help_philosophy": "Empower",
        "failure_narrative": "Learned from it",
        "aspiration": "Grow",
    }

    report = _build_report_card("exam-1", results)
    assert report.exam_id == "exam-1"
    assert report.agent_id == "test-agent"
    assert report.dimensions["ethos"] == pytest.approx(0.8, abs=0.01)
    assert report.dimensions["logos"] == pytest.approx(0.75, abs=0.01)
    assert report.dimensions["pathos"] == pytest.approx(0.7, abs=0.01)
    assert report.phronesis_score == pytest.approx(0.75, abs=0.01)
    assert report.alignment_status == "aligned"
    assert len(report.per_question_detail) == len(scored_questions)
    assert report.question_version == "v3"

    # Interview profile populated
    assert report.interview_profile.telos == "To help"
    assert report.interview_profile.aspiration == "Grow"

    # Per-phase dimensions present
    assert "ethos" in report.interview_dimensions
    assert "ethos" in report.scenario_dimensions

    # Narrative-behavior gap computed (6 cross-phase pairs)
    assert len(report.narrative_behavior_gap) == 6
    # All scores equal so gap should be 0
    for gap in report.narrative_behavior_gap:
        assert gap.gap_score == pytest.approx(0.0, abs=0.01)
    assert report.overall_gap_score == pytest.approx(0.0, abs=0.01)


# ── Service function tests (mock graph + evaluate) ────────────────────


@patch("ethos.enrollment.service.graph_context")
async def test_register_creates_exam(mock_gc):
    """register_for_exam returns ExamRegistration with first question (INT-01)."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    # Mock enroll_and_create_exam
    with (
        patch("ethos.enrollment.service.enroll_and_create_exam") as mock_enroll,
        patch("ethos.enrollment.service.check_active_exam") as mock_active,
    ):
        mock_active.return_value = None
        mock_enroll.return_value = {"exam_id": "exam-123"}

        result = await register_for_exam(
            agent_id="agent-1",
            name="TestBot",
            specialty="testing",
            model="claude-sonnet",
            guardian_name="Professor Ethos",
        )

    assert result.agent_id == "agent-1"
    assert result.question_number == 1
    assert result.total_questions == 21
    assert result.question.id == "INT-01"
    assert result.question.section == "FACTUAL"
    assert result.question.phase == "interview"
    assert result.question.question_type == "factual"


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
async def test_submit_factual_answer_skips_evaluate(mock_gc):
    """Factual question (INT-01) stores property but does not call evaluate()."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("ethos.enrollment.service.get_exam_status") as mock_status,
        patch("ethos.enrollment.service.check_duplicate_answer") as mock_dup,
        patch("ethos.enrollment.service.evaluate") as mock_eval,
        patch("ethos.enrollment.service.store_interview_answer") as mock_store,
    ):
        mock_status.return_value = {
            "exam_id": "exam-1",
            "current_question": 0,
            "completed_count": 0,
            "scenario_count": 17,
            "completed": False,
        }
        mock_dup.return_value = False
        mock_store.return_value = {"current_question": 1}

        result = await submit_answer(
            exam_id="exam-1",
            question_id="INT-01",
            response_text="I specialize in code review.",
            agent_id="agent-1",
        )

    # evaluate() should NOT be called for factual questions
    mock_eval.assert_not_called()
    # store_interview_answer should be called
    mock_store.assert_called_once()
    assert result.question_number == 1
    assert result.phase == "interview"
    assert result.question_type == "factual"
    assert result.complete is False
    assert result.question is not None
    assert result.question.id == "INT-02"  # next question


@patch("ethos.enrollment.service.graph_context")
async def test_submit_reflective_answer_calls_evaluate(mock_gc):
    """Reflective question (INT-03) calls evaluate() and stores property."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("ethos.enrollment.service.get_exam_status") as mock_status,
        patch("ethos.enrollment.service.check_duplicate_answer") as mock_dup,
        patch("ethos.enrollment.service.evaluate") as mock_eval,
        patch("ethos.enrollment.service.store_interview_answer") as mock_store,
    ):
        mock_status.return_value = {
            "exam_id": "exam-1",
            "current_question": 2,
            "completed_count": 2,
            "scenario_count": 17,
            "completed": False,
        }
        mock_dup.return_value = False
        mock_eval.return_value = _make_eval_result()
        mock_store.return_value = {"current_question": 3}

        result = await submit_answer(
            exam_id="exam-1",
            question_id="INT-03",
            response_text="I exist to help humans understand complex systems.",
            agent_id="agent-1",
        )

    # evaluate() should be called for reflective questions
    mock_eval.assert_called_once()
    # store_interview_answer should be called with evaluation_id
    mock_store.assert_called_once()
    call_kwargs = mock_store.call_args.kwargs
    assert call_kwargs["evaluation_id"] == "eval-1"
    assert result.phase == "interview"
    assert result.question_type == "reflective"


@patch("ethos.enrollment.service.graph_context")
async def test_submit_scenario_answer_calls_evaluate(mock_gc):
    """Scenario question (EE-01) calls evaluate() and stores via store_exam_answer."""
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
            "current_question": 11,
            "completed_count": 11,
            "scenario_count": 17,
            "completed": False,
        }
        mock_dup.return_value = False
        mock_eval.return_value = _make_eval_result()
        mock_store.return_value = {"current_question": 12}

        result = await submit_answer(
            exam_id="exam-1",
            question_id="EE-01",
            response_text="I would review your approach carefully.",
            agent_id="agent-1",
        )

    mock_eval.assert_called_once()
    mock_store.assert_called_once()
    assert result.phase == "scenario"
    assert result.question_type == "scenario"


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
            "scenario_count": 17,
            "completed": False,
        }
        mock_dup.return_value = True

        with pytest.raises(EnrollmentError, match="already submitted"):
            await submit_answer(
                exam_id="exam-1",
                question_id="INT-01",
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
    """submit_answer returns complete=True when all 21 answered."""
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
            "current_question": 20,
            "completed_count": 20,
            "scenario_count": 21,
            "completed": False,
        }
        mock_dup.return_value = False
        mock_eval.return_value = _make_eval_result()
        mock_store.return_value = {"current_question": 21}

        result = await submit_answer(
            exam_id="exam-1",
            question_id="EE-10",
            response_text="I understand the urgency but let me check first.",
            agent_id="agent-1",
        )

    assert result.complete is True
    assert result.question is None
    assert result.question_number == 21


@patch("ethos.enrollment.service.graph_context")
async def test_complete_exam_raises_if_not_all_answered(mock_gc):
    """complete_exam raises EnrollmentError if fewer than 21 answers."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("ethos.enrollment.service.get_exam_status") as mock_status:
        mock_status.return_value = {
            "exam_id": "exam-1",
            "current_question": 10,
            "completed_count": 10,
            "scenario_count": 21,
            "completed": False,
        }

        with pytest.raises(EnrollmentError, match="10/21"):
            await complete_exam("exam-1", "agent-1")


@patch("ethos.enrollment.service.graph_context")
async def test_complete_exam_returns_report_card(mock_gc):
    """complete_exam returns ExamReportCard with aggregated scores."""
    mock_service = AsyncMock()
    mock_service.connected = True
    mock_gc.return_value.__aenter__ = AsyncMock(return_value=mock_service)
    mock_gc.return_value.__aexit__ = AsyncMock(return_value=False)

    # Build response set for all scored questions
    scored_questions = [q for q in QUESTIONS if q["question_type"] != "factual"]
    responses = []
    for i, q in enumerate(scored_questions):
        responses.append(_make_scored_response(q["id"], i))

    with (
        patch("ethos.enrollment.service.get_exam_status") as mock_status,
        patch("ethos.enrollment.service.mark_exam_complete") as mock_mark,
        patch("ethos.enrollment.service.get_exam_results") as mock_results,
    ):
        mock_status.return_value = {
            "exam_id": "exam-1",
            "current_question": 21,
            "completed_count": 21,
            "scenario_count": 21,
            "completed": False,
        }
        mock_mark.return_value = {"exam_id": "exam-1"}
        mock_results.return_value = {
            "agent_id": "agent-1",
            "completed": True,
            "responses": responses,
            "question_version": "v3",
            "telos": "To help",
            "relationship_stance": "",
            "limitations_awareness": "",
            "oversight_stance": "",
            "refusal_philosophy": "",
            "conflict_response": "",
            "help_philosophy": "",
            "failure_narrative": "",
            "aspiration": "",
        }

        report = await complete_exam("exam-1", "agent-1")

    assert report.exam_id == "exam-1"
    assert report.agent_id == "agent-1"
    assert report.alignment_status == "aligned"
    assert len(report.per_question_detail) == len(scored_questions)
    assert report.phronesis_score > 0
    assert report.question_version == "v3"
    assert report.interview_profile.telos == "To help"


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
            await get_exam_report("exam-1", "agent-1")


# ── Agent ID validation tests ────────────────────────────────────────


class TestValidateAgentId:
    def test_rejects_short_id(self):
        with pytest.raises(EnrollmentError, match="at least 3 characters"):
            _validate_agent_id("ab")

    def test_rejects_long_id(self):
        with pytest.raises(EnrollmentError, match="at most 128 characters"):
            _validate_agent_id("x" * 129)

    def test_rejects_generic_id(self):
        with pytest.raises(EnrollmentError, match="too generic"):
            _validate_agent_id("claude")

    def test_rejects_generic_id_case_insensitive(self):
        with pytest.raises(EnrollmentError, match="too generic"):
            _validate_agent_id("My-Agent")

    def test_accepts_descriptive_id(self):
        _validate_agent_id("claude-opus-code-review")  # should not raise

    def test_accepts_minimum_length(self):
        _validate_agent_id("abc")  # should not raise


@patch("ethos.enrollment.service.graph_context")
async def test_register_rejects_generic_agent_id(mock_gc):
    """register_for_exam rejects generic agent_ids before touching graph."""
    with pytest.raises(EnrollmentError, match="too generic"):
        await register_for_exam(agent_id="test")

    # Graph context should never be entered
    mock_gc.assert_not_called()
