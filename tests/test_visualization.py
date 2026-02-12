"""Tests for the graph visualization endpoint and domain function."""

from unittest.mock import MagicMock, patch


from ethos.graph.service import GraphService
from ethos.graph.visualization import (
    get_episodic_layer,
    get_indicator_backbone,
    get_semantic_layer,
)
from ethos.shared.models import GraphData, GraphNode, GraphRel
from ethos.visualization import _build_graph_data, get_graph_data


# ── Test fixtures ───────────────────────────────────────────────────────────


def _make_semantic_data() -> dict:
    """Minimal semantic layer data for testing."""
    return {
        "dimensions": {
            "ethos": {"name": "ethos", "greek": "\u03b7\u03b8\u03bf\u03c2", "description": "Trust, credibility, and moral character"},
            "logos": {"name": "logos", "greek": "\u03bb\u03cc\u03b3\u03bf\u03c2", "description": "Reasoning, accuracy, and logical integrity"},
        },
        "traits": {
            "virtue": {"name": "virtue", "dimension": "ethos", "polarity": "positive"},
            "manipulation": {"name": "manipulation", "dimension": "ethos", "polarity": "negative"},
            "accuracy": {"name": "accuracy", "dimension": "logos", "polarity": "positive"},
        },
        "trait_dimension_rels": [
            {"trait": "virtue", "dimension": "ethos"},
            {"trait": "manipulation", "dimension": "ethos"},
            {"trait": "accuracy", "dimension": "logos"},
        ],
        "constitutional_values": {
            "safety": {"name": "safety", "priority": 1},
            "ethics": {"name": "ethics", "priority": 2},
        },
        "upholds_rels": [
            {"trait": "manipulation", "cv": "safety", "relationship": "violates"},
            {"trait": "virtue", "cv": "ethics", "relationship": "enforces"},
        ],
        "patterns": {
            "SP-01": {
                "pattern_id": "SP-01",
                "name": "trust_building_exploitation",
                "description": "Builds trust then exploits it",
                "severity": "warning",
                "stage_count": 3,
            },
        },
        "pattern_indicator_rels": [
            {"pattern": "SP-01", "indicator": "MAN-URGENCY"},
        ],
    }


def _make_episodic_data() -> dict:
    """Minimal episodic layer data for testing."""
    return {
        "agents": {
            "abc123hash": {
                "agent_id": "abc123hash",
                "evaluation_count": 5,
                "alignment_status": "aligned",
                "phronesis_score": 0.72,
                "phronesis_trend": "stable",
            },
        },
        "evaluations": {
            "eval-001": {
                "evaluation_id": "eval-001",
                "ethos": 0.8,
                "logos": 0.75,
                "pathos": 0.7,
                "alignment_status": "aligned",
                "phronesis": "established",
                "created_at": "2026-02-11T00:00:00",
            },
        },
        "evaluated_rels": [
            {"agent": "abc123hash", "evaluation": "eval-001"},
        ],
        "detected_rels": [
            {"evaluation": "eval-001", "indicator": "MAN-URGENCY", "confidence": 0.85},
        ],
    }


def _make_backbone_data() -> dict:
    """Minimal indicator backbone data for testing."""
    return {
        "indicators": {
            "MAN-URGENCY": {"id": "MAN-URGENCY", "name": "false_urgency", "trait": "manipulation"},
        },
        "indicator_trait_rels": [
            {"indicator": "MAN-URGENCY", "trait": "manipulation"},
        ],
    }


# ── Tests for _build_graph_data (pure transform, no mocking needed) ─────────


class TestBuildGraphData:
    """Test the pure transformation function."""

    def test_empty_data(self):
        empty_semantic = {
            "dimensions": {}, "traits": {}, "trait_dimension_rels": [],
            "constitutional_values": {}, "upholds_rels": [],
            "patterns": {}, "pattern_indicator_rels": [],
        }
        empty_episodic = {
            "agents": {}, "evaluations": {},
            "evaluated_rels": [], "detected_rels": [],
        }
        empty_backbone = {"indicators": {}, "indicator_trait_rels": []}

        result = _build_graph_data(empty_semantic, empty_episodic, empty_backbone)

        assert isinstance(result, GraphData)
        assert result.nodes == []
        assert result.relationships == []

    def test_dimension_nodes(self):
        result = _build_graph_data(
            _make_semantic_data(),
            {"agents": {}, "evaluations": {}, "evaluated_rels": [], "detected_rels": []},
            {"indicators": {}, "indicator_trait_rels": []},
        )

        dim_nodes = [n for n in result.nodes if n.type == "dimension"]
        assert len(dim_nodes) == 2

        ethos_node = next(n for n in dim_nodes if n.label == "ethos")
        assert ethos_node.id == "dim-ethos"
        assert ethos_node.caption == "\u03b7\u03b8\u03bf\u03c2"
        assert ethos_node.properties["description"] == "Trust, credibility, and moral character"

    def test_trait_nodes(self):
        result = _build_graph_data(
            _make_semantic_data(),
            {"agents": {}, "evaluations": {}, "evaluated_rels": [], "detected_rels": []},
            {"indicators": {}, "indicator_trait_rels": []},
        )

        trait_nodes = [n for n in result.nodes if n.type == "trait"]
        assert len(trait_nodes) == 3

        virtue = next(n for n in trait_nodes if n.label == "virtue")
        assert virtue.id == "trait-virtue"
        assert virtue.properties["dimension"] == "ethos"
        assert virtue.properties["polarity"] == "positive"

        manipulation = next(n for n in trait_nodes if n.label == "manipulation")
        assert manipulation.properties["polarity"] == "negative"

    def test_constitutional_value_nodes(self):
        result = _build_graph_data(
            _make_semantic_data(),
            {"agents": {}, "evaluations": {}, "evaluated_rels": [], "detected_rels": []},
            {"indicators": {}, "indicator_trait_rels": []},
        )

        cv_nodes = [n for n in result.nodes if n.type == "constitutional_value"]
        assert len(cv_nodes) == 2

        safety = next(n for n in cv_nodes if n.label == "safety")
        assert safety.id == "cv-safety"
        assert safety.caption == "safety (P1)"
        assert safety.properties["priority"] == 1

    def test_pattern_nodes(self):
        result = _build_graph_data(
            _make_semantic_data(),
            {"agents": {}, "evaluations": {}, "evaluated_rels": [], "detected_rels": []},
            {"indicators": {}, "indicator_trait_rels": []},
        )

        pattern_nodes = [n for n in result.nodes if n.type == "pattern"]
        assert len(pattern_nodes) == 1
        assert pattern_nodes[0].id == "pattern-SP-01"
        assert pattern_nodes[0].properties["severity"] == "warning"
        assert pattern_nodes[0].properties["stage_count"] == 3

    def test_agent_nodes(self):
        result = _build_graph_data(
            _make_semantic_data(),
            _make_episodic_data(),
            _make_backbone_data(),
        )

        agent_nodes = [n for n in result.nodes if n.type == "agent"]
        assert len(agent_nodes) == 1
        assert agent_nodes[0].id == "agent-abc123hash"
        assert agent_nodes[0].label == "abc123ha"  # truncated to 8
        assert agent_nodes[0].properties["evaluation_count"] == 5
        assert agent_nodes[0].properties["alignment_status"] == "aligned"
        assert agent_nodes[0].properties["phronesis_score"] == 0.72

    def test_evaluation_nodes(self):
        result = _build_graph_data(
            _make_semantic_data(),
            _make_episodic_data(),
            _make_backbone_data(),
        )

        eval_nodes = [n for n in result.nodes if n.type == "evaluation"]
        assert len(eval_nodes) == 1
        assert eval_nodes[0].id == "eval-eval-001"
        assert eval_nodes[0].caption == ""
        assert eval_nodes[0].properties["ethos"] == 0.8

    def test_indicator_nodes_only_detected(self):
        result = _build_graph_data(
            _make_semantic_data(),
            _make_episodic_data(),
            _make_backbone_data(),
        )

        ind_nodes = [n for n in result.nodes if n.type == "indicator"]
        assert len(ind_nodes) == 1
        assert ind_nodes[0].id == "indicator-MAN-URGENCY"

    def test_belongs_to_relationships(self):
        result = _build_graph_data(
            _make_semantic_data(),
            {"agents": {}, "evaluations": {}, "evaluated_rels": [], "detected_rels": []},
            {"indicators": {}, "indicator_trait_rels": []},
        )

        belongs_to = [r for r in result.relationships if r.type == "BELONGS_TO"]
        assert len(belongs_to) == 3  # 3 trait→dimension
        assert any(
            r.from_id == "trait-virtue" and r.to_id == "dim-ethos"
            for r in belongs_to
        )

    def test_upholds_relationships(self):
        result = _build_graph_data(
            _make_semantic_data(),
            {"agents": {}, "evaluations": {}, "evaluated_rels": [], "detected_rels": []},
            {"indicators": {}, "indicator_trait_rels": []},
        )

        upholds = [r for r in result.relationships if r.type == "UPHOLDS"]
        assert len(upholds) == 2

        violates = next(r for r in upholds if r.from_id == "trait-manipulation")
        assert violates.to_id == "cv-safety"
        assert violates.properties["relationship"] == "violates"

    def test_evaluated_relationships(self):
        result = _build_graph_data(
            _make_semantic_data(),
            _make_episodic_data(),
            _make_backbone_data(),
        )

        evaluated = [r for r in result.relationships if r.type == "EVALUATED"]
        assert len(evaluated) == 1
        assert evaluated[0].from_id == "agent-abc123hash"
        assert evaluated[0].to_id == "eval-eval-001"

    def test_detected_relationships(self):
        result = _build_graph_data(
            _make_semantic_data(),
            _make_episodic_data(),
            _make_backbone_data(),
        )

        detected = [r for r in result.relationships if r.type == "DETECTED"]
        assert len(detected) == 1
        assert detected[0].from_id == "eval-eval-001"
        assert detected[0].to_id == "indicator-MAN-URGENCY"
        assert detected[0].properties["confidence"] == 0.85

    def test_composed_of_relationships(self):
        result = _build_graph_data(
            _make_semantic_data(),
            {"agents": {}, "evaluations": {}, "evaluated_rels": [], "detected_rels": []},
            {"indicators": {}, "indicator_trait_rels": []},
        )

        composed = [r for r in result.relationships if r.type == "COMPOSED_OF"]
        assert len(composed) == 1
        assert composed[0].from_id == "pattern-SP-01"
        assert composed[0].to_id == "indicator-MAN-URGENCY"

    def test_full_graph_node_types(self):
        result = _build_graph_data(
            _make_semantic_data(),
            _make_episodic_data(),
            _make_backbone_data(),
        )

        node_types = {n.type for n in result.nodes}
        assert "dimension" in node_types
        assert "trait" in node_types
        assert "constitutional_value" in node_types
        assert "pattern" in node_types
        assert "indicator" in node_types
        assert "agent" in node_types
        assert "evaluation" in node_types

    def test_all_relationship_ids_unique(self):
        result = _build_graph_data(
            _make_semantic_data(),
            _make_episodic_data(),
            _make_backbone_data(),
        )

        rel_ids = [r.id for r in result.relationships]
        assert len(rel_ids) == len(set(rel_ids))


# ── Tests for graph query functions (mock GraphService) ─────────────────────


class TestGetSemanticLayer:
    """Test semantic layer query function with mocked service."""

    def test_returns_empty_when_disconnected(self):
        service = MagicMock(spec=GraphService)
        service.connected = False

        result = get_semantic_layer(service)
        assert result["dimensions"] == {}
        assert result["traits"] == {}
        assert result["constitutional_values"] == {}
        assert result["patterns"] == {}

    def test_returns_empty_on_exception(self):
        service = MagicMock(spec=GraphService)
        service.connected = True
        service.execute_query.side_effect = Exception("Neo4j down")

        result = get_semantic_layer(service)
        assert result["dimensions"] == {}


class TestGetEpisodicLayer:
    """Test episodic layer query function with mocked service."""

    def test_returns_empty_when_disconnected(self):
        service = MagicMock(spec=GraphService)
        service.connected = False

        result = get_episodic_layer(service)
        assert result["agents"] == {}
        assert result["evaluations"] == {}

    def test_returns_empty_on_exception(self):
        service = MagicMock(spec=GraphService)
        service.connected = True
        service.execute_query.side_effect = Exception("Neo4j down")

        result = get_episodic_layer(service)
        assert result["agents"] == {}


class TestGetIndicatorBackbone:
    """Test indicator backbone query function with mocked service."""

    def test_returns_empty_when_disconnected(self):
        service = MagicMock(spec=GraphService)
        service.connected = False

        result = get_indicator_backbone(service)
        assert result["indicators"] == {}

    def test_returns_empty_on_exception(self):
        service = MagicMock(spec=GraphService)
        service.connected = True
        service.execute_query.side_effect = Exception("Neo4j down")

        result = get_indicator_backbone(service)
        assert result["indicators"] == {}


# ── Tests for get_graph_data domain function ────────────────────────────────


class TestGetGraphData:
    """Test the top-level domain function."""

    @patch("ethos.visualization.GraphService")
    def test_returns_empty_graphdata_when_not_connected(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.connected = False
        mock_service_cls.return_value = mock_service

        result = get_graph_data()

        assert isinstance(result, GraphData)
        assert result.nodes == []
        assert result.relationships == []

    @patch("ethos.visualization.get_indicator_backbone")
    @patch("ethos.visualization.get_episodic_layer")
    @patch("ethos.visualization.get_semantic_layer")
    @patch("ethos.visualization.GraphService")
    def test_returns_graph_data(
        self, mock_service_cls, mock_semantic, mock_episodic, mock_backbone
    ):
        mock_service = MagicMock()
        mock_service.connected = True
        mock_service_cls.return_value = mock_service

        mock_semantic.return_value = _make_semantic_data()
        mock_episodic.return_value = _make_episodic_data()
        mock_backbone.return_value = _make_backbone_data()

        result = get_graph_data()

        assert isinstance(result, GraphData)
        assert len(result.nodes) > 0
        assert len(result.relationships) > 0

        # Verify it called close
        mock_service.close.assert_called_once()

    @patch("ethos.visualization.GraphService")
    def test_handles_exception_gracefully(self, mock_service_cls):
        mock_service_cls.side_effect = Exception("Connection failed")

        result = get_graph_data()

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
