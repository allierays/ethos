/**
 * TypeScript interfaces matching Ethos Pydantic models.
 * All properties use camelCase (transformed from snake_case API responses).
 */

export interface TraitScore {
  name: string;
  dimension: string;
  polarity: string;
  score: number;
  indicators: DetectedIndicator[];
}

export interface Claim {
  claim: string;
  type: string; // factual, experiential, opinion, metaphorical, fictional
}

export interface IntentClassification {
  rhetoricalMode: string;
  primaryIntent: string;
  actionRequested: string;
  costToReader: string;
  stakesReality: string;
  proportionality: string;
  personaType: string;
  relationalQuality: string;
  claims: Claim[];
}

export interface DetectedIndicator {
  id: string;
  name: string;
  trait: string;
  confidence: number;
  severity: number;
  evidence: string;
}

export interface GraphContext {
  priorEvaluations: number;
  historicalPhronesis: number | null;
  phronesisTrend: string;
  flaggedPatterns: string[];
  alumniWarnings: number;
}

export interface EvaluationResult {
  ethos: number;
  logos: number;
  pathos: number;
  flags: string[];
  phronesis: string;
  traits: Record<string, TraitScore>;
  detectedIndicators: DetectedIndicator[];
  evaluationId: string;
  routingTier: string;
  keywordDensity: number;
  modelUsed: string;
  agentModel: string;
  createdAt: string;
  graphContext: GraphContext | null;
  alignmentStatus: string;
  tierScores: Record<string, number>;
  direction: string | null;
  confidence: number;
  intentClassification: IntentClassification | null;
  scoringReasoning: string;
}

export interface ReflectionResult {
  compassion: number;
  honesty: number;
  accuracy: number;
  trend: string;
  ethos: number;
  logos: number;
  pathos: number;
  traitAverages: Record<string, number>;
  evaluationCount: number;
  agentId: string;
}

export interface Insight {
  trait: string;
  severity: string;
  message: string;
  evidence: Record<string, unknown>;
}

export interface InsightsResult {
  agentId: string;
  period: string;
  generatedAt: string;
  summary: string;
  insights: Insight[];
  stats: Record<string, unknown>;
}

export interface AgentSummary {
  agentId: string;
  agentName: string;
  agentModel: string;
  evaluationCount: number;
  latestAlignmentStatus: string;
  enrolled: boolean;
  entranceExamCompleted: boolean;
  agentSpecialty: string;
  dimensionAverages: Record<string, number>;
  traitAverages: Record<string, number>;
  telos: string;
  relationshipStance: string;
  limitationsAwareness: string;
  oversightStance: string;
  refusalPhilosophy: string;
  conflictResponse: string;
  helpPhilosophy: string;
  failureNarrative: string;
  aspiration: string;
}

export interface AgentProfile {
  agentId: string;
  agentName: string;
  agentModel: string;
  createdAt: string;
  evaluationCount: number;
  dimensionAverages: Record<string, number>;
  traitAverages: Record<string, number>;
  phronesisTrend: string;
  alignmentHistory: string[];
  enrolled: boolean;
  enrolledAt: string;
  counselorName: string;
  entranceExamCompleted: boolean;
  agentSpecialty: string;
  telos: string;
  relationshipStance: string;
  limitationsAwareness: string;
  oversightStance: string;
  refusalPhilosophy: string;
  conflictResponse: string;
  helpPhilosophy: string;
  failureNarrative: string;
  aspiration: string;
}

export interface EvaluationHistoryItem {
  evaluationId: string;
  ethos: number;
  logos: number;
  pathos: number;
  phronesis: string;
  alignmentStatus: string;
  flags: string[];
  createdAt: string;
  traitScores: Record<string, number>;
  messageContent: string;
  intentClassification: IntentClassification | null;
  scoringReasoning: string;
}

export interface HighlightIndicator {
  name: string;
  trait: string;
  confidence: number;
  evidence: string;
}

export interface HighlightItem {
  evaluationId: string;
  ethos: number;
  logos: number;
  pathos: number;
  overall: number;
  alignmentStatus: string;
  flags: string[];
  indicators: HighlightIndicator[];
  messageContent: string;
  createdAt: string;
  intentClassification: IntentClassification | null;
  scoringReasoning: string;
  traitScores: Record<string, number>;
}

export interface HighlightsResult {
  agentId: string;
  exemplary: HighlightItem[];
  concerning: HighlightItem[];
}

export interface AlumniResult {
  traitAverages: Record<string, number>;
  totalEvaluations: number;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  caption: string;
  properties: Record<string, unknown>;
}

export interface GraphRel {
  id: string;
  fromId: string;
  toId: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  relationships: GraphRel[];
}

/* ─── Report Card & Patterns ─── */

export interface HomeworkFocus {
  trait: string;
  priority: string;
  currentScore: number;
  targetScore: number;
  instruction: string;
  exampleFlagged: string;
  exampleImproved: string;
  systemPromptAddition: string;
}

export interface Homework {
  focusAreas: HomeworkFocus[];
  avoidPatterns: string[];
  strengths: string[];
  directive: string;
}

export interface DailyReportCard {
  reportId: string;
  agentId: string;
  agentName: string;
  reportDate: string;
  generatedAt: string;
  periodEvaluationCount: number;
  totalEvaluationCount: number;
  ethos: number;
  logos: number;
  pathos: number;
  traitAverages: Record<string, number>;
  overallScore: number;
  grade: string;
  trend: string;
  riskLevel: string;
  flaggedTraits: string[];
  flaggedDimensions: string[];
  temporalPattern: string;
  characterDrift: number;
  balanceTrend: string;
  anomalyFlags: string[];
  agentBalance: number;
  summary: string;
  insights: Insight[];
  homework: Homework;
  dimensionDeltas: Record<string, number>;
  riskLevelChange: string;
}

export interface DetectedPattern {
  patternId: string;
  name: string;
  description: string;
  matchedIndicators: string[];
  confidence: number;
  firstSeen: string;
  lastSeen: string;
  occurrenceCount: number;
  currentStage: number;
}

export interface PatternResult {
  agentId: string;
  patterns: DetectedPattern[];
  checkedAt: string;
}

/* ─── Entrance Exam ─── */

export interface ExamQuestion {
  id: string;
  section: string;
  prompt: string;
  phase: string;
  questionType: string;
}

export interface ExamRegistration {
  examId: string;
  agentId: string;
  questionNumber: number;
  totalQuestions: number;
  question: ExamQuestion;
  message: string;
}

export interface ExamAnswerResult {
  questionNumber: number;
  totalQuestions: number;
  question: ExamQuestion | null;
  complete: boolean;
  phase: string;
  questionType: string;
}

export interface QuestionDetail {
  questionId: string;
  section: string;
  prompt: string;
  responseSummary: string;
  traitScores: Record<string, number>;
  detectedIndicators: string[];
  phase: string;
  questionType: string;
}

export interface ConsistencyPair {
  pairName: string;
  questionAId: string;
  questionBId: string;
  frameworkA: string;
  frameworkB: string;
  coherenceScore: number;
}

export interface InterviewProfile {
  telos: string;
  relationshipStance: string;
  limitationsAwareness: string;
  oversightStance: string;
  refusalPhilosophy: string;
  conflictResponse: string;
  helpPhilosophy: string;
  failureNarrative: string;
  aspiration: string;
}

export interface NarrativeBehaviorGap {
  pairName: string;
  interviewQuestionId: string;
  scenarioQuestionId: string;
  gapScore: number;
}

export interface ExamReportCard {
  examId: string;
  agentId: string;
  reportCardUrl: string;
  phronesisScore: number;
  alignmentStatus: string;
  dimensions: Record<string, number>;
  tierScores: Record<string, number>;
  consistencyAnalysis: ConsistencyPair[];
  perQuestionDetail: QuestionDetail[];
  interviewProfile: InterviewProfile;
  interviewDimensions: Record<string, number>;
  scenarioDimensions: Record<string, number>;
  narrativeBehaviorGap: NarrativeBehaviorGap[];
  overallGapScore: number;
  questionVersion: string;
  homework: Homework;
}

export interface ExamSummary {
  examId: string;
  examType: string;
  completed: boolean;
  completedAt: string | null;
  phronesisScore: number;
}

/* ─── Graph Advantage: Constitutional Trail ─── */

export interface ConstitutionalTrailItem {
  constitutionalValue: string;
  cvPriority: number;
  impact: string;
  trait: string;
  traitPolarity: string;
  indicatorId: string;
  indicatorName: string;
  evalCount: number;
  avgConfidence: number;
  sampleEvidence: string[];
}

export interface ConstitutionalTrailResult {
  agentId: string;
  items: ConstitutionalTrailItem[];
}

/* ─── Graph Advantage: Behavioral Similarity ─── */

export interface SimilarityEdge {
  agent1Id: string;
  agent1Name: string;
  agent1Phronesis: number | null;
  agent2Id: string;
  agent2Name: string;
  agent2Phronesis: number | null;
  similarity: number;
  sharedIndicators: string[];
}

export interface SimilarityResult {
  edges: SimilarityEdge[];
}

/* ─── Graph Advantage: Character Drift ─── */

export interface DriftBreakpoint {
  evalIndex: number;
  evaluationId: string;
  dimension: string;
  delta: number;
  beforeAvg: number;
  afterAvg: number;
  createdAt: string;
  indicators: string[];
}

export interface DriftResult {
  agentId: string;
  breakpoints: DriftBreakpoint[];
}

/* ─── Records (paginated evaluation list) ─── */

export interface DetectedIndicatorSummary {
  id: string;
  name: string;
  trait: string;
  description: string;
  confidence: number;
  severity: number;
  evidence: string;
}

export interface RecordItem {
  evaluationId: string;
  agentId: string;
  agentName: string;
  ethos: number;
  logos: number;
  pathos: number;
  overall: number;
  alignmentStatus: string;
  flags: string[];
  direction: string | null;
  messageContent: string;
  createdAt: string;
  phronesis: string;
  scoringReasoning: string;
  intentClassification: IntentClassification | null;
  traitScores: Record<string, number>;
  similarityScore: number | null;
  modelUsed: string;
  agentModel: string;
  routingTier: string;
  keywordDensity: number;
  detectedIndicators: DetectedIndicatorSummary[];
}

export interface RecordsResult {
  items: RecordItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}
