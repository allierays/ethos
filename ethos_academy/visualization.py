"""Visualization domain function — transform graph data into NVL-ready format.

Radial hierarchy centered on Ethos Academy:
  Center: Ethos Academy
  Ring 1: 3 Dimensions (Integrity, Logic, Empathy)
  Ring 2: 12 Traits (4 per dimension)
  Ring 3: 208 Indicators (sized by detection frequency)
  Ring 4: Agents (connected to the indicators they triggered)

This reveals which behavioral signals each agent activates and how the
208-indicator framework maps to real-world agent behavior.
"""

from __future__ import annotations

import logging
import math

from ethos_academy.graph.service import graph_context
from ethos_academy.graph.visualization import (
    get_agent_indicator_data,
    get_indicator_frequency_data,
)
from ethos_academy.shared.models import GraphData, GraphNode, GraphRel

logger = logging.getLogger(__name__)

# Radial distances from center
_R_DIMENSION = 250
_R_TRAIT = 550
_R_INDICATOR = 900
_R_AGENT = 1300

# Dimension base angles (equally spaced, top/bottom-left/bottom-right)
_DIM_ANGLES = {
    "ethos": math.radians(270),  # top
    "logos": math.radians(150),  # bottom-left
    "pathos": math.radians(30),  # bottom-right
}

_DIM_LABELS = {
    "ethos": "Integrity",
    "logos": "Logic",
    "pathos": "Empathy",
}


def _polar(angle: float, radius: float) -> tuple[float, float]:
    """Convert polar to cartesian, y-inverted for screen coords."""
    return round(radius * math.cos(angle), 1), round(radius * math.sin(angle), 1)


async def get_graph_data() -> GraphData:
    """Pull full taxonomy + agent connections and build radial graph.

    Returns empty GraphData if Neo4j is unavailable.
    """
    try:
        async with graph_context() as service:
            if not service.connected:
                return GraphData()

            indicator_rows = await get_indicator_frequency_data(service)
            agent_rows = await get_agent_indicator_data(service)
            return _build_radial_graph(indicator_rows, agent_rows)

    except Exception as exc:
        logger.warning("Failed to get graph data: %s", exc)
        return GraphData()


def _build_radial_graph(
    indicator_rows: list[dict],
    agent_rows: list[dict],
) -> GraphData:
    """Build radial graph: Academy → Dimensions → Traits → Indicators → Agents."""
    nodes: list[GraphNode] = []
    relationships: list[GraphRel] = []
    rel_id = 0

    # ── Parse indicator taxonomy ───────────────────────────────────────────
    trait_to_dim: dict[str, str] = {}
    trait_polarity: dict[str, str] = {}
    dim_traits: dict[str, list[str]] = {}
    trait_indicators: dict[str, list[dict]] = {}

    for row in indicator_rows:
        dim = row["dimension"]
        trait = row["trait"]
        trait_to_dim[trait] = dim
        trait_polarity[trait] = row.get("trait_polarity", "positive")
        if trait not in dim_traits.get(dim, []):
            dim_traits.setdefault(dim, []).append(trait)
        trait_indicators.setdefault(trait, []).append(row)

    # Deduplicate trait lists
    for dim in dim_traits:
        seen: list[str] = []
        for t in dim_traits[dim]:
            if t not in seen:
                seen.append(t)
        dim_traits[dim] = seen

    max_det = max((r["det_count"] for r in indicator_rows), default=1) or 1

    # ── Center node: Ethos Academy ─────────────────────────────────────────
    nodes.append(
        GraphNode(
            id="academy",
            type="academy",
            label="Ethos Academy",
            caption="Ethos Academy",
            properties={"x": 0, "y": 0, "pinned": True},
        )
    )

    # ── Ring 1: Dimension nodes ────────────────────────────────────────────
    # Track angle ranges for each dimension (for trait/indicator placement)
    dim_positions: dict[str, tuple[float, float]] = {}

    for dim_key, base_angle in _DIM_ANGLES.items():
        dx, dy = _polar(base_angle, _R_DIMENSION)
        dim_positions[dim_key] = (dx, dy)

        nodes.append(
            GraphNode(
                id=f"dim-{dim_key}",
                type="dimension",
                label=dim_key,
                caption=_DIM_LABELS.get(dim_key, dim_key),
                properties={"x": dx, "y": dy, "pinned": True},
            )
        )

        # Academy → Dimension
        rel_id += 1
        relationships.append(
            GraphRel(
                id=f"rel-{rel_id}",
                from_id="academy",
                to_id=f"dim-{dim_key}",
                type="HAS_DIMENSION",
                properties={},
            )
        )

    # ── Ring 2: Trait nodes ────────────────────────────────────────────────
    trait_positions: dict[str, tuple[float, float]] = {}
    trait_angles: dict[str, float] = {}

    for dim_key, traits in dim_traits.items():
        base_angle = _DIM_ANGLES[dim_key]
        # Spread 4 traits across a 100-degree arc centered on dimension
        spread = math.radians(90)
        n_traits = len(traits)

        for i, trait in enumerate(traits):
            if n_traits > 1:
                offset = spread * (i / (n_traits - 1) - 0.5)
            else:
                offset = 0
            angle = base_angle + offset
            tx, ty = _polar(angle, _R_TRAIT)
            trait_positions[trait] = (tx, ty)
            trait_angles[trait] = angle

            polarity = trait_polarity.get(trait, "positive")
            nodes.append(
                GraphNode(
                    id=f"trait-{trait}",
                    type="trait",
                    label=trait,
                    caption=trait.replace("_", " ").title(),
                    properties={
                        "x": tx,
                        "y": ty,
                        "pinned": True,
                        "dimension": dim_key,
                        "polarity": polarity,
                    },
                )
            )

            # Dimension → Trait
            rel_id += 1
            relationships.append(
                GraphRel(
                    id=f"rel-{rel_id}",
                    from_id=f"dim-{dim_key}",
                    to_id=f"trait-{trait}",
                    type="BELONGS_TO",
                    properties={},
                )
            )

    # ── Ring 3: Indicator nodes ────────────────────────────────────────────
    indicator_angles: dict[str, float] = {}

    for trait, ind_list in trait_indicators.items():
        trait_angle = trait_angles.get(trait, 0)
        count = len(ind_list)
        # Spread indicators across a narrower arc around their trait
        arc = math.radians(25)  # each trait gets ~25 degrees of arc

        for i, ind in enumerate(ind_list):
            if count > 1:
                offset = arc * (i / (count - 1) - 0.5)
            else:
                offset = 0
            angle = trait_angle + offset
            ix, iy = _polar(angle, _R_INDICATOR)

            det_count = ind["det_count"]
            size_ratio = det_count / max_det
            size = 3 + size_ratio * 22

            dim_key = trait_to_dim.get(trait, "ethos")
            ind_id = ind["indicator_id"]
            indicator_angles[ind_id] = angle

            nodes.append(
                GraphNode(
                    id=f"ind-{ind_id}",
                    type="indicator",
                    label=ind["indicator_name"],
                    caption=ind["indicator_name"].replace("_", " "),
                    properties={
                        "x": ix,
                        "y": iy,
                        "pinned": True,
                        "detection_count": det_count,
                        "dimension": dim_key,
                        "trait": trait,
                        "polarity": trait_polarity.get(trait, "positive"),
                        "size": round(size, 1),
                    },
                )
            )

            # Trait → Indicator
            rel_id += 1
            relationships.append(
                GraphRel(
                    id=f"rel-{rel_id}",
                    from_id=f"trait-{trait}",
                    to_id=f"ind-{ind_id}",
                    type="INDICATES",
                    properties={"weight": det_count},
                )
            )

    # ── Ring 4: Agent nodes ────────────────────────────────────────────────
    # Group agent_rows by agent_id
    agent_indicators: dict[str, list[dict]] = {}
    agent_meta: dict[str, dict] = {}
    for row in agent_rows:
        aid = row["agent_id"]
        agent_indicators.setdefault(aid, []).append(row)
        if aid not in agent_meta:
            agent_meta[aid] = {
                "name": row.get("agent_name") or aid,
                "phronesis_score": row.get("phronesis_score"),
            }

    # Position each agent at the average angle of their detected indicators
    for aid, ind_rows in agent_indicators.items():
        # Compute average angle weighted by detection count
        sin_sum = 0.0
        cos_sum = 0.0
        total_weight = 0
        for row in ind_rows:
            ind_id = row["indicator_id"]
            weight = row["times_detected"]
            angle = indicator_angles.get(ind_id)
            if angle is not None:
                sin_sum += math.sin(angle) * weight
                cos_sum += math.cos(angle) * weight
                total_weight += weight

        if total_weight > 0:
            avg_angle = math.atan2(sin_sum / total_weight, cos_sum / total_weight)
        else:
            continue  # skip agents with no positioned indicators

        # Add small jitter to prevent overlap
        jitter = (hash(aid) % 100 - 50) * 0.5
        ax, ay = _polar(avg_angle, _R_AGENT + jitter)

        meta = agent_meta[aid]
        indicator_count = len(ind_rows)
        total_detections = sum(r["times_detected"] for r in ind_rows)

        nodes.append(
            GraphNode(
                id=f"agent-{aid}",
                type="agent",
                label=meta["name"],
                caption=meta["name"],
                properties={
                    "x": ax,
                    "y": ay,
                    "pinned": True,
                    "indicator_count": indicator_count,
                    "total_detections": total_detections,
                    "phronesis_score": meta.get("phronesis_score"),
                },
            )
        )

        # Agent → Indicator edges (only top 10 per agent to reduce clutter)
        top_indicators = sorted(
            ind_rows, key=lambda r: r["times_detected"], reverse=True
        )[:10]
        for row in top_indicators:
            ind_id = row["indicator_id"]
            rel_id += 1
            relationships.append(
                GraphRel(
                    id=f"rel-{rel_id}",
                    from_id=f"agent-{aid}",
                    to_id=f"ind-{ind_id}",
                    type="TRIGGERED",
                    properties={"weight": row["times_detected"]},
                )
            )

    return GraphData(nodes=nodes, relationships=relationships)
