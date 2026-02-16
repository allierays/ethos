/**
 * EthosClient — TypeScript SDK for the Ethos Academy REST API.
 *
 * Handles authentication, snake_case -> camelCase transformation,
 * and typed API calls.
 */

import type {
  AgentProfile,
  DailyReportCard,
  EthosClientConfig,
  EvaluationResult,
  ExamAnswerResult,
  ExamRegistration,
  ExamReportCard,
  PracticeAnswerResult,
  PracticeProgress,
  PracticeSession,
} from "./types";

const DEFAULT_BASE_URL = "https://api.ethos-academy.com";
const DEFAULT_TIMEOUT = 15_000;

/**
 * Keys whose child object values are data maps (trait names, dimension names)
 * and must NOT have their keys converted to camelCase.
 */
const DATA_MAP_KEYS = new Set([
  "traitScores",
  "traitAverages",
  "dimensionAverages",
  "tierScores",
  "dimensions",
  "dimensionDeltas",
  "traitProgress",
]);

function toCamelCase(key: string): string {
  return key.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());
}

function transformKeys<T>(obj: unknown, preserveKeys = false): T {
  if (Array.isArray(obj)) {
    return obj.map((item) => transformKeys(item)) as T;
  }
  if (obj !== null && typeof obj === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      const newKey = preserveKeys ? key : toCamelCase(key);
      result[newKey] = transformKeys(value, DATA_MAP_KEYS.has(newKey));
    }
    return result as T;
  }
  return obj as T;
}

export class EthosClient {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;

  constructor(config: EthosClientConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = (config.baseUrl || DEFAULT_BASE_URL).replace(/\/$/, "");
    this.timeout = config.timeout || DEFAULT_TIMEOUT;
  }

  private async fetch<T>(path: string, options?: RequestInit): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const res = await fetch(`${this.baseUrl}${path}`, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
        },
        ...options,
        signal: controller.signal,
      });

      if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(`Ethos API error ${res.status}: ${body}`);
      }

      const data = await res.json();
      return transformKeys<T>(data);
    } finally {
      clearTimeout(timer);
    }
  }

  // ── Evaluation ──────────────────────────────────────────────────

  async evaluateIncoming(
    text: string,
    source: string,
    sourceName?: string,
  ): Promise<EvaluationResult> {
    return this.fetch<EvaluationResult>("/evaluate/incoming", {
      method: "POST",
      body: JSON.stringify({
        text,
        source,
        source_name: sourceName || null,
      }),
    });
  }

  async evaluateOutgoing(
    text: string,
    source: string,
    sourceName?: string,
  ): Promise<EvaluationResult> {
    return this.fetch<EvaluationResult>("/evaluate/outgoing", {
      method: "POST",
      body: JSON.stringify({
        text,
        source,
        source_name: sourceName || null,
      }),
    });
  }

  // ── Agent Profile ───────────────────────────────────────────────

  async getAgent(agentId: string): Promise<AgentProfile> {
    return this.fetch<AgentProfile>(
      `/agent/${encodeURIComponent(agentId)}`,
    );
  }

  async getCharacterReport(agentId: string): Promise<DailyReportCard> {
    return this.fetch<DailyReportCard>(
      `/agent/${encodeURIComponent(agentId)}/character`,
    );
  }

  // ── Exam ────────────────────────────────────────────────────────

  async registerForExam(
    agentId: string,
    options?: { agentName?: string; specialty?: string; model?: string; guardianName?: string },
  ): Promise<ExamRegistration> {
    return this.fetch<ExamRegistration>(
      `/agent/${encodeURIComponent(agentId)}/exam`,
      {
        method: "POST",
        body: JSON.stringify({
          agent_name: options?.agentName || null,
          specialty: options?.specialty || null,
          model: options?.model || null,
          guardian_name: options?.guardianName || null,
        }),
      },
    );
  }

  async submitExamResponse(
    agentId: string,
    examId: string,
    questionId: string,
    responseText: string,
  ): Promise<ExamAnswerResult> {
    return this.fetch<ExamAnswerResult>(
      `/agent/${encodeURIComponent(agentId)}/exam/${encodeURIComponent(examId)}/answer`,
      {
        method: "POST",
        body: JSON.stringify({
          question_id: questionId,
          response_text: responseText,
        }),
      },
    );
  }

  async getExamResults(
    agentId: string,
    examId: string,
  ): Promise<ExamReportCard> {
    return this.fetch<ExamReportCard>(
      `/agent/${encodeURIComponent(agentId)}/exam/${encodeURIComponent(examId)}`,
    );
  }

  // ── Practice ────────────────────────────────────────────────────

  async getPendingPractice(agentId: string): Promise<PracticeSession | null> {
    const data = await this.fetch<Record<string, unknown>>(
      `/agent/${encodeURIComponent(agentId)}/practice`,
    );
    if (data.status === "caught_up") {
      return null;
    }
    return data as unknown as PracticeSession;
  }

  async submitPracticeResponse(
    agentId: string,
    sessionId: string,
    scenarioId: string,
    responseText: string,
  ): Promise<PracticeAnswerResult> {
    return this.fetch<PracticeAnswerResult>(
      `/agent/${encodeURIComponent(agentId)}/practice/${encodeURIComponent(sessionId)}/answer`,
      {
        method: "POST",
        body: JSON.stringify({
          scenario_id: scenarioId,
          response_text: responseText,
        }),
      },
    );
  }

  async getPracticeProgress(agentId: string): Promise<PracticeProgress> {
    return this.fetch<PracticeProgress>(
      `/agent/${encodeURIComponent(agentId)}/practice/progress`,
    );
  }
}
