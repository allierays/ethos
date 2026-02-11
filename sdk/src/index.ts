/**
 * ethos-ai — Evaluate AI agent messages for trustworthiness.
 *
 * SDK + CLI. All intelligence lives server-side.
 * This package is a thin HTTP client that calls the Ethos API.
 */

export { evaluate } from './evaluate'
export { reflect } from './reflect'
export { Ethos } from './client'
export type { EvaluationResult, TraitScore, ReflectionResult } from './types'
