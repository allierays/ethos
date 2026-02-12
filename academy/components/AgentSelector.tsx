"use client";

import { useEffect, useState } from "react";
import { getAgents } from "../lib/api";
import type { AgentSummary } from "../lib/types";

interface AgentSelectorProps {
  selectedAgentId: string | null;
  onSelect: (agentId: string) => void;
}

export default function AgentSelector({
  selectedAgentId,
  onSelect,
}: AgentSelectorProps) {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await getAgents();
        if (!cancelled) {
          setAgents(data);
          setLoading(false);
        }
      } catch {
        if (!cancelled) {
          setError("Failed to load agents");
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted border-t-teal" />
        Loading agents...
      </div>
    );
  }

  if (error) {
    return <div className="text-sm text-misaligned">{error}</div>;
  }

  if (agents.length === 0) {
    return (
      <div className="text-sm text-muted">No agents evaluated yet</div>
    );
  }

  return (
    <select
      value={selectedAgentId ?? ""}
      onChange={(e) => onSelect(e.target.value)}
      className="rounded-lg border border-border bg-white px-3 py-2 text-sm focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal"
      data-testid="agent-selector"
    >
      <option value="" disabled>
        Select an agent...
      </option>
      {agents.map((agent) => (
        <option key={agent.agentId} value={agent.agentId}>
          {agent.agentId} ({agent.evaluationCount} evals)
        </option>
      ))}
    </select>
  );
}
