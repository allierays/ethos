"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "motion/react";
import { getAgent } from "../../lib/api";
import { DIMENSION_COLORS, TREND_DISPLAY, ALIGNMENT_STYLES } from "../../lib/colors";
import type { AgentProfile } from "../../lib/types";

interface AgentDetailSidebarProps {
  agentId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function AgentDetailSidebar({
  agentId,
  isOpen,
  onClose,
}: AgentDetailSidebarProps) {
  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!agentId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setProfile(null);

    async function fetchAgent() {
      try {
        const data = await getAgent(agentId!);
        if (!cancelled) setProfile(data);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Unable to load agent profile"
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchAgent();

    return () => {
      cancelled = true;
    };
  }, [agentId]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  const trend = profile
    ? (TREND_DISPLAY[profile.phronesisTrend] ??
      TREND_DISPLAY.insufficient_data)
    : TREND_DISPLAY.insufficient_data;

  const latestAlignment =
    profile?.alignmentHistory?.[profile.alignmentHistory.length - 1] ??
    "unknown";

  const alignmentStyle =
    ALIGNMENT_STYLES[latestAlignment] ?? "bg-muted/10 text-muted";

  return (
    <AnimatePresence>
      {isOpen && agentId && (
        <motion.aside
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="fixed right-0 top-0 z-40 flex h-dvh w-full sm:w-[28rem] max-w-[90vw] flex-col border-l border-border bg-white/90 backdrop-blur-xl shadow-xl"
          role="complementary"
          aria-label="Agent detail"
          data-testid="agent-detail-sidebar"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <h2 className="text-sm font-semibold text-foreground">Agent Detail</h2>
            <button
              type="button"
              onClick={onClose}
              className="rounded-md p-1 text-muted transition-colors hover:bg-muted/10 hover:text-foreground"
              data-testid="sidebar-close"
              aria-label="Close sidebar"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-4 py-4">
            {loading && (
              <div className="flex items-center justify-center py-12" data-testid="sidebar-loading">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-action border-t-transparent" />
              </div>
            )}

            {error && (
              <div className="py-12 text-center" data-testid="sidebar-error">
                <p className="text-sm text-misaligned">{error}</p>
              </div>
            )}

            {!loading && !error && profile && (
              <div className="space-y-5">
                {/* Agent Name + ID */}
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-muted">
                    Agent
                  </p>
                  {profile.agentName && (
                    <p className="mt-1 text-sm font-semibold text-foreground">
                      {profile.agentName}
                    </p>
                  )}
                  <p
                    className={`font-mono text-xs text-muted ${profile.agentName ? "mt-0.5" : "mt-1"}`}
                    title={profile.agentId}
                  >
                    {profile.agentId.length > 12
                      ? `${profile.agentId.slice(0, 12)}...`
                      : profile.agentId}
                  </p>
                </div>

                {/* Dimension Scores */}
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-muted">
                    Dimensions
                  </p>
                  <div className="mt-2 space-y-2">
                    {(["ethos", "logos", "pathos"] as const).map((dim) => {
                      const score = profile.dimensionAverages[dim] ?? 0;
                      const pct = Math.round(score * 100);
                      return (
                        <div key={dim}>
                          <div className="flex items-center justify-between text-xs">
                            <span className="capitalize text-foreground">
                              {dim}
                            </span>
                            <span className="text-muted">{pct}%</span>
                          </div>
                          <div className="mt-1 h-2 w-full rounded-full bg-muted/10">
                            <div
                              className="h-2 rounded-full transition-all duration-300"
                              style={{
                                width: `${pct}%`,
                                backgroundColor:
                                  DIMENSION_COLORS[dim] ?? "#94a3b8",
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Trend */}
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium uppercase tracking-wider text-muted">
                    Trend
                  </p>
                  <span className={`text-lg font-semibold ${trend.color}`}>
                    {trend.arrow}
                  </span>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg bg-muted/5 p-3">
                    <p className="text-xs text-muted">Evaluations</p>
                    <p className="mt-1 text-lg font-semibold text-foreground">
                      {profile.evaluationCount}
                    </p>
                  </div>
                  <div className="rounded-lg bg-muted/5 p-3">
                    <p className="text-xs text-muted">Alignment</p>
                    <p className="mt-1">
                      <span
                        className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${alignmentStyle}`}
                      >
                        {latestAlignment}
                      </span>
                    </p>
                  </div>
                </div>

                {/* Alignment History */}
                {profile.alignmentHistory.length > 0 && (
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-muted">
                      History
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {profile.alignmentHistory
                        .slice(-10)
                        .map((status, i) => {
                          const style =
                            ALIGNMENT_STYLES[status] ?? "bg-muted/10 text-muted";
                          return (
                            <span
                              key={`${status}-${i}`}
                              className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium ${style}`}
                            >
                              {status}
                            </span>
                          );
                        })}
                    </div>
                  </div>
                )}

                {/* View full report link */}
                <Link
                  href={`/agent/${encodeURIComponent(agentId)}`}
                  className="mt-2 flex items-center gap-1.5 text-sm font-medium text-action transition-colors hover:text-action-hover"
                >
                  View full report
                  <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                    <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
                  </svg>
                </Link>
              </div>
            )}

            {!loading && !error && !profile && (
              <div className="py-12 text-center">
                <p className="text-sm text-muted">Agent not found</p>
              </div>
            )}
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
