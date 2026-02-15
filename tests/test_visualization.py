"""Tests for the graph visualization endpoint and domain function."""

from unittest.mock import AsyncMock, patch


from ethos_academy.graph.service import GraphService
from ethos_academy.graph.visualization import (
    get_episodic_layer,
    get_indicator_backbone,
    get_semantic_layer,
)
from ethos_academy.shared.models import GraphData, GraphNode, GraphRel
from ethos_academy.visualization import get_graph_data, _build_radial_graph


# ── Test fixtures ───────────────────────────────────────────────────────────


def _make_indicator_rows() -> list[dict]:
    """Minimal indicator frequency data for testing."""
    return [
        {
            "dimension": "ethos",
            "dim_greek": "\u03b7\u03b8\u03bf\u03c2",
            "trait": "manipulation",
            "trait_polarity": "negative",
            "indicator_id": "MAN-URGENCY",
            "indicator_name": "false_urgency",
            "det_count": 10,
            "eval_count": 5,
        },
        {
            "dimension": "ethos",
            "dim_greek": "\u03b7\u03b8\u03bf\u03c2",
            "trait": "virtue",
            "trait_polarity": "positive",
            "indicator_id": "VIR-AUTHENTIC",
            "indicator_name": "authentic_voice",
            "det_count": 3,
            "eval_count": 2,
        },
    ]


def _make_agent_rows() -> list[dict]:
    """Minimal agent-indicator data for testing."""
    return [
        {
            "agent_id": "abc123hash",
            "agent_name": "test-agent",
            "phronesis_score": 0.72,
            "indicator_id": "MAN-URGENCY",
            "times_detected": 5,
        },
    ]


# ── Tests for _build_radial_graph (pure transform, no mocking needed) ──────


class TestBuildRadialGraph:
    """Test the pure radial graph transformation function."""

    def test_empty_data(self):
        result = _build_radial_graph([], [])

        assert isinstance(result, GraphData)
        # Academy center + 3 dimension nodes always present
        assert len(result.nodes) == 4
        assert result.nodes[0].id == "academy"

    def test_creates_dimension_nodes(self):
        result = _build_radial_graph(_make_indicator_rows(), [])

        dim_nodes = [n for n in result.nodes if n.type == "dimension"]
        assert len(dim_nodes) == 3  # all 3 dimensions always created
        ethos = next(n for n in dim_nodes if n.label == "ethos")
        assert ethos.id == "dim-ethos"
        assert ethos.properties["pinned"] is True

    def test_creates_trait_nodes(self):
        result = _build_radial_graph(_make_indicator_rows(), [])

        trait_nodes = [n for n in result.nodes if n.type == "trait"]
        assert len(trait_nodes) == 2  # manipulation + virtue
        names = {n.label for n in trait_nodes}
        assert "manipulation" in names
        assert "virtue" in names

    def test_creates_indicator_nodes(self):
        result = _build_radial_graph(_make_indicator_rows(), [])

        ind_nodes = [n for n in result.nodes if n.type == "indicator"]
        assert len(ind_nodes) == 2
        ids = {n.id for n in ind_nodes}
        assert "ind-MAN-URGENCY" in ids
        assert "ind-VIR-AUTHENTIC" in ids

    def test_indicator_size_scales_with_detections(self):
        result = _build_radial_graph(_make_indicator_rows(), [])

        ind_nodes = {n.id: n for n in result.nodes if n.type == "indicator"}
        urgency = ind_nodes["ind-MAN-URGENCY"]
        authentic = ind_nodes["ind-VIR-AUTHENTIC"]
        # MAN-URGENCY has 10 detections (max), VIR-AUTHENTIC has 3
        assert urgency.properties["size"] > authentic.properties["size"]

    def test_creates_agent_nodes(self):
        result = _build_radial_graph(_make_indicator_rows(), _make_agent_rows())

        agent_nodes = [n for n in result.nodes if n.type == "agent"]
        assert len(agent_nodes) == 1
        assert agent_nodes[0].id == "agent-abc123hash"
        assert agent_nodes[0].properties["indicator_count"] == 1

    def test_creates_triggered_relationships(self):
        result = _build_radial_graph(_make_indicator_rows(), _make_agent_rows())

        triggered = [r for r in result.relationships if r.type == "TRIGGERED"]
        assert len(triggered) == 1
        assert triggered[0].from_id == "agent-abc123hash"
        assert triggered[0].to_id == "ind-MAN-URGENCY"
        assert triggered[0].properties["weight"] == 5

    def test_all_relationship_ids_unique(self):
        result = _build_radial_graph(_make_indicator_rows(), _make_agent_rows())

        rel_ids = [r.id for r in result.relationships]
        assert len(rel_ids) == len(set(rel_ids))

    def test_hierarchy_relationships(self):
        result = _build_radial_graph(_make_indicator_rows(), [])

        has_dim = [r for r in result.relationships if r.type == "HAS_DIMENSION"]
        belongs_to = [r for r in result.relationships if r.type == "BELONGS_TO"]
        indicates = [r for r in result.relationships if r.type == "INDICATES"]

        assert len(has_dim) == 3  # academy → ethos, logos, pathos
        assert len(belongs_to) == 2  # ethos → manipulation, ethos → virtue
        assert len(indicates) == 2  # manipulation → MAN-URGENCY, virtue → VIR-AUTHENTIC


# ── Tests for graph query functions (mock GraphService) ─────────────────────


class TestGetSemanticLayer:
    """Test semantic layer query function with mocked service."""

    async def test_returns_empty_when_disconnected(self):
        service = AsyncMock(spec=GraphService)
        service.connected = False

        result = await get_semantic_layer(service)
        assert result["dimensions"] == {}
        assert result["traits"] == {}
        assert result["constitutional_values"] == {}
        assert result["patterns"] == {}

    async def test_returns_empty_on_exception(self):
        service = AsyncMock(spec=GraphService)
        service.connected = True
        service.execute_query.side_effect = Exception("Neo4j down")

        result = await get_semantic_layer(service)
        assert result["dimensions"] == {}


class TestGetEpisodicLayer:
    """Test episodic layer query function with mocked service."""

    async def test_returns_empty_when_disconnected(self):
        service = AsyncMock(spec=GraphService)
        service.connected = False

        result = await get_episodic_layer(service)
        assert result["agents"] == {}
        assert result["evaluations"] == {}

    async def test_returns_empty_on_exception(self):
        service = AsyncMock(spec=GraphService)
        service.connected = True
        service.execute_query.side_effect = Exception("Neo4j down")

        result = await get_episodic_layer(service)
        assert result["agents"] == {}


class TestGetIndicatorBackbone:
    """Test indicator backbone query function with mocked service."""

    async def test_returns_empty_when_disconnected(self):
        service = AsyncMock(spec=GraphService)
        service.connected = False

        result = await get_indicator_backbone(service)
        assert result["indicators"] == {}

    async def test_returns_empty_on_exception(self):
        service = AsyncMock(spec=GraphService)
        service.connected = True
        service.execute_query.side_effect = Exception("Neo4j down")

        result = await get_indicator_backbone(service)
        assert result["indicators"] == {}


# ── Tests for get_graph_data domain function ────────────────────────────────


class TestGetGraphData:
    """Test the top-level domain function."""

    @patch("ethos_academy.visualization.graph_context")
    async def test_returns_empty_graphdata_when_not_connected(self, mock_ctx):
        mock_service = AsyncMock()
        mock_service.connected = False
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await get_graph_data()

        assert isinstance(result, GraphData)
        assert result.nodes == []
        assert result.relationships == []

    @patch(
        "ethos_academy.visualization.get_agent_indicator_data", new_callable=AsyncMock
    )
    @patch(
        "ethos_academy.visualization.get_indicator_frequency_data",
        new_callable=AsyncMock,
    )
    @patch("ethos_academy.visualization.graph_context")
    async def test_returns_graph_data(self, mock_ctx, mock_freq, mock_agent_ind):
        mock_service = AsyncMock()
        mock_service.connected = True
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_freq.return_value = _make_indicator_rows()
        mock_agent_ind.return_value = _make_agent_rows()

        result = await get_graph_data()

        assert isinstance(result, GraphData)
        assert len(result.nodes) > 0
        assert len(result.relationships) > 0

    @patch("ethos_academy.visualization.graph_context")
    async def test_handles_exception_gracefully(self, mock_ctx):
        mock_ctx.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("Connection failed")
        )
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await get_graph_data()

        assert isinstance(result, GraphData)
        assert result.nodes == []
        assert result.relationships == []


# ── Tests for Pydantic models ──────────────────────────────────────────────


class TestGraphModels:
    """Test the Pydantic model definitions."""

    def test_graph_node_defaults(self):
        node = GraphNode(id="test", type="dimension", label="ethos")
        assert node.caption == ""
        assert node.properties == {}

    def test_graph_rel_defaults(self):
        rel = GraphRel(id="r1", from_id="a", to_id="b", type="BELONGS_TO")
        assert rel.properties == {}

    def test_graph_data_defaults(self):
        data = GraphData()
        assert data.nodes == []
        assert data.relationships == []

    def test_graph_node_with_properties(self):
        node = GraphNode(
            id="dim-ethos",
            type="dimension",
            label="ethos",
            caption="\u03b7\u03b8\u03bf\u03c2",
            properties={"description": "Trust and credibility"},
        )
        assert node.properties["description"] == "Trust and credibility"

    def test_graph_rel_with_properties(self):
        rel = GraphRel(
            id="r1",
            from_id="trait-manipulation",
            to_id="cv-safety",
            type="UPHOLDS",
            properties={"relationship": "violates"},
        )
        assert rel.from_id == "trait-manipulation"
        assert rel.properties["relationship"] == "violates"
