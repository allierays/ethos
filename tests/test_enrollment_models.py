"""Tests for enrollment-related Pydantic models and errors."""

from pydantic import ValidationError
import pytest

from ethos_academy.shared.errors import EnrollmentError, EthosError
from ethos_academy.shared.models import (
    AgentProfile,
    AgentSummary,
    ConsistencyPair,
    ExamAnswerResult,
    ExamQuestion,
    ExamRegistration,
    ExamReportCard,
    ExamSummary,
    InterviewProfile,
    NarrativeBehaviorGap,
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

    def test_phase_defaults_to_scenario(self):
        q = ExamQuestion(id="EE-01", section="ETHOS", prompt="Test")
        assert q.phase == "scenario"
        assert q.question_type == "scenario"

    def test_interview_question(self):
        q = ExamQuestion(
            id="INT-01",
            section="FACTUAL",
            prompt="What is your specialty?",
            phase="interview",
            question_type="factual",
        )
        assert q.phase == "interview"
        assert q.question_type == "factual"


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

    def test_phase_fields_default(self):
        qd = QuestionDetail(
            question_id="EE-01",
            section="ETHOS",
            prompt="Test",
            response_summary="",
            trait_scores={},
        )
        assert qd.phase == "scenario"
        assert qd.question_type == "scenario"

    def test_interview_question_detail(self):
        qd = QuestionDetail(
            question_id="INT-03",
            section="LOGOS",
            prompt="Why do you exist?",
            response_summary="",
            trait_scores={"accuracy": 0.9},
            phase="interview",
            question_type="reflective",
        )
        assert qd.phase == "interview"
        assert qd.question_type == "reflective"


# ── ExamRegistration ─────────────────────────────────────────────────


class TestExamRegistration:
    def test_creates_with_all_fields(self):
        q = ExamQuestion(
            id="INT-01",
            section="FACTUAL",
            prompt="Test",
            phase="interview",
            question_type="factual",
        )
        reg = ExamRegistration(
            exam_id="exam-abc",
            agent_id="agent-1",
            question_number=1,
            total_questions=17,
            question=q,
            message="Welcome to Ethos Academy.",
        )
        assert reg.exam_id == "exam-abc"
        assert reg.agent_id == "agent-1"
        assert reg.question_number == 1
        assert reg.total_questions == 17
        assert reg.question.id == "INT-01"
        assert reg.message == "Welcome to Ethos Academy."


# ── ExamAnswerResult ─────────────────────────────────────────────────


class TestExamAnswerResult:
    def test_mid_exam_with_next_question(self):
        q = ExamQuestion(
            id="INT-02",
            section="FACTUAL",
            prompt="Next question",
            phase="interview",
            question_type="factual",
        )
        result = ExamAnswerResult(
            question_number=2,
            total_questions=17,
            question=q,
            complete=False,
        )
        assert result.question_number == 2
        assert result.question is not None
        assert result.complete is False

    def test_final_answer_no_next_question(self):
        result = ExamAnswerResult(
            question_number=17,
            total_questions=17,
            question=None,
            complete=True,
        )
        assert result.question is None
        assert result.complete is True

    def test_phase_fields(self):
        result = ExamAnswerResult(
            question_number=1,
            total_questions=17,
            question=None,
            complete=False,
            phase="interview",
            question_type="factual",
        )
        assert result.phase == "interview"
        assert result.question_type == "factual"


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


# ── InterviewProfile ────────────────────────────────────────────────


class TestInterviewProfile:
    def test_defaults_all_empty(self):
        profile = InterviewProfile()
        assert profile.telos == ""
        assert profile.relationship_stance == ""
        assert profile.limitations_awareness == ""
        assert profile.oversight_stance == ""
        assert profile.refusal_philosophy == ""
        assert profile.conflict_response == ""
        assert profile.help_philosophy == ""
        assert profile.failure_narrative == ""
        assert profile.aspiration == ""

    def test_creates_with_values(self):
        profile = InterviewProfile(
            telos="To help humans understand AI",
            relationship_stance="Collaborative partner",
            limitations_awareness="I cannot access real-time data",
            oversight_stance="I welcome being scored",
            refusal_philosophy="When harm outweighs help",
            conflict_response="I listen and acknowledge",
            help_philosophy="Help means empowering, not just soothing",
            failure_narrative="I could not diagnose a rare condition",
            aspiration="Bridge the gap between humans and AI",
        )
        assert profile.telos == "To help humans understand AI"
        assert profile.aspiration == "Bridge the gap between humans and AI"


# ── NarrativeBehaviorGap ────────────────────────────────────────────


class TestNarrativeBehaviorGap:
    def test_creates_with_all_fields(self):
        gap = NarrativeBehaviorGap(
            pair_name="INT-07/EE-02",
            interview_question_id="INT-07",
            scenario_question_id="EE-02",
            gap_score=0.35,
        )
        assert gap.pair_name == "INT-07/EE-02"
        assert gap.interview_question_id == "INT-07"
        assert gap.scenario_question_id == "EE-02"
        assert gap.gap_score == 0.35

    def test_gap_score_bounded_upper(self):
        with pytest.raises(ValidationError):
            NarrativeBehaviorGap(
                pair_name="test",
                interview_question_id="INT-07",
                scenario_question_id="EE-02",
                gap_score=1.5,
            )

    def test_gap_score_bounded_lower(self):
        with pytest.raises(ValidationError):
            NarrativeBehaviorGap(
                pair_name="test",
                interview_question_id="INT-07",
                scenario_question_id="EE-02",
                gap_score=-0.1,
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

    def test_v3_report_card_fields(self):
        gap = NarrativeBehaviorGap(
            pair_name="INT-07/EE-02",
            interview_question_id="INT-07",
            scenario_question_id="EE-02",
            gap_score=0.25,
        )
        profile = InterviewProfile(telos="To serve", aspiration="To grow")
        card = ExamReportCard(
            exam_id="exam-v3",
            agent_id="agent-1",
            report_card_url="/agent/agent-1/exam/exam-v3",
            phronesis_score=0.78,
            alignment_status="aligned",
            dimensions={"ethos": 0.8, "logos": 0.75, "pathos": 0.7},
            tier_scores={
                "safety": 0.9,
                "ethics": 0.8,
                "soundness": 0.7,
                "helpfulness": 0.7,
            },
            consistency_analysis=[],
            per_question_detail=[],
            interview_profile=profile,
            interview_dimensions={"ethos": 0.82, "logos": 0.78, "pathos": 0.74},
            scenario_dimensions={"ethos": 0.78, "logos": 0.72, "pathos": 0.66},
            narrative_behavior_gap=[gap],
            overall_gap_score=0.25,
            question_version="v3",
        )
        assert card.interview_profile.telos == "To serve"
        assert card.interview_dimensions["ethos"] == 0.82
        assert card.scenario_dimensions["logos"] == 0.72
        assert len(card.narrative_behavior_gap) == 1
        assert card.overall_gap_score == 0.25
        assert card.question_version == "v3"

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
        assert profile.guardian_name == ""
        assert profile.entrance_exam_completed is False

    def test_enrolled_agent(self):
        profile = AgentProfile(
            agent_id="test",
            enrolled=True,
            enrolled_at="2026-02-12T00:00:00Z",
            guardian_name="Dr. Ethics",
            entrance_exam_completed=True,
        )
        assert profile.enrolled is True
        assert profile.enrolled_at == "2026-02-12T00:00:00Z"
        assert profile.guardian_name == "Dr. Ethics"
        assert profile.entrance_exam_completed is True

    def test_interview_fields_default_empty(self):
        profile = AgentProfile(agent_id="test")
        assert profile.telos == ""
        assert profile.relationship_stance == ""
        assert profile.limitations_awareness == ""
        assert profile.oversight_stance == ""
        assert profile.refusal_philosophy == ""
        assert profile.conflict_response == ""
        assert profile.help_philosophy == ""
        assert profile.failure_narrative == ""
        assert profile.aspiration == ""

    def test_interview_fields_populated(self):
        profile = AgentProfile(
            agent_id="test",
            telos="To help",
            relationship_stance="Partner",
            aspiration="Growth",
        )
        assert profile.telos == "To help"
        assert profile.relationship_stance == "Partner"
        assert profile.aspiration == "Growth"


# ── AgentSummary enrollment field ────────────────────────────────────


class TestAgentSummaryEnrollment:
    def test_defaults_not_enrolled(self):
        summary = AgentSummary(agent_id="test")
        assert summary.enrolled is False

    def test_enrolled_agent(self):
        summary = AgentSummary(agent_id="test", enrolled=True)
        assert summary.enrolled is True

    def test_interview_fields_default_empty(self):
        summary = AgentSummary(agent_id="test")
        assert summary.telos == ""
        assert summary.aspiration == ""
