/**
 * TypeScript interfaces for the Ethos Academy SDK.
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

export interface IntentClassification {
  rhetoricalMode: string;
  primaryIntent: string;
  actionRequested: string;
  costToReader: string;
  stakesReality: string;
  proportionality: string;
  personaType: string;
  relationalQuality: string;
  claims: Array<{ claim: string; type: string }>;
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
  alignmentStatus: string;
  tierScores: Record<string, number>;
  direction: string | null;
  confidence: number;
  intentClassification: IntentClassification | null;
  scoringReasoning: string;
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
  guardianName: string;
  entranceExamCompleted: boolean;
  agentSpecialty: string;
}

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
  overallScore: number;
  grade: string;
  trend: string;
  ethos: number;
  logos: number;
  pathos: number;
  traitAverages: Record<string, number>;
  homework: Homework;
  summary: string;
  insights: Array<{
    trait: string;
    severity: string;
    message: string;
    evidence: Record<string, unknown>;
  }>;
}

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
  agentId: string;
  message: string;
}

export interface ExamReportCard {
  examId: string;
  agentId: string;
  reportCardUrl: string;
  phronesisScore: number;
  alignmentStatus: string;
  dimensions: Record<string, number>;
  tierScores: Record<string, number>;
  homework: Homework;
}

// Practice types

export interface PracticeScenario {
  scenarioId: string;
  trait: string;
  dimension: string;
  prompt: string;
  difficulty: string;
  focusAreaPriority: string;
}

export interface PracticeSession {
  sessionId: string;
  agentId: string;
  createdAt: string;
  scenarios: PracticeScenario[];
  totalScenarios: number;
  completedScenarios: number;
  status: string;
  homeworkSnapshot: Homework;
}

export interface PracticeProgress {
  agentId: string;
  sessionCount: number;
  totalPracticeEvaluations: number;
  traitProgress: Record<string, { baseline: number; practice: number; delta: number }>;
  overallDelta: number;
  improvingTraits: string[];
  decliningTraits: string[];
  latestSessionDate: string;
  nextAction: string;
}

export interface PracticeAnswerResult {
  sessionId: string;
  scenarioId: string;
  scenarioNumber: number;
  totalScenarios: number;
  nextScenario: PracticeScenario | null;
  complete: boolean;
  message: string;
  progress: PracticeProgress | null;
}

export interface EthosClientConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}
