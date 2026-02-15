"use client";

import { useCallback, useState } from "react";
import { motion } from "motion/react";
import PhronesisGraph from "../../components/graph/PhronesisGraph";
import type { NodeClickContext } from "../../components/graph/PhronesisGraph";
import CohortInsights from "../../components/graph/CohortInsights";
import AlumniPanel from "../../components/alumni/AlumniPanel";
import DimensionBalance from "../../components/shared/DimensionBalance";
import AgentDetailSidebar from "../../components/agent/AgentDetailSidebar";
import TaxonomySidebar from "../../components/graph/TaxonomySidebar";
import type { TaxonomyNodeType } from "../../components/graph/TaxonomySidebar";
import { useGlossary } from "../../lib/GlossaryContext";
import { fadeUp, whileInView } from "../../lib/motion";
import GlossaryTerm from "../../components/shared/GlossaryTerm";

const TABS = ["Graph", "Insights", "Alumni", "Balance"] as const;
type Tab = (typeof TABS)[number];

export default function ExploreClient({
  initialAlumniDimensions,
}: {
  initialAlumniDimensions: Record<string, number>;
}) {
  const [activeTab, setActiveTab] = useState<Tab>("Graph");
  const [fullScreen, setFullScreen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [taxonomyType, setTaxonomyType] = useState<TaxonomyNodeType | null>(null);
  const [taxonomyId, setTaxonomyId] = useState<string | null>(null);
  const [taxonomyCtx, setTaxonomyCtx] = useState<NodeClickContext>({});
  const { closeGlossary } = useGlossary();
  const alumniDimensions = initialAlumniDimensions;

  const handleNodeClick = useCallback(
    (nodeId: string, nodeType: string, nodeLabel: string, context?: NodeClickContext) => {
      switch (nodeType) {
        case "agent": {
          closeGlossary();
          setTaxonomyType(null);
          const agentId = nodeId.replace(/^agent-/, "");
          setSelectedAgent(agentId);
          break;
        }
        case "trait": {
          setSelectedAgent(null);
          closeGlossary();
          setTaxonomyType("trait");
          setTaxonomyId(nodeId.replace(/^trait-/, ""));
          setTaxonomyCtx(context ?? {});
          break;
        }
        case "indicator": {
          setSelectedAgent(null);
          closeGlossary();
          setTaxonomyType("indicator");
          setTaxonomyId(nodeId.replace(/^ind-/, ""));
          setTaxonomyCtx(context ?? {});
          break;
        }
        case "dimension": {
          setSelectedAgent(null);
          closeGlossary();
          setTaxonomyType("dimension");
          setTaxonomyId(nodeLabel);
          setTaxonomyCtx(context ?? {});
          break;
        }
      }
    },
    [closeGlossary]
  );

  const handleCloseSidebar = useCallback(() => {
    setSelectedAgent(null);
  }, []);

  const handleCloseTaxonomy = useCallback(() => {
    setTaxonomyType(null);
  }, []);

  const handleTaxonomyAgentClick = useCallback((agentId: string) => {
    setTaxonomyType(null);
    setSelectedAgent(agentId);
  }, []);

  return (
    <>
      {/* Full-screen overlay */}
      {fullScreen && (
        <div className="fixed inset-0 z-50 bg-[#0f1a2e]">
          <button
            type="button"
            onClick={() => setFullScreen(false)}
            className="absolute right-4 top-4 z-50 rounded-lg bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200"
          >
            Exit Full Screen
          </button>
          <PhronesisGraph
            className="h-screen"
            onNodeClick={handleNodeClick}
          />
          <AgentDetailSidebar
            agentId={selectedAgent}
            isOpen={selectedAgent !== null}
            onClose={handleCloseSidebar}
          />
          <TaxonomySidebar
            nodeType={taxonomyType}
            nodeId={taxonomyId}
            context={taxonomyCtx}
            isOpen={taxonomyType !== null}
            onClose={handleCloseTaxonomy}
            onAgentClick={handleTaxonomyAgentClick}
          />
        </div>
      )}

      {/* Banner */}
      <section className="relative overflow-hidden py-20 sm:py-24">
        <img
          src="/insights.jpeg"
          alt=""
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-[#1a2538]/75" />
        <div className="relative px-6 text-center">
          <div className="mx-auto inline-block rounded-2xl border border-white/20 bg-white/10 px-8 py-4 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]">
            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl" style={{ textShadow: "0 1px 3px rgba(0,0,0,0.4)" }}>
              Insights
            </h1>
          </div>
          <p className="mt-4 text-base text-white/80 max-w-lg mx-auto" style={{ textShadow: "0 1px 3px rgba(0,0,0,0.4)" }}>
            Insights about the Ethos Academy alumni agents and their capacity for practical wisdom (<GlossaryTerm slug="phronesis">phronesis</GlossaryTerm>).
          </p>
        </div>
      </section>

      <main className="mx-auto max-w-7xl px-6 py-8">

        {/* Tab navigation */}
        <div className="mt-6 flex flex-wrap items-center gap-1 rounded-lg bg-border/20 p-1">
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
          {activeTab === "Graph" && (
            <button
              type="button"
              onClick={() => setFullScreen(true)}
              className="ml-auto rounded-md px-3 py-2 text-sm text-muted transition-colors hover:text-foreground"
            >
              <svg viewBox="0 0 20 20" fill="currentColor" className="inline h-4 w-4 mr-1">
                <path d="M3.28 2.22a.75.75 0 00-1.06 1.06L5.44 6.5H3.75a.75.75 0 000 1.5h4.5a.75.75 0 00.75-.75v-4.5a.75.75 0 00-1.5 0v1.69L4.22 1.16a.75.75 0 00-1.06 0l.12.06zM11.75 13.5a.75.75 0 000 1.5h1.69l-3.22 3.22a.75.75 0 101.06 1.06l3.22-3.22v1.69a.75.75 0 001.5 0v-4.5a.75.75 0 00-.75-.75h-4.5z" />
              </svg>
              Full Screen
            </button>
          )}
        </div>

        {/* Tab content */}
        <div className="mt-6 space-y-6">
          {activeTab === "Graph" && (
            <motion.div {...whileInView} variants={fadeUp}>
              {/* Graph intro */}
              <div className="mb-4 rounded-xl border border-border bg-white p-5">
                <h2 className="text-base font-semibold text-foreground">
                  The Phronesis Graph
                </h2>
                <p className="mt-1.5 text-sm leading-relaxed text-muted">
                  Every agent, trait, and behavioral indicator lives in a single connected graph.
                  The structure mirrors how Aristotle described character: integrity, reasoning, and
                  empathy aren&apos;t separate scores. They reinforce and constrain each other.
                </p>
                <div className="mt-3 grid grid-cols-1 gap-2 text-xs text-muted sm:grid-cols-2 lg:grid-cols-4">
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 inline-block h-3 w-3 shrink-0 rounded-full bg-[#394646]" />
                    <span><strong className="text-foreground">Ethos Academy</strong> sits at the center. Three dimensions branch out from it.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 inline-block h-3 w-3 shrink-0 rounded-full bg-[#389590]" />
                    <span><strong className="text-foreground">Dimensions &amp; Traits</strong> form the middle ring. 12 traits across integrity, logic, and empathy.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 inline-block h-3 w-3 shrink-0 rounded-full bg-[#94a3b8]" />
                    <span><strong className="text-foreground">Indicators</strong> are the outer nodes. 214 specific behaviors. Larger means detected more often.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 inline-block h-3 w-3 shrink-0 rounded-full bg-[#8a857a]" />
                    <span><strong className="text-foreground">Agents</strong> connect to the indicators they triggered. Click one to see its report card.</span>
                  </div>
                </div>
                <p className="mt-3 text-xs text-muted">
                  <strong className="text-foreground">How to navigate:</strong> Scroll to zoom. Use the arrow buttons (bottom-right) to pan. Click any node to open its detail panel.
                </p>
              </div>
              <PhronesisGraph
                className="h-[70vh]"
                onNodeClick={handleNodeClick}
              />
            </motion.div>
          )}

          {activeTab === "Insights" && (
            <motion.div {...whileInView} variants={fadeUp}>
              <CohortInsights onAgentClick={(agentId) => {
                closeGlossary();
                setSelectedAgent(agentId);
              }} />
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
                title="Alumni Dimension Balance"
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

      {/* Sidebars (outside fullscreen so they work in both modes) */}
      {!fullScreen && (
        <>
          <AgentDetailSidebar
            agentId={selectedAgent}
            isOpen={selectedAgent !== null}
            onClose={handleCloseSidebar}
          />
          <TaxonomySidebar
            nodeType={taxonomyType}
            nodeId={taxonomyId}
            context={taxonomyCtx}
            isOpen={taxonomyType !== null}
            onClose={handleCloseTaxonomy}
            onAgentClick={handleTaxonomyAgentClick}
          />
        </>
      )}
    </>
  );
}
