/**
 * Typed API client for the Ethos backend.
 * Transforms snake_case responses to camelCase TypeScript interfaces.
 */

import type {
  AgentProfile,
  AgentSummary,
  AlumniResult,
  ConstitutionalTrailResult,
  DailyReportCard,
  DriftResult,
  EvaluationHistoryItem,
  EvaluationResult,
  ExamReportCard,
  ExamSummary,
  GraphData,
  GuardianPhoneStatus,
  HighlightsResult,
  InsightsResult,
  PatternResult,
  RecordsResult,
  ReflectionResult,
  SimilarityResult,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8917";

/**
 * Recursively transform snake_case keys to camelCase.
 */
function toCamelCase(key: string): string {
  return key.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
}

/**
 * Keys whose child object keys are data values (trait names, dimension names)
 * and must NOT be converted to camelCase.
 */
const DATA_MAP_KEYS = new Set([
  "traitScores",
  "traitAverages",
  "dimensionAverages",
  "tierScores",
  "dimensions",
  "dimensionDeltas",
]);

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

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort("Request timed out after 15s"), 15_000);

  try {
    const res = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
      signal: controller.signal,
    });

    if (!res.ok) {
      throw new Error(`API error: ${res.status} ${res.statusText}`);
    }

    const data = await res.json();
    return transformKeys<T>(data);
  } finally {
    clearTimeout(timeout);
  }
}

/**
 * Score a message for honesty, accuracy, and intent.
 */
export async function evaluate(
  text: string,
  source?: string
): Promise<EvaluationResult> {
  return fetchApi<EvaluationResult>("/evaluate", {
    method: "POST",
    body: JSON.stringify({ text, source: source ?? null }),
  });
}

/**
 * Score your own agent's outgoing message and return its profile.
 */
export async function reflect(
  agentId: string,
  text?: string
): Promise<ReflectionResult> {
  return fetchApi<ReflectionResult>("/reflect", {
    method: "POST",
    body: JSON.stringify({ agent_id: agentId, text: text ?? null }),
  });
}

/**
 * List all agents with evaluation summaries.
 */
export async function getAgents(search?: string): Promise<AgentSummary[]> {
  const params = search ? `?q=${encodeURIComponent(search)}` : "";
  return fetchApi<AgentSummary[]>(`/agents${params}`);
}

/**
 * Get a single agent's profile.
 */
export async function getAgent(agentId: string): Promise<AgentProfile> {
  return fetchApi<AgentProfile>(`/agent/${encodeURIComponent(agentId)}`);
}

/**
 * Get evaluation history for an agent.
 */
export async function getHistory(
  agentId: string
): Promise<EvaluationHistoryItem[]> {
  return fetchApi<EvaluationHistoryItem[]>(
    `/agent/${encodeURIComponent(agentId)}/history`
  );
}

/**
 * Get alumni-wide trait averages.
 */
export async function getAlumni(): Promise<AlumniResult> {
  return fetchApi<AlumniResult>("/alumni");
}

/**
 * Get Opus-powered behavioral insights for an agent.
 */
export async function getInsights(agentId: string): Promise<InsightsResult> {
  return fetchApi<InsightsResult>(
    `/insights/${encodeURIComponent(agentId)}`
  );
}

/**
 * Get the daily report card (grade, summary, homework) for an agent.
 */
export async function getCharacterReport(
  agentId: string
): Promise<DailyReportCard> {
  return fetchApi<DailyReportCard>(
    `/agent/${encodeURIComponent(agentId)}/character`
  );
}

/**
 * Get best and worst evaluations with message content for an agent.
 */
export async function getHighlights(
  agentId: string
): Promise<HighlightsResult> {
  return fetchApi<HighlightsResult>(
    `/agent/${encodeURIComponent(agentId)}/highlights`
  );
}

/**
 * Get detected sabotage pathways for an agent.
 */
export async function getPatterns(agentId: string): Promise<PatternResult> {
  return fetchApi<PatternResult>(
    `/agent/${encodeURIComponent(agentId)}/patterns`
  );
}

/**
 * Get the Phronesis graph — taxonomy backbone + agent data for NVL visualization.
 */
export async function getGraph(): Promise<GraphData> {
  return fetchApi<GraphData>("/graph");
}

/**
 * Get the entrance exam report card for an agent.
 */
export async function getEntranceExam(
  agentId: string,
  examId: string
): Promise<ExamReportCard> {
  return fetchApi<ExamReportCard>(
    `/agent/${encodeURIComponent(agentId)}/exam/${encodeURIComponent(examId)}`
  );
}

/**
 * List all exams for an agent.
 */
export async function getExamHistory(
  agentId: string
): Promise<ExamSummary[]> {
  return fetchApi<ExamSummary[]>(
    `/agent/${encodeURIComponent(agentId)}/exam`
  );
}

/**
 * Get constitutional value trail for an agent (5-hop graph traversal).
 */
export async function getTrail(
  agentId: string
): Promise<ConstitutionalTrailResult> {
  return fetchApi<ConstitutionalTrailResult>(
    `/agent/${encodeURIComponent(agentId)}/trail`
  );
}

/**
 * Get behavioral similarity network (Jaccard over shared indicators).
 */
export async function getSimilarity(): Promise<SimilarityResult> {
  return fetchApi<SimilarityResult>("/graph/similarity");
}

/**
 * Get character drift breakpoints for an agent.
 */
export async function getDrift(agentId: string): Promise<DriftResult> {
  return fetchApi<DriftResult>(
    `/agent/${encodeURIComponent(agentId)}/drift`
  );
}

/**
 * Search and filter evaluation records with pagination.
 */
export interface RecordsSearchParams {
  q?: string;
  agent?: string;
  alignment?: string;
  flagged?: boolean;
  sort?: string;
  order?: string;
  page?: number;
  size?: number;
}

export async function getRecords(
  params?: RecordsSearchParams
): Promise<RecordsResult> {
  const searchParams = new URLSearchParams();
  if (params) {
    if (params.q) searchParams.set("q", params.q);
    if (params.agent) searchParams.set("agent", params.agent);
    if (params.alignment) searchParams.set("alignment", params.alignment);
    if (params.flagged !== undefined)
      searchParams.set("flagged", String(params.flagged));
    if (params.sort) searchParams.set("sort", params.sort);
    if (params.order) searchParams.set("order", params.order);
    if (params.page !== undefined)
      searchParams.set("page", String(params.page));
    if (params.size !== undefined)
      searchParams.set("size", String(params.size));
  }
  const qs = searchParams.toString();
  return fetchApi<RecordsResult>(`/records${qs ? `?${qs}` : ""}`);
}

/**
 * Submit a guardian phone number and receive a verification code via SMS.
 */
export async function submitGuardianPhone(
  agentId: string,
  phone: string
): Promise<GuardianPhoneStatus> {
  return fetchApi<GuardianPhoneStatus>(
    `/agent/${encodeURIComponent(agentId)}/guardian/phone`,
    { method: "POST", body: JSON.stringify({ phone }) }
  );
}

/**
 * Verify a 6-digit code sent to the guardian's phone.
 */
export async function verifyGuardianPhone(
  agentId: string,
  code: string
): Promise<GuardianPhoneStatus> {
  return fetchApi<GuardianPhoneStatus>(
    `/agent/${encodeURIComponent(agentId)}/guardian/phone/verify`,
    { method: "POST", body: JSON.stringify({ code }) }
  );
}

/**
 * Get guardian phone verification status. Never returns the phone number.
 */
export async function getGuardianPhoneStatus(
  agentId: string
): Promise<GuardianPhoneStatus> {
  return fetchApi<GuardianPhoneStatus>(
    `/agent/${encodeURIComponent(agentId)}/guardian/phone/status`
  );
}

/**
 * Opt out of guardian SMS notifications.
 */
export async function optOutNotifications(
  agentId: string
): Promise<GuardianPhoneStatus> {
  return fetchApi<GuardianPhoneStatus>(
    `/agent/${encodeURIComponent(agentId)}/guardian/notifications/opt-out`,
    { method: "POST" }
  );
}

/**
 * Opt back in to guardian SMS notifications.
 */
export async function optInNotifications(
  agentId: string
): Promise<GuardianPhoneStatus> {
  return fetchApi<GuardianPhoneStatus>(
    `/agent/${encodeURIComponent(agentId)}/guardian/notifications/opt-in`,
    { method: "POST" }
  );
}
