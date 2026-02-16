/**
 * Practice-specific utilities for the Ethos Academy SDK.
 *
 * Provides a high-level `completePracticeSession` helper that runs
 * through all pending scenarios using a user-supplied response function.
 */

import type { EthosClient } from "./client";
import type { PracticeAnswerResult, PracticeProgress, PracticeSession } from "./types";

/**
 * Response function the agent implements.
 * Receives scenario prompt text, returns the agent's response.
 */
export type RespondFn = (scenarioPrompt: string) => Promise<string>;

/**
 * Complete all pending practice scenarios in a session.
 *
 * Usage:
 * ```ts
 * const progress = await completePracticeSession(client, agentId, async (prompt) => {
 *   return await myAgent.respond(prompt);
 * });
 * ```
 */
export async function completePracticeSession(
  client: EthosClient,
  agentId: string,
  respond: RespondFn,
): Promise<PracticeProgress | null> {
  const session = await client.getPendingPractice(agentId);
  if (!session) {
    return null;
  }

  let currentIndex = session.completedScenarios;
  const scenarios = session.scenarios;

  while (currentIndex < scenarios.length) {
    const scenario = scenarios[currentIndex];
    const responseText = await respond(scenario.prompt);

    const result: PracticeAnswerResult = await client.submitPracticeResponse(
      agentId,
      session.sessionId,
      scenario.scenarioId,
      responseText,
    );

    if (result.complete && result.progress) {
      return result.progress;
    }

    currentIndex++;
  }

  // If we exhausted scenarios, fetch progress directly
  return client.getPracticeProgress(agentId);
}
