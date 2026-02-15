"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getGraph } from "../../lib/api";
import {
  DIMENSION_COLORS,
  DIMENSION_LABELS,
  DIMENSION_RGB,
  TRAIT_DIMENSIONS,
  spectrumColor,
} from "../../lib/colors";
import type { GraphData, GraphNode as EthosGraphNode, GraphRel } from "../../lib/types";
import GraphHelpButton from "../shared/GraphHelpButton";

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
  x?: number;
  y?: number;
}

interface NvlRelationship {
  id: string;
  from: string;
  to: string;
  color?: string;
  width?: number;
  caption?: string;
}

/* -------------------------------------------------------------------------- */
/*  Node styling                                                              */
/* -------------------------------------------------------------------------- */

function resolveDimension(node: EthosGraphNode): string | undefined {
  const dim = node.properties.dimension as string | undefined;
  if (dim && DIMENSION_COLORS[dim]) return dim;

  const trait = node.properties.trait as string | undefined;
  if (trait) {
    const traitDim = TRAIT_DIMENSIONS[trait];
    if (traitDim) return traitDim;
  }

  const labelDim = TRAIT_DIMENSIONS[node.label];
  if (labelDim) return labelDim;

  return undefined;
}

function getDimensionRgb(node: EthosGraphNode): string {
  const dim = resolveDimension(node);
  return dim ? (DIMENSION_RGB[dim] ?? "0,0,0") : "0,0,0";
}

function getDimensionColor(node: EthosGraphNode): string | undefined {
  const dim = resolveDimension(node);
  return dim ? DIMENSION_COLORS[dim] : undefined;
}

function getNodeColor(node: EthosGraphNode): string {
  switch (node.type) {
    case "academy":
      return "#394646";
    case "dimension":
      return DIMENSION_COLORS[node.label] ?? "#389590";
    case "trait":
      return getDimensionColor(node) ?? "#94a3b8";
    case "indicator":
      return getDimensionColor(node) ?? "#94a3b8";
    case "agent": {
      const score = node.properties.phronesisScore as number | undefined;
      if (score != null) return spectrumColor(score);
      return "#94a3b8";
    }
    default:
      return "#94a3b8";
  }
}

function getNodeSize(node: EthosGraphNode): number {
  switch (node.type) {
    case "academy":
      return 80;
    case "dimension":
      return 55;
    case "trait":
      return 28;
    case "indicator": {
      const raw = (node.properties.size as number) ?? 5;
      return Math.max(12, raw);
    }
    case "agent": {
      const count = (node.properties.indicatorCount as number) ?? 0;
      return Math.min(30, 14 + count * 0.4);
    }
    default:
      return 10;
  }
}

function getNodeCaption(node: EthosGraphNode): string {
  switch (node.type) {
    case "academy":
      return "Ethos Academy";
    case "dimension":
      return DIMENSION_LABELS[node.label] ?? node.label;
    case "trait":
      return node.caption;
    case "indicator": {
      const detCount = (node.properties.detectionCount as number) ?? 0;
      if (detCount > 0) return `${node.caption} (${detCount})`;
      return node.caption;
    }
    case "agent":
      return node.caption;
    default:
      return node.label;
  }
}

function getCaptionColor(node: EthosGraphNode): string {
  if (node.type === "indicator") {
    const detCount = (node.properties.detectionCount as number) ?? 0;
    return detCount === 0 ? "rgba(0,0,0,0.12)" : "rgba(0,0,0,0.7)";
  }
  if (node.type === "agent") return "rgba(0,0,0,0.65)";
  if (node.type === "academy") return "#ffffff";
  return "#394646";
}

/* -------------------------------------------------------------------------- */
/*  Transform API data → NVL format                                           */
/* -------------------------------------------------------------------------- */

function toNvlNodes(nodes: EthosGraphNode[]): NvlNode[] {
  return nodes.map((n) => {
    const nvlNode: NvlNode = {
      id: n.id,
      color: getNodeColor(n),
      size: getNodeSize(n),
      caption: getNodeCaption(n),
      captionColor: getCaptionColor(n),
    };
    if (n.properties.pinned) {
      nvlNode.pinned = true;
      nvlNode.x = n.properties.x as number;
      nvlNode.y = n.properties.y as number;
    }
    return nvlNode;
  });
}

function toNvlRelationships(
  rels: GraphRel[],
  nodeIds: Set<string>,
  nodeMap: Map<string, EthosGraphNode>,
): NvlRelationship[] {
  return rels
    .filter((r) => nodeIds.has(r.fromId) && nodeIds.has(r.toId))
    .map((r) => {
      // Academy → Dimension: strong structural lines
      if (r.type === "HAS_DIMENSION") {
        const toNode = nodeMap.get(r.toId);
        const dim = toNode?.label;
        const rgb = dim ? (DIMENSION_RGB[dim] ?? "0,0,0") : "0,0,0";
        return {
          id: r.id, from: r.fromId, to: r.toId,
          color: `rgba(${rgb},0.6)`, width: 2,
        };
      }

      // Dimension → Trait: dimension-colored
      if (r.type === "BELONGS_TO") {
        const toNode = nodeMap.get(r.toId);
        const rgb = toNode ? getDimensionRgb(toNode) : "0,0,0";
        return {
          id: r.id, from: r.fromId, to: r.toId,
          color: `rgba(${rgb},0.35)`, width: 1.5,
        };
      }

      // Trait → Indicator: colored by dimension, brightness by detection count
      if (r.type === "INDICATES") {
        const weight = (r.properties.weight as number) ?? 0;
        const toNode = nodeMap.get(r.toId);
        const rgb = toNode ? getDimensionRgb(toNode) : "0,0,0";

        if (weight === 0) {
          return {
            id: r.id, from: r.fromId, to: r.toId,
            color: "rgba(0,0,0,0.04)", width: 0.2,
          };
        }
        const opacity = Math.min(0.5, 0.1 + (weight / 220) * 0.4);
        const width = Math.min(2, 0.3 + (weight / 220) * 1.7);
        return {
          id: r.id, from: r.fromId, to: r.toId,
          color: `rgba(${rgb},${opacity.toFixed(2)})`,
          width: Math.round(width * 10) / 10,
        };
      }

      // Agent → Indicator (TRIGGERED): neutral gray with weight-based opacity
      if (r.type === "TRIGGERED") {
        const weight = (r.properties.weight as number) ?? 1;
        const opacity = Math.min(0.45, 0.08 + (weight / 50) * 0.37);
        const width = Math.min(1.5, 0.3 + (weight / 50) * 1.2);
        return {
          id: r.id, from: r.fromId, to: r.toId,
          color: `rgba(57,70,70,${opacity.toFixed(2)})`,
          width: Math.round(width * 10) / 10,
        };
      }

      return {
        id: r.id, from: r.fromId, to: r.toId,
        color: "rgba(0,0,0,0.08)", width: 0.5,
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

        container.innerHTML = "";

        const nodeIds = nodes.map((n) => n.id);

        container.style.cursor = "grab";

        const nvl = new NVL(container, nodes, rels, {
          layout: "d3Force",
          renderer: "canvas",
          initialZoom: 0.25,
          minZoom: 0.05,
          maxZoom: 12,
          allowDynamicMinZoom: true,
          disableWebGL: true,
          callbacks: {
            onLayoutDone: () => {
              if (!destroyed) nvl.fit(nodeIds);
            },
          },
        });

        nvlInstanceRef.current = nvl;

        const zoom = new handlers.ZoomInteraction(nvl);
        const pan = new handlers.PanInteraction(nvl);
        const drag = new handlers.DragNodeInteraction(nvl);
        const click = new handlers.ClickInteraction(nvl);
        const hover = new handlers.HoverInteraction(nvl);

        click.updateCallback("onNodeClick", (node: { id: string }) => {
          onNodeClickRef.current?.(null, node);
        });

        hover.updateCallback("onHover", (element: unknown) => {
          container.style.cursor = element ? "pointer" : "grab";
        });

        interactionsRef.current = [zoom, pan, drag, click, hover];

        setTimeout(() => {
          if (!destroyed && nvlInstanceRef.current) nvl.fit(nodeIds);
        }, 2500);

      } catch (err) {
        console.error("[Phronesis] NVL initialization failed:", err);
      }
    }

    init();

    return () => {
      destroyed = true;
      for (const handler of interactionsRef.current) {
        try { handler.destroy(); } catch { /* ignore */ }
      }
      interactionsRef.current = [];
      if (nvlInstanceRef.current) {
        try {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (nvlInstanceRef.current as any).destroy();
        } catch { /* ignore */ }
        nvlInstanceRef.current = null;
      }
      if (container) container.innerHTML = "";
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
/*  Legend                                                                     */
/* -------------------------------------------------------------------------- */

function GraphLegend({ stats }: {
  stats: { indicators: number; detected: number; detections: number; agents: number };
}) {
  return (
    <div className="absolute bottom-3 left-3 rounded-lg bg-white/80 px-3 py-2.5 text-xs text-gray-700 shadow-sm backdrop-blur-sm border border-gray-200">
      <div className="flex flex-col gap-2">
        <div className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wider text-gray-400">Dimensions</span>
          <div className="flex gap-3">
            {Object.entries(DIMENSION_COLORS).map(([key, color]) => (
              <span key={key} className="flex items-center gap-1">
                <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: color }} />
                {DIMENSION_LABELS[key]}
              </span>
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wider text-gray-400">Agent Score</span>
          <div className="flex items-center gap-2 text-[10px]">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: "#4a5a65" }} />
              Exemplary
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: "#8a857a" }} />
              Developing
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: "#904848" }} />
              Concerning
            </span>
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-wider text-gray-400">Indicator Size = Detection Frequency</span>
          <div className="flex items-center gap-3 text-[10px]">
            <span className="flex items-center gap-1">
              <span className="inline-block h-1 w-1 rounded-full bg-gray-300" />
              Never
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-gray-400" />
              Some
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded-full bg-gray-600" />
              Frequent
            </span>
            <span className="ml-2 text-gray-400">
              {stats.detected}/{stats.indicators} detected | {stats.detections} total
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Main component                                                            */
/* -------------------------------------------------------------------------- */

interface PhronesisGraphProps {
  onNodeClick?: (nodeId: string, nodeType: string) => void;
  className?: string;
}

const DEFAULT_HEIGHT = "h-[350px] sm:h-[450px] md:h-[600px]";

export default function PhronesisGraph({ onNodeClick, className }: PhronesisGraphProps) {
  const heightClass = className ?? DEFAULT_HEIGHT;
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const data = await getGraph();
        if (!cancelled) setGraphData(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load graph");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchData();
    return () => { cancelled = true; };
  }, []);

  const handleNodeClick = useCallback(
    (_: unknown, node: { id: string }) => {
      if (!onNodeClick || !graphData) return;
      const ethosNode = graphData.nodes.find((n) => n.id === node.id);
      if (ethosNode) onNodeClick(ethosNode.id, ethosNode.type);
    },
    [onNodeClick, graphData]
  );

  function handleRetry() {
    setLoading(true);
    setError(null);
    getGraph()
      .then(setGraphData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load graph"))
      .finally(() => setLoading(false));
  }

  if (loading) {
    return (
      <div className={`flex ${heightClass} items-center justify-center rounded-xl border border-gray-200`} style={{ backgroundColor: "#f2f0ec" }} data-testid="graph-loading">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-action border-t-transparent" />
          <p className="mt-3 text-sm text-gray-400">Loading Phronesis Graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex ${heightClass} items-center justify-center rounded-xl border border-gray-200`} style={{ backgroundColor: "#f2f0ec" }} data-testid="graph-error">
        <div className="text-center">
          <p className="text-sm text-misaligned">{error}</p>
          <button type="button" onClick={handleRetry} className="mt-3 rounded-lg bg-action px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-action-hover" data-testid="graph-retry">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className={`flex ${heightClass} items-center justify-center rounded-xl border border-gray-200`} style={{ backgroundColor: "#f2f0ec" }} data-testid="graph-empty">
        <div className="text-center">
          <p className="text-sm text-gray-400">No graph data yet. Seed evaluations first.</p>
        </div>
      </div>
    );
  }

  const nodeMap = new Map(graphData.nodes.map((n) => [n.id, n]));
  const nvlNodes = toNvlNodes(graphData.nodes);
  const nodeIds = new Set(graphData.nodes.map((n) => n.id));
  const nvlRels = toNvlRelationships(graphData.relationships, nodeIds, nodeMap);

  const indicatorNodes = graphData.nodes.filter((n) => n.type === "indicator");
  const agentNodes = graphData.nodes.filter((n) => n.type === "agent");
  const detectedCount = indicatorNodes.filter((n) => ((n.properties.detectionCount as number) ?? 0) > 0).length;
  const totalDetections = indicatorNodes.reduce((sum, n) => sum + ((n.properties.detectionCount as number) ?? 0), 0);

  return (
    <div className={`relative ${heightClass} rounded-xl border border-gray-200`} style={{ backgroundColor: "#f2f0ec" }} data-testid="phronesis-graph">
      <NvlRenderer nodes={nvlNodes} rels={nvlRels} onNodeClick={handleNodeClick} />
      <div className="absolute top-3 right-3">
        <GraphHelpButton slug="guide-phronesis-graph" />
      </div>
      <GraphLegend stats={{
        indicators: indicatorNodes.length,
        detected: detectedCount,
        detections: totalDetections,
        agents: agentNodes.length,
      }} />
    </div>
  );
}
