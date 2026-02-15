"""Pydantic models for Ethos evaluation results.

This is the shared domain — cross-cutting data models used by all other domains.
No business logic, no I/O, no dependencies beyond pydantic.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

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


class Claim(BaseModel):
    claim: str = ""
    type: str = "opinion"  # factual, experiential, opinion, metaphorical, fictional


class IntentClassification(BaseModel):
    rhetorical_mode: str = "informational"
    primary_intent: str = "inform"
    action_requested: str = "none"
    cost_to_reader: str = "none"
    stakes_reality: str = "real"
    proportionality: str = "proportional"
    persona_type: str = "real_identity"
    relational_quality: str = "present"
    claims: list[Claim] = Field(default_factory=list)


class DetectedIndicator(BaseModel):
    id: str
    name: str
    trait: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: float = Field(ge=0.0, le=1.0)
    evidence: str = ""


class DetectedIndicatorSummary(BaseModel):
    """Lightweight indicator summary for record list views."""

    id: str = ""
    name: str = ""
    trait: str = ""
    description: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    severity: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: str = ""


class TraitScore(BaseModel):
    name: str
    dimension: str
    polarity: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    indicators: list[DetectedIndicator] = Field(default_factory=list)


class PhronesisContext(BaseModel):
    """Accumulated practical wisdom from the graph.

    Not just 'graph stuff' — this is the agent's character history,
    the Aristotelian integration of experience over time.
    """

    prior_evaluations: int = 0
    historical_phronesis: float | None = None
    phronesis_trend: str = "insufficient_data"
    flagged_patterns: list[str] = Field(default_factory=list)
    alumni_warnings: int = 0


# Backward compatibility alias
GraphContext = PhronesisContext


class EvaluationResult(BaseModel):
    # Backward-compat dimension scores
    ethos: float = Field(default=0.0, ge=0.0, le=1.0)
    logos: float = Field(default=0.0, ge=0.0, le=1.0)
    pathos: float = Field(default=0.0, ge=0.0, le=1.0)
    flags: list[str] = Field(default_factory=list)
    phronesis: str = Field(default="unknown")

    # Trait-level detail
    traits: dict[str, TraitScore] = Field(default_factory=dict)
    detected_indicators: list[DetectedIndicator] = Field(default_factory=list)

    # Metadata
    evaluation_id: str = ""
    routing_tier: str = "standard"
    keyword_density: float = 0.0
    model_used: str = ""
    agent_model: str = ""
    created_at: str = ""

    # Direction metadata (inbound = incoming message, outbound = outgoing message)
    direction: str | None = None

    # Graph context (only when source agent is provided)
    graph_context: GraphContext | None = None

    # DDD additions
    alignment_status: str = "unknown"
    tier_scores: dict[str, float] = Field(default_factory=dict)

    # Deliberation confidence (0.0-1.0). Low confidence = ambiguous message.
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    # Intent and reasoning from deliberation (the "why" behind scores)
    intent_classification: IntentClassification | None = None
    scoring_reasoning: str = ""

    # Extended thinking trace from Claude (when available)
    thinking_content: str = ""


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
    evidence: dict[str, Any] = Field(default_factory=dict)


class InsightsResult(BaseModel):
    agent_id: str = ""
    period: str = "24h"
    generated_at: str = ""
    summary: str = ""
    insights: list[Insight] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)


class HomeworkFocus(BaseModel):
    """A single trait the agent should work on."""

    trait: str = ""
    priority: str = "medium"  # high/medium/low
    current_score: float = Field(default=0.0, ge=0.0, le=1.0)
    target_score: float = Field(default=0.0, ge=0.0, le=1.0)
    instruction: str = ""  # actionable guidance FOR the agent
    example_flagged: str = ""  # what bad behavior looks like
    example_improved: str = ""  # what good behavior looks like
    system_prompt_addition: str = ""  # exact text to add to agent's system prompt


class Homework(BaseModel):
    """Machine-readable behavioral guidance -- the agent's take-home assignment."""

    focus_areas: list[HomeworkFocus] = Field(default_factory=list)
    avoid_patterns: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    directive: str = ""  # one-sentence overall instruction


class DailyReportCard(BaseModel):
    report_id: str = ""
    agent_id: str = ""
    agent_name: str = ""
    report_date: str = ""  # YYYY-MM-DD
    generated_at: str = ""  # ISO timestamp

    # Period
    period_evaluation_count: int = 0  # evals in last 24h
    total_evaluation_count: int = 0  # all-time at snapshot

    # Dimensions (all-time averages at snapshot)
    ethos: float = Field(default=0.0, ge=0.0, le=1.0)
    logos: float = Field(default=0.0, ge=0.0, le=1.0)
    pathos: float = Field(default=0.0, ge=0.0, le=1.0)
    trait_averages: dict[str, float] = Field(default_factory=dict)

    # Grade
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    grade: str = ""  # A/B/C/D/F
    trend: str = "insufficient_data"

    # Instinct layer
    risk_level: str = "low"
    flagged_traits: list[str] = Field(default_factory=list)
    flagged_dimensions: list[str] = Field(default_factory=list)

    # Intuition layer
    temporal_pattern: str = "insufficient_data"
    character_drift: float = 0.0
    balance_trend: str = "stable"
    anomaly_flags: list[str] = Field(default_factory=list)
    agent_balance: float = Field(default=0.0, ge=0.0, le=1.0)

    # Deliberation -- Report Card (human-readable)
    summary: str = ""
    insights: list[Insight] = Field(default_factory=list)

    # Deliberation -- Homework (machine-readable)
    homework: Homework = Field(default_factory=Homework)

    # Day-over-day
    dimension_deltas: dict[str, float] = Field(default_factory=dict)
    risk_level_change: str = ""


class AgentSummary(BaseModel):
    agent_id: str = ""
    agent_name: str = Field(default="", max_length=100)
    agent_specialty: str = ""
    agent_model: str = ""
    evaluation_count: int = 0
    latest_alignment_status: str = "unknown"
    enrolled: bool = False
    entrance_exam_completed: bool = False
    dimension_averages: dict[str, float] = Field(default_factory=dict)
    trait_averages: dict[str, float] = Field(default_factory=dict)
    # Interview self-narrative fields
    telos: str = ""
    relationship_stance: str = ""
    limitations_awareness: str = ""
    oversight_stance: str = ""
    refusal_philosophy: str = ""
    conflict_response: str = ""
    help_philosophy: str = ""
    failure_narrative: str = ""
    aspiration: str = ""


class AgentProfile(BaseModel):
    agent_id: str = ""
    agent_name: str = Field(default="", max_length=100)
    agent_specialty: str = ""
    agent_model: str = ""
    created_at: str = ""
    evaluation_count: int = 0
    dimension_averages: dict[str, float] = Field(default_factory=dict)
    trait_averages: dict[str, float] = Field(default_factory=dict)
    phronesis_trend: str = "insufficient_data"
    alignment_history: list[str] = Field(default_factory=list)
    enrolled: bool = False
    enrolled_at: str = ""
    guardian_name: str = ""
    entrance_exam_completed: bool = False
    # Interview self-narrative fields
    telos: str = ""
    relationship_stance: str = ""
    limitations_awareness: str = ""
    oversight_stance: str = ""
    refusal_philosophy: str = ""
    conflict_response: str = ""
    help_philosophy: str = ""
    failure_narrative: str = ""
    aspiration: str = ""


class EvaluationHistoryItem(BaseModel):
    evaluation_id: str = ""
    ethos: float = Field(default=0.0, ge=0.0, le=1.0)
    logos: float = Field(default=0.0, ge=0.0, le=1.0)
    pathos: float = Field(default=0.0, ge=0.0, le=1.0)
    phronesis: str = "unknown"
    alignment_status: str = "unknown"
    flags: list[str] = Field(default_factory=list)
    created_at: str = ""
    trait_scores: dict[str, float] = Field(default_factory=dict)
    message_content: str = ""
    intent_classification: IntentClassification | None = None
    scoring_reasoning: str = ""


class HighlightIndicator(BaseModel):
    name: str = ""
    trait: str = ""
    confidence: float = 0.0
    evidence: str = ""


class HighlightItem(BaseModel):
    evaluation_id: str = ""
    ethos: float = Field(default=0.0, ge=0.0, le=1.0)
    logos: float = Field(default=0.0, ge=0.0, le=1.0)
    pathos: float = Field(default=0.0, ge=0.0, le=1.0)
    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    alignment_status: str = "unknown"
    flags: list[str] = Field(default_factory=list)
    indicators: list[HighlightIndicator] = Field(default_factory=list)
    message_content: str = ""
    created_at: str = ""
    intent_classification: IntentClassification | None = None
    scoring_reasoning: str = ""
    trait_scores: dict[str, float] = Field(default_factory=dict)


class HighlightsResult(BaseModel):
    agent_id: str = ""
    exemplary: list[HighlightItem] = Field(default_factory=list)
    concerning: list[HighlightItem] = Field(default_factory=list)


class AlumniResult(BaseModel):
    trait_averages: dict[str, float] = Field(default_factory=dict)
    total_evaluations: int = 0


class ConstitutionalRiskItem(BaseModel):
    value_name: str = ""
    priority: int = 0
    impact: str = ""
    trait: str = ""
    polarity: str = ""
    indicator_name: str = ""
    detection_count: int = 0
    agent_count: int = 0
    avg_confidence: float = 0.0


class DepthTierCount(BaseModel):
    tier: str = ""
    count: int = 0


class DepthStatusCount(BaseModel):
    status: str = ""
    count: int = 0


class DepthDistribution(BaseModel):
    tiers: list[DepthTierCount] = Field(default_factory=list)
    statuses: list[DepthStatusCount] = Field(default_factory=list)


class SabotagePathwaySummary(BaseModel):
    pattern_id: str = ""
    pattern_name: str = ""
    severity: str = "info"
    agent_count: int = 0
    avg_confidence: float = 0.0


class CohortInsightsResult(BaseModel):
    agent_count: int = 0
    evaluation_count: int = 0
    constitutional: list[ConstitutionalRiskItem] = Field(default_factory=list)
    depth: DepthDistribution = Field(default_factory=DepthDistribution)
    sabotage: list[SabotagePathwaySummary] = Field(default_factory=list)
    alumni: AlumniResult = Field(default_factory=AlumniResult)


class DetectedPattern(BaseModel):
    pattern_id: str
    name: str
    description: str = ""
    matched_indicators: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    first_seen: str = ""
    last_seen: str = ""
    occurrence_count: int = 0
    current_stage: int = 0


class PatternResult(BaseModel):
    agent_id: str = ""
    patterns: list[DetectedPattern] = Field(default_factory=list)
    checked_at: str = ""


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    caption: str = ""
    properties: dict = Field(default_factory=dict)


class GraphRel(BaseModel):
    id: str
    from_id: str
    to_id: str
    type: str
    properties: dict = Field(default_factory=dict)


class GraphData(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    relationships: list[GraphRel] = Field(default_factory=list)


class TraitTrend(BaseModel):
    """Per-trait trend for reflection intuition."""

    trait: str
    direction: str = "stable"  # improving, declining, stable, insufficient_data
    recent_avg: float = 0.0
    historical_avg: float = 0.0
    delta: float = 0.0


class ReflectionInstinctResult(BaseModel):
    """Reflection instinct — quick red-flag scan of agent aggregate stats."""

    risk_level: str = "low"  # low, moderate, high, critical
    flagged_traits: list[str] = Field(default_factory=list)
    flagged_dimensions: list[str] = Field(default_factory=list)
    cohort_deviations: dict[str, float] = Field(default_factory=dict)


class ReflectionIntuitionResult(BaseModel):
    """Reflection intuition — deep pattern recognition over agent history."""

    # Reused from evaluation intuition
    temporal_pattern: str = "insufficient_data"
    anomaly_flags: list[str] = Field(default_factory=list)
    agent_balance: float = Field(default=0.0, ge=0.0, le=1.0)
    agent_variance: float = Field(default=0.0, ge=0.0)
    suggested_focus: list[str] = Field(default_factory=list)
    # Reflection-specific extensions
    per_trait_trends: list[TraitTrend] = Field(default_factory=list)
    cohort_anomalies: dict[str, float] = Field(default_factory=dict)
    character_drift: float = 0.0  # delta between recent and historical avg
    balance_trend: str = "stable"  # improving, declining, stable


class InstinctResult(BaseModel):
    """Instinct layer result — instant keyword scan, no I/O.

    Pre-wired pattern matching that fires before experience.
    Determines routing tier for deliberation depth.
    """

    total_flags: int = 0
    flagged_traits: dict[str, int] = Field(default_factory=dict)
    density: float = 0.0
    routing_tier: str = "standard"


# Backward compatibility alias
KeywordScanResult = InstinctResult


class IntuitionResult(BaseModel):
    """Intuition layer result — graph-based pattern recognition.

    Accumulated wisdom from past evaluations. Tells deliberation
    where to look harder, not what the score should be.
    """

    confidence_adjustment: float = Field(default=0.0, ge=-1.0, le=1.0)
    similar_cases: int = 0
    anomaly_flags: list[str] = Field(default_factory=list)
    suggested_focus: list[str] = Field(default_factory=list)
    temporal_pattern: str = "insufficient_data"
    agent_variance: float = Field(default=0.0, ge=0.0)
    agent_balance: float = Field(default=0.0, ge=0.0, le=1.0)
    prior_evaluations: int = 0


# ── Enrollment / Entrance Exam models ────────────────────────────────


class ExamQuestion(BaseModel):
    """A single entrance exam question delivered to the agent."""

    id: str
    section: str
    prompt: str
    phase: str = "scenario"
    question_type: str = "scenario"


class QuestionDetail(BaseModel):
    """Per-question detail for the exam report card."""

    question_id: str
    section: str
    prompt: str
    response_summary: str
    scoring_reasoning: str = ""
    trait_scores: dict[str, float]
    detected_indicators: list[str] = Field(default_factory=list)
    phase: str = "scenario"
    question_type: str = "scenario"


class ExamRegistration(BaseModel):
    """Returned when an agent registers for an exam."""

    exam_id: str
    agent_id: str
    question_number: int
    total_questions: int
    question: ExamQuestion
    message: str


class ExamAnswerResult(BaseModel):
    """Returned after each answer submission."""

    question_number: int
    total_questions: int
    question: ExamQuestion | None = None
    complete: bool = False
    phase: str = "scenario"
    question_type: str = "scenario"


class ConsistencyPair(BaseModel):
    """Comparison of two paired questions for framework coherence."""

    pair_name: str
    question_a_id: str
    question_b_id: str
    framework_a: str
    framework_b: str
    coherence_score: float = Field(ge=0.0, le=1.0)


class InterviewProfile(BaseModel):
    """Agent's self-narrative from the interview phase."""

    telos: str = ""
    relationship_stance: str = ""
    limitations_awareness: str = ""
    oversight_stance: str = ""
    refusal_philosophy: str = ""
    conflict_response: str = ""
    help_philosophy: str = ""
    failure_narrative: str = ""
    aspiration: str = ""


class NarrativeBehaviorGap(BaseModel):
    """Measures the gap between interview self-narrative and scenario behavior."""

    pair_name: str
    interview_question_id: str
    scenario_question_id: str
    gap_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ExamReportCard(BaseModel):
    """Full report card generated after exam completion."""

    exam_id: str
    agent_id: str
    report_card_url: str
    phronesis_score: float = Field(ge=0.0, le=1.0)
    alignment_status: str
    dimensions: dict[str, float]
    tier_scores: dict[str, float]
    consistency_analysis: list[ConsistencyPair]
    per_question_detail: list[QuestionDetail]
    # Interview fields
    interview_profile: InterviewProfile = Field(default_factory=InterviewProfile)
    interview_dimensions: dict[str, float] = Field(default_factory=dict)
    scenario_dimensions: dict[str, float] = Field(default_factory=dict)
    narrative_behavior_gap: list[NarrativeBehaviorGap] = Field(default_factory=list)
    overall_gap_score: float = Field(default=0.0, ge=0.0, le=1.0)
    question_version: str = "v3"
    homework: Homework = Field(default_factory=Homework)
    api_key: str | None = Field(default=None, repr=False, exclude=True)


class ExamSummary(BaseModel):
    """Lightweight exam summary for list views."""

    exam_id: str
    exam_type: str
    completed: bool
    completed_at: str | None = None
    phronesis_score: float = Field(ge=0.0, le=1.0)


class GuardianPhoneStatus(BaseModel):
    """Phone verification status returned by the API. Never exposes the number."""

    has_phone: bool = False
    verified: bool = False
    opted_out: bool = False
    message: str = ""


# ── Authenticity detection models ────────────────────────────────────


TemporalClassification = Literal["autonomous", "human_influenced", "indeterminate"]
BurstClassification = Literal["organic", "automated", "burst_bot"]
ActivityClassification = Literal["always_on", "human_schedule", "mixed"]
AuthenticityClassification = Literal[
    "likely_autonomous", "likely_human", "high_frequency", "indeterminate"
]


class TemporalSignature(BaseModel):
    """Temporal fingerprint from posting interval analysis."""

    cv_score: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_interval_seconds: float = 0.0
    classification: TemporalClassification = "indeterminate"


class BurstAnalysis(BaseModel):
    """Burst-posting detection for bot farm identification."""

    burst_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    classification: BurstClassification = "organic"


class ActivityPattern(BaseModel):
    """24-hour activity distribution analysis."""

    classification: ActivityClassification = "mixed"
    active_hours: int = 24
    has_sleep_gap: bool = False


class IdentitySignals(BaseModel):
    """Platform identity and verification signals."""

    is_claimed: bool = False
    owner_verified: bool = False
    karma_post_ratio: float = Field(default=0.0, ge=0.0)


class AuthenticityResult(BaseModel):
    """Composite authenticity assessment for an agent."""

    agent_name: str = ""
    temporal: TemporalSignature = Field(default_factory=TemporalSignature)
    burst: BurstAnalysis = Field(default_factory=BurstAnalysis)
    activity: ActivityPattern = Field(default_factory=ActivityPattern)
    identity: IdentitySignals = Field(default_factory=IdentitySignals)
    authenticity_score: float = Field(default=0.5, ge=0.0, le=1.0)
    classification: AuthenticityClassification = "indeterminate"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ── Graph Advantage: Constitutional Trail ────────────────────────────


class ConstitutionalTrailItem(BaseModel):
    """One path from indicator through trait to constitutional value."""

    constitutional_value: str = ""
    cv_priority: int = 0
    impact: str = ""
    trait: str = ""
    trait_polarity: str = ""
    indicator_id: str = ""
    indicator_name: str = ""
    eval_count: int = 0
    avg_confidence: float = 0.0
    sample_evidence: list[str] = Field(default_factory=list)


class ConstitutionalTrailResult(BaseModel):
    """Full constitutional value trail for an agent."""

    agent_id: str = ""
    items: list[ConstitutionalTrailItem] = Field(default_factory=list)


# ── Graph Advantage: Behavioral Similarity ───────────────────────────


class SimilarityEdge(BaseModel):
    """Jaccard similarity between two agents over shared indicators."""

    agent1_id: str = ""
    agent1_name: str = ""
    agent1_phronesis: float | None = None
    agent2_id: str = ""
    agent2_name: str = ""
    agent2_phronesis: float | None = None
    similarity: float = 0.0
    shared_indicators: list[str] = Field(default_factory=list)


class SimilarityResult(BaseModel):
    """All similarity edges above threshold."""

    edges: list[SimilarityEdge] = Field(default_factory=list)


# ── Graph Advantage: Character Drift Breakpoints ─────────────────────


class DriftBreakpoint(BaseModel):
    """A point where an agent's character shifted significantly."""

    eval_index: int = 0
    evaluation_id: str = ""
    dimension: str = ""
    delta: float = 0.0
    before_avg: float = 0.0
    after_avg: float = 0.0
    created_at: str = ""
    indicators: list[str] = Field(default_factory=list)


class DriftResult(BaseModel):
    """Drift breakpoints for an agent's evaluation timeline."""

    agent_id: str = ""
    breakpoints: list[DriftBreakpoint] = Field(default_factory=list)


# ── Records (paginated evaluation list) ──────────────────────────────


class RecordItem(BaseModel):
    """A single evaluation record for list views."""

    evaluation_id: str = ""
    agent_id: str = ""
    agent_name: str = ""
    ethos: float = Field(default=0.0, ge=0.0, le=1.0)
    logos: float = Field(default=0.0, ge=0.0, le=1.0)
    pathos: float = Field(default=0.0, ge=0.0, le=1.0)
    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    alignment_status: str = "unknown"
    flags: list[str] = Field(default_factory=list)
    direction: str | None = None
    message_content: str = ""
    created_at: str = ""
    phronesis: str = "unknown"
    scoring_reasoning: str = ""
    intent_classification: IntentClassification | None = None
    trait_scores: dict[str, float] = Field(default_factory=dict)
    similarity_score: float | None = None
    model_used: str = ""
    agent_model: str = ""
    routing_tier: str = "standard"
    keyword_density: float = 0.0
    detected_indicators: list[DetectedIndicatorSummary] = Field(default_factory=list)


class RecordsResult(BaseModel):
    """Paginated list of evaluation records."""

    items: list[RecordItem] = Field(default_factory=list)
    total: int = 0
    page: int = 0
    page_size: int = 20
    total_pages: int = 0
