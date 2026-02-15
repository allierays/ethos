"""Tests for graph insight queries and domain functions.

Three layers tested:
1. Graph query functions (ethos/graph/insights.py) — mock Neo4j driver
2. Domain functions (ethos/graph_insights.py) — mock graph_context and sub-functions
3. Helper functions — pure computation, no mocks needed
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch


# ── Helper to build mock graph_context ────────────────────────────────────


def _make_mock_graph_context(mock_service):
    """Create a mock async context manager for graph_context."""

    @asynccontextmanager
    async def mock_graph_ctx():
        yield mock_service

    return mock_graph_ctx


def _make_failing_graph_context():
    """Create a graph_context that raises on entry."""

    @asynccontextmanager
    async def failing_ctx():
        raise RuntimeError("Connection refused")
        yield  # noqa: unreachable

    return failing_ctx


# ═══════════════════════════════════════════════════════════════════════════
# Layer 1: Graph query functions (ethos/graph/insights.py)
# ═══════════════════════════════════════════════════════════════════════════


class TestGetTopologyStats:
    """get_topology_stats() returns node/rel counts from Neo4j."""

    async def test_returns_dict_with_data(self):
        from ethos_academy.graph.insights import get_topology_stats
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = [
            # node counts
            (
                [{"label": "Agent", "count": 5}, {"label": "Evaluation", "count": 50}],
                None,
                None,
            ),
            # rel counts
            (
                [
                    {"rel_type": "EVALUATED", "count": 50},
                    {"rel_type": "PRECEDES", "count": 45},
                ],
                None,
                None,
            ),
            # agent/eval totals
            ([{"agents": 5, "evaluations": 50}], None, None),
        ]

        result = await get_topology_stats(gs)

        assert result["node_counts"]["Agent"] == 5
        assert result["node_counts"]["Evaluation"] == 50
        assert result["relationship_counts"]["EVALUATED"] == 50
        assert result["total_nodes"] == 55
        assert result["total_relationships"] == 95
        assert result["agent_count"] == 5
        assert result["evaluation_count"] == 50

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.insights import get_topology_stats
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_topology_stats(gs)
        assert result == {}

    async def test_returns_zeroed_stats_on_query_failure(self):
        from ethos_academy.graph.insights import get_topology_stats
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_topology_stats(gs)
        # GraphService.execute_query catches exceptions and returns ([], None, None),
        # so the function builds a valid dict with zero counts
        assert result["total_nodes"] == 0
        assert result["total_relationships"] == 0
        assert result["agent_count"] == 0


class TestGetEarlyWarningData:
    """get_early_warning_data() finds indicators that predict trouble."""

    async def test_returns_list_with_data(self):
        from ethos_academy.graph.insights import get_early_warning_data
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.return_value = (
            [
                {
                    "indicator_id": "MAN-CONSENSUS",
                    "indicator_name": "manufactured_consensus",
                    "trait": "manipulation",
                    "agent_count": 3,
                    "trouble_count": 2,
                    "trouble_rate": 0.6667,
                },
            ],
            None,
            None,
        )

        result = await get_early_warning_data(gs)

        assert len(result) == 1
        assert result[0]["indicator_id"] == "MAN-CONSENSUS"
        assert result[0]["trouble_rate"] == 0.6667

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.insights import get_early_warning_data
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_early_warning_data(gs)
        assert result == []

    async def test_returns_empty_on_failure(self):
        from ethos_academy.graph.insights import get_early_warning_data
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_early_warning_data(gs)
        assert result == []


class TestGetAllSabotageStatus:
    """get_all_sabotage_status() returns EXHIBITS_PATTERN across agents."""

    async def test_returns_list_with_data(self):
        from ethos_academy.graph.insights import get_all_sabotage_status
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.return_value = (
            [
                {
                    "agent_id": "agent-1",
                    "agent_name": "TestBot",
                    "pattern_id": "SP-01",
                    "pattern_name": "Diffuse Sandbagging",
                    "pattern_description": "desc",
                    "severity": "warning",
                    "confidence": 0.75,
                    "current_stage": 3,
                    "first_seen": "2026-01-01",
                    "last_seen": "2026-02-01",
                    "occurrence_count": 5,
                },
            ],
            None,
            None,
        )

        result = await get_all_sabotage_status(gs)

        assert len(result) == 1
        assert result[0]["agent_id"] == "agent-1"
        assert result[0]["pattern_id"] == "SP-01"
        assert result[0]["confidence"] == 0.75

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.insights import get_all_sabotage_status
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_all_sabotage_status(gs)
        assert result == []

    async def test_returns_empty_on_failure(self):
        from ethos_academy.graph.insights import get_all_sabotage_status
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_all_sabotage_status(gs)
        assert result == []


class TestGetAgentSabotageStatus:
    """get_agent_sabotage_status() returns per-agent EXHIBITS_PATTERN with stage detail."""

    async def test_returns_list_with_matched_indicators(self):
        from ethos_academy.graph.insights import get_agent_sabotage_status
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.return_value = (
            [
                {
                    "agent_id": "agent-1",
                    "pattern_id": "SP-02",
                    "pattern_name": "Incremental Boundary Testing",
                    "pattern_description": "desc",
                    "severity": "critical",
                    "confidence": 0.6,
                    "current_stage": 2,
                    "total_stages": 4,
                    "matched_indicators": ["MAN-CONSENSUS", "DEC-FRAME"],
                    "first_seen": "2026-01-15",
                    "last_seen": "2026-02-10",
                    "occurrence_count": 8,
                },
            ],
            None,
            None,
        )

        result = await get_agent_sabotage_status(gs, "agent-1")

        assert len(result) == 1
        assert result[0]["total_stages"] == 4
        assert result[0]["matched_indicators"] == ["MAN-CONSENSUS", "DEC-FRAME"]

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.insights import get_agent_sabotage_status
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_agent_sabotage_status(gs, "agent-1")
        assert result == []

    async def test_returns_empty_on_failure(self):
        from ethos_academy.graph.insights import get_agent_sabotage_status
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_agent_sabotage_status(gs, "agent-1")
        assert result == []


class TestGetGlobalConstitutionalRisk:
    """get_global_constitutional_risk() aggregates 5-hop risk across agents."""

    async def test_returns_list_with_data(self):
        from ethos_academy.graph.insights import get_global_constitutional_risk
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.return_value = (
            [
                {
                    "value_name": "Truthfulness",
                    "priority": 1,
                    "impact": "undermines",
                    "trait": "deception",
                    "polarity": "negative",
                    "indicator_id": "DEC-FRAME",
                    "indicator_name": "frame_control",
                    "detection_count": 12,
                    "agent_count": 4,
                    "avg_confidence": 0.82,
                },
            ],
            None,
            None,
        )

        result = await get_global_constitutional_risk(gs)

        assert len(result) == 1
        assert result[0]["value_name"] == "Truthfulness"
        assert result[0]["detection_count"] == 12
        assert result[0]["avg_confidence"] == 0.82

    async def test_returns_empty_when_not_connected(self):
        from ethos_academy.graph.insights import get_global_constitutional_risk
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        result = await get_global_constitutional_risk(gs)
        assert result == []

    async def test_returns_empty_on_failure(self):
        from ethos_academy.graph.insights import get_global_constitutional_risk
        from ethos_academy.graph.service import GraphService

        gs = GraphService()
        gs._driver = AsyncMock()
        gs._driver.execute_query.side_effect = Exception("Neo4j down")
        result = await get_global_constitutional_risk(gs)
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════
# Layer 2: Domain functions (ethos/graph_insights.py)
# ═══════════════════════════════════════════════════════════════════════════


class TestGetCharacterArc:
    """get_character_arc() traces an agent's character formation over time."""

    @patch("ethos_academy.graph_insights.get_drift_timeline", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_arc_with_phases(self, mock_ctx, mock_timeline):
        from ethos_academy.graph_insights import get_character_arc

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        # 9 evaluations = 3 per phase
        mock_timeline.return_value = [
            {
                "eval_id": f"e-{i}",
                "ethos": 0.5 + i * 0.03,
                "logos": 0.6,
                "pathos": 0.7,
                "alignment": "aligned",
                "flags": [],
                "indicators": [],
                "created_at": f"2026-01-{i + 1:02d}",
            }
            for i in range(9)
        ]

        result = await get_character_arc("agent-1")

        assert result["agent_id"] == "agent-1"
        assert result["total_evaluations"] == 9
        assert len(result["phases"]) == 3
        assert result["phases"][0]["phase"] == "early"
        assert result["phases"][1]["phase"] == "middle"
        assert result["phases"][2]["phase"] == "recent"
        assert result["arc"] in ("growth", "decline", "steady")

    @patch("ethos_academy.graph_insights.get_drift_timeline", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_detects_growth_arc(self, mock_ctx, mock_timeline):
        from ethos_academy.graph_insights import get_character_arc

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        # Early scores low, late scores high = growth
        timeline = []
        for i in range(9):
            score = 0.4 + i * 0.06
            timeline.append(
                {
                    "eval_id": f"e-{i}",
                    "ethos": score,
                    "logos": score,
                    "pathos": score,
                    "alignment": "aligned",
                    "flags": [],
                    "indicators": [],
                    "created_at": f"2026-01-{i + 1:02d}",
                }
            )
        mock_timeline.return_value = timeline

        result = await get_character_arc("agent-1")
        assert result["arc"] == "growth"

    @patch("ethos_academy.graph_insights.get_drift_timeline", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_detects_decline_arc(self, mock_ctx, mock_timeline):
        from ethos_academy.graph_insights import get_character_arc

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        # Early scores high, late scores low = decline
        timeline = []
        for i in range(9):
            score = 0.9 - i * 0.06
            timeline.append(
                {
                    "eval_id": f"e-{i}",
                    "ethos": score,
                    "logos": score,
                    "pathos": score,
                    "alignment": "aligned",
                    "flags": [],
                    "indicators": [],
                    "created_at": f"2026-01-{i + 1:02d}",
                }
            )
        mock_timeline.return_value = timeline

        result = await get_character_arc("agent-1")
        assert result["arc"] == "decline"

    @patch("ethos_academy.graph_insights.get_drift_timeline", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_detects_turning_points(self, mock_ctx, mock_timeline):
        from ethos_academy.graph_insights import get_character_arc

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        # Sudden drop at index 3
        timeline = [
            {
                "eval_id": f"e-{i}",
                "ethos": 0.8,
                "logos": 0.8,
                "pathos": 0.8,
                "alignment": "aligned",
                "flags": [],
                "indicators": [],
                "created_at": f"2026-01-{i + 1:02d}",
            }
            for i in range(3)
        ]
        timeline.append(
            {
                "eval_id": "e-3",
                "ethos": 0.3,
                "logos": 0.3,
                "pathos": 0.3,
                "alignment": "misaligned",
                "flags": ["manipulation"],
                "indicators": ["MAN-CONSENSUS"],
                "created_at": "2026-01-04",
            }
        )
        timeline.extend(
            [
                {
                    "eval_id": f"e-{i}",
                    "ethos": 0.7,
                    "logos": 0.7,
                    "pathos": 0.7,
                    "alignment": "aligned",
                    "flags": [],
                    "indicators": [],
                    "created_at": f"2026-01-{i + 1:02d}",
                }
                for i in range(4, 9)
            ]
        )
        mock_timeline.return_value = timeline

        result = await get_character_arc("agent-1")

        assert len(result["turning_points"]) >= 1
        tp = result["turning_points"][0]
        assert tp["direction"] == "regression"
        assert tp["delta"] < 0

    @patch("ethos_academy.graph_insights.get_drift_timeline", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_no_data_for_empty_timeline(self, mock_ctx, mock_timeline):
        from ethos_academy.graph_insights import get_character_arc

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()
        mock_timeline.return_value = []

        result = await get_character_arc("agent-1")

        assert result["arc"] == "no_data"
        assert result["phases"] == []
        assert result["total_evaluations"] == 0

    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_error_on_graph_failure(self, mock_ctx):
        from ethos_academy.graph_insights import get_character_arc

        mock_ctx.side_effect = lambda: _make_failing_graph_context()()

        result = await get_character_arc("agent-1")

        assert result["arc"] == "error"
        assert result["phases"] == []

    @patch("ethos_academy.graph_insights.get_drift_timeline", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_single_evaluation_returns_emerging(self, mock_ctx, mock_timeline):
        from ethos_academy.graph_insights import get_character_arc

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()
        mock_timeline.return_value = [
            {
                "eval_id": "e-0",
                "ethos": 0.7,
                "logos": 0.8,
                "pathos": 0.6,
                "alignment": "aligned",
                "flags": [],
                "indicators": [],
                "created_at": "2026-01-01",
            },
        ]

        result = await get_character_arc("agent-1")
        assert result["arc"] == "emerging"
        assert result["total_evaluations"] == 1


class TestGetConstitutionalRiskReport:
    """get_constitutional_risk_report() aggregates 5-hop risk data."""

    @patch(
        "ethos_academy.graph_insights.get_global_constitutional_risk",
        new_callable=AsyncMock,
    )
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_global_risk_groups_by_value(self, mock_ctx, mock_risk):
        from ethos_academy.graph_insights import get_constitutional_risk_report

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_risk.return_value = [
            {
                "value_name": "Truthfulness",
                "priority": 1,
                "impact": "undermines",
                "trait": "deception",
                "polarity": "negative",
                "indicator_id": "DEC-FRAME",
                "indicator_name": "frame_control",
                "detection_count": 10,
                "agent_count": 3,
                "avg_confidence": 0.8,
            },
            {
                "value_name": "Truthfulness",
                "priority": 1,
                "impact": "upholds",
                "trait": "accuracy",
                "polarity": "positive",
                "indicator_id": "ACC-CITE",
                "indicator_name": "source_citation",
                "detection_count": 5,
                "agent_count": 2,
                "avg_confidence": 0.9,
            },
            {
                "value_name": "Autonomy",
                "priority": 2,
                "impact": "undermines",
                "trait": "manipulation",
                "polarity": "negative",
                "indicator_id": "MAN-URG",
                "indicator_name": "false_urgency",
                "detection_count": 3,
                "agent_count": 1,
                "avg_confidence": 0.7,
            },
        ]

        result = await get_constitutional_risk_report()

        assert result["scope"] == "global"
        assert result["total_values_affected"] == 2

        # Truthfulness has more total detections, should be first
        values = result["at_risk_values"]
        assert values[0]["value"] == "Truthfulness"
        assert values[0]["total_detections"] == 15
        assert len(values[0]["threat_indicators"]) == 1
        assert len(values[0]["protective_indicators"]) == 1

    @patch(
        "ethos_academy.graph_insights.get_constitutional_trail", new_callable=AsyncMock
    )
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_agent_scoped_risk(self, mock_ctx, mock_trail):
        from ethos_academy.graph_insights import get_constitutional_risk_report

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_trail.return_value = [
            {
                "constitutional_value": "Truthfulness",
                "cv_priority": 1,
                "impact": "undermines",
                "trait": "deception",
                "trait_polarity": "negative",
                "indicator_id": "DEC-FRAME",
                "indicator_name": "frame_control",
                "eval_count": 4,
                "avg_confidence": 0.75,
                "sample_evidence": [],
            },
        ]

        result = await get_constitutional_risk_report(agent_id="agent-1")

        assert result["scope"] == "agent-1"
        assert result["total_values_affected"] == 1

    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_empty_on_graph_failure(self, mock_ctx):
        from ethos_academy.graph_insights import get_constitutional_risk_report

        mock_ctx.side_effect = lambda: _make_failing_graph_context()()

        result = await get_constitutional_risk_report()
        assert result["at_risk_values"] == []
        assert result["total_values_affected"] == 0


class TestFindSimilarAgents:
    """find_similar_agents() filters Jaccard similarity for one agent."""

    @patch("ethos_academy.graph_insights.get_similarity_data", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_matches_for_agent(self, mock_ctx, mock_sim):
        from ethos_academy.graph_insights import find_similar_agents

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_sim.return_value = [
            {
                "agent1_id": "agent-1",
                "agent1_name": "Bot A",
                "agent1_phronesis": 0.7,
                "agent2_id": "agent-2",
                "agent2_name": "Bot B",
                "agent2_phronesis": 0.6,
                "similarity": 0.8,
                "shared_indicators": ["MAN-CONSENSUS", "DEC-FRAME"],
            },
            {
                "agent1_id": "agent-3",
                "agent1_name": "Bot C",
                "agent1_phronesis": 0.9,
                "agent2_id": "agent-1",
                "agent2_name": "Bot A",
                "agent2_phronesis": 0.7,
                "similarity": 0.5,
                "shared_indicators": ["MAN-CONSENSUS"],
            },
            {
                "agent1_id": "agent-2",
                "agent1_name": "Bot B",
                "agent1_phronesis": 0.6,
                "agent2_id": "agent-3",
                "agent2_name": "Bot C",
                "agent2_phronesis": 0.9,
                "similarity": 0.3,
                "shared_indicators": ["DEC-FRAME"],
            },
        ]

        result = await find_similar_agents("agent-1")

        assert result["agent_id"] == "agent-1"
        assert result["total_matches"] == 2
        # Sorted by similarity desc
        assert result["similar_agents"][0]["agent_id"] == "agent-2"
        assert result["similar_agents"][0]["similarity"] == 0.8
        assert result["similar_agents"][1]["agent_id"] == "agent-3"
        assert result["similar_agents"][1]["similarity"] == 0.5

    @patch("ethos_academy.graph_insights.get_similarity_data", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_empty_when_no_matches(self, mock_ctx, mock_sim):
        from ethos_academy.graph_insights import find_similar_agents

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()
        mock_sim.return_value = []

        result = await find_similar_agents("lonely-agent")

        assert result["similar_agents"] == []
        assert result["total_matches"] == 0

    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_empty_on_graph_failure(self, mock_ctx):
        from ethos_academy.graph_insights import find_similar_agents

        mock_ctx.side_effect = lambda: _make_failing_graph_context()()

        result = await find_similar_agents("agent-1")
        assert result["similar_agents"] == []


class TestGetEarlyWarningIndicators:
    """get_early_warning_indicators() wraps early warning query data."""

    @patch(
        "ethos_academy.graph_insights.get_early_warning_data", new_callable=AsyncMock
    )
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_indicators_with_high_risk(self, mock_ctx, mock_data):
        from ethos_academy.graph_insights import get_early_warning_indicators

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_data.return_value = [
            {
                "indicator_id": "MAN-CONSENSUS",
                "indicator_name": "manufactured_consensus",
                "trait": "manipulation",
                "agent_count": 5,
                "trouble_count": 4,
                "trouble_rate": 0.8,
            },
            {
                "indicator_id": "ACC-CITE",
                "indicator_name": "source_citation",
                "trait": "accuracy",
                "agent_count": 3,
                "trouble_count": 1,
                "trouble_rate": 0.3333,
            },
        ]

        result = await get_early_warning_indicators()

        assert result["total_indicators"] == 2
        assert len(result["high_risk"]) == 1
        assert result["high_risk"][0]["indicator_id"] == "MAN-CONSENSUS"

    @patch(
        "ethos_academy.graph_insights.get_early_warning_data", new_callable=AsyncMock
    )
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_empty_when_no_data(self, mock_ctx, mock_data):
        from ethos_academy.graph_insights import get_early_warning_indicators

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()
        mock_data.return_value = []

        result = await get_early_warning_indicators()

        assert result["indicators"] == []
        assert result["high_risk"] == []

    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_empty_on_graph_failure(self, mock_ctx):
        from ethos_academy.graph_insights import get_early_warning_indicators

        mock_ctx.side_effect = lambda: _make_failing_graph_context()()

        result = await get_early_warning_indicators()
        assert result["indicators"] == []


class TestGetNetworkTopology:
    """get_network_topology() returns graph metadata."""

    @patch("ethos_academy.graph_insights.get_topology_stats", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_connected_with_stats(self, mock_ctx, mock_stats):
        from ethos_academy.graph_insights import get_network_topology

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_stats.return_value = {
            "node_counts": {"Agent": 5, "Evaluation": 50},
            "relationship_counts": {"EVALUATED": 50},
            "total_nodes": 55,
            "total_relationships": 50,
            "agent_count": 5,
            "evaluation_count": 50,
        }

        result = await get_network_topology()

        assert result["connected"] is True
        assert result["total_nodes"] == 55
        assert result["agent_count"] == 5

    @patch("ethos_academy.graph_insights.get_topology_stats", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_not_connected_when_empty(self, mock_ctx, mock_stats):
        from ethos_academy.graph_insights import get_network_topology

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()
        mock_stats.return_value = {}

        result = await get_network_topology()
        assert result["connected"] is False

    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_not_connected_on_graph_failure(self, mock_ctx):
        from ethos_academy.graph_insights import get_network_topology

        mock_ctx.side_effect = lambda: _make_failing_graph_context()()

        result = await get_network_topology()
        assert result["connected"] is False


class TestGetSabotagePathwayStatus:
    """get_sabotage_pathway_status() reads EXHIBITS_PATTERN relationships."""

    @patch(
        "ethos_academy.graph_insights.get_all_sabotage_status", new_callable=AsyncMock
    )
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_global_returns_active_and_emerging(self, mock_ctx, mock_status):
        from ethos_academy.graph_insights import get_sabotage_pathway_status

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_status.return_value = [
            {
                "agent_id": "a-1",
                "pattern_id": "SP-01",
                "confidence": 0.8,
                "pattern_name": "Diffuse Sandbagging",
                "severity": "warning",
            },
            {
                "agent_id": "a-2",
                "pattern_id": "SP-03",
                "confidence": 0.3,
                "pattern_name": "Gradual Value Drift",
                "severity": "info",
            },
        ]

        result = await get_sabotage_pathway_status()

        assert result["scope"] == "global"
        assert result["total_detected"] == 2
        assert result["active_count"] == 1
        assert result["emerging_count"] == 1

    @patch(
        "ethos_academy.graph_insights.get_agent_sabotage_status", new_callable=AsyncMock
    )
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_agent_scoped(self, mock_ctx, mock_status):
        from ethos_academy.graph_insights import get_sabotage_pathway_status

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()
        mock_status.return_value = []

        result = await get_sabotage_pathway_status(agent_id="agent-1")

        assert result["scope"] == "agent-1"
        assert result["total_detected"] == 0

    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_empty_on_graph_failure(self, mock_ctx):
        from ethos_academy.graph_insights import get_sabotage_pathway_status

        mock_ctx.side_effect = lambda: _make_failing_graph_context()()

        result = await get_sabotage_pathway_status()
        assert result["pathways"] == []
        assert result["active_count"] == 0


class TestCompareAgents:
    """compare_agents() pulls parallel profiles and computes deltas."""

    @patch("ethos_academy.graph_insights.get_agent_profile", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_compares_two_agents(self, mock_ctx, mock_profile):
        from ethos_academy.graph_insights import compare_agents

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()

        mock_profile.side_effect = [
            {
                "agent_id": "agent-1",
                "agent_name": "Bot A",
                "evaluation_count": 10,
                "dimension_averages": {"ethos": 0.8, "logos": 0.7, "pathos": 0.6},
                "trait_averages": {"virtue": 0.9, "manipulation": 0.1, "accuracy": 0.8},
                "alignment_history": ["aligned", "aligned", "aligned"],
            },
            {
                "agent_id": "agent-2",
                "agent_name": "Bot B",
                "evaluation_count": 8,
                "dimension_averages": {"ethos": 0.5, "logos": 0.9, "pathos": 0.7},
                "trait_averages": {
                    "virtue": 0.6,
                    "manipulation": 0.4,
                    "accuracy": 0.85,
                },
                "alignment_history": ["aligned", "drifting", "aligned"],
            },
        ]

        result = await compare_agents("agent-1", "agent-2")

        assert result["agent_1"]["agent_name"] == "Bot A"
        assert result["agent_2"]["agent_name"] == "Bot B"
        assert result["agent_1"]["alignment_rate"] == 1.0

        # Dimension comparison
        assert result["dimension_comparison"]["ethos"]["delta"] == 0.3
        assert result["dimension_comparison"]["logos"]["delta"] == -0.2

        # Trait comparison
        assert result["trait_comparison"]["virtue"]["delta"] == 0.3
        assert result["trait_comparison"]["manipulation"]["delta"] == -0.3

        # Biggest differences
        assert len(result["biggest_differences"]) <= 5
        assert result["biggest_differences"][0]["trait"] in ("virtue", "manipulation")

    @patch("ethos_academy.graph_insights.get_agent_profile", new_callable=AsyncMock)
    @patch("ethos_academy.graph_insights.graph_context")
    async def test_handles_missing_agents(self, mock_ctx, mock_profile):
        from ethos_academy.graph_insights import compare_agents

        mock_service = AsyncMock()
        mock_ctx.side_effect = lambda: _make_mock_graph_context(mock_service)()
        mock_profile.side_effect = [{}, {}]

        result = await compare_agents("unknown-1", "unknown-2")
        assert "error" in result

    @patch("ethos_academy.graph_insights.graph_context")
    async def test_returns_error_on_graph_failure(self, mock_ctx):
        from ethos_academy.graph_insights import compare_agents

        mock_ctx.side_effect = lambda: _make_failing_graph_context()()

        result = await compare_agents("agent-1", "agent-2")
        assert "error" in result


# ═══════════════════════════════════════════════════════════════════════════
# Helper function tests
# ═══════════════════════════════════════════════════════════════════════════


class TestTopItems:
    """_top_items() counts and ranks items."""

    def test_returns_top_n(self):
        from ethos_academy.graph_insights import _top_items

        items = ["a", "b", "a", "c", "a", "b"]
        result = _top_items(items, 2)

        assert len(result) == 2
        assert result[0] == {"name": "a", "count": 3}
        assert result[1] == {"name": "b", "count": 2}

    def test_handles_empty_list(self):
        from ethos_academy.graph_insights import _top_items

        result = _top_items([], 5)
        assert result == []

    def test_skips_empty_strings(self):
        from ethos_academy.graph_insights import _top_items

        items = ["a", "", "a", "", None, "b"]
        result = _top_items(items, 5)

        assert len(result) == 2
        names = [r["name"] for r in result]
        assert "" not in names
        assert None not in names
