import { getAgents } from "../../lib/api";
import type { AgentSummary } from "../../lib/types";
import AlumniClient from "./AlumniClient";

export const dynamic = "force-dynamic";

export default async function AlumniPage() {
  let agents: AgentSummary[] = [];
  let error: string | null = null;
  try {
    agents = await getAgents();
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to load agents.";
  }

  return <AlumniClient initialAgents={agents} initialError={error} />;
}
