"""Pydantic models for Ethos evaluation results.

This is the shared domain — cross-cutting data models used by all other domains.
No business logic, no I/O, no dependencies beyond pydantic.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RoutingTier(str, Enum):
    STANDARD = "standard"
    FOCUSED = "focused"
    DEEP = "deep"
    DEEP_WITH_CONTEXT = "deep_with_context"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    STANDARD = "standard"
    LOW = "low"


class DetectedIndicator(BaseModel):
    id: str
    name: str
    trait: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: float = Field(ge=0.0, le=1.0)
    evidence: str = ""


class TraitScore(BaseModel):
    name: str
    dimension: str
    polarity: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    indicators: list[DetectedIndicator] = Field(default_factory=list)


class GraphContext(BaseModel):
    prior_evaluations: int = 0
    historical_trust: float | None = None
    trust_trend: str = "insufficient_data"
    flagged_patterns: list[str] = Field(default_factory=list)
    network_warnings: int = 0


class EvaluationResult(BaseModel):
    # Backward-compat dimension scores
    ethos: float = Field(default=0.0, ge=0.0, le=1.0)
    logos: float = Field(default=0.0, ge=0.0, le=1.0)
    pathos: float = Field(default=0.0, ge=0.0, le=1.0)
    flags: list[str] = Field(default_factory=list)
    trust: str = Field(default="unknown")

    # Trait-level detail
    traits: dict[str, TraitScore] = Field(default_factory=dict)
    detected_indicators: list[DetectedIndicator] = Field(default_factory=list)

    # Metadata
    evaluation_id: str = ""
    routing_tier: str = "standard"
    keyword_density: float = 0.0
    model_used: str = ""
    created_at: str = ""

    # Graph context (only when source agent is provided)
    graph_context: GraphContext | None = None

    # DDD additions
    alignment_status: str = "unknown"
    tier_scores: dict[str, float] = Field(default_factory=dict)


class ReflectionResult(BaseModel):
    # Backward-compat fields
    compassion: float = Field(default=0.0, ge=0.0, le=1.0)
    honesty: float = Field(default=0.0, ge=0.0, le=1.0)
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    trend: str = Field(default="stable")

    # New fields
    ethos: float = Field(default=0.0, ge=0.0, le=1.0)
    logos: float = Field(default=0.0, ge=0.0, le=1.0)
    pathos: float = Field(default=0.0, ge=0.0, le=1.0)
    trait_averages: dict[str, float] = Field(default_factory=dict)
    evaluation_count: int = 0
    agent_id: str = ""


class Insight(BaseModel):
    trait: str
    severity: str = "info"  # info, warning, critical
    message: str = ""
    evidence: dict = Field(default_factory=dict)


class InsightsResult(BaseModel):
    agent_id: str = ""
    period: str = "24h"
    generated_at: str = ""
    summary: str = ""
    insights: list[Insight] = Field(default_factory=list)
    stats: dict = Field(default_factory=dict)


class KeywordScanResult(BaseModel):
    total_flags: int = 0
    flagged_traits: dict[str, int] = Field(default_factory=dict)
    density: float = 0.0
    routing_tier: str = "standard"
