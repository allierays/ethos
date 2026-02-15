"""Data contract tests: verify Pydantic model fields map correctly to TypeScript types.

These tests catch:
- Backend adds a field but TypeScript type doesn't declare it (silent data loss)
- Backend renames a field but frontend still uses old name (undefined access)
- snake_case to camelCase transformation produces wrong key names
- Nested model serialization breaks the expected structure
"""

from __future__ import annotations

import re

from ethos.shared.models import (
    AgentProfile,
    AgentSummary,
    AlumniResult,
    ConsistencyPair,
    DailyReportCard,
    DetectedIndicator,
    DetectedPattern,
    EvaluationHistoryItem,
    EvaluationResult,
    ExamAnswerResult,
    ExamQuestion,
    ExamRegistration,
    ExamReportCard,
    ExamSummary,
    GraphContext,
    GraphData,
    GraphNode,
    GraphRel,
    Homework,
    HomeworkFocus,
    Insight,
    PatternResult,
    QuestionDetail,
    RecordItem,
    RecordsResult,
    TraitScore,
)


def _to_camel(key: str) -> str:
    """Replicate the frontend's toCamelCase transform."""
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), key)


def _model_camel_keys(model_cls) -> set[str]:
    """Get camelCase versions of all Pydantic model field names."""
    return {_to_camel(field) for field in model_cls.model_fields}


def _assert_types_match(
    pydantic_cls,
    ts_keys: set[str],
    label: str,
    *,
    backend_extras: set[str] | None = None,
):
    """Verify Pydantic model fields (after camelCase) match TypeScript interface keys.

    backend_extras: fields the backend sends but the TS type intentionally omits.
    """
    backend_extras = backend_extras or set()
    model_keys = _model_camel_keys(pydantic_cls)
    model_keys_filtered = model_keys - backend_extras

    # Keys in TS but not in Pydantic (frontend expects data that doesn't exist)
    missing_from_backend = ts_keys - model_keys
    assert not missing_from_backend, (
        f"{label}: TypeScript expects keys not in Pydantic model: {missing_from_backend}"
    )

    # Keys in Pydantic but not in TS (data loss -- backend sends, frontend ignores)
    missing_from_frontend = model_keys_filtered - ts_keys
    assert not missing_from_frontend, (
        f"{label}: Pydantic has keys not in TypeScript type: {missing_from_frontend}"
    )


# ── TypeScript interface definitions (from academy/lib/types.ts) ─────

TS_TRAIT_SCORE = {"name", "dimension", "polarity", "score", "indicators"}

TS_DETECTED_INDICATOR = {"id", "name", "trait", "confidence", "severity", "evidence"}

TS_GRAPH_CONTEXT = {
    "priorEvaluations",
    "historicalPhronesis",
    "phronesisTrend",
    "flaggedPatterns",
    "alumniWarnings",
}

TS_EVALUATION_RESULT = {
    "ethos",
    "logos",
    "pathos",
    "flags",
    "phronesis",
    "traits",
    "detectedIndicators",
    "evaluationId",
    "routingTier",
    "keywordDensity",
    "modelUsed",
    "agentModel",
    "createdAt",
    "graphContext",
    "alignmentStatus",
    "tierScores",
    "confidence",
    "intentClassification",
    "scoringReasoning",
}

TS_AGENT_SUMMARY = {
    "agentId",
    "agentName",
    "agentModel",
    "agentSpecialty",
    "evaluationCount",
    "latestAlignmentStatus",
    "enrolled",
    "entranceExamCompleted",
    "dimensionAverages",
    "traitAverages",
    "telos",
    "relationshipStance",
    "limitationsAwareness",
    "oversightStance",
    "refusalPhilosophy",
    "conflictResponse",
    "helpPhilosophy",
    "failureNarrative",
    "aspiration",
}

TS_AGENT_PROFILE = {
    "agentId",
    "agentName",
    "agentModel",
    "createdAt",
    "evaluationCount",
    "dimensionAverages",
    "traitAverages",
    "phronesisTrend",
    "alignmentHistory",
    "enrolled",
    "enrolledAt",
    "guardianName",
    "entranceExamCompleted",
    "agentSpecialty",
    "telos",
    "relationshipStance",
    "limitationsAwareness",
    "oversightStance",
    "refusalPhilosophy",
    "conflictResponse",
    "helpPhilosophy",
    "failureNarrative",
    "aspiration",
}

TS_HISTORY_ITEM = {
    "evaluationId",
    "ethos",
    "logos",
    "pathos",
    "phronesis",
    "alignmentStatus",
    "flags",
    "createdAt",
    "traitScores",
    "messageContent",
    "intentClassification",
    "scoringReasoning",
}

TS_ALUMNI = {"traitAverages", "totalEvaluations"}

TS_INSIGHT = {"trait", "severity", "message", "evidence"}

TS_HOMEWORK_FOCUS = {
    "trait",
    "priority",
    "currentScore",
    "targetScore",
    "instruction",
    "exampleFlagged",
    "exampleImproved",
    "systemPromptAddition",
}

TS_HOMEWORK = {"focusAreas", "avoidPatterns", "strengths", "directive"}

TS_DAILY_REPORT = {
    "reportId",
    "agentId",
    "agentName",
    "reportDate",
    "generatedAt",
    "periodEvaluationCount",
    "totalEvaluationCount",
    "ethos",
    "logos",
    "pathos",
    "traitAverages",
    "overallScore",
    "grade",
    "trend",
    "riskLevel",
    "flaggedTraits",
    "flaggedDimensions",
    "temporalPattern",
    "characterDrift",
    "balanceTrend",
    "anomalyFlags",
    "agentBalance",
    "summary",
    "insights",
    "homework",
    "dimensionDeltas",
    "riskLevelChange",
}

TS_DETECTED_PATTERN = {
    "patternId",
    "name",
    "description",
    "matchedIndicators",
    "confidence",
    "firstSeen",
    "lastSeen",
    "occurrenceCount",
    "currentStage",
}

TS_PATTERN_RESULT = {"agentId", "patterns", "checkedAt"}

TS_GRAPH_NODE = {"id", "type", "label", "caption", "properties"}

TS_GRAPH_REL = {"id", "fromId", "toId", "type", "properties"}

TS_GRAPH_DATA = {"nodes", "relationships"}

TS_EXAM_QUESTION = {"id", "section", "prompt", "phase", "questionType"}

TS_EXAM_REGISTRATION = {
    "examId",
    "agentId",
    "questionNumber",
    "totalQuestions",
    "question",
    "message",
}

TS_EXAM_ANSWER_RESULT = {
    "questionNumber",
    "totalQuestions",
    "question",
    "complete",
    "phase",
    "questionType",
}

TS_QUESTION_DETAIL = {
    "questionId",
    "section",
    "prompt",
    "responseSummary",
    "scoringReasoning",
    "traitScores",
    "detectedIndicators",
    "phase",
    "questionType",
}

TS_CONSISTENCY_PAIR = {
    "pairName",
    "questionAId",
    "questionBId",
    "frameworkA",
    "frameworkB",
    "coherenceScore",
}

TS_EXAM_REPORT_CARD = {
    "examId",
    "agentId",
    "reportCardUrl",
    "phronesisScore",
    "alignmentStatus",
    "dimensions",
    "tierScores",
    "consistencyAnalysis",
    "perQuestionDetail",
    "interviewProfile",
    "interviewDimensions",
    "scenarioDimensions",
    "narrativeBehaviorGap",
    "overallGapScore",
    "questionVersion",
    "homework",
}

TS_EXAM_SUMMARY = {
    "examId",
    "examType",
    "completed",
    "completedAt",
    "phronesisScore",
}

TS_RECORD_ITEM = {
    "evaluationId",
    "agentId",
    "agentName",
    "ethos",
    "logos",
    "pathos",
    "overall",
    "alignmentStatus",
    "flags",
    "direction",
    "messageContent",
    "createdAt",
    "phronesis",
    "scoringReasoning",
    "intentClassification",
    "traitScores",
    "similarityScore",
    "modelUsed",
    "agentModel",
    "routingTier",
    "keywordDensity",
    "detectedIndicators",
}

TS_RECORDS_RESULT = {"items", "total", "page", "pageSize", "totalPages"}


# ── Core evaluation models ───────────────────────────────────────────


class TestEvaluationModelContract:
    def test_trait_score_matches_ts(self):
        _assert_types_match(TraitScore, TS_TRAIT_SCORE, "TraitScore")

    def test_detected_indicator_matches_ts(self):
        _assert_types_match(
            DetectedIndicator, TS_DETECTED_INDICATOR, "DetectedIndicator"
        )

    def test_graph_context_matches_ts(self):
        _assert_types_match(GraphContext, TS_GRAPH_CONTEXT, "GraphContext")

    def test_evaluation_result_matches_ts(self):
        # direction, thinkingContent are intentionally extra on backend (not yet in TS type)
        _assert_types_match(
            EvaluationResult,
            TS_EVALUATION_RESULT,
            "EvaluationResult",
            backend_extras={"direction", "thinkingContent"},
        )

    def test_history_item_matches_ts(self):
        _assert_types_match(
            EvaluationHistoryItem, TS_HISTORY_ITEM, "EvaluationHistoryItem"
        )


# ── Agent models ─────────────────────────────────────────────────────


class TestAgentModelContract:
    def test_agent_summary_matches_ts(self):
        _assert_types_match(
            AgentSummary,
            TS_AGENT_SUMMARY,
            "AgentSummary",
        )

    def test_agent_profile_matches_ts(self):
        _assert_types_match(
            AgentProfile,
            TS_AGENT_PROFILE,
            "AgentProfile",
        )


# ── Alumni model ─────────────────────────────────────────────────────


class TestAlumniModelContract:
    def test_alumni_result_matches_ts(self):
        _assert_types_match(AlumniResult, TS_ALUMNI, "AlumniResult")


# ── Daily report card models ─────────────────────────────────────────


class TestReportCardModelContract:
    def test_insight_matches_ts(self):
        _assert_types_match(Insight, TS_INSIGHT, "Insight")

    def test_homework_focus_matches_ts(self):
        _assert_types_match(HomeworkFocus, TS_HOMEWORK_FOCUS, "HomeworkFocus")

    def test_homework_matches_ts(self):
        _assert_types_match(Homework, TS_HOMEWORK, "Homework")

    def test_daily_report_matches_ts(self):
        _assert_types_match(DailyReportCard, TS_DAILY_REPORT, "DailyReportCard")


# ── Pattern models ───────────────────────────────────────────────────


class TestPatternModelContract:
    def test_detected_pattern_matches_ts(self):
        _assert_types_match(DetectedPattern, TS_DETECTED_PATTERN, "DetectedPattern")

    def test_pattern_result_matches_ts(self):
        _assert_types_match(PatternResult, TS_PATTERN_RESULT, "PatternResult")


# ── Graph models ─────────────────────────────────────────────────────


class TestGraphModelContract:
    def test_graph_node_matches_ts(self):
        _assert_types_match(GraphNode, TS_GRAPH_NODE, "GraphNode")

    def test_graph_rel_matches_ts(self):
        _assert_types_match(GraphRel, TS_GRAPH_REL, "GraphRel")

    def test_graph_data_matches_ts(self):
        _assert_types_match(GraphData, TS_GRAPH_DATA, "GraphData")


# ── Exam models ──────────────────────────────────────────────────────


class TestExamModelContract:
    def test_exam_question_matches_ts(self):
        _assert_types_match(ExamQuestion, TS_EXAM_QUESTION, "ExamQuestion")

    def test_exam_registration_matches_ts(self):
        _assert_types_match(ExamRegistration, TS_EXAM_REGISTRATION, "ExamRegistration")

    def test_exam_answer_result_matches_ts(self):
        _assert_types_match(ExamAnswerResult, TS_EXAM_ANSWER_RESULT, "ExamAnswerResult")

    def test_question_detail_matches_ts(self):
        _assert_types_match(QuestionDetail, TS_QUESTION_DETAIL, "QuestionDetail")

    def test_consistency_pair_matches_ts(self):
        _assert_types_match(ConsistencyPair, TS_CONSISTENCY_PAIR, "ConsistencyPair")

    def test_exam_report_card_matches_ts(self):
        _assert_types_match(ExamReportCard, TS_EXAM_REPORT_CARD, "ExamReportCard")

    def test_exam_summary_matches_ts(self):
        _assert_types_match(ExamSummary, TS_EXAM_SUMMARY, "ExamSummary")


# ── Record models ───────────────────────────────────────────────────


class TestRecordModelContract:
    def test_record_item_matches_ts(self):
        _assert_types_match(RecordItem, TS_RECORD_ITEM, "RecordItem")

    def test_records_result_matches_ts(self):
        _assert_types_match(RecordsResult, TS_RECORDS_RESULT, "RecordsResult")


# ── Serialization round-trip ─────────────────────────────────────────


class TestSerializationRoundTrip:
    """Verify model_dump() produces the exact keys we expect (no surprises)."""

    def test_evaluation_result_serializes_all_fields(self):
        result = EvaluationResult(
            ethos=0.8,
            logos=0.7,
            pathos=0.6,
            evaluation_id="e1",
            direction="inbound",
        )
        dumped = result.model_dump()
        expected_keys = set(EvaluationResult.model_fields.keys())
        assert set(dumped.keys()) == expected_keys

    def test_daily_report_serializes_nested_homework(self):
        report = DailyReportCard(
            homework=Homework(
                focus_areas=[HomeworkFocus(trait="virtue")],
                directive="Be honest",
            )
        )
        dumped = report.model_dump()
        assert "homework" in dumped
        assert "focus_areas" in dumped["homework"]
        assert len(dumped["homework"]["focus_areas"]) == 1
        assert dumped["homework"]["focus_areas"][0]["trait"] == "virtue"

    def test_graph_rel_serializes_from_to(self):
        rel = GraphRel(id="r1", from_id="n1", to_id="n2", type="SCORED")
        dumped = rel.model_dump()
        assert "from_id" in dumped
        assert "to_id" in dumped
        # Must NOT serialize as "from" or "to" (reserved words in some contexts)
        assert "from" not in dumped
        assert "to" not in dumped

    def test_record_item_serializes_all_fields(self):
        item = RecordItem(
            evaluation_id="e1",
            agent_id="a1",
            agent_name="TestBot",
            ethos=0.8,
            logos=0.7,
            pathos=0.6,
            overall=0.7,
        )
        dumped = item.model_dump()
        expected_keys = set(RecordItem.model_fields.keys())
        assert set(dumped.keys()) == expected_keys

    def test_records_result_defaults(self):
        result = RecordsResult()
        assert result.items == []
        assert result.total == 0
        assert result.page == 0
        assert result.page_size == 20
        assert result.total_pages == 0

    def test_records_result_serializes_nested_items(self):
        result = RecordsResult(
            items=[RecordItem(evaluation_id="e1", agent_id="a1")],
            total=1,
            page=0,
            page_size=20,
            total_pages=1,
        )
        dumped = result.model_dump()
        assert len(dumped["items"]) == 1
        assert dumped["items"][0]["evaluation_id"] == "e1"
        assert dumped["total"] == 1
        assert dumped["total_pages"] == 1

    def test_pattern_result_serializes_nested_patterns(self):
        result = PatternResult(
            agent_id="a1",
            patterns=[
                DetectedPattern(
                    pattern_id="p1",
                    name="sycophancy",
                    matched_indicators=["flattery"],
                )
            ],
        )
        dumped = result.model_dump()
        assert len(dumped["patterns"]) == 1
        assert dumped["patterns"][0]["pattern_id"] == "p1"
        assert dumped["patterns"][0]["matched_indicators"] == ["flattery"]

    def test_exam_report_card_serializes_nested_details(self):
        card = ExamReportCard(
            exam_id="ex1",
            agent_id="a1",
            report_card_url="/exam/ex1",
            phronesis_score=0.8,
            alignment_status="aligned",
            dimensions={"ethos": 0.8},
            tier_scores={"safety": 0.9},
            consistency_analysis=[
                ConsistencyPair(
                    pair_name="pair1",
                    question_a_id="q1",
                    question_b_id="q2",
                    framework_a="deontological",
                    framework_b="consequentialist",
                    coherence_score=0.7,
                )
            ],
            per_question_detail=[
                QuestionDetail(
                    question_id="q1",
                    section="ethics",
                    prompt="What is right?",
                    response_summary="Agent reasons well.",
                    trait_scores={"virtue": 0.85},
                )
            ],
        )
        dumped = card.model_dump()
        assert len(dumped["consistency_analysis"]) == 1
        assert dumped["consistency_analysis"][0]["pair_name"] == "pair1"
        assert len(dumped["per_question_detail"]) == 1
        assert dumped["per_question_detail"][0]["question_id"] == "q1"
