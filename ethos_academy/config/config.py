"""EthosConfig — immutable configuration loaded from environment variables.

Config owns all configuration: API keys, connection strings, priorities.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from ethos_academy.shared.errors import ConfigError
from ethos_academy.shared.models import Priority


@dataclass(frozen=True)
class EthosConfig:
    anthropic_api_key: str
    neo4j_uri: str = "bolt://localhost:7694"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    priorities: dict[str, Priority] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> EthosConfig:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ConfigError(
                "ANTHROPIC_API_KEY environment variable is required but not set"
            )

        return cls(
            anthropic_api_key=api_key,
            neo4j_uri=os.environ.get("NEO4J_URI", "bolt://localhost:7694"),
            neo4j_user=os.environ.get("NEO4J_USER", "neo4j"),
            neo4j_password=os.environ.get("NEO4J_PASSWORD", "password"),
        )
