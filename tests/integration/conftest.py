"""Integration test fixtures -- skip when Neo4j or API key unavailable."""

import os
import pytest

from ethos_academy.graph.service import GraphService


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless -m integration is specified."""
    if "integration" not in (config.option.markexpr or ""):
        skip = pytest.mark.skip(reason="integration tests require -m integration")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)


@pytest.fixture
async def neo4j_service():
    """Provide a connected GraphService. Skip test if Neo4j is unreachable."""
    service = GraphService()
    await service.connect()
    if not service.connected:
        pytest.skip("Neo4j not available")
    yield service
    await service.close()


@pytest.fixture
def api_key_available():
    """Check if ANTHROPIC_API_KEY is set. Skip test if not."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
