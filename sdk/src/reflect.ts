import { Ethos } from './client'
import type { ReflectOptions, ReflectionResult } from './types'

/** Reflect on an agent's trust profile. Uses default config. */
export async function reflect(options: ReflectOptions): Promise<ReflectionResult> {
  const client = new Ethos()
  return client.reflect(options)
}
