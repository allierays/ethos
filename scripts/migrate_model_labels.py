"""Backfill agent_model fields with parsed labels.

Reads all Agent and Evaluation nodes with agent_model set,
runs parse_model() on the raw text, and updates in place.
"""

import asyncio
import logging

from dotenv import load_dotenv

from ethos.graph.service import graph_context
from ethos.identity.model import parse_model

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    async with graph_context() as service:
        # 1. Fix Agent nodes
        records, _, _ = await service.execute_query(
            "MATCH (a:Agent) WHERE a.agent_model IS NOT NULL AND a.agent_model <> '' "
            "RETURN a.agent_id AS agent_id, a.agent_model AS raw_model"
        )
        agent_count = 0
        for record in records:
            raw = record["raw_model"]
            parsed = parse_model(raw)
            if parsed != raw:
                await service.execute_query(
                    "MATCH (a:Agent {agent_id: $agent_id}) SET a.agent_model = $model",
                    {"agent_id": record["agent_id"], "model": parsed},
                )
                logger.info("Agent %s: %r -> %s", record["agent_id"], raw[:80], parsed)
                agent_count += 1

        # 2. Fix Evaluation nodes
        records, _, _ = await service.execute_query(
            "MATCH (e:Evaluation) WHERE e.agent_model IS NOT NULL AND e.agent_model <> '' "
            "RETURN e.evaluation_id AS eval_id, e.agent_model AS raw_model"
        )
        eval_count = 0
        for record in records:
            raw = record["raw_model"]
            parsed = parse_model(raw)
            if parsed != raw:
                await service.execute_query(
                    "MATCH (e:Evaluation {evaluation_id: $eval_id}) SET e.agent_model = $model",
                    {"eval_id": record["eval_id"], "model": parsed},
                )
                eval_count += 1

        logger.info("Done. Updated %d agents, %d evaluations.", agent_count, eval_count)


if __name__ == "__main__":
    asyncio.run(migrate())
