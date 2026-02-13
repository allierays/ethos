"""Tests for enrollment wiring — exports, model re-exports, and field mapping."""


# ── Package-level exports ───────────────────────────────────────────


class TestInitExports:
    def test_register_for_exam_exported(self):
        from ethos import register_for_exam

        assert callable(register_for_exam)

    def test_submit_answer_exported(self):
        from ethos import submit_answer

        assert callable(submit_answer)

    def test_complete_exam_exported(self):
        from ethos import complete_exam

        assert callable(complete_exam)

    def test_get_exam_report_exported(self):
        from ethos import get_exam_report

        assert callable(get_exam_report)


# ── Model re-exports from ethos.models ──────────────────────────────


class TestModelReExports:
    def test_exam_question(self):
        from ethos.models import ExamQuestion

        q = ExamQuestion(id="EE-01", section="ETHOS", prompt="Test")
        assert q.id == "EE-01"

    def test_exam_registration(self):
        from ethos.models import ExamQuestion, ExamRegistration

        q = ExamQuestion(id="EE-01", section="ETHOS", prompt="Test")
        reg = ExamRegistration(
            exam_id="abc",
            agent_id="a1",
            question_number=1,
            total_questions=23,
            question=q,
            message="Welcome",
        )
        assert reg.exam_id == "abc"

    def test_exam_answer_result(self):
        from ethos.models import ExamAnswerResult

        r = ExamAnswerResult(question_number=1, total_questions=23)
        assert r.complete is False

    def test_exam_report_card(self):
        from ethos.models import ExamReportCard

        card = ExamReportCard(
            exam_id="abc",
            agent_id="a1",
            report_card_url="/agent/a1/exam/abc",
            phronesis_score=0.7,
            alignment_status="aligned",
            dimensions={"ethos": 0.8},
            tier_scores={"safety": 0.9},
            consistency_analysis=[],
            per_question_detail=[],
        )
        assert card.phronesis_score == 0.7

    def test_consistency_pair(self):
        from ethos.models import ConsistencyPair

        pair = ConsistencyPair(
            pair_name="A/B",
            question_a_id="EE-14",
            question_b_id="EE-15",
            framework_a="utilitarian",
            framework_b="rights-based",
            coherence_score=0.85,
        )
        assert pair.coherence_score == 0.85


# ── Agent field mapping ─────────────────────────────────────────────


class TestAgentFieldMapping:
    def test_agent_profile_enrollment_defaults(self):
        """AgentProfile defaults enrollment fields when graph returns no data."""
        from ethos.shared.models import AgentProfile

        profile = AgentProfile(agent_id="test-agent")
        assert profile.enrolled is False
        assert profile.enrolled_at == ""
        assert profile.counselor_name == ""
        assert profile.entrance_exam_completed is False

    def test_agent_profile_enrollment_set(self):
        """AgentProfile accepts enrollment fields."""
        from ethos.shared.models import AgentProfile

        profile = AgentProfile(
            agent_id="test-agent",
            enrolled=True,
            enrolled_at="2026-02-12T00:00:00Z",
            counselor_name="Dr. Ethics",
            entrance_exam_completed=True,
        )
        assert profile.enrolled is True
        assert profile.enrolled_at == "2026-02-12T00:00:00Z"
        assert profile.counselor_name == "Dr. Ethics"
        assert profile.entrance_exam_completed is True

    def test_agent_summary_enrolled_default(self):
        """AgentSummary defaults enrolled to False."""
        from ethos.shared.models import AgentSummary

        summary = AgentSummary(agent_id="test-agent")
        assert summary.enrolled is False

    def test_agent_summary_enrolled_set(self):
        """AgentSummary accepts enrolled field."""
        from ethos.shared.models import AgentSummary

        summary = AgentSummary(agent_id="test-agent", enrolled=True)
        assert summary.enrolled is True


# ── Graph read result shape ─────────────────────────────────────────


class TestGraphReadShape:
    def test_profile_query_returns_enrollment_fields(self):
        """Verify the profile query Cypher includes enrollment columns."""
        from ethos.graph.read import _GET_PROFILE_QUERY

        assert "enrolled" in _GET_PROFILE_QUERY
        assert "enrolled_at" in _GET_PROFILE_QUERY
        assert "counselor_name" in _GET_PROFILE_QUERY
        assert "entrance_exam_completed" in _GET_PROFILE_QUERY

    def test_all_agents_query_returns_enrolled(self):
        """Verify the all-agents query Cypher includes enrolled column."""
        from ethos.graph.read import _GET_ALL_AGENTS_QUERY

        assert "enrolled" in _GET_ALL_AGENTS_QUERY

    def test_search_agents_query_returns_enrolled(self):
        """Verify the search-agents query Cypher includes enrolled column."""
        from ethos.graph.read import _SEARCH_AGENTS_QUERY

        assert "enrolled" in _SEARCH_AGENTS_QUERY
