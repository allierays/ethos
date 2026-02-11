/** Score for a single trait (0.0–1.0). */
export interface TraitScore {
  name: string
  score: number
  dimension: 'ethos' | 'logos' | 'pathos'
  polarity: 'positive' | 'negative'
}

/** Full evaluation result from the Ethos API. */
export interface EvaluationResult {
  traits: Record<string, TraitScore>
  dimensions: { ethos: number; logos: number; pathos: number }
  trust: 'trusted' | 'cautious' | 'suspicious' | 'untrusted'
  flags: string[]
  alignment_status: string
}

/** Reflection result — agent trust profile over time. */
export interface ReflectionResult {
  trait_averages: Record<string, number>
  dimensions: { ethos: number; logos: number; pathos: number }
  trend: string
  evaluation_count: number
}

/** Options for evaluate(). */
export interface EvaluateOptions {
  text: string
  source?: string
}

/** Options for reflect(). */
export interface ReflectOptions {
  agent_id: string
}

/** Client configuration. */
export interface EthosConfig {
  apiUrl?: string
  apiKey?: string
  priorities?: Record<string, 'critical' | 'high' | 'standard' | 'low'>
}
