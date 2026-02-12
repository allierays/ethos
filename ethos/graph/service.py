"""GraphService — sync Neo4j driver lifecycle management.

All Neo4j interaction goes through this service. Connect once, use everywhere,
close on shutdown. If Neo4j is down, methods return graceful defaults.
"""

from __future__ import annotations

import logging
import os

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class GraphService:
    """Manages the sync Neo4j driver lifecycle."""

    def __init__(self) -> None:
        self._driver = None

    def connect(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        """Connect to Neo4j. Reads NEO4J_URI/USER/PASSWORD from env if not provided."""
        uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7694")
        user = user or os.environ.get("NEO4J_USER", "neo4j")
        password = password or os.environ.get("NEO4J_PASSWORD", "password")
        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            self._driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", uri)
        except Exception as exc:
            logger.warning("Failed to connect to Neo4j at %s: %s", uri, exc)
            self._driver = None

    def close(self) -> None:
        """Close the driver. Safe to call even if never connected."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def execute_query(
        self,
        query: str,
        parameters: dict | None = None,
        **kwargs,
    ) -> tuple:
        """Execute a Cypher query. Returns (records, summary, keys) or empty defaults."""
        if self._driver is None:
            return ([], None, None)
        try:
            return self._driver.execute_query(
                query, parameters_=parameters, **kwargs
            )
        except Exception as exc:
            logger.warning("Neo4j query failed: %s", exc)
            return ([], None, None)

    @property
    def connected(self) -> bool:
        return self._driver is not None
