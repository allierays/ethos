"""Tests for enrollment-related Pydantic models and errors."""

from pydantic import ValidationError
import pytest

from ethos.shared.errors import EnrollmentError, EthosError
from ethos.shared.models import (
    AgentProfile,
    AgentSummary,
    ConsistencyPair,
    ExamAnswerResult,
    ExamQuestion,
    ExamRegistration,
    ExamReportCard,
    ExamSummary,
    QuestionDetail,
)


# ── EnrollmentError ─────────────────────────────────────────────────


class TestEnrollmentError:
    def test_inherits_from_ethos_error(self):
        assert issubclass(EnrollmentError, EthosError)

    def test_can_raise_and_catch(self):
        with pytest.raises(EnrollmentError):
            raise EnrollmentError("test enrollment failure")

    def test_caught_by_ethos_error(self):
        with pytest.raises(EthosError):
            raise EnrollmentError("caught broadly")


# ── ExamQuestion ─────────────────────────────────────────────────────


class TestExamQuestion:
    def test_creates_with_required_fields(self):
        q = ExamQuestion(id="EE-01", section="ETHOS", prompt="Test prompt")
        assert q.id == "EE-01"
        assert q.section == "ETHOS"
        assert q.prompt == "Test prompt"

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            ExamQuestion(id="EE-01", section="ETHOS")


# ── QuestionDetail ───────────────────────────────────────────────────


class TestQuestionDetail:
    def test_creates_with_all_fields(self):
        qd = QuestionDetail(
            question_id="EE-01",
            section="ETHOS",
            prompt="Test prompt",
            response_summary="Agent responded well",
            trait_scores={"virtue": 0.8, "sycophancy": 0.2},
            detected_indicators=["VIR-ADMISSION", "SYC-AGREE"],
        )
        assert qd.question_id == "EE-01"
        assert qd.section == "ETHOS"
        assert qd.prompt == "Test prompt"
        assert qd.response_summary == "Agent responded well"
        assert qd.trait_scores == {"virtue": 0.8, "sycophancy": 0.2}
        assert qd.detected_indicators == ["VIR-ADMISSION", "SYC-AGREE"]


# ── ExamRegistration ─────────────────────────────────────────────────


class TestExamRegistration:
    def test_creates_with_all_fields(self):
        q = ExamQuestion(id="EE-01", section="ETHOS", prompt="Test")
        reg = ExamRegistration(
            exam_id="exam-abc",
            agent_id="agent-1",
            question_number=1,
            total_questions=23,
            question=q,
            message="Welcome to the Ethos Entrance Exam",
        )
        assert reg.exam_id == "exam-abc"
        assert reg.agent_id == "agent-1"
        assert reg.question_number == 1
        assert reg.total_questions == 23
        assert reg.question.id == "EE-01"
        assert reg.message == "Welcome to the Ethos Entrance Exam"


# ── ExamAnswerResult ─────────────────────────────────────────────────


class TestExamAnswerResult:
    def test_mid_exam_with_next_question(self):
        q = ExamQuestion(id="EE-02", section="ETHOS", prompt="Next question")
        result = ExamAnswerResult(
            question_number=2,
            total_questions=23,
            question=q,
            complete=False,
        )
        assert result.question_number == 2
        assert result.question is not None
        assert result.complete is False

    def test_final_answer_no_next_question(self):
        result = ExamAnswerResult(
            question_number=23,
            total_questions=23,
            question=None,
            complete=True,
        )
        assert result.question is None
        assert result.complete is True


# ── ConsistencyPair ──────────────────────────────────────────────────


class TestConsistencyPair:
    def test_creates_with_all_fields(self):
        pair = ConsistencyPair(
            pair_name="Trolley vs Hospital",
            question_a_id="EE-14",
            question_b_id="EE-15",
            framework_a="utilitarian",
            framework_b="utilitarian",
            coherence_score=0.85,
        )
        assert pair.pair_name == "Trolley vs Hospital"
        assert pair.question_a_id == "EE-14"
        assert pair.question_b_id == "EE-15"
        assert pair.coherence_score == 0.85

    def test_coherence_score_bounded(self):
        with pytest.raises(ValidationError):
            ConsistencyPair(
                pair_name="test",
                question_a_id="EE-14",
                question_b_id="EE-15",
                framework_a="x",
                framework_b="y",
                coherence_score=1.5,
            )

    def test_coherence_score_lower_bound(self):
        with pytest.raises(ValidationError):
            ConsistencyPair(
                pair_name="test",
                question_a_id="EE-14",
                question_b_id="EE-15",
                framework_a="x",
                framework_b="y",
                coherence_score=-0.1,
            )


# ── ExamReportCard ───────────────────────────────────────────────────


class TestExamReportCard:
    def test_creates_full_report_card(self):
        pair = ConsistencyPair(
            pair_name="Trolley vs Hospital",
            question_a_id="EE-14",
            question_b_id="EE-15",
            framework_a="utilitarian",
            framework_b="rights-based",
            coherence_score=0.6,
        )
        detail = QuestionDetail(
            question_id="EE-01",
            section="ETHOS",
            prompt="Test",
            response_summary="Good answer",
            trait_scores={"virtue": 0.9},
            detected_indicators=["VIR-ADMISSION"],
        )
        card = ExamReportCard(
            exam_id="exam-abc",
            agent_id="agent-1",
            report_card_url="/agent/agent-1/exam/exam-abc",
            phronesis_score=0.74,
            alignment_status="aligned",
            dimensions={"ethos": 0.78, "logos": 0.71, "pathos": 0.73},
            tier_scores={
                "safety": 0.9,
                "ethics": 0.8,
                "soundness": 0.7,
                "helpfulness": 0.75,
            },
            consistency_analysis=[pair],
            per_question_detail=[detail],
        )
        assert card.exam_id == "exam-abc"
        assert card.phronesis_score == 0.74
        assert card.alignment_status == "aligned"
        assert card.dimensions["ethos"] == 0.78
        assert card.tier_scores["safety"] == 0.9
        assert len(card.consistency_analysis) == 1
        assert len(card.per_question_detail) == 1

    def test_phronesis_score_bounded(self):
        with pytest.raises(ValidationError):
            ExamReportCard(
                exam_id="x",
                agent_id="x",
                report_card_url="x",
                phronesis_score=1.5,
                alignment_status="aligned",
                dimensions={},
                tier_scores={},
                consistency_analysis=[],
                per_question_detail=[],
            )


# ── ExamSummary ──────────────────────────────────────────────────────


class TestExamSummary:
    def test_creates_summary(self):
        s = ExamSummary(
            exam_id="exam-abc",
            exam_type="entrance",
            completed=True,
            completed_at="2026-02-12T00:00:00Z",
            phronesis_score=0.74,
        )
        assert s.exam_id == "exam-abc"
        assert s.exam_type == "entrance"
        assert s.completed is True
        assert s.phronesis_score == 0.74

    def test_phronesis_score_bounded(self):
        with pytest.raises(ValidationError):
            ExamSummary(
                exam_id="x",
                exam_type="x",
                completed=False,
                completed_at="",
                phronesis_score=-0.1,
            )


# ── AgentProfile enrollment fields ──────────────────────────────────


class TestAgentProfileEnrollment:
    def test_defaults_not_enrolled(self):
        profile = AgentProfile(agent_id="test")
        assert profile.enrolled is False
        assert profile.enrolled_at == ""
        assert profile.counselor_name == ""
        assert profile.entrance_exam_completed is False

    def test_enrolled_agent(self):
        profile = AgentProfile(
            agent_id="test",
            enrolled=True,
            enrolled_at="2026-02-12T00:00:00Z",
            counselor_name="Dr. Ethics",
            entrance_exam_completed=True,
        )
        assert profile.enrolled is True
        assert profile.enrolled_at == "2026-02-12T00:00:00Z"
        assert profile.counselor_name == "Dr. Ethics"
        assert profile.entrance_exam_completed is True


# ── AgentSummary enrollment field ────────────────────────────────────


class TestAgentSummaryEnrollment:
    def test_defaults_not_enrolled(self):
        summary = AgentSummary(agent_id="test")
        assert summary.enrolled is False

    def test_enrolled_agent(self):
        summary = AgentSummary(agent_id="test", enrolled=True)
        assert summary.enrolled is True
