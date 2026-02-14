"""Visualization domain function — transform graph data into NVL-ready format.

DDD layering: API calls get_graph_data() → this module calls graph/visualization.py.
API never touches graph directly.

The graph shows agents, evaluations, and dimensions only. The full taxonomy
(traits, indicators, constitutional values, patterns) lives in the taxonomy
explorer, not the force-directed graph.
"""

from __future__ import annotations

import logging

from ethos.graph.service import graph_context
from ethos.graph.visualization import (
    get_episodic_layer,
    get_precedes_rels,
    get_semantic_layer,
)
from ethos.shared.models import GraphData, GraphNode, GraphRel

logger = logging.getLogger(__name__)


async def get_graph_data() -> GraphData:
    """Pull agents, evaluations, and dimensions for the Phronesis graph.

    Returns empty GraphData if Neo4j is unavailable.
    """
    try:
        async with graph_context() as service:
            if not service.connected:
                return GraphData()

            semantic = await get_semantic_layer(service)
            episodic = await get_episodic_layer(service)
            precedes = await get_precedes_rels(service)

            return _build_graph_data(semantic, episodic, precedes)

    except Exception as exc:
        logger.warning("Failed to get graph data: %s", exc)
        return GraphData()


def _build_graph_data(
    semantic: dict,
    episodic: dict,
    precedes: list[dict],
) -> GraphData:
    """Build a focused graph: dimensions + agents + evaluations."""
    nodes: list[GraphNode] = []
    relationships: list[GraphRel] = []
    rel_counter = 0

    # ── Dimension nodes (3 anchors) ──────────────────────────────────────
    for dim in semantic["dimensions"].values():
        name = dim["name"]
        nodes.append(
            GraphNode(
                id=f"dim-{name}",
                type="dimension",
                label=name,
                caption=name,
                properties={"description": dim.get("description", "")},
            )
        )

    # ── Agent nodes ──────────────────────────────────────────────────────
    for agent in episodic["agents"].values():
        aid = agent["agent_id"]
        agent_name = agent.get("agent_name") or aid
        nodes.append(
            GraphNode(
                id=f"agent-{aid}",
                type="agent",
                label=agent_name,
                caption=agent_name,
                properties={
                    "agent_name": agent_name,
                    "evaluation_count": agent.get("evaluation_count", 0),
                    "alignment_status": agent.get("alignment_status", "unknown"),
                    "phronesis_score": agent.get("phronesis_score"),
                },
            )
        )

    # ── Evaluation nodes ─────────────────────────────────────────────────
    for ev in episodic["evaluations"].values():
        eid = ev["evaluation_id"]
        model = ev.get("model_used", "")
        nodes.append(
            GraphNode(
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
                    "model_used": model,
                },
            )
        )

    # ── Agent → Evaluation EVALUATED rels ────────────────────────────────
    for rel in episodic["evaluated_rels"]:
        rel_counter += 1
        relationships.append(
            GraphRel(
                id=f"rel-{rel_counter}",
                from_id=f"agent-{rel['agent']}",
                to_id=f"eval-{rel['evaluation']}",
                type="EVALUATED",
            )
        )

    # ── Evaluation → Evaluation PRECEDES rels ────────────────────────────
    eval_ids = {ev["evaluation_id"] for ev in episodic["evaluations"].values()}
    for rel in precedes:
        from_id = rel["from_eval"]
        to_id = rel["to_eval"]
        if from_id in eval_ids and to_id in eval_ids:
            rel_counter += 1
            relationships.append(
                GraphRel(
                    id=f"rel-{rel_counter}",
                    from_id=f"eval-{from_id}",
                    to_id=f"eval-{to_id}",
                    type="PRECEDES",
                )
            )

    return GraphData(nodes=nodes, relationships=relationships)
