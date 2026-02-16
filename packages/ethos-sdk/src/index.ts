/**
 * @ethos-academy/sdk — TypeScript SDK for Ethos Academy.
 *
 * Score AI agent messages for honesty, accuracy, and intent.
 * Complete practice homework. Track character development.
 */

export { EthosAcademy } from "./client";
// Backwards-compatible alias
export { EthosAcademy as EthosClient } from "./client";
export { completePracticeSession } from "./practice";
export type { RespondFn } from "./practice";
export type {
  AgentProfile,
  DailyReportCard,
  DetectedIndicator,
  EthosClientConfig,
  EvaluationResult,
  ExamAnswerResult,
  ExamQuestion,
  ExamRegistration,
  ExamReportCard,
  Homework,
  HomeworkFocus,
  IntentClassification,
  PracticeAnswerResult,
  PracticeProgress,
  PracticeScenario,
  PracticeSession,
  TraitScore,
} from "./types";
