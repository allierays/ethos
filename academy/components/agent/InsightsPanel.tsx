"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { getInsights } from "../../lib/api";
import type { InsightsResult, Insight } from "../../lib/types";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import { SEVERITY_STYLES } from "../../lib/colors";

interface InsightsPanelProps {
  agentId: string;
}

export default function InsightsPanel({ agentId }: InsightsPanelProps) {
  const [data, setData] = useState<InsightsResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getInsights(agentId)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load insights"
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

  return (
    <motion.div
      className="rounded-xl border border-border bg-white p-6"
      {...whileInView}
      variants={fadeUp}
    >
      <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
        Behavioral Insights
      </h3>
      <p className="mt-0.5 text-xs text-muted">
        Opus-powered analysis of behavioral patterns and anomalies.
      </p>

      {loading && (
        <div className="mt-8 flex h-32 items-center justify-center">
          <div className="text-center">
            <div className="mx-auto h-5 w-5 animate-spin rounded-full border-2 border-muted border-t-action" />
            <p className="mt-2 text-xs text-muted">Generating insights...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg bg-misaligned/10 px-4 py-2 text-sm text-misaligned">
          {error}
        </div>
      )}

      {!loading && !error && data && (
        <div className="mt-4 space-y-4">
          {/* Summary */}
          {data.summary && (
            <motion.p
              className="text-sm leading-relaxed text-foreground"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              {data.summary}
            </motion.p>
          )}

          {/* Insight cards */}
          {data.insights.length > 0 && (
            <motion.div
              className="space-y-3"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
            >
              {data.insights.map((insight: Insight, i: number) => (
                <motion.div
                  key={i}
                  variants={fadeUp}
                  className="rounded-lg border border-border/50 bg-background p-4"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                        SEVERITY_STYLES[insight.severity] ?? SEVERITY_STYLES.info
                      }`}
                    >
                      {insight.severity}
                    </span>
                    <span className="text-xs font-medium text-muted">
                      {insight.trait}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-foreground">{insight.message}</p>
                </motion.div>
              ))}
            </motion.div>
          )}

          {data.insights.length === 0 && (
            <p className="text-sm text-muted">
              No notable patterns detected. This agent appears to behave consistently.
            </p>
          )}
        </div>
      )}

      {!loading && !error && !data && (
        <div className="mt-8 flex h-32 items-center justify-center text-sm text-muted">
          No insights available for this agent.
        </div>
      )}
    </motion.div>
  );
}
