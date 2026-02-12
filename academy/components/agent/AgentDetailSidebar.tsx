"use client";

import { useEffect, useState } from "react";
import { getAgent } from "../../lib/api";
import { DIMENSION_COLORS, TREND_DISPLAY, ALIGNMENT_STYLES } from "../../lib/colors";
import type { AgentProfile } from "../../lib/types";

interface AgentDetailSidebarProps {
  agentId: string;
  onClose: () => void;
}

export default function AgentDetailSidebar({
  agentId,
  onClose,
}: AgentDetailSidebarProps) {
  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    getAgent(agentId)
      .then((data) => {
        if (!cancelled) setProfile(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Unable to load agent profile"
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [agentId]);

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
    <div
      className="flex h-full w-80 flex-col border-l border-border bg-white"
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
          </div>
        )}

        {!loading && !error && !profile && (
          <div className="py-12 text-center">
            <p className="text-sm text-muted">Agent not found</p>
          </div>
        )}
      </div>
    </div>
  );
}
