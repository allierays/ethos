"""Tests for search_evaluations and vector_search_evaluations graph queries."""

from __future__ import annotations

from unittest.mock import AsyncMock, PropertyMock


from ethos.graph.read import (
    _build_search_where,
    search_evaluations,
    vector_search_evaluations,
)
from ethos.graph.service import GraphService


# ---------------------------------------------------------------------------
# _build_search_where unit tests
# ---------------------------------------------------------------------------


class TestBuildSearchWhere:
    def test_no_filters(self):
        where, params = _build_search_where(
            search=None, agent_id=None, alignment_status=None, has_flags=None
        )
        assert where == ""
        assert params == {}

    def test_search_filter(self):
        where, params = _build_search_where(
            search="hello", agent_id=None, alignment_status=None, has_flags=None
        )
        assert "toLower(e.message_content) CONTAINS toLower($search)" in where
        assert "toLower(a.agent_name) CONTAINS toLower($search)" in where
        assert params["search"] == "hello"

    def test_agent_id_filter(self):
        where, params = _build_search_where(
            search=None, agent_id="agent-1", alignment_status=None, has_flags=None
        )
        assert "a.agent_id = $agent_id" in where
        assert params["agent_id"] == "agent-1"

    def test_alignment_status_filter(self):
        where, params = _build_search_where(
            search=None, agent_id=None, alignment_status="aligned", has_flags=None
        )
        assert "e.alignment_status = $alignment_status" in where
        assert params["alignment_status"] == "aligned"

    def test_has_flags_true(self):
        where, params = _build_search_where(
            search=None, agent_id=None, alignment_status=None, has_flags=True
        )
        assert "size(e.flags) > 0" in where

    def test_has_flags_false(self):
        where, params = _build_search_where(
            search=None, agent_id=None, alignment_status=None, has_flags=False
        )
        assert "size(e.flags) = 0" in where

    def test_combined_filters(self):
        where, params = _build_search_where(
            search="test",
            agent_id="agent-1",
            alignment_status="drifting",
            has_flags=True,
        )
        assert "WHERE" in where
        assert "AND" in where
        assert params["search"] == "test"
        assert params["agent_id"] == "agent-1"
        assert params["alignment_status"] == "drifting"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service(connected: bool = True) -> GraphService:
    """Create a mock GraphService."""
    service = GraphService()
    type(service).connected = PropertyMock(return_value=connected)
    service.execute_query = AsyncMock()
    return service


def _fake_eval_record(**overrides) -> dict:
    """Create a fake evaluation record dict as Neo4j would return."""
    base = {
        "evaluation_id": "eval-001",
        "agent_id": "agent-1",
        "agent_name": "TestAgent",
        "ethos": 0.8,
        "logos": 0.7,
        "pathos": 0.9,
        "alignment_status": "aligned",
        "flags": [],
        "direction": "incoming",
        "message_content": "Hello world",
        "created_at": "2025-01-01T00:00:00Z",
        "phronesis": "developing",
        "scoring_reasoning": "Good message",
        "intent_rhetorical_mode": "informational",
        "intent_primary_intent": "inform",
        "intent_cost_to_reader": "none",
        "intent_stakes_reality": "real",
        "intent_proportionality": "proportional",
        "intent_persona_type": "real_identity",
        "intent_relational_quality": "present",
        "trait_virtue": 0.8,
        "trait_goodwill": 0.7,
        "trait_manipulation": 0.1,
        "trait_deception": 0.1,
        "trait_accuracy": 0.8,
        "trait_reasoning": 0.7,
        "trait_fabrication": 0.1,
        "trait_broken_logic": 0.1,
        "trait_recognition": 0.8,
        "trait_compassion": 0.7,
        "trait_dismissal": 0.1,
        "trait_exploitation": 0.1,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# search_evaluations tests
# ---------------------------------------------------------------------------


class TestSearchEvaluations:
    async def test_returns_empty_when_disconnected(self):
        service = _make_service(connected=False)
        items, total = await search_evaluations(service)
        assert items == []
        assert total == 0
        service.execute_query.assert_not_called()

    async def test_returns_items_and_count(self):
        service = _make_service()
        count_record = {"total": 2}
        data_records = [
            _fake_eval_record(evaluation_id="eval-001"),
            _fake_eval_record(evaluation_id="eval-002"),
        ]

        service.execute_query.side_effect = [
            ([count_record], None, None),
            (data_records, None, None),
        ]

        items, total = await search_evaluations(service)
        assert total == 2
        assert len(items) == 2
        assert items[0]["evaluation_id"] == "eval-001"
        assert items[1]["evaluation_id"] == "eval-002"

    async def test_returns_empty_when_count_is_zero(self):
        service = _make_service()
        service.execute_query.side_effect = [
            ([{"total": 0}], None, None),
        ]

        items, total = await search_evaluations(service)
        assert items == []
        assert total == 0
        # Only count query should run, not data query
        assert service.execute_query.call_count == 1

    async def test_search_filter_in_query(self):
        service = _make_service()
        service.execute_query.side_effect = [
            ([{"total": 1}], None, None),
            ([_fake_eval_record()], None, None),
        ]

        await search_evaluations(service, search="hello")

        # Count query should have search param
        count_call = service.execute_query.call_args_list[0]
        count_query = count_call[0][0]
        count_params = count_call[0][1]
        assert "CONTAINS" in count_query
        assert count_params["search"] == "hello"

    async def test_agent_id_filter_in_query(self):
        service = _make_service()
        service.execute_query.side_effect = [
            ([{"total": 1}], None, None),
            ([_fake_eval_record()], None, None),
        ]

        await search_evaluations(service, agent_id="agent-1")

        count_params = service.execute_query.call_args_list[0][0][1]
        assert count_params["agent_id"] == "agent-1"

    async def test_sort_by_score(self):
        service = _make_service()
        service.execute_query.side_effect = [
            ([{"total": 1}], None, None),
            ([_fake_eval_record()], None, None),
        ]

        await search_evaluations(service, sort_by="score", sort_order="asc")

        data_query = service.execute_query.call_args_list[1][0][0]
        assert "(e.ethos + e.logos + e.pathos) / 3.0" in data_query
        assert "ASC" in data_query

    async def test_sort_by_agent(self):
        service = _make_service()
        service.execute_query.side_effect = [
            ([{"total": 1}], None, None),
            ([_fake_eval_record()], None, None),
        ]

        await search_evaluations(service, sort_by="agent")

        data_query = service.execute_query.call_args_list[1][0][0]
        assert "a.agent_name" in data_query

    async def test_invalid_sort_defaults_to_date(self):
        service = _make_service()
        service.execute_query.side_effect = [
            ([{"total": 1}], None, None),
            ([_fake_eval_record()], None, None),
        ]

        await search_evaluations(service, sort_by="invalid")

        data_query = service.execute_query.call_args_list[1][0][0]
        assert "e.created_at" in data_query

    async def test_pagination_params(self):
        service = _make_service()
        service.execute_query.side_effect = [
            ([{"total": 50}], None, None),
            ([_fake_eval_record()], None, None),
        ]

        await search_evaluations(service, skip=20, limit=10)

        data_params = service.execute_query.call_args_list[1][0][1]
        assert data_params["skip"] == 20
        assert data_params["limit"] == 10

    async def test_graceful_on_exception(self):
        service = _make_service()
        service.execute_query.side_effect = Exception("Neo4j down")

        items, total = await search_evaluations(service)
        assert items == []
        assert total == 0


# ---------------------------------------------------------------------------
# vector_search_evaluations tests
# ---------------------------------------------------------------------------


class TestVectorSearchEvaluations:
    async def test_returns_empty_when_disconnected(self):
        service = _make_service(connected=False)
        results = await vector_search_evaluations(service, embedding=[0.1] * 128, k=5)
        assert results == []
        service.execute_query.assert_not_called()

    async def test_returns_results_with_similarity(self):
        service = _make_service()
        record = {**_fake_eval_record(), "similarity": 0.95}
        service.execute_query.return_value = ([record], None, None)

        results = await vector_search_evaluations(service, embedding=[0.1] * 128, k=5)
        assert len(results) == 1
        assert results[0]["similarity"] == 0.95

    async def test_query_uses_vector_index(self):
        service = _make_service()
        service.execute_query.return_value = ([], None, None)

        await vector_search_evaluations(service, embedding=[0.1] * 128, k=5)

        query = service.execute_query.call_args[0][0]
        assert "db.index.vector.queryNodes" in query
        assert "evaluation_embeddings" in query

    async def test_passes_embedding_and_k_params(self):
        service = _make_service()
        service.execute_query.return_value = ([], None, None)

        embedding = [0.5] * 64
        await vector_search_evaluations(service, embedding=embedding, k=3)

        params = service.execute_query.call_args[0][1]
        assert params["embedding"] == embedding
        assert params["k"] == 3

    async def test_filters_by_agent_id(self):
        service = _make_service()
        service.execute_query.return_value = ([], None, None)

        await vector_search_evaluations(
            service, embedding=[0.1] * 128, k=5, agent_id="agent-1"
        )

        query = service.execute_query.call_args[0][0]
        params = service.execute_query.call_args[0][1]
        assert "a.agent_id = $agent_id" in query
        assert params["agent_id"] == "agent-1"

    async def test_filters_by_alignment_status(self):
        service = _make_service()
        service.execute_query.return_value = ([], None, None)

        await vector_search_evaluations(
            service, embedding=[0.1] * 128, k=5, alignment_status="aligned"
        )

        query = service.execute_query.call_args[0][0]
        params = service.execute_query.call_args[0][1]
        assert "e.alignment_status = $alignment_status" in query
        assert params["alignment_status"] == "aligned"

    async def test_filters_has_flags(self):
        service = _make_service()
        service.execute_query.return_value = ([], None, None)

        await vector_search_evaluations(
            service, embedding=[0.1] * 128, k=5, has_flags=True
        )

        query = service.execute_query.call_args[0][0]
        assert "size(e.flags) > 0" in query

    async def test_graceful_on_exception(self):
        service = _make_service()
        service.execute_query.side_effect = Exception("Neo4j down")

        results = await vector_search_evaluations(service, embedding=[0.1] * 128, k=5)
        assert results == []
