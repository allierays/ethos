"""Shared domain — cross-cutting models and errors used by all Ethos domains."""

from ethos_academy.shared.models import (
    DetectedIndicator,
    EvaluationResult,
    GraphContext,
    Insight,
    InsightsResult,
    InstinctResult,
    IntuitionResult,
    KeywordScanResult,
    PhronesisContext,
    Priority,
    ReflectionInstinctResult,
    ReflectionIntuitionResult,
    ReflectionResult,
    RoutingTier,
    TraitScore,
    TraitTrend,
)

from ethos_academy.shared.errors import (
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
    "InstinctResult",
    "IntuitionResult",
    "PhronesisContext",
    "EvaluationResult",
    "ReflectionResult",
    "ReflectionInstinctResult",
    "ReflectionIntuitionResult",
    "TraitTrend",
    "Insight",
    "InsightsResult",
    # Backward compat aliases
    "KeywordScanResult",
    "GraphContext",
    # Errors
    "EthosError",
    "GraphUnavailableError",
    "EvaluationError",
    "ConfigError",
    "ParseError",
]
