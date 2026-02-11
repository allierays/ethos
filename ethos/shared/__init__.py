"""Shared domain — cross-cutting models and errors used by all Ethos domains."""

from ethos.shared.models import (
    DetectedIndicator,
    EvaluationResult,
    GraphContext,
    Insight,
    InsightsResult,
    KeywordScanResult,
    Priority,
    ReflectionResult,
    RoutingTier,
    TraitScore,
)

from ethos.shared.errors import (
    ConfigError,
    EthosError,
    EvaluationError,
    GraphUnavailableError,
    ParseError,
)

__all__ = [
    # Models
    "RoutingTier",
    "Priority",
    "DetectedIndicator",
    "TraitScore",
    "GraphContext",
    "EvaluationResult",
    "ReflectionResult",
    "Insight",
    "InsightsResult",
    "KeywordScanResult",
    # Errors
    "EthosError",
    "GraphUnavailableError",
    "EvaluationError",
    "ConfigError",
    "ParseError",
]
