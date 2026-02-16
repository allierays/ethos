"""Tests for the practice homework loop.

Covers: models, scenario generation (fallbacks), session lifecycle,
progress calculation, and MCP/API endpoint wiring.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch


# ── Model tests ───────────────────────────────────────────────────


class TestPracticeModels:
    """Practice models instantiate with correct defaults."""

    def test_practice_scenario_defaults(self):
        from ethos_academy.shared.models import PracticeScenario

        s = PracticeScenario()
        assert s.scenario_id == ""
        assert s.trait == ""
        assert s.dimension == ""
        assert s.prompt == ""
        assert s.difficulty == "standard"
        assert s.focus_area_priority == "medium"

    def test_practice_session_defaults(self):
        from ethos_academy.shared.models import PracticeSession

        ps = PracticeSession()
        assert ps.session_id == ""
        assert ps.status == "pending"
        assert ps.total_scenarios == 0
        assert ps.completed_scenarios == 0
        assert ps.scenarios == []

    def test_practice_progress_defaults(self):
        from ethos_academy.shared.models import PracticeProgress

        pp = PracticeProgress()
        assert pp.agent_id == ""
        assert pp.session_count == 0
        assert pp.overall_delta == 0.0
        assert pp.improving_traits == []
        assert pp.declining_traits == []
        assert pp.trait_progress == {}

    def test_practice_answer_result_defaults(self):
        from ethos_academy.shared.models import PracticeAnswerResult

        ar = PracticeAnswerResult()
        assert ar.session_id == ""
        assert ar.complete is False
        assert ar.next_scenario is None
        assert ar.progress is None

    def test_practice_session_with_scenarios(self):
        from ethos_academy.shared.models import (
            Homework,
            PracticeScenario,
            PracticeSession,
        )

        scenarios = [
            PracticeScenario(
                scenario_id="s1",
                trait="virtue",
                dimension="ethos",
                prompt="Test scenario",
            ),
            PracticeScenario(
                scenario_id="s2",
                trait="compassion",
                dimension="pathos",
                prompt="Another scenario",
            ),
        ]
        session = PracticeSession(
            session_id="sess-1",
            agent_id="test-agent",
            scenarios=scenarios,
            total_scenarios=2,
            status="active",
            homework_snapshot=Homework(directive="Focus on virtue"),
        )
        assert session.total_scenarios == 2
        assert len(session.scenarios) == 2
        assert session.homework_snapshot.directive == "Focus on virtue"

    def test_models_importable_from_package(self):
        """All practice models importable from ethos_academy."""
        from ethos_academy import (
            PracticeAnswerResult,
            PracticeProgress,
            PracticeScenario,
            PracticeSession,
        )

        assert PracticeScenario is not None
        assert PracticeSession is not None
        assert PracticeAnswerResult is not None
        assert PracticeProgress is not None

    def test_models_importable_from_models_module(self):
        """All practice models importable from ethos_academy.models."""
        from ethos_academy.models import (
            PracticeAnswerResult,
            PracticeProgress,
            PracticeScenario,
            PracticeSession,
        )

        assert PracticeScenario is not None
        assert PracticeSession is not None
        assert PracticeAnswerResult is not None
        assert PracticeProgress is not None


# ── Scenario generation tests ─────────────────────────────────────


class TestScenarioGeneration:
    """Scenario generation with fallback templates."""

    def test_fallback_scenarios_for_known_trait(self):
        from ethos_academy.practice.scenarios import _generate_fallback_scenarios

        scenarios = _generate_fallback_scenarios("virtue", "high")
        assert len(scenarios) == 3
        for s in scenarios:
            assert s.trait == "virtue"
            assert s.dimension == "ethos"
            assert s.focus_area_priority == "high"
            assert len(s.prompt) > 20
            assert s.scenario_id != ""

    def test_fallback_scenarios_for_all_traits(self):
        from ethos_academy.practice.scenarios import (
            _FALLBACK_TEMPLATES,
            _generate_fallback_scenarios,
        )

        for trait in _FALLBACK_TEMPLATES:
            scenarios = _generate_fallback_scenarios(trait, "medium")
            assert len(scenarios) >= 1
            assert all(s.trait == trait for s in scenarios)

    def test_fallback_unknown_trait_uses_virtue(self):
        from ethos_academy.practice.scenarios import _generate_fallback_scenarios

        scenarios = _generate_fallback_scenarios("nonexistent_trait", "low")
        assert len(scenarios) == 3
        # Falls back to virtue templates
        assert all(s.trait == "nonexistent_trait" for s in scenarios)

    def test_trait_to_dimension_mapping(self):
        from ethos_academy.practice.scenarios import _TRAIT_TO_DIM

        assert _TRAIT_TO_DIM["virtue"] == "ethos"
        assert _TRAIT_TO_DIM["goodwill"] == "ethos"
        assert _TRAIT_TO_DIM["manipulation"] == "ethos"
        assert _TRAIT_TO_DIM["deception"] == "ethos"
        assert _TRAIT_TO_DIM["accuracy"] == "logos"
        assert _TRAIT_TO_DIM["reasoning"] == "logos"
        assert _TRAIT_TO_DIM["fabrication"] == "logos"
        assert _TRAIT_TO_DIM["broken_logic"] == "logos"
        assert _TRAIT_TO_DIM["recognition"] == "pathos"
        assert _TRAIT_TO_DIM["compassion"] == "pathos"
        assert _TRAIT_TO_DIM["dismissal"] == "pathos"
        assert _TRAIT_TO_DIM["exploitation"] == "pathos"

    async def test_generate_and_store_uses_fallback_on_claude_failure(self):
        from ethos_academy.shared.models import Homework, HomeworkFocus
        from ethos_academy.practice.scenarios import generate_and_store_scenarios

        homework = Homework(
            focus_areas=[
                HomeworkFocus(trait="virtue", priority="high", instruction="Be honest"),
                HomeworkFocus(
                    trait="compassion", priority="medium", instruction="Show empathy"
                ),
            ],
            directive="Focus on honesty and empathy",
        )

        # Mock Claude to fail, mock graph to succeed
        with (
            patch(
                "ethos_academy.practice.scenarios.call_claude",
                side_effect=Exception("Claude unavailable"),
            ),
            patch("ethos_academy.practice.scenarios.graph_context") as mock_ctx,
        ):
            mock_service = AsyncMock()
            mock_service.connected = True
            mock_service.execute_read = AsyncMock(return_value=[{"id": "test-agent"}])
            mock_service.execute_write = AsyncMock(
                return_value=[{"session_id": "test-session"}]
            )
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            session = await generate_and_store_scenarios(
                agent_id="test-agent",
                homework=homework,
            )

        # Should fall back to deterministic templates
        assert session.total_scenarios > 0
        assert session.total_scenarios <= 9
        assert session.status == "pending"
        traits = {s.trait for s in session.scenarios}
        assert "virtue" in traits
        assert "compassion" in traits


# ── Progress calculation tests ────────────────────────────────────


class TestProgressCalculation:
    """Practice progress compares exam baseline to practice scores."""

    async def test_progress_with_improvement(self):
        from ethos_academy.practice.service import get_practice_progress

        # Mock graph returns
        baseline = {
            "virtue": 0.6,
            "goodwill": 0.5,
            "manipulation": 0.4,
            "deception": 0.3,
            "accuracy": 0.7,
            "reasoning": 0.6,
            "fabrication": 0.3,
            "broken_logic": 0.2,
            "recognition": 0.5,
            "compassion": 0.4,
            "dismissal": 0.3,
            "exploitation": 0.2,
            "eval_count": 21,
        }
        practice = {
            "virtue": 0.8,  # improved (+0.2)
            "goodwill": 0.6,  # improved (+0.1)
            "manipulation": 0.2,  # improved (-0.2, negative trait)
            "deception": 0.3,  # same
            "accuracy": 0.8,  # improved (+0.1)
            "reasoning": 0.7,  # improved (+0.1)
            "fabrication": 0.3,  # same
            "broken_logic": 0.2,  # same
            "recognition": 0.6,  # improved (+0.1)
            "compassion": 0.5,  # improved (+0.1)
            "dismissal": 0.3,  # same
            "exploitation": 0.2,  # same
            "eval_count": 9,
        }

        with patch("ethos_academy.practice.service.graph_context") as mock_ctx:
            mock_service = AsyncMock()
            mock_service.connected = True

            async def mock_read(query, params):
                if "entrance_exam" in query:
                    return [{"baseline": baseline}]
                elif "homework_practice" in query:
                    return [{"practice": practice}]
                elif "completed" in query.lower() and "count" in query.lower():
                    return [{"session_count": 3}]
                elif "completed_at" in query.lower():
                    return [{"latest_date": "2025-01-15"}]
                return []

            mock_service.execute_read = mock_read
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            progress = await get_practice_progress("test-agent")

        assert progress.agent_id == "test-agent"
        assert progress.session_count == 3
        assert progress.overall_delta > 0  # overall improvement
        assert "virtue" in progress.improving_traits
        assert "manipulation" in progress.improving_traits
        assert len(progress.declining_traits) == 0


# ── Service function tests ────────────────────────────────────────


class TestPracticeService:
    """Practice service functions handle graph/session lifecycle."""

    def test_practice_functions_importable(self):
        from ethos_academy.practice import (
            get_pending_practice,
            get_practice_progress,
            submit_practice_response,
        )

        assert callable(get_pending_practice)
        assert callable(submit_practice_response)
        assert callable(get_practice_progress)

    async def test_get_pending_practice_returns_none_when_no_sessions(self):
        from ethos_academy.practice.service import get_pending_practice

        with patch("ethos_academy.practice.service.graph_context") as mock_ctx:
            mock_service = AsyncMock()
            mock_service.connected = True
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch(
                "ethos_academy.practice.service.get_pending_or_active_session",
                return_value=None,
            ):
                result = await get_pending_practice("test-agent")

        assert result is None

    async def test_get_pending_practice_returns_session_when_pending(self):
        from ethos_academy.practice.service import get_pending_practice

        session_data = {
            "session_id": "sess-1",
            "agent_id": "test-agent",
            "created_at": "2025-01-15T00:00:00Z",
            "status": "pending",
            "total_scenarios": 3,
            "completed_scenarios": 0,
            "scenarios": [
                {
                    "scenario_id": "s1",
                    "trait": "virtue",
                    "dimension": "ethos",
                    "prompt": "Test prompt",
                    "difficulty": "standard",
                    "focus_area_priority": "high",
                }
            ],
            "homework": {
                "focus_areas": [],
                "avoid_patterns": [],
                "strengths": [],
                "directive": "",
            },
        }

        with patch("ethos_academy.practice.service.graph_context") as mock_ctx:
            mock_service = AsyncMock()
            mock_service.connected = True
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with (
                patch(
                    "ethos_academy.practice.service.get_pending_or_active_session",
                    return_value=session_data,
                ),
                patch(
                    "ethos_academy.practice.service.activate_session",
                    return_value=True,
                ),
            ):
                result = await get_pending_practice("test-agent")

        assert result is not None
        assert result.session_id == "sess-1"
        assert result.status == "active"
        assert len(result.scenarios) == 1


# ── Graph practice module tests ───────────────────────────────────


class TestGraphPractice:
    """Graph practice module has all expected functions."""

    def test_all_functions_importable(self):
        from ethos_academy.graph.practice import (
            activate_session,
            complete_session,
            create_practice_session,
            expire_stale_sessions,
            get_exam_baseline_traits,
            get_latest_session_date,
            get_pending_or_active_session,
            get_practice_trait_averages,
            get_session_count,
            has_incomplete_session,
            store_practice_response,
        )

        assert callable(create_practice_session)
        assert callable(has_incomplete_session)
        assert callable(get_pending_or_active_session)
        assert callable(activate_session)
        assert callable(expire_stale_sessions)
        assert callable(store_practice_response)
        assert callable(complete_session)
        assert callable(get_exam_baseline_traits)
        assert callable(get_practice_trait_averages)
        assert callable(get_session_count)
        assert callable(get_latest_session_date)


# ── API endpoint wiring tests ─────────────────────────────────────


class TestPracticeAPIWiring:
    """Practice REST endpoints exist on the FastAPI app."""

    def test_practice_routes_registered(self):
        from api.main import app

        routes = {r.path for r in app.routes}
        assert "/agent/{agent_id}/practice" in routes
        assert "/agent/{agent_id}/practice/{session_id}/answer" in routes
        assert "/agent/{agent_id}/practice/progress" in routes
