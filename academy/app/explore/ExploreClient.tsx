"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "motion/react";
import PhronesisGraph from "../../components/graph/PhronesisGraph";
import SimilarityNetwork from "../../components/graph/SimilarityNetwork";
import AlumniPanel from "../../components/alumni/AlumniPanel";
import DimensionBalance from "../../components/shared/DimensionBalance";
import { fadeUp, whileInView } from "../../lib/motion";
import GlossaryTerm from "../../components/shared/GlossaryTerm";

const TABS = ["Graph", "Similarity", "Alumni", "Balance"] as const;
type Tab = (typeof TABS)[number];

export default function ExploreClient({
  initialAlumniDimensions,
}: {
  initialAlumniDimensions: Record<string, number>;
}) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("Graph");
  const alumniDimensions = initialAlumniDimensions;

  const handleNodeClick = useCallback(
    (nodeId: string, nodeType: string) => {
      if (nodeType === "agent") {
        const agentId = nodeId.replace(/^agent-/, "");
        router.push(`/agent/${encodeURIComponent(agentId)}`);
      }
    },
    [router]
  );

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      <motion.div {...whileInView} variants={fadeUp}>
        <h1 className="text-2xl font-semibold tracking-tight">
          <GlossaryTerm slug="phronesis">Phronesis</GlossaryTerm> Explorer
        </h1>
        <p className="mt-1 text-sm text-muted">
          The forest — agents, traits, dimensions, and patterns as a living network.
        </p>
      </motion.div>

      {/* Tab navigation */}
      <div className="mt-6 flex gap-1 rounded-lg bg-border/20 p-1 w-fit">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? "bg-white text-foreground shadow-sm"
                : "text-muted hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="mt-6 space-y-6">
        {activeTab === "Graph" && (
          <motion.div {...whileInView} variants={fadeUp}>
            <PhronesisGraph onNodeClick={handleNodeClick} />
            <p className="mt-3 text-xs text-muted">
              Click an agent node to view their full report card.
            </p>
          </motion.div>
        )}

        {activeTab === "Similarity" && (
          <motion.div {...whileInView} variants={fadeUp}>
            <SimilarityNetwork onAgentClick={(agentId) => router.push(`/agent/${encodeURIComponent(agentId)}`)} />
            <p className="mt-3 text-xs text-muted">
              Agents never interact but trigger the same indicators? That&apos;s behavioral similarity
              only a graph can reveal.
            </p>
          </motion.div>
        )}

        {activeTab === "Alumni" && (
          <motion.div {...whileInView} variants={fadeUp}>
            <AlumniPanel />
          </motion.div>
        )}

        {activeTab === "Balance" && (
          <motion.div {...whileInView} variants={fadeUp}>
            <DimensionBalance
              dimensionAverages={alumniDimensions}
              title="Network Dimension Balance"
            />
            <div className="mt-4 rounded-xl border border-border bg-white p-6">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
                Research Question
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                Do agents strong in all three dimensions outperform those strong in only one?
                The balance view reveals whether a holistic approach to integrity, logic,
                and empathy produces agents with stronger practical wisdom than specialization.
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </main>
  );
}
