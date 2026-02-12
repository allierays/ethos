"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getGraph } from "../../lib/api";
import {
  DIMENSION_COLORS,
  ALIGNMENT_COLORS,
  PATTERN_SEVERITY_COLORS,
  REL_STYLES,
} from "../../lib/colors";
import type { GraphData, GraphNode as EthosGraphNode, GraphRel } from "../../lib/types";

/* -------------------------------------------------------------------------- */
/*  NVL type interfaces                                                       */
/* -------------------------------------------------------------------------- */

interface NvlNode {
  id: string;
  color?: string;
  size?: number;
  caption?: string;
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
      return DIMENSION_COLORS[node.label] ?? "#3b8a98";
    case "trait": {
      const polarity = properties.polarity as string | undefined;
      if (polarity === "negative") return "#ef4444";
      const dim = properties.dimension as string | undefined;
      return dim ? (DIMENSION_COLORS[dim] ?? "#94a3b8") : "#94a3b8";
    }
    case "constitutional_value":
      return "#8b5cf6";
    case "pattern": {
      const severity = properties.severity as string | undefined;
      return severity
        ? (PATTERN_SEVERITY_COLORS[severity] ?? "#e0a53c")
        : "#e0a53c";
    }
    case "indicator":
      return "#94a3b8";
    case "agent": {
      const status = properties.alignmentStatus as string | undefined;
      return status
        ? (ALIGNMENT_COLORS[status] ?? "#10b981")
        : "#10b981";
    }
    case "evaluation":
      return "rgba(59, 138, 152, 0.5)";
    default:
      return "#94a3b8";
  }
}

function getNodeSize(node: EthosGraphNode): number {
  switch (node.type) {
    case "dimension":
      return 40;
    case "trait":
      return 25;
    case "constitutional_value":
      return 30;
    case "pattern":
      return 20;
    case "indicator":
      return 8;
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
    case "trait":
      return node.label;
    case "constitutional_value":
      return node.label;
    case "pattern":
      return node.label;
    case "agent":
      return node.label;
    case "indicator":
      return "";
    case "evaluation":
      return "";
    default:
      return node.label;
  }
}

/* -------------------------------------------------------------------------- */
/*  Relationship color + width mapping                                        */
/* -------------------------------------------------------------------------- */

/* -------------------------------------------------------------------------- */
/*  Transform API data → NVL format                                           */
/* -------------------------------------------------------------------------- */

function toNvlNodes(nodes: EthosGraphNode[]): NvlNode[] {
  return nodes.map((n) => ({
    id: n.id,
    color: getNodeColor(n),
    size: getNodeSize(n),
    caption: getNodeCaption(n),
  }));
}

function toNvlRelationships(rels: GraphRel[], nodeIds: Set<string>): NvlRelationship[] {
  return rels
    .filter((r) => nodeIds.has(r.fromId) && nodeIds.has(r.toId))
    .map((r) => {
      const style = REL_STYLES[r.type] ?? { color: "#cbd5e1", width: 1 };
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

    async function init() {
      if (!containerRef.current) return;

      try {
        const [{ default: NVL }, handlers] = await Promise.all([
          import("@neo4j-nvl/base"),
          import("@neo4j-nvl/interaction-handlers"),
        ]);

        if (destroyed || !containerRef.current) return;

        // Clean any stale content
        containerRef.current.innerHTML = "";

        const nodeIds = nodes.map((n) => n.id);

        const nvl = new NVL(containerRef.current, nodes, rels, {
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
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
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
        className="flex h-[600px] items-center justify-center rounded-xl border border-border bg-white"
        data-testid="graph-loading"
      >
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-action border-t-transparent" />
          <p className="mt-3 text-sm text-muted">Loading Phronesis Graph...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div
        className="flex h-[600px] items-center justify-center rounded-xl border border-border bg-white"
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
        className="flex h-[600px] items-center justify-center rounded-xl border border-border bg-white"
        data-testid="graph-empty"
      >
        <div className="text-center">
          <p className="text-sm text-muted">
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
      className="relative h-[600px] rounded-xl border border-border bg-white"
      data-testid="phronesis-graph"
    >
      <NvlRenderer
        nodes={nvlNodes}
        rels={nvlRels}
        onNodeClick={handleNodeClick}
      />

      {/* Node count legend */}
      <div className="absolute bottom-3 left-3 flex gap-3 rounded-lg bg-white/90 px-3 py-2 text-xs text-muted backdrop-blur-sm">
        <span>
          Nodes: {graphData.nodes.length}
        </span>
        <span>
          Agents: {graphData.nodes.filter((n) => n.type === "agent").length}
        </span>
        <span>
          Evaluations:{" "}
          {graphData.nodes.filter((n) => n.type === "evaluation").length}
        </span>
      </div>
    </div>
  );
}
