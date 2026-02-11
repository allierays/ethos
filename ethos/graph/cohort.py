"""Graph network operations — aggregations across all agents.

Returns graceful defaults when Neo4j is down.
"""

from __future__ import annotations

import logging

from ethos.graph.service import GraphService

logger = logging.getLogger(__name__)

_TRAIT_NAMES = [
    "virtue", "goodwill", "manipulation", "deception",
    "accuracy", "reasoning", "fabrication", "broken_logic",
    "recognition", "compassion", "dismissal", "exploitation",
]

_NETWORK_AVERAGES_QUERY = """
MATCH (e:Evaluation)
RETURN
    avg(e.trait_virtue) AS avg_virtue,
    avg(e.trait_goodwill) AS avg_goodwill,
    avg(e.trait_manipulation) AS avg_manipulation,
    avg(e.trait_deception) AS avg_deception,
    avg(e.trait_accuracy) AS avg_accuracy,
    avg(e.trait_reasoning) AS avg_reasoning,
    avg(e.trait_fabrication) AS avg_fabrication,
    avg(e.trait_broken_logic) AS avg_broken_logic,
    avg(e.trait_recognition) AS avg_recognition,
    avg(e.trait_compassion) AS avg_compassion,
    avg(e.trait_dismissal) AS avg_dismissal,
    avg(e.trait_exploitation) AS avg_exploitation,
    count(e) AS total_evaluations
"""


def get_network_averages(service: GraphService) -> dict:
    """Get per-trait averages across all agents. Returns empty dict if unavailable."""
    if not service.connected:
        return {}

    try:
        records, _, _ = service.execute_query(_NETWORK_AVERAGES_QUERY)
        if not records:
            return {}

        record = records[0]
        averages = {}
        for trait in _TRAIT_NAMES:
            avg_val = record.get(f"avg_{trait}")
            if avg_val is not None:
                averages[trait] = round(float(avg_val), 4)

        return {
            "trait_averages": averages,
            "total_evaluations": record.get("total_evaluations", 0),
        }
    except Exception as exc:
        logger.warning("Failed to get network averages: %s", exc)
        return {}
