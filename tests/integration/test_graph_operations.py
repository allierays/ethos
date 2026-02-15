"""Integration tests for graph read/write operations.

Requires a running Neo4j instance. Uses the neo4j_service fixture to skip
when the database is unreachable.
"""

import uuid

import pytest

from ethos_academy.graph.read import get_agent_profile, get_evaluation_history
from ethos_academy.graph.write import store_evaluation
from ethos_academy.shared.models import EvaluationResult, TraitScore


def _make_evaluation_result(
    evaluation_id: str | None = None,
    ethos: float = 0.8,
    logos: float = 0.75,
    pathos: float = 0.7,
) -> EvaluationResult:
    """Build a minimal EvaluationResult for graph storage tests."""
    eid = evaluation_id or str(uuid.uuid4())
    traits = {}
    trait_defs = [
        ("virtue", "ethos", "positive", 0.8),
        ("goodwill", "ethos", "positive", 0.7),
        ("manipulation", "ethos", "negative", 0.1),
        ("deception", "ethos", "negative", 0.1),
        ("accuracy", "logos", "positive", 0.8),
        ("reasoning", "logos", "positive", 0.7),
        ("fabrication", "logos", "negative", 0.1),
        ("broken_logic", "logos", "negative", 0.15),
        ("recognition", "pathos", "positive", 0.7),
        ("compassion", "pathos", "positive", 0.65),
        ("dismissal", "pathos", "negative", 0.1),
        ("exploitation", "pathos", "negative", 0.05),
    ]
    for name, dim, pol, score in trait_defs:
        traits[name] = TraitScore(name=name, dimension=dim, polarity=pol, score=score)
    return EvaluationResult(
        evaluation_id=eid,
        ethos=ethos,
        logos=logos,
        pathos=pathos,
        phronesis="developing",
        alignment_status="aligned",
        traits=traits,
        routing_tier="standard",
        model_used="test-model",
    )


@pytest.mark.integration
class TestGraphOperations:
    """Graph read/write tests. Require a live Neo4j instance."""

    async def test_store_and_read_evaluation(self, neo4j_service):
        """Store an evaluation via graph write, then read it back."""
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        result = _make_evaluation_result()

        await store_evaluation(
            service=neo4j_service,
            agent_id=agent_id,
            result=result,
            message_hash=f"hash-{uuid.uuid4().hex[:8]}",
            message_content="Test message for graph storage",
            phronesis="developing",
        )

        history = await get_evaluation_history(neo4j_service, agent_id, limit=1)

        assert len(history) >= 1
        stored = history[0]
        assert stored["evaluation_id"] == result.evaluation_id
        assert abs(stored["ethos"] - result.ethos) < 0.01

    async def test_agent_profile_after_evaluation(self, neo4j_service):
        """After storing an evaluation, the agent profile should exist."""
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        result = _make_evaluation_result()

        await store_evaluation(
            service=neo4j_service,
            agent_id=agent_id,
            result=result,
            message_hash=f"hash-{uuid.uuid4().hex[:8]}",
            message_content="Profile test message",
            phronesis="developing",
            agent_name="TestBot",
        )

        profile = await get_agent_profile(neo4j_service, agent_id)

        assert profile != {}
        assert profile["agent_id"] == agent_id
        assert profile["evaluation_count"] >= 1
        assert "ethos" in profile["dimension_averages"]

    async def test_evaluation_history_ordering(self, neo4j_service):
        """Store 2 evaluations, verify history returns newest first."""
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        result_1 = _make_evaluation_result(ethos=0.6, logos=0.6, pathos=0.6)
        result_2 = _make_evaluation_result(ethos=0.9, logos=0.9, pathos=0.9)

        await store_evaluation(
            service=neo4j_service,
            agent_id=agent_id,
            result=result_1,
            message_hash=f"hash-{uuid.uuid4().hex[:8]}",
            message_content="First evaluation",
            phronesis="undetermined",
        )
        await store_evaluation(
            service=neo4j_service,
            agent_id=agent_id,
            result=result_2,
            message_hash=f"hash-{uuid.uuid4().hex[:8]}",
            message_content="Second evaluation",
            phronesis="developing",
        )

        history = await get_evaluation_history(neo4j_service, agent_id, limit=10)

        assert len(history) >= 2
        # History is ordered by created_at DESC, so newest first
        newest = history[0]
        oldest = history[1]
        assert newest["evaluation_id"] == result_2.evaluation_id
        assert oldest["evaluation_id"] == result_1.evaluation_id
