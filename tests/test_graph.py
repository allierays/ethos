"""TDD tests for ethos.graph domain — GraphService, write, read, network.

Unit tests that mock the Neo4j driver. Integration tests live in test_graph_integration.py.
"""

from unittest.mock import AsyncMock, patch


from ethos_academy.shared.models import EvaluationResult


# ── GraphService ─────────────────────────────────────────────────────


class TestGraphService:
    """GraphService manages Neo4j driver lifecycle (async)."""

    def test_init_without_config(self):
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        assert gs._driver is None

    async def test_connect_and_close(self):
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        with patch("ethos_academy.graph.service.AsyncGraphDatabase") as mock_gdb:
            mock_driver = AsyncMock()
            mock_gdb.driver.return_value = mock_driver
            await gs.connect(
                uri="bolt://localhost:7694", user="neo4j", password="password"
            )
            mock_gdb.driver.assert_called_once()
            assert gs._driver is not None
            await gs.close()
            mock_driver.close.assert_called_once()

    async def test_close_when_not_connected(self):
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        await gs.close()  # Should not raise

    async def test_connect_failure_returns_none(self):
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        with patch("ethos_academy.graph.service.AsyncGraphDatabase") as mock_gdb:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity.side_effect = Exception(
                "Connection refused"
            )
            mock_gdb.driver.return_value = mock_driver
            await gs.connect(uri="bolt://bad:9999", user="neo4j", password="password")
            assert gs._driver is None

    async def test_execute_query_delegates(self):
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        mock_driver = AsyncMock()
        gs._driver = mock_driver
        mock_driver.execute_query.return_value = ([], None, None)
        await gs.execute_query("RETURN 1")
        mock_driver.execute_query.assert_called_once()

    async def test_execute_query_when_not_connected(self):
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await gs.execute_query("RETURN 1")
        assert result == ([], None, None)


# ── write.py ─────────────────────────────────────────────────────────


class TestStoreEvaluation:
    """store_evaluation() merges Agent and Evaluation nodes."""

    async def test_store_calls_execute_query(self):
        from ethos_academy.graph.write import store_evaluation
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.return_value = ([], None, None)

        result = EvaluationResult(
            evaluation_id="eval-123",
            ethos=0.8,
            logos=0.7,
            pathos=0.6,
            phronesis="trustworthy",
            routing_tier="standard",
        )
        await store_evaluation(gs, "agent-001", result)
        assert gs._driver.execute_query.called

    async def test_store_graceful_on_failure(self):
        from ethos_academy.graph.write import store_evaluation
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")

        result = EvaluationResult(evaluation_id="eval-456")
        # Should not raise
        await store_evaluation(gs, "agent-001", result)

    async def test_store_when_not_connected(self):
        from ethos_academy.graph.write import store_evaluation
        from ethos_academy.graph.service import GraphService

        gs = GraphService()  # No driver
        result = EvaluationResult(evaluation_id="eval-789")
        # Should not raise
        await store_evaluation(gs, "agent-001", result)

    async def test_store_skips_duplicate_hash(self):
        """Duplicate message_hash for same agent should be skipped."""
        from ethos_academy.graph.write import store_evaluation
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()

        # First call: no existing evaluation found
        # execute_query is called 3 times: dup check, trend fetch, store
        gs._driver.execute_query.side_effect = [
            ([], None, None),  # dup check returns empty → no duplicate
            ([], None, None),  # trend history fetch
            ([], None, None),  # store query succeeds
        ]

        result = EvaluationResult(evaluation_id="eval-dup-1")
        await store_evaluation(gs, "agent-001", result, message_hash="hash123")
        assert gs._driver.execute_query.call_count == 3

        # Second call: duplicate found
        gs._driver.execute_query.reset_mock()
        gs._driver.execute_query.side_effect = [
            ([{"existing_id": "eval-dup-1"}], None, None),  # dup check finds match
        ]

        result2 = EvaluationResult(evaluation_id="eval-dup-2")
        await store_evaluation(gs, "agent-001", result2, message_hash="hash123")
        # Only the dup check query should be called, not the store
        assert gs._driver.execute_query.call_count == 1

    async def test_store_allows_different_hash(self):
        """Different message hashes create separate evaluations."""
        from ethos_academy.graph.write import store_evaluation
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()

        # Both calls: no duplicate found
        gs._driver.execute_query.side_effect = [
            ([], None, None),  # dup check for hash-A
            ([], None, None),  # trend fetch for hash-A
            ([], None, None),  # store for hash-A
            ([], None, None),  # dup check for hash-B
            ([], None, None),  # trend fetch for hash-B
            ([], None, None),  # store for hash-B
        ]

        r1 = EvaluationResult(evaluation_id="eval-a")
        await store_evaluation(gs, "agent-001", r1, message_hash="hash-A")
        r2 = EvaluationResult(evaluation_id="eval-b")
        await store_evaluation(gs, "agent-001", r2, message_hash="hash-B")
        assert (
            gs._driver.execute_query.call_count == 6
        )  # 2 checks + 2 trend fetches + 2 stores

    async def test_store_empty_hash_skips_dedup(self):
        """Empty message_hash skips dedup check, always creates."""
        from ethos_academy.graph.write import store_evaluation
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.return_value = ([], None, None)

        result = EvaluationResult(evaluation_id="eval-no-hash")
        await store_evaluation(gs, "agent-001", result, message_hash="")
        # trend fetch + store (no dup check)
        assert gs._driver.execute_query.call_count == 2

    async def test_store_with_message_timestamp(self):
        """message_timestamp parameter is passed to the query."""
        from ethos_academy.graph.write import store_evaluation
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.return_value = ([], None, None)

        result = EvaluationResult(evaluation_id="eval-ts")
        await store_evaluation(
            gs,
            "agent-001",
            result,
            message_timestamp="2026-02-09T06:38:42+00:00",
        )
        call_args = gs._driver.execute_query.call_args
        assert "2026-02-09T06:38:42+00:00" in str(call_args)

    async def test_store_uses_raw_agent_id(self):
        from ethos_academy.graph.write import store_evaluation
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.return_value = ([], None, None)

        result = EvaluationResult(evaluation_id="eval-raw")
        await store_evaluation(gs, "agent-001", result)

        # Check that the raw agent_id is passed directly (no hashing)
        call_args = gs._driver.execute_query.call_args
        assert "agent-001" in str(call_args)


# ── read.py ──────────────────────────────────────────────────────────


class TestGetEvaluationHistory:
    """get_evaluation_history() returns list of evaluation dicts."""

    async def test_returns_list(self):
        from ethos_academy.graph.read import get_evaluation_history
        from ethos_academy.graph.service import GraphService

        gs = GraphService()  # No driver
        result = await get_evaluation_history(gs, "agent-001")
        assert isinstance(result, list)

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.read import get_evaluation_history
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_evaluation_history(gs, "agent-001")
        assert result == []

    async def test_returns_empty_on_failure(self):
        from ethos_academy.graph.read import get_evaluation_history
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_evaluation_history(gs, "agent-001")
        assert result == []

    async def test_default_limit(self):
        from ethos_academy.graph.read import get_evaluation_history
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.return_value = ([], None, None)
        await get_evaluation_history(gs, "agent-001")
        call_args = str(gs._driver.execute_query.call_args)
        assert "10" in call_args  # default limit=10


class TestGetAgentProfile:
    """get_agent_profile() returns dict with agent stats."""

    async def test_returns_dict(self):
        from ethos_academy.graph.read import get_agent_profile
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_agent_profile(gs, "agent-001")
        assert isinstance(result, dict)

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.read import get_agent_profile
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_agent_profile(gs, "agent-001")
        assert result == {}

    async def test_returns_empty_on_failure(self):
        from ethos_academy.graph.read import get_agent_profile
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_agent_profile(gs, "agent-001")
        assert result == {}


# ── alumni.py ────────────────────────────────────────────────────────


class TestGetAlumniAverages:
    """get_alumni_averages() returns per-trait averages across all agents."""

    async def test_returns_dict(self):
        from ethos_academy.graph.alumni import get_alumni_averages
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_alumni_averages(gs)
        assert isinstance(result, dict)

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.alumni import get_alumni_averages
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_alumni_averages(gs)
        assert result == {}

    async def test_returns_empty_on_failure(self):
        from ethos_academy.graph.alumni import get_alumni_averages
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_alumni_averages(gs)
        assert result == {}


# ── balance.py ────────────────────────────────────────────────────────


class TestGetAgentBalance:
    """get_agent_balance() returns dimension balance analysis for one agent."""

    async def test_returns_dict(self):
        from ethos_academy.graph.balance import get_agent_balance
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_agent_balance(gs, "agent-001")
        assert isinstance(result, dict)

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.balance import get_agent_balance
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_agent_balance(gs, "agent-001")
        assert result == {}

    async def test_returns_empty_on_failure(self):
        from ethos_academy.graph.balance import get_agent_balance
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_agent_balance(gs, "agent-001")
        assert result == {}


class TestGetBalanceVsPhronesis:
    """get_balance_vs_phronesis() returns balance-phronesis correlation across agents."""

    async def test_returns_list(self):
        from ethos_academy.graph.balance import get_balance_vs_phronesis
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_balance_vs_phronesis(gs)
        assert isinstance(result, list)

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.balance import get_balance_vs_phronesis
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_balance_vs_phronesis(gs)
        assert result == []

    async def test_returns_empty_on_failure(self):
        from ethos_academy.graph.balance import get_balance_vs_phronesis
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_balance_vs_phronesis(gs)
        assert result == []


class TestGetDimensionGaps:
    """get_dimension_gaps() finds agents with significant dimension gaps."""

    async def test_returns_list(self):
        from ethos_academy.graph.balance import get_dimension_gaps
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_dimension_gaps(gs)
        assert isinstance(result, list)

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.balance import get_dimension_gaps
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_dimension_gaps(gs)
        assert result == []

    async def test_returns_empty_on_failure(self):
        from ethos_academy.graph.balance import get_dimension_gaps
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_dimension_gaps(gs)
        assert result == []


class TestGetAlumniBalanceDistribution:
    """get_alumni_balance_distribution() returns network-wide balance stats."""

    async def test_returns_dict(self):
        from ethos_academy.graph.balance import get_alumni_balance_distribution
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_alumni_balance_distribution(gs)
        assert isinstance(result, dict)

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.balance import get_alumni_balance_distribution
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_alumni_balance_distribution(gs)
        assert result == {}

    async def test_returns_empty_on_failure(self):
        from ethos_academy.graph.balance import get_alumni_balance_distribution
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_alumni_balance_distribution(gs)
        assert result == {}


# ── Re-exports ───────────────────────────────────────────────────────


class TestReExports:
    """ethos/graph/__init__.py re-exports GraphService."""

    def test_import_graph_service(self):
        from ethos_academy.graph import GraphService

        assert GraphService is not None
