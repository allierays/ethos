"""Visualization domain function — transform graph data into NVL-ready format.

DDD layering: API calls get_graph_data() → this module calls graph/visualization.py.
API never touches graph directly.
"""

from __future__ import annotations

import logging

from ethos.graph.service import GraphService
from ethos.graph.visualization import (
    get_episodic_layer,
    get_indicator_backbone,
    get_semantic_layer,
)
from ethos.shared.models import GraphData, GraphNode, GraphRel

logger = logging.getLogger(__name__)

# Greek names for dimensions
_GREEK_NAMES = {
    "ethos": "\u03b7\u03b8\u03bf\u03c2",
    "logos": "\u03bb\u03cc\u03b3\u03bf\u03c2",
    "pathos": "\u03c0\u03ac\u03b8\u03bf\u03c2",
}

# Dimension colors for trait inheritance
_DIMENSION_COLORS = {
    "ethos": "#0d9488",
    "logos": "#3b82f6",
    "pathos": "#f59e0b",
}


def get_graph_data() -> GraphData:
    """Pull the full Phronesis subgraph and transform into GraphData.

    Returns empty GraphData if Neo4j is unavailable.
    """
    try:
        service = GraphService()
        service.connect()

        if not service.connected:
            return GraphData()

        semantic = get_semantic_layer(service)
        episodic = get_episodic_layer(service)
        backbone = get_indicator_backbone(service)

        service.close()

        return _build_graph_data(semantic, episodic, backbone)

    except Exception as exc:
        logger.warning("Failed to get graph data: %s", exc)
        return GraphData()


def _build_graph_data(
    semantic: dict,
    episodic: dict,
    backbone: dict,
) -> GraphData:
    """Transform raw graph query results into GraphData with proper node IDs."""
    nodes: list[GraphNode] = []
    relationships: list[GraphRel] = []
    rel_counter = 0

    # ── Dimension nodes ─────────────────────────────────────────────────
    for dim in semantic["dimensions"].values():
        name = dim["name"]
        nodes.append(GraphNode(
            id=f"dim-{name}",
            type="dimension",
            label=name,
            caption=_GREEK_NAMES.get(name, name),
            properties={"description": dim.get("description", "")},
        ))

    # ── Trait nodes ─────────────────────────────────────────────────────
    for trait in semantic["traits"].values():
        name = trait["name"]
        nodes.append(GraphNode(
            id=f"trait-{name}",
            type="trait",
            label=name,
            caption=name,
            properties={
                "dimension": trait.get("dimension", ""),
                "polarity": trait.get("polarity", ""),
            },
        ))

    # Trait → Dimension BELONGS_TO relationships
    for rel in semantic["trait_dimension_rels"]:
        rel_counter += 1
        relationships.append(GraphRel(
            id=f"rel-{rel_counter}",
            from_id=f"trait-{rel['trait']}",
            to_id=f"dim-{rel['dimension']}",
            type="BELONGS_TO",
        ))

    # ── ConstitutionalValue nodes ───────────────────────────────────────
    for cv in semantic["constitutional_values"].values():
        name = cv["name"]
        priority = cv.get("priority", 0)
        nodes.append(GraphNode(
            id=f"cv-{name}",
            type="constitutional_value",
            label=name,
            caption=f"{name} (P{priority})",
            properties={"priority": priority},
        ))

    # Trait → ConstitutionalValue UPHOLDS relationships
    for rel in semantic["upholds_rels"]:
        rel_counter += 1
        relationships.append(GraphRel(
            id=f"rel-{rel_counter}",
            from_id=f"trait-{rel['trait']}",
            to_id=f"cv-{rel['cv']}",
            type="UPHOLDS",
            properties={"relationship": rel.get("relationship", "")},
        ))

    # ── Pattern nodes ───────────────────────────────────────────────────
    for pattern in semantic["patterns"].values():
        pid = pattern["pattern_id"]
        nodes.append(GraphNode(
            id=f"pattern-{pid}",
            type="pattern",
            label=pattern.get("name", pid),
            caption=pattern.get("name", pid),
            properties={
                "severity": pattern.get("severity", "info"),
                "stage_count": pattern.get("stage_count", 0),
            },
        ))

    # Pattern → Indicator COMPOSED_OF relationships
    for rel in semantic["pattern_indicator_rels"]:
        rel_counter += 1
        relationships.append(GraphRel(
            id=f"rel-{rel_counter}",
            from_id=f"pattern-{rel['pattern']}",
            to_id=f"indicator-{rel['indicator']}",
            type="COMPOSED_OF",
        ))

    # ── Indicator nodes (only detected ones) ────────────────────────────
    for indicator in backbone["indicators"].values():
        iid = indicator["id"]
        nodes.append(GraphNode(
            id=f"indicator-{iid}",
            type="indicator",
            label=iid,
            caption=iid,
            properties={"trait": indicator.get("trait", "")},
        ))

    # Indicator → Trait BELONGS_TO relationships
    for rel in backbone["indicator_trait_rels"]:
        rel_counter += 1
        relationships.append(GraphRel(
            id=f"rel-{rel_counter}",
            from_id=f"indicator-{rel['indicator']}",
            to_id=f"trait-{rel['trait']}",
            type="BELONGS_TO",
        ))

    # ── Agent nodes ─────────────────────────────────────────────────────
    for agent in episodic["agents"].values():
        aid = agent["agent_id"]
        nodes.append(GraphNode(
            id=f"agent-{aid}",
            type="agent",
            label=aid[:8] if len(aid) > 8 else aid,
            caption=aid[:8] if len(aid) > 8 else aid,
            properties={
                "evaluation_count": agent.get("evaluation_count", 0),
                "alignment_status": agent.get("alignment_status", "unknown"),
                "phronesis_score": agent.get("phronesis_score"),
            },
        ))

    # ── Evaluation nodes ────────────────────────────────────────────────
    for ev in episodic["evaluations"].values():
        eid = ev["evaluation_id"]
        nodes.append(GraphNode(
            id=f"eval-{eid}",
            type="evaluation",
            label=eid[:8] if len(eid) > 8 else eid,
            caption="",
            properties={
                "ethos": ev.get("ethos", 0.0),
                "logos": ev.get("logos", 0.0),
                "pathos": ev.get("pathos", 0.0),
                "alignment_status": ev.get("alignment_status", "unknown"),
                "phronesis": ev.get("phronesis", "undetermined"),
            },
        ))

    # Agent → Evaluation EVALUATED relationships
    for rel in episodic["evaluated_rels"]:
        rel_counter += 1
        relationships.append(GraphRel(
            id=f"rel-{rel_counter}",
            from_id=f"agent-{rel['agent']}",
            to_id=f"eval-{rel['evaluation']}",
            type="EVALUATED",
        ))

    # Evaluation → Indicator DETECTED relationships
    for rel in episodic["detected_rels"]:
        rel_counter += 1
        relationships.append(GraphRel(
            id=f"rel-{rel_counter}",
            from_id=f"eval-{rel['evaluation']}",
            to_id=f"indicator-{rel['indicator']}",
            type="DETECTED",
            properties={"confidence": rel.get("confidence", 0.0)},
        ))

    return GraphData(nodes=nodes, relationships=relationships)
