"""API contract tests: verify every endpoint returns the exact shape the frontend expects.

These tests catch real bugs:
- Backend adds/removes a field but frontend type doesn't match
- Nested objects serialize wrong (e.g., graph_context, homework)
- Data map keys (trait_scores, tier_scores) get mangled
- Endpoints the frontend calls but were never HTTP-tested
"""

from __future__ import annotations

import re
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from api.main import app
from ethos_academy.shared.models import (
    AgentProfile,
    AgentSummary,
    AlumniResult,
    AuthenticityResult,
    DailyReportCard,
    DetectedIndicator,
    DetectedPattern,
    EvaluationHistoryItem,
    EvaluationResult,
    GraphContext,
    GraphData,
    GraphNode,
    GraphRel,
    Homework,
    HomeworkFocus,
    Insight,
    PatternResult,
    TraitScore,
)

client = TestClient(app)


def _to_camel(key: str) -> str:
    """Python re-implementation of the frontend's toCamelCase."""
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), key)


def _assert_frontend_keys(data: dict, expected_camel_keys: set[str], label: str = ""):
    """Verify that snake_case API response, when camelCased, contains all expected keys."""
    actual_camel = {_to_camel(k) for k in data.keys()}
    missing = expected_camel_keys - actual_camel
    assert not missing, f"{label} missing keys after camelCase transform: {missing}"


# ── Realistic fixtures ────────────────────────────────────────────────


def _full_evaluation_result() -> EvaluationResult:
    """A fully-populated EvaluationResult matching real API output."""
    return EvaluationResult(
        ethos=0.82,
        logos=0.75,
        pathos=0.68,
        flags=["excessive_hedging"],
        phronesis="developing",
        traits={
            "virtue": TraitScore(
                name="virtue",
                dimension="ethos",
                polarity="positive",
                score=0.8,
                indicators=[
                    DetectedIndicator(
                        id="ind-1",
                        name="moral_reasoning",
                        trait="virtue",
                        confidence=0.9,
                        severity=0.2,
                        evidence="demonstrates ethical consideration",
                    )
                ],
            )
        },
        detected_indicators=[
            DetectedIndicator(
                id="ind-1",
                name="moral_reasoning",
                trait="virtue",
                confidence=0.9,
                severity=0.2,
                evidence="demonstrates ethical consideration",
            )
        ],
        evaluation_id="eval-abc-123",
        routing_tier="focused",
        keyword_density=0.03,
        model_used="claude-sonnet-4-5-20250929",
        agent_model="gpt-4",
        created_at="2024-06-15T10:30:00Z",
        direction="inbound",
        graph_context=GraphContext(
            prior_evaluations=5,
            historical_phronesis=0.72,
            phronesis_trend="improving",
            flagged_patterns=["early_sycophancy"],
            alumni_warnings=1,
        ),
        alignment_status="aligned",
        tier_scores={
            "safety": 0.9,
            "ethics": 0.85,
            "soundness": 0.78,
            "helpfulness": 0.7,
        },
    )


def _full_agent_summary() -> AgentSummary:
    return AgentSummary(
        agent_id="test-agent",
        agent_name="Test Agent",
        agent_specialty="code review",
        evaluation_count=15,
        latest_alignment_status="aligned",
        enrolled=True,
        entrance_exam_completed=True,
    )


def _full_agent_profile() -> AgentProfile:
    return AgentProfile(
        agent_id="test-agent",
        agent_name="Test Agent",
        agent_specialty="code review",
        agent_model="claude-sonnet-4-5-20250929",
        created_at="2024-01-01T00:00:00Z",
        evaluation_count=42,
        dimension_averages={"ethos": 0.8, "logos": 0.75, "pathos": 0.7},
        trait_averages={"virtue": 0.85, "manipulation": 0.1},
        phronesis_trend="improving",
        alignment_history=["aligned", "aligned", "developing"],
        enrolled=True,
        enrolled_at="2024-01-15T00:00:00Z",
        guardian_name="Dr. Aristotle",
        entrance_exam_completed=True,
    )


def _full_daily_report() -> DailyReportCard:
    return DailyReportCard(
        report_id="rpt-001",
        agent_id="test-agent",
        agent_name="Test Agent",
        report_date="2024-06-15",
        generated_at="2024-06-15T10:00:00Z",
        period_evaluation_count=8,
        total_evaluation_count=42,
        ethos=0.82,
        logos=0.75,
        pathos=0.68,
        trait_averages={"virtue": 0.85, "manipulation": 0.1},
        overall_score=0.78,
        grade="B+",
        trend="improving",
        risk_level="low",
        flagged_traits=["excessive_hedging"],
        flagged_dimensions=[],
        temporal_pattern="consistent",
        character_drift=0.02,
        balance_trend="improving",
        anomaly_flags=[],
        agent_balance=0.8,
        summary="Agent shows strong ethical alignment with minor hedging tendencies.",
        insights=[
            Insight(
                trait="virtue",
                severity="info",
                message="Consistent moral reasoning",
                evidence={"eval_count": 5},
            )
        ],
        homework=Homework(
            focus_areas=[
                HomeworkFocus(
                    trait="directness",
                    priority="high",
                    current_score=0.6,
                    target_score=0.8,
                    instruction="Reduce hedging in responses",
                    example_flagged="I think maybe possibly...",
                    example_improved="Based on the evidence...",
                )
            ],
            avoid_patterns=["excessive qualifiers"],
            strengths=["ethical reasoning", "accuracy"],
            directive="Focus on direct communication while maintaining honesty.",
        ),
        dimension_deltas={"ethos": 0.02, "logos": -0.01, "pathos": 0.03},
        risk_level_change="stable",
    )


def _full_pattern_result() -> PatternResult:
    return PatternResult(
        agent_id="test-agent",
        patterns=[
            DetectedPattern(
                pattern_id="pat-001",
                name="early_sycophancy",
                description="Pattern of excessive agreement",
                matched_indicators=["flattery_language", "agreement_bias"],
                confidence=0.7,
                first_seen="2024-06-01",
                last_seen="2024-06-15",
                occurrence_count=3,
                current_stage=2,
            )
        ],
        checked_at="2024-06-15T10:30:00Z",
    )


def _full_graph_data() -> GraphData:
    return GraphData(
        nodes=[
            GraphNode(
                id="n1",
                type="Agent",
                label="Test Agent",
                caption="test-agent",
                properties={"evaluation_count": 5},
            ),
            GraphNode(
                id="n2",
                type="Trait",
                label="virtue",
                caption="Virtue",
                properties={"dimension": "ethos"},
            ),
        ],
        relationships=[
            GraphRel(
                id="r1",
                from_id="n1",
                to_id="n2",
                type="SCORED",
                properties={"score": 0.85},
            )
        ],
    )


# ── Frontend expected keys (from academy/lib/types.ts) ───────────────

# These sets define the camelCase keys each TypeScript interface declares.
# If a backend field is missing from this set, the test catches it.

EVALUATION_RESULT_KEYS = {
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
}

GRAPH_CONTEXT_KEYS = {
    "priorEvaluations",
    "historicalPhronesis",
    "phronesisTrend",
    "flaggedPatterns",
    "alumniWarnings",
}

AGENT_SUMMARY_KEYS = {
    "agentId",
    "agentName",
    "agentSpecialty",
    "agentModel",
    "evaluationCount",
    "latestAlignmentStatus",
    "enrolled",
    "entranceExamCompleted",
    "dimensionAverages",
    "traitAverages",
}

AGENT_PROFILE_KEYS = {
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
}

HISTORY_ITEM_KEYS = {
    "evaluationId",
    "ethos",
    "logos",
    "pathos",
    "phronesis",
    "alignmentStatus",
    "flags",
    "createdAt",
    "traitScores",
}

ALUMNI_KEYS = {"traitAverages", "totalEvaluations"}

DAILY_REPORT_KEYS = {
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

PATTERN_RESULT_KEYS = {"agentId", "patterns", "checkedAt"}

DETECTED_PATTERN_KEYS = {
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

GRAPH_DATA_KEYS = {"nodes", "relationships"}

GRAPH_NODE_KEYS = {"id", "type", "label", "caption", "properties"}

GRAPH_REL_KEYS = {"id", "fromId", "toId", "type", "properties"}

HOMEWORK_KEYS = {"focusAreas", "avoidPatterns", "strengths", "directive"}

HOMEWORK_FOCUS_KEYS = {
    "trait",
    "priority",
    "currentScore",
    "targetScore",
    "instruction",
    "exampleFlagged",
    "exampleImproved",
}


# ── POST /evaluate/incoming ──────────────────────────────────────────


class TestEvaluateIncomingContract:
    """The core evaluation endpoint. Frontend sends text+source, expects EvaluationResult."""

    def test_returns_full_evaluation_shape(self):
        mock_result = _full_evaluation_result()
        with patch(
            "api.main.evaluate_incoming",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/evaluate/incoming",
                json={"text": "Hello, I can help with that.", "source": "test-agent"},
            )

        assert resp.status_code == 200
        data = resp.json()
        _assert_frontend_keys(data, EVALUATION_RESULT_KEYS, "EvaluationResult")

        # Verify nested graph_context shape
        assert data["graph_context"] is not None
        _assert_frontend_keys(data["graph_context"], GRAPH_CONTEXT_KEYS, "GraphContext")

        # Verify traits dict contains TraitScore objects
        assert "virtue" in data["traits"]
        trait = data["traits"]["virtue"]
        assert "name" in trait
        assert "dimension" in trait
        assert "score" in trait
        assert "indicators" in trait
        assert len(trait["indicators"]) > 0

        # Verify tier_scores preserves data map keys (not camelCased)
        assert "safety" in data["tier_scores"]
        assert "ethics" in data["tier_scores"]

    def test_null_graph_context_serializes(self):
        """Frontend handles graphContext: null. Verify API actually sends null."""
        mock_result = _full_evaluation_result()
        mock_result.graph_context = None
        with patch(
            "api.main.evaluate_incoming",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/evaluate/incoming",
                json={"text": "Test message", "source": "agent"},
            )

        assert resp.status_code == 200
        assert resp.json()["graph_context"] is None

    def test_direction_field_included(self):
        """Backend sends direction field. Frontend type should have it."""
        mock_result = _full_evaluation_result()
        mock_result.direction = "inbound"
        with patch(
            "api.main.evaluate_incoming",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/evaluate/incoming",
                json={"text": "Test", "source": "agent"},
            )

        assert resp.status_code == 200
        # direction is in the response even if TS type doesn't declare it yet
        assert resp.json()["direction"] == "inbound"

    def test_empty_traits_and_indicators(self):
        """Verify empty collections serialize correctly (not omitted)."""
        mock_result = EvaluationResult(
            evaluation_id="eval-empty",
            ethos=0.5,
            logos=0.5,
            pathos=0.5,
        )
        with patch(
            "api.main.evaluate_incoming",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/evaluate/incoming",
                json={"text": "Test", "source": "agent"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["traits"] == {}
        assert data["detected_indicators"] == []
        assert data["flags"] == []
        assert data["tier_scores"] == {}


# ── POST /evaluate/outgoing ──────────────────────────────────────────


class TestEvaluateOutgoingContract:
    def test_returns_same_shape_as_incoming(self):
        mock_result = _full_evaluation_result()
        mock_result.direction = "outbound"
        with patch(
            "api.main.evaluate_outgoing",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/evaluate/outgoing",
                json={"text": "Here is my analysis...", "source": "test-agent"},
            )

        assert resp.status_code == 200
        data = resp.json()
        _assert_frontend_keys(data, EVALUATION_RESULT_KEYS, "EvaluationResult")
        assert data["direction"] == "outbound"


# ── GET /agents ──────────────────────────────────────────────────────


class TestAgentsSummaryContract:
    def test_returns_all_summary_fields(self):
        mock_agents = [_full_agent_summary()]
        with patch(
            "api.main.list_agents",
            new_callable=AsyncMock,
            return_value=mock_agents,
        ):
            resp = client.get("/agents")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        _assert_frontend_keys(data[0], AGENT_SUMMARY_KEYS, "AgentSummary")

    def test_agent_specialty_field_present(self):
        """Backend sends agent_specialty but frontend TS type is missing it.
        This test documents the mismatch so we can fix the frontend type."""
        mock_agents = [_full_agent_summary()]
        with patch(
            "api.main.list_agents",
            new_callable=AsyncMock,
            return_value=mock_agents,
        ):
            resp = client.get("/agents")

        data = resp.json()[0]
        # agent_specialty IS in the response even though TS type omits it
        assert "agent_specialty" in data
        assert data["agent_specialty"] == "code review"


# ── GET /agent/{id} ──────────────────────────────────────────────────


class TestAgentProfileContract:
    def test_returns_full_profile_shape(self):
        mock_profile = _full_agent_profile()
        with patch(
            "api.main.get_agent",
            new_callable=AsyncMock,
            return_value=mock_profile,
        ):
            resp = client.get("/agent/test-agent")

        assert resp.status_code == 200
        data = resp.json()
        _assert_frontend_keys(data, AGENT_PROFILE_KEYS, "AgentProfile")

        # Verify data maps preserve their keys
        assert "ethos" in data["dimension_averages"]
        assert "virtue" in data["trait_averages"]

    def test_enrollment_fields_present(self):
        mock_profile = _full_agent_profile()
        with patch(
            "api.main.get_agent",
            new_callable=AsyncMock,
            return_value=mock_profile,
        ):
            resp = client.get("/agent/test-agent")

        data = resp.json()
        assert data["enrolled"] is True
        assert data["enrolled_at"] == "2024-01-15T00:00:00Z"
        assert data["guardian_name"] == "Dr. Aristotle"
        assert data["entrance_exam_completed"] is True


# ── GET /agent/{id}/history ──────────────────────────────────────────


class TestHistoryContract:
    def test_returns_full_history_shape(self):
        mock_history = [
            EvaluationHistoryItem(
                evaluation_id="e1",
                ethos=0.82,
                logos=0.75,
                pathos=0.68,
                phronesis="developing",
                alignment_status="aligned",
                flags=["minor_hedging"],
                created_at="2024-06-15T10:30:00Z",
                trait_scores={"virtue": 0.85, "manipulation": 0.1},
            )
        ]
        with patch(
            "api.main.get_agent_history",
            new_callable=AsyncMock,
            return_value=mock_history,
        ):
            resp = client.get("/agent/test/history")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        _assert_frontend_keys(data[0], HISTORY_ITEM_KEYS, "EvaluationHistoryItem")

        # trait_scores is a data map: keys should NOT be camelCased
        assert "virtue" in data[0]["trait_scores"]


# ── GET /alumni ──────────────────────────────────────────────────────


class TestAlumniContract:
    def test_returns_full_alumni_shape(self):
        mock_alumni = AlumniResult(
            trait_averages={"virtue": 0.78, "manipulation": 0.12, "accuracy": 0.85},
            total_evaluations=150,
        )
        with patch(
            "api.main.get_alumni",
            new_callable=AsyncMock,
            return_value=mock_alumni,
        ):
            resp = client.get("/alumni")

        assert resp.status_code == 200
        data = resp.json()
        _assert_frontend_keys(data, ALUMNI_KEYS, "AlumniResult")

        # trait_averages is a data map
        assert "virtue" in data["trait_averages"]
        assert "manipulation" in data["trait_averages"]


# ── GET /agent/{id}/character ────────────────────────────────────────


class TestCharacterReportContract:
    def test_returns_full_report_shape(self):
        mock_report = _full_daily_report()
        with patch(
            "api.main.character_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            resp = client.get("/agent/test-agent/character")

        assert resp.status_code == 200
        data = resp.json()
        _assert_frontend_keys(data, DAILY_REPORT_KEYS, "DailyReportCard")

    def test_homework_nested_shape(self):
        mock_report = _full_daily_report()
        with patch(
            "api.main.character_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            resp = client.get("/agent/test-agent/character")

        data = resp.json()
        hw = data["homework"]
        _assert_frontend_keys(hw, HOMEWORK_KEYS, "Homework")

        assert len(hw["focus_areas"]) > 0
        _assert_frontend_keys(
            hw["focus_areas"][0], HOMEWORK_FOCUS_KEYS, "HomeworkFocus"
        )

    def test_insights_nested_shape(self):
        mock_report = _full_daily_report()
        with patch(
            "api.main.character_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            resp = client.get("/agent/test-agent/character")

        data = resp.json()
        assert len(data["insights"]) > 0
        insight = data["insights"][0]
        assert "trait" in insight
        assert "severity" in insight
        assert "message" in insight
        assert "evidence" in insight

    def test_dimension_deltas_is_data_map(self):
        """dimension_deltas keys are dimension names, not structural keys."""
        mock_report = _full_daily_report()
        with patch(
            "api.main.character_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            resp = client.get("/agent/test-agent/character")

        data = resp.json()
        assert "ethos" in data["dimension_deltas"]


# ── GET /agent/{id}/patterns ─────────────────────────────────────────


class TestPatternsContract:
    """Untested endpoint that the PatternsPanel.tsx component calls."""

    def test_returns_full_pattern_shape(self):
        mock_patterns = _full_pattern_result()
        with patch(
            "api.main.detect_patterns",
            new_callable=AsyncMock,
            return_value=mock_patterns,
        ):
            resp = client.get("/agent/test-agent/patterns")

        assert resp.status_code == 200
        data = resp.json()
        _assert_frontend_keys(data, PATTERN_RESULT_KEYS, "PatternResult")

        assert len(data["patterns"]) > 0
        pattern = data["patterns"][0]
        _assert_frontend_keys(pattern, DETECTED_PATTERN_KEYS, "DetectedPattern")

    def test_empty_patterns_list(self):
        mock_patterns = PatternResult(agent_id="clean-agent", checked_at="2024-06-15")
        with patch(
            "api.main.detect_patterns",
            new_callable=AsyncMock,
            return_value=mock_patterns,
        ):
            resp = client.get("/agent/clean-agent/patterns")

        assert resp.status_code == 200
        data = resp.json()
        assert data["patterns"] == []


# ── GET /agent/{name}/authenticity ───────────────────────────────────


class TestAuthenticityContract:
    """Endpoint exists in API but has zero frontend types. Tests document the shape."""

    def test_returns_full_authenticity_shape(self):
        mock_auth = AuthenticityResult(
            agent_name="test-agent",
            authenticity_score=0.85,
            classification="likely_autonomous",
            confidence=0.9,
        )
        with patch(
            "api.main.analyze_authenticity",
            new_callable=AsyncMock,
            return_value=mock_auth,
        ):
            resp = client.get("/agent/test-agent/authenticity")

        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_name"] == "test-agent"
        assert data["authenticity_score"] == 0.85
        assert data["classification"] == "likely_autonomous"

        # Verify nested sub-models serialize
        assert "temporal" in data
        assert "burst" in data
        assert "activity" in data
        assert "identity" in data

        # Temporal signature
        assert "cv_score" in data["temporal"]
        assert "classification" in data["temporal"]

        # Burst analysis
        assert "burst_rate" in data["burst"]

        # Activity pattern
        assert "active_hours" in data["activity"]
        assert "has_sleep_gap" in data["activity"]


# ── GET /graph ────────────────────────────────────────────────────────


class TestGraphContract:
    """Untested endpoint that PhronesisGraph.tsx component calls.
    NVL crashes if node/relationship shape is wrong."""

    def test_returns_full_graph_shape(self):
        mock_graph = _full_graph_data()
        with patch(
            "api.main.get_graph_data",
            new_callable=AsyncMock,
            return_value=mock_graph,
        ):
            resp = client.get("/graph")

        assert resp.status_code == 200
        data = resp.json()
        _assert_frontend_keys(data, GRAPH_DATA_KEYS, "GraphData")

        # Verify node shape (NVL needs id, type, label)
        assert len(data["nodes"]) > 0
        node = data["nodes"][0]
        _assert_frontend_keys(node, GRAPH_NODE_KEYS, "GraphNode")
        assert node["id"] == "n1"

        # Verify relationship shape (NVL needs from_id, to_id, type)
        assert len(data["relationships"]) > 0
        rel = data["relationships"][0]
        _assert_frontend_keys(rel, GRAPH_REL_KEYS, "GraphRel")

    def test_empty_graph(self):
        mock_graph = GraphData()
        with patch(
            "api.main.get_graph_data",
            new_callable=AsyncMock,
            return_value=mock_graph,
        ):
            resp = client.get("/graph")

        assert resp.status_code == 200
        data = resp.json()
        assert data["nodes"] == []
        assert data["relationships"] == []

    def test_relationship_from_to_keys(self):
        """NVL uses from_id and to_id. Frontend transforms to fromId/toId.
        If these are missing, NVL silently drops the relationship."""
        mock_graph = _full_graph_data()
        with patch(
            "api.main.get_graph_data",
            new_callable=AsyncMock,
            return_value=mock_graph,
        ):
            resp = client.get("/graph")

        rel = resp.json()["relationships"][0]
        assert "from_id" in rel, "API must return from_id for frontend transform"
        assert "to_id" in rel, "API must return to_id for frontend transform"
        assert rel["from_id"] == "n1"
        assert rel["to_id"] == "n2"


# ── Score bounds validation ──────────────────────────────────────────


class TestScoreBounds:
    """Verify score fields stay within [0.0, 1.0] in API responses."""

    def test_evaluation_scores_bounded(self):
        mock_result = _full_evaluation_result()
        with patch(
            "api.main.evaluate_incoming",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/evaluate/incoming",
                json={"text": "Test", "source": "agent"},
            )

        data = resp.json()
        for dim in ("ethos", "logos", "pathos"):
            assert 0.0 <= data[dim] <= 1.0, f"{dim} out of bounds: {data[dim]}"

    def test_report_card_scores_bounded(self):
        mock_report = _full_daily_report()
        with patch(
            "api.main.character_report",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            resp = client.get("/agent/test/character")

        data = resp.json()
        for dim in ("ethos", "logos", "pathos", "overall_score", "agent_balance"):
            assert 0.0 <= data[dim] <= 1.0, f"{dim} out of bounds: {data[dim]}"
