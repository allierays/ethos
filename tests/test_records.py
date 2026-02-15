"""Tests for search_evaluations, vector_search_evaluations, and GET /records."""

from __future__ import annotations

from unittest.mock import AsyncMock, PropertyMock, patch

from fastapi.testclient import TestClient

from api.main import app
from ethos_academy.graph.read import (
    _build_search_where,
    search_evaluations,
    vector_search_evaluations,
)
from ethos_academy.graph.service import GraphService
from ethos_academy.shared.models import (
    DetectedIndicatorSummary,
    RecordItem,
    RecordsResult,
)

client = TestClient(app)


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
        "model_used": "claude-sonnet-4-20250514",
        "agent_model": "gpt-4",
        "routing_tier": "focused",
        "keyword_density": 0.05,
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
        "indicators": [
            {
                "id": "ind-001",
                "name": "Hedging language",
                "trait": "deception",
                "description": "Uses qualifiers to avoid commitment",
                "confidence": 0.85,
                "severity": 0.3,
                "evidence": "Found hedging in response",
            },
        ],
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


# ---------------------------------------------------------------------------
# GET /records integration tests
# ---------------------------------------------------------------------------


def _mock_records_result(**overrides) -> RecordsResult:
    """Build a RecordsResult with sensible defaults."""
    defaults = dict(
        items=[
            RecordItem(
                evaluation_id="eval-001",
                agent_id="agent-1",
                agent_name="TestAgent",
                ethos=0.8,
                logos=0.7,
                pathos=0.9,
                overall=0.8,
                alignment_status="aligned",
                message_content="Hello world",
                created_at="2025-01-01T00:00:00Z",
            ),
        ],
        total=1,
        page=0,
        page_size=20,
        total_pages=1,
    )
    defaults.update(overrides)
    return RecordsResult(**defaults)


class TestRecordsEndpoint:
    def test_returns_200_with_correct_shape(self):
        mock_result = _mock_records_result()
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.get("/records")

        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 1
        assert data["items"][0]["evaluation_id"] == "eval-001"

    def test_returns_empty_on_no_results(self):
        mock_result = RecordsResult()
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.get("/records")

        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_passes_search_query(self):
        mock_result = _mock_records_result()
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_fn:
            client.get("/records?q=hello")

        mock_fn.assert_called_once()
        assert mock_fn.call_args.kwargs["search"] == "hello"

    def test_passes_alignment_filter(self):
        mock_result = _mock_records_result()
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_fn:
            client.get("/records?alignment=drifting")

        assert mock_fn.call_args.kwargs["alignment_status"] == "drifting"

    def test_passes_agent_filter(self):
        mock_result = _mock_records_result()
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_fn:
            client.get("/records?agent=agent-1")

        assert mock_fn.call_args.kwargs["agent_id"] == "agent-1"

    def test_passes_flagged_filter(self):
        mock_result = _mock_records_result()
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_fn:
            client.get("/records?flagged=true")

        assert mock_fn.call_args.kwargs["has_flags"] is True

    def test_pagination_params_pass_through(self):
        mock_result = _mock_records_result(page=2, page_size=10)
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_fn:
            client.get("/records?page=2&size=10")

        assert mock_fn.call_args.kwargs["page"] == 2
        assert mock_fn.call_args.kwargs["page_size"] == 10

    def test_size_capped_at_50(self):
        mock_result = _mock_records_result()
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_fn:
            client.get("/records?size=100")

        assert mock_fn.call_args.kwargs["page_size"] == 50

    def test_sort_params_pass_through(self):
        mock_result = _mock_records_result()
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_fn:
            client.get("/records?sort=score&order=asc")

        assert mock_fn.call_args.kwargs["sort_by"] == "score"
        assert mock_fn.call_args.kwargs["sort_order"] == "asc"

    def test_overall_score_computed(self):
        """Verify overall = (ethos + logos + pathos) / 3."""
        mock_result = _mock_records_result(
            items=[
                RecordItem(
                    evaluation_id="eval-002",
                    ethos=0.6,
                    logos=0.9,
                    pathos=0.3,
                    overall=0.6,
                ),
            ],
        )
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.get("/records")

        item = resp.json()["items"][0]
        assert item["overall"] == 0.6

    def test_total_pages_in_response(self):
        mock_result = _mock_records_result(total=45, page_size=20, total_pages=3)
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.get("/records")

        assert resp.json()["total_pages"] == 3

    def test_detected_indicators_in_response(self):
        """Verify detected_indicators round-trip through the API."""
        mock_result = _mock_records_result(
            items=[
                RecordItem(
                    evaluation_id="eval-ind",
                    agent_id="agent-1",
                    agent_name="TestAgent",
                    ethos=0.8,
                    logos=0.7,
                    pathos=0.9,
                    overall=0.8,
                    model_used="claude-sonnet-4-20250514",
                    agent_model="gpt-4",
                    routing_tier="focused",
                    keyword_density=0.05,
                    detected_indicators=[
                        DetectedIndicatorSummary(
                            id="ind-001",
                            name="Hedging language",
                            trait="deception",
                            description="Uses qualifiers",
                            confidence=0.85,
                            severity=0.3,
                            evidence="Found hedging",
                        ),
                    ],
                ),
            ],
        )
        with patch(
            "api.main.search_records",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.get("/records")

        item = resp.json()["items"][0]
        assert item["model_used"] == "claude-sonnet-4-20250514"
        assert item["agent_model"] == "gpt-4"
        assert item["routing_tier"] == "focused"
        assert item["keyword_density"] == 0.05
        assert len(item["detected_indicators"]) == 1
        ind = item["detected_indicators"][0]
        assert ind["id"] == "ind-001"
        assert ind["name"] == "Hedging language"
        assert ind["trait"] == "deception"
        assert ind["confidence"] == 0.85
        assert ind["severity"] == 0.3
