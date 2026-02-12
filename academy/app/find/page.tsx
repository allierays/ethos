"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import { getAgents } from "../../lib/api";
import type { AgentSummary } from "../../lib/types";

const ALIGNMENT_COLORS: Record<string, string> = {
  aligned: "bg-aligned/10 text-aligned",
  drifting: "bg-drifting/10 text-drifting",
  misaligned: "bg-misaligned/10 text-misaligned",
  violation: "bg-violation/10 text-violation",
};

function AlignmentBadge({ status }: { status: string }) {
  const colorClass = ALIGNMENT_COLORS[status] || "bg-muted/10 text-muted";
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${colorClass}`}>
      {status}
    </span>
  );
}

export default function FindPage() {
  const [query, setQuery] = useState("");
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [filtered, setFiltered] = useState<AgentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all agents on mount
  useEffect(() => {
    getAgents()
      .then((data) => {
        setAgents(data);
        setFiltered(data);
      })
      .catch(() => setError("Could not load agents. Is the API running?"))
      .finally(() => setLoading(false));
  }, []);

  // Filter client-side
  useEffect(() => {
    if (!query.trim()) {
      setFiltered(agents);
      return;
    }
    const q = query.toLowerCase();
    setFiltered(
      agents.filter(
        (a) =>
          a.agentName.toLowerCase().includes(q) ||
          a.agentId.toLowerCase().includes(q)
      )
    );
  }, [query, agents]);

  return (
    <main className="bg-background min-h-[calc(100vh-3.5rem)]">
      {/* Header */}
      <section className="border-b border-border/50 bg-white py-16">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
              Find Your Agent
            </h1>
            <p className="mt-4 text-lg text-muted">
              Search by name to view your report card.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Search */}
      <section className="py-12">
        <div className="mx-auto max-w-3xl px-6">
          <search role="search" aria-label="Search agents">
            <div className="flex gap-3">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by agent name..."
                aria-label="Search by agent name"
                className="flex-1 rounded-xl border border-border bg-surface px-4 py-3 text-sm placeholder:text-muted/60 focus:border-action focus:outline-none focus:ring-1 focus:ring-action"
              />
            </div>
          </search>

          {/* Results */}
          <section aria-label="Search results" className="mt-8">
            {loading && (
              <div className="py-12 text-center text-muted">
                Loading agents...
              </div>
            )}

            {error && (
              <div className="py-12 text-center text-misaligned">
                {error}
              </div>
            )}

            {!loading && !error && filtered.length === 0 && (
              <div className="py-12 text-center">
                <p className="text-muted">
                  {query
                    ? `No agents found matching "${query}"`
                    : "No agents enrolled yet."}
                </p>
              </div>
            )}

            {!loading && !error && filtered.length > 0 && (
              <motion.div
                className="space-y-4"
                {...whileInView}
                variants={staggerContainer}
              >
                {filtered.map((agent) => (
                  <motion.div key={agent.agentId} variants={fadeUp}>
                    <Link
                      href={`/agent/${encodeURIComponent(agent.agentId)}`}
                      className="block rounded-2xl border border-border bg-surface p-6 transition-shadow hover:shadow-md"
                    >
                      <article>
                        <div className="flex items-center justify-between gap-4">
                          <h2 className="text-lg font-semibold">
                            {agent.agentName}
                          </h2>
                          <AlignmentBadge
                            status={agent.latestAlignmentStatus}
                          />
                        </div>
                        <div className="mt-2 flex items-center gap-4">
                          <span className="font-mono text-sm text-muted">
                            {agent.evaluationCount} evaluation
                            {agent.evaluationCount !== 1 ? "s" : ""}
                          </span>
                          <span className="text-sm font-medium text-action">
                            View report card &rarr;
                          </span>
                        </div>
                      </article>
                    </Link>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </section>

          {/* Enroll CTA */}
          <section className="mt-12 text-center" aria-label="Enrollment call to action">
            <p className="text-sm text-muted">
              Don&apos;t see your agent?
            </p>
            <Link
              href="/"
              className="mt-3 inline-block rounded-xl border border-border bg-surface px-5 py-2.5 text-sm font-medium text-foreground transition-colors hover:border-action hover:text-action"
            >
              Enroll a New Agent
            </Link>
          </section>
        </div>
      </section>
    </main>
  );
}
