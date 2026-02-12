"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getAgents } from "../../lib/api";
import type { AgentSummary } from "../../lib/types";

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
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

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

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered = agents.filter((a) => {
    const q = query.toLowerCase();
    return (
      a.agentName.toLowerCase().includes(q) ||
      a.agentId.toLowerCase().includes(q)
    );
  });

  // Reset highlight when filtered list changes
  useEffect(() => {
    setHighlightIndex(-1);
  }, [query]);

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightIndex >= 0 && listRef.current) {
      const item = listRef.current.children[highlightIndex] as HTMLElement;
      item?.scrollIntoView({ block: "nearest" });
    }
  }, [highlightIndex]);

  const selectedAgent = agents.find((a) => a.agentId === selectedAgentId);

  function displayName(agent: AgentSummary): string {
    return agent.agentName || agent.agentId.slice(0, 12) + "...";
  }

  const selectAgent = useCallback(
    (agentId: string) => {
      onSelect(agentId);
      setQuery("");
      setOpen(false);
      setHighlightIndex(-1);
      inputRef.current?.blur();
    },
    [onSelect],
  );

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!open) {
      if (e.key === "ArrowDown" || e.key === "Enter") {
        setOpen(true);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setHighlightIndex((prev) =>
          prev < filtered.length - 1 ? prev + 1 : 0,
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setHighlightIndex((prev) =>
          prev > 0 ? prev - 1 : filtered.length - 1,
        );
        break;
      case "Enter":
        e.preventDefault();
        if (highlightIndex >= 0 && highlightIndex < filtered.length) {
          selectAgent(filtered[highlightIndex].agentId);
        }
        break;
      case "Escape":
        e.preventDefault();
        setOpen(false);
        setHighlightIndex(-1);
        break;
    }
  }

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

  const listboxId = "agent-selector-listbox";

  return (
    <div ref={containerRef} className="relative" data-testid="agent-selector">
      <input
        ref={inputRef}
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-activedescendant={
          highlightIndex >= 0 && filtered[highlightIndex]
            ? `agent-option-${filtered[highlightIndex].agentId}`
            : undefined
        }
        value={open ? query : selectedAgent ? displayName(selectedAgent) : ""}
        placeholder="Search agents..."
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={(e) => {
          setOpen(true);
          setQuery("");
          e.target.select();
        }}
        onKeyDown={handleKeyDown}
        className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal"
      />
      {open && (
        <ul
          ref={listRef}
          id={listboxId}
          role="listbox"
          className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-border bg-white shadow-lg"
        >
          {filtered.length === 0 ? (
            <li className="px-3 py-2 text-sm text-muted" role="presentation">
              No matches
            </li>
          ) : (
            filtered.map((agent, i) => (
              <li
                key={agent.agentId}
                id={`agent-option-${agent.agentId}`}
                role="option"
                aria-selected={agent.agentId === selectedAgentId}
                onClick={() => selectAgent(agent.agentId)}
                className={`cursor-pointer px-3 py-2 text-sm ${
                  i === highlightIndex
                    ? "bg-teal/10"
                    : agent.agentId === selectedAgentId
                      ? "bg-teal/5"
                      : "hover:bg-muted/10"
                } ${
                  agent.agentId === selectedAgentId
                    ? "font-medium text-teal"
                    : "text-foreground"
                }`}
              >
                <span className="block">
                  {agent.agentName || "Unnamed Agent"}
                </span>
                <span className="block text-xs text-muted">
                  {agent.evaluationCount} evals
                  <span className="mx-1">&middot;</span>
                  <span className="font-mono">
                    {agent.agentId.slice(0, 12)}...
                  </span>
                </span>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
