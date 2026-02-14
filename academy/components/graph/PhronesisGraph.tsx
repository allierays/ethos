"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getGraph } from "../../lib/api";
import {
  DIMENSION_COLORS,
  REL_STYLES,
} from "../../lib/colors";
import type { GraphData, GraphNode as EthosGraphNode, GraphRel } from "../../lib/types";
import GraphHelpButton from "../shared/GraphHelpButton";

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

const AGENT_COLORS: Record<string, string> = {
  aligned: "#16a34a",
  drifting: "#d97706",
  misaligned: "#991b1b",
  violation: "#991b1b",
};

const MODEL_COLORS = {
  sonnet: "rgba(56,149,144,0.6)",
  opus: "rgba(224,165,60,0.6)",
  unknown: "rgba(255,255,255,0.15)",
};

function getModelColor(modelUsed: string | undefined): string {
  if (!modelUsed) return MODEL_COLORS.unknown;
  if (modelUsed.includes("opus")) return MODEL_COLORS.opus;
  if (modelUsed.includes("sonnet")) return MODEL_COLORS.sonnet;
  return MODEL_COLORS.unknown;
}

/* -------------------------------------------------------------------------- */
/*  NVL type interfaces                                                       */
/* -------------------------------------------------------------------------- */

interface NvlNode {
  id: string;
  color?: string;
  size?: number;
  caption?: string;
  captionColor?: string;
  pinned?: boolean;
}

interface NvlRelationship {
  id: string;
  from: string;
  to: string;
  color?: string;
  width?: number;
  caption?: string;
}

function getNodeColor(node: EthosGraphNode): string {
  const { type, properties } = node;

  switch (type) {
    case "dimension":
      return DIMENSION_COLORS[node.label] ?? "#389590";
    case "agent": {
      const status = properties.alignmentStatus as string | undefined;
      return status ? (AGENT_COLORS[status] ?? "#16a34a") : "#16a34a";
    }
    case "evaluation":
      return getModelColor(properties.modelUsed as string | undefined);
    default:
      return "#94a3b8";
  }
}

function getNodeSize(node: EthosGraphNode): number {
  switch (node.type) {
    case "dimension":
      return 40;
    case "agent": {
      const count = (node.properties.evaluationCount as number) ?? 0;
      return Math.min(35, 15 + count * 2);
    }
    case "evaluation":
      return 6;
    default:
      return 10;
  }
}

function getNodeCaption(node: EthosGraphNode): string {
  switch (node.type) {
    case "dimension":
      return node.label;
    case "agent": {
      const name = node.properties.agentName as string | undefined;
      return name || node.label;
    }
    case "evaluation":
      return "";
    default:
      return node.label;
  }
}

/* -------------------------------------------------------------------------- */
/*  Transform API data → NVL format                                           */
/* -------------------------------------------------------------------------- */

function toNvlNodes(nodes: EthosGraphNode[]): NvlNode[] {
  return nodes.map((n) => ({
    id: n.id,
    color: getNodeColor(n),
    size: getNodeSize(n),
    caption: getNodeCaption(n),
    captionColor: "#ffffff",
  }));
}

function toNvlRelationships(rels: GraphRel[], nodeIds: Set<string>): NvlRelationship[] {
  return rels
    .filter((r) => nodeIds.has(r.fromId) && nodeIds.has(r.toId))
    .map((r) => {
      const style = REL_STYLES[r.type] ?? { color: "rgba(255,255,255,0.08)", width: 0.5 };
      return {
        id: r.id,
        from: r.fromId,
        to: r.toId,
        color: style.color,
        width: style.width,
      };
    });
}

/* -------------------------------------------------------------------------- */
/*  Inner NVL component — only mounts after data + NVL are ready             */
/* -------------------------------------------------------------------------- */

interface NvlRendererProps {
  nodes: NvlNode[];
  rels: NvlRelationship[];
  onNodeClick?: (event: unknown, node: { id: string }) => void;
}

function NvlRenderer({ nodes, rels, onNodeClick }: NvlRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const nvlInstanceRef = useRef<unknown>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const interactionsRef = useRef<any[]>([]);
  const onNodeClickRef = useRef(onNodeClick);
  onNodeClickRef.current = onNodeClick;

  useEffect(() => {
    let destroyed = false;
    const container = containerRef.current;

    async function init() {
      if (!container) return;

      try {
        const [{ default: NVL }, handlers] = await Promise.all([
          import("@neo4j-nvl/base"),
          import("@neo4j-nvl/interaction-handlers"),
        ]);

        if (destroyed || !container) return;

        // Clean any stale content
        container.innerHTML = "";

        const nodeIds = nodes.map((n) => n.id);

        const nvl = new NVL(container, nodes, rels, {
          layout: "d3Force",
          renderer: "canvas",
          initialZoom: 0.3,
          minZoom: 0.05,
          maxZoom: 5,
          allowDynamicMinZoom: true,
          disableWebGL: true,
          callbacks: {
            onLayoutDone: () => {
              if (!destroyed) {
                nvl.fit(nodeIds);
              }
            },
          },
        });

        nvlInstanceRef.current = nvl;

        // Attach interaction handlers for zoom, pan, drag, click
        const zoom = new handlers.ZoomInteraction(nvl);
        const pan = new handlers.PanInteraction(nvl);
        const drag = new handlers.DragNodeInteraction(nvl);
        const click = new handlers.ClickInteraction(nvl);

        click.updateCallback("onNodeClick", (node: { id: string }) => {
          onNodeClickRef.current?.(null, node);
        });

        interactionsRef.current = [zoom, pan, drag, click];

        // Fit after layout has had time to compute initial positions
        setTimeout(() => {
          if (!destroyed && nvlInstanceRef.current) {
            nvl.fit(nodeIds);
          }
        }, 2000);

      } catch (err) {
        console.error("[Phronesis] NVL initialization failed:", err);
      }
    }

    init();

    return () => {
      destroyed = true;
      for (const handler of interactionsRef.current) {
        try {
          handler.destroy();
        } catch {
          // ignore cleanup errors
        }
      }
      interactionsRef.current = [];
      if (nvlInstanceRef.current) {
        try {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (nvlInstanceRef.current as any).destroy();
        } catch {
          // ignore cleanup errors
        }
        nvlInstanceRef.current = null;
      }
      if (container) {
        container.innerHTML = "";
      }
    };
  }, [nodes, rels]);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: "100%", position: "relative" }}
    />
  );
}

/* -------------------------------------------------------------------------- */
/*  Legend component                                                           */
/* -------------------------------------------------------------------------- */

function GraphLegend({ nodeCount, agentCount, evalCount }: {
  nodeCount: number;
  agentCount: number;
  evalCount: number;
}) {
  return (
    <div className="absolute bottom-3 left-3 rounded-lg bg-black/40 px-3 py-2.5 text-xs text-white/80 backdrop-blur-sm">
      <div className="flex gap-5">
        <div className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wider text-white/50">Alignment</span>
          <div className="flex gap-2">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: "#16a34a" }} />
              Aligned
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: "#d97706" }} />
              Drifting
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: "#991b1b" }} />
              Misaligned
            </span>
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wider text-white/50">Model</span>
          <div className="flex gap-2">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: MODEL_COLORS.sonnet }} />
              Sonnet
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: MODEL_COLORS.opus }} />
              Opus
            </span>
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wider text-white/50">Dimensions</span>
          <div className="flex gap-2">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: "#2e4a6e" }} />
              Integrity
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: "#389590" }} />
              Logic
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: "#e0a53c" }} />
              Empathy
            </span>
          </div>
        </div>
      </div>
      <div className="mt-1.5 flex gap-3 text-[10px] text-white/40">
        <span>Agents: {agentCount}</span>
        <span>Evaluations: {evalCount}</span>
        <span>Total: {nodeCount}</span>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Main component                                                            */
/* -------------------------------------------------------------------------- */

interface PhronesisGraphProps {
  onNodeClick?: (nodeId: string, nodeType: string) => void;
}

export default function PhronesisGraph({ onNodeClick }: PhronesisGraphProps) {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch graph data
  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const data = await getGraph();
        if (!cancelled) {
          setGraphData(data);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : "Failed to load graph";
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleNodeClick = useCallback(
    (_: unknown, node: { id: string }) => {
      if (!onNodeClick || !graphData) return;
      const ethosNode = graphData.nodes.find((n) => n.id === node.id);
      if (ethosNode) {
        onNodeClick(ethosNode.id, ethosNode.type);
      }
    },
    [onNodeClick, graphData]
  );

  function handleRetry() {
    setLoading(true);
    setError(null);
    getGraph()
      .then(setGraphData)
      .catch((err) => {
        const message =
          err instanceof Error ? err.message : "Failed to load graph";
        setError(message);
      })
      .finally(() => setLoading(false));
  }

  // Loading state
  if (loading) {
    return (
      <div
        className="flex h-[600px] items-center justify-center rounded-xl border border-white/10"
        style={{ backgroundColor: "#152438" }}
        data-testid="graph-loading"
      >
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-action border-t-transparent" />
          <p className="mt-3 text-sm text-white/50">Loading Phronesis Graph...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div
        className="flex h-[600px] items-center justify-center rounded-xl border border-white/10"
        style={{ backgroundColor: "#152438" }}
        data-testid="graph-error"
      >
        <div className="text-center">
          <p className="text-sm text-misaligned">{error}</p>
          <button
            type="button"
            onClick={handleRetry}
            className="mt-3 rounded-lg bg-action px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-action-hover"
            data-testid="graph-retry"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div
        className="flex h-[600px] items-center justify-center rounded-xl border border-white/10"
        style={{ backgroundColor: "#152438" }}
        data-testid="graph-empty"
      >
        <div className="text-center">
          <p className="text-sm text-white/50">
            No graph data yet. Seed evaluations first.
          </p>
        </div>
      </div>
    );
  }

  const nvlNodes = toNvlNodes(graphData.nodes);
  const nodeIds = new Set(graphData.nodes.map((n) => n.id));
  const nvlRels = toNvlRelationships(graphData.relationships, nodeIds);

  return (
    <div
      className="relative h-[600px] rounded-xl border border-white/10"
      style={{ backgroundColor: "#152438" }}
      data-testid="phronesis-graph"
    >
      <NvlRenderer
        nodes={nvlNodes}
        rels={nvlRels}
        onNodeClick={handleNodeClick}
      />

      {/* Help button */}
      <div className="absolute top-3 right-3">
        <GraphHelpButton slug="guide-phronesis-graph" />
      </div>

      {/* Legend */}
      <GraphLegend
        nodeCount={graphData.nodes.length}
        agentCount={graphData.nodes.filter((n) => n.type === "agent").length}
        evalCount={graphData.nodes.filter((n) => n.type === "evaluation").length}
      />
    </div>
  );
}
