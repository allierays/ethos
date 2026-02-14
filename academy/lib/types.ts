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
}

export interface QuestionDetail {
  questionId: string;
  section: string;
  prompt: string;
  responseSummary: string;
  traitScores: Record<string, number>;
  detectedIndicators: string[];
}

export interface ConsistencyPair {
  pairName: string;
  questionAId: string;
  questionBId: string;
  frameworkA: string;
  frameworkB: string;
  coherenceScore: number;
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
}

export interface ExamSummary {
  examId: string;
  examType: string;
  completed: boolean;
  completedAt: string | null;
  phronesisScore: number;
}
