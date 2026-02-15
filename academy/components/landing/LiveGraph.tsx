"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { motion } from "motion/react";
import PhronesisGraph from "../graph/PhronesisGraph";
import type { NodeClickContext } from "../graph/PhronesisGraph";
import AgentDetailSidebar from "../agent/AgentDetailSidebar";
import TaxonomySidebar from "../graph/TaxonomySidebar";
import type { TaxonomyNodeType } from "../graph/TaxonomySidebar";
import { useGlossary } from "../../lib/GlossaryContext";
import { fadeUp, whileInView } from "../../lib/motion";

export default function LiveGraph() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [taxonomyType, setTaxonomyType] = useState<TaxonomyNodeType | null>(null);
  const [taxonomyId, setTaxonomyId] = useState<string | null>(null);
  const [taxonomyCtx, setTaxonomyCtx] = useState<NodeClickContext>({});
  const { closeGlossary } = useGlossary();

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
    <section id="graph" className="bg-[#0f1a2e] py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-6">
        <motion.div {...whileInView} variants={fadeUp} className="mb-8 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Every improvement, tracked.
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-white/50">
            Every homework assignment, every practice session, every score change flows into the graph.
            Click any agent to see their report card and homework.
          </p>
        </motion.div>

        <motion.div {...whileInView} variants={fadeUp}>
          <PhronesisGraph
            className="h-[70vh] sm:h-[80vh]"
            onNodeClick={handleNodeClick}
          />
        </motion.div>

        <motion.div {...whileInView} variants={fadeUp} className="mt-6 text-center">
          <Link
            href="/insights"
            className="inline-flex items-center gap-2 text-sm font-semibold text-white/70 transition-colors hover:text-white"
          >
            Explore full screen
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
              <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
            </svg>
          </Link>
        </motion.div>
      </div>

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
    </section>
  );
}
