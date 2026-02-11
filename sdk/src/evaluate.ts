import { Ethos } from './client'
import type { EvaluateOptions, EvaluationResult } from './types'

/** Evaluate a message for honesty, accuracy, and intent. Uses default config. */
export async function evaluate(options: EvaluateOptions): Promise<EvaluationResult> {
  const client = new Ethos()
  return client.evaluate(options)
}
