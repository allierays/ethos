"use client";

import { useCallback, useEffect, useSyncExternalStore } from "react";
import {
  ReactFlow,
  type Node,
  type Edge,
  type NodeProps,
  Handle,
  Position,
} from "@xyflow/react";
import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "@/lib/motion";

/* ─── Faculty Data ─── */

const FACULTIES = [
  {
    id: "instinct",
    number: "01",
    title: "Instinct",
    description:
      "208 behavioral indicators. Matches patterns in milliseconds. No LLM call.",
    subtitle: "Routes to the right depth: Standard \u2192 Enhanced \u2192 Deep",
  },
  {
    id: "intuition",
    number: "02",
    title: "Intuition",
    description:
      "Claude evaluates every trait with structured reasoning. 12 scores from 0.0 to 1.0, each with evidence from the text.",
    subtitle: "",
  },
  {
    id: "deliberation",
    number: "03",
    title: "Deliberation",
    description:
      "Applies Anthropic\u2019s published Constitution. Four values in priority order: Safety, Ethics, Soundness, Helpfulness.",
    subtitle: "",
    badges: ["Aligned", "Drifting", "Misaligned", "Violation"],
  },
] as const;

const BADGE_COLORS: Record<string, string> = {
  Aligned: "bg-aligned/20 text-aligned",
  Drifting: "bg-drifting/20 text-drifting",
  Misaligned: "bg-misaligned/20 text-misaligned",
  Violation: "bg-violation/20 text-violation",
};

/* ─── Custom Node ─── */

function FacultyNode({ data }: NodeProps) {
  const d = data as (typeof FACULTIES)[number];
  return (
    <div className="w-[340px] rounded-2xl border border-white/20 bg-white p-6 shadow-lg">
      <Handle type="target" position={Position.Top} className="!bg-ethos-500 !border-none !w-2 !h-2" />
      <span className="font-mono text-xs text-muted">{d.number}</span>
      <h3 className="mt-1 text-lg font-bold text-foreground">{d.title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-foreground/70">
        {d.description}
      </p>
      {d.subtitle && (
        <p className="mt-2 font-mono text-xs text-ethos-600">{d.subtitle}</p>
      )}
      {"badges" in d && d.badges && (
        <div className="mt-3 flex flex-wrap gap-2">
          {d.badges.map((b) => (
            <span
              key={b}
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${BADGE_COLORS[b] ?? ""}`}
            >
              {b}
            </span>
          ))}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="!bg-ethos-500 !border-none !w-2 !h-2" />
    </div>
  );
}

const nodeTypes = { faculty: FacultyNode };

/* ─── Flow Data ─── */

const nodes: Node[] = FACULTIES.map((f, i) => ({
  id: f.id,
  type: "faculty",
  position: { x: 0, y: i * 260 },
  data: f,
}));

const edges: Edge[] = [
  {
    id: "e1",
    source: "instinct",
    target: "intuition",
    animated: true,
    type: "smoothstep",
    style: { stroke: "#3b8a98", strokeWidth: 2 },
  },
  {
    id: "e2",
    source: "intuition",
    target: "deliberation",
    animated: true,
    type: "smoothstep",
    style: { stroke: "#3b8a98", strokeWidth: 2 },
  },
];

/* ─── Mobile Fallback ─── */

function MobileFacultyCards() {
  return (
    <motion.div
      className="flex flex-col gap-6"
      {...whileInView}
      variants={staggerContainer}
    >
      {FACULTIES.map((f, i) => (
        <motion.div key={f.id} variants={fadeUp}>
          <div className="rounded-2xl border border-white/20 bg-white p-6 shadow-lg">
            <span className="font-mono text-xs text-muted">{f.number}</span>
            <h3 className="mt-1 text-lg font-bold text-foreground">
              {f.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-foreground/70">
              {f.description}
            </p>
            {f.subtitle && (
              <p className="mt-2 font-mono text-xs text-ethos-600">
                {f.subtitle}
              </p>
            )}
            {"badges" in f && f.badges && (
              <div className="mt-3 flex flex-wrap gap-2">
                {f.badges.map((b) => (
                  <span
                    key={b}
                    className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${BADGE_COLORS[b] ?? ""}`}
                  >
                    {b}
                  </span>
                ))}
              </div>
            )}
          </div>
          {i < FACULTIES.length - 1 && (
            <div className="mx-auto h-6 w-px bg-ethos-500/40" />
          )}
        </motion.div>
      ))}
    </motion.div>
  );
}

/* ─── Export ─── */

export default function FacultyFlow() {
  const subscribe = useCallback((cb: () => void) => {
    const mq = window.matchMedia("(min-width: 768px)");
    mq.addEventListener("change", cb);
    return () => mq.removeEventListener("change", cb);
  }, []);
  const getSnapshot = () => window.matchMedia("(min-width: 768px)").matches;
  const getServerSnapshot = () => false;
  const isDesktop = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  if (!isDesktop) return <MobileFacultyCards />;

  return (
    <div className="h-[700px] w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        preventScrolling={false}
        fitView
        proOptions={{ hideAttribution: true }}
      />
    </div>
  );
}
