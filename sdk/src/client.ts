import type { EthosConfig, EvaluateOptions, EvaluationResult, ReflectOptions, ReflectionResult } from './types'

const DEFAULT_API_URL = 'http://localhost:8917'

/** Ethos client — configurable SDK for evaluating agent messages. */
export class Ethos {
  private apiUrl: string
  private apiKey?: string
  private priorities?: Record<string, string>

  constructor(config: EthosConfig = {}) {
    this.apiUrl = config.apiUrl ?? DEFAULT_API_URL
    this.apiKey = config.apiKey
    this.priorities = config.priorities
  }

  async evaluate(options: EvaluateOptions): Promise<EvaluationResult> {
    const res = await fetch(`${this.apiUrl}/evaluate`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(options),
    })
    if (!res.ok) throw new Error(`Ethos API error: ${res.status}`)
    return res.json()
  }

  async reflect(options: ReflectOptions): Promise<ReflectionResult> {
    const res = await fetch(`${this.apiUrl}/reflect`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(options),
    })
    if (!res.ok) throw new Error(`Ethos API error: ${res.status}`)
    return res.json()
  }

  private headers(): Record<string, string> {
    const h: Record<string, string> = { 'Content-Type': 'application/json' }
    if (this.apiKey) h['Authorization'] = `Bearer ${this.apiKey}`
    return h
  }
}
