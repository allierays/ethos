import { getAgents } from "../../lib/api";
import type { AgentSummary } from "../../lib/types";
import AlumniClient from "./AlumniClient";

export default async function AlumniPage() {
  let agents: AgentSummary[] = [];
  try {
    agents = await getAgents();
  } catch {
    agents = [];
  }

  return <AlumniClient initialAgents={agents} />;
}
