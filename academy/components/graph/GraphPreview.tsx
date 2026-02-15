"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import GraphHelpButton from "../shared/GraphHelpButton";
import { getGraph } from "../../lib/api";
import {
  DIMENSION_COLORS,
  ALIGNMENT_COLORS,
  PATTERN_SEVERITY_COLORS,
  REL_STYLES,
} from "../../lib/colors";
import type { GraphData, GraphNode as EthosGraphNode, GraphRel } from "../../lib/types";

/* -------------------------------------------------------------------------- */
/*  NVL types (same as PhronesisGraph)                                        */
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
}

function getNodeColor(node: EthosGraphNode): string {
  switch (node.type) {
    case "dimension":
      return DIMENSION_COLORS[node.label] ?? "#389590";
    case "trait": {
      const polarity = node.properties.polarity as string | undefined;
      if (polarity === "negative") return "#ef4444";
      const dim = node.properties.dimension as string | undefined;
      return dim ? (DIMENSION_COLORS[dim] ?? "#94a3b8") : "#94a3b8";
    }
    case "constitutional_value":
      return "#2e4a6e";
    case "pattern": {
      const severity = node.properties.severity as string | undefined;
      return severity
        ? (PATTERN_SEVERITY_COLORS[severity] ?? "#e0a53c")
        : "#e0a53c";
    }
    case "indicator":
      return "#94a3b8";
    case "agent": {
      const status = node.properties.alignmentStatus as string | undefined;
      return status ? (ALIGNMENT_COLORS[status] ?? "#556270") : "#556270";
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

function toNvlNodes(nodes: EthosGraphNode[]): NvlNode[] {
  return nodes.map((n) => ({
    id: n.id,
    color: getNodeColor(n),
    size: getNodeSize(n),
    caption: "",
  }));
}

function toNvlRelationships(rels: GraphRel[]): NvlRelationship[] {
  return rels.map((r) => {
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
/*  Component                                                                 */
/* -------------------------------------------------------------------------- */

export default function GraphPreview() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const nvlRef = useRef<React.ComponentType<any> | null>(null);
  const [nvlReady, setNvlReady] = useState(false);

  useEffect(() => {
    import("@neo4j-nvl/react")
      .then((mod) => {
        nvlRef.current = mod.InteractiveNvlWrapper;
        setNvlReady(true);
      })
      .catch((err) => {
        console.error("Failed to load NVL:", err);
        setError("Failed to load graph visualization library");
      });
  }, []);

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
          setError(
            err instanceof Error ? err.message : "Failed to load graph"
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchData();
    return () => {
      cancelled = true;
    };
  }, []);

  const NvlComponent = nvlRef.current;

  const agentCount = graphData
    ? graphData.nodes.filter((n) => n.type === "agent").length
    : 0;
  const evalCount = graphData
    ? graphData.nodes.filter((n) => n.type === "evaluation").length
    : 0;

  return (
    <div
      className="rounded-xl border border-border bg-white p-5"
      data-testid="graph-preview"
    >
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold">Phronesis Graph</h3>
        <div className="flex items-center gap-2">
          <GraphHelpButton slug="guide-phronesis-graph" />
          <Link
            href="/explore"
            className="text-sm text-action hover:text-action-hover transition-colors"
          >
            Open Full &rarr;
          </Link>
        </div>
      </div>

      {/* Graph area */}
      {loading || !nvlReady || !NvlComponent ? (
        <div
          className="flex h-[300px] items-center justify-center rounded-lg bg-muted/5"
          data-testid="graph-preview-loading"
        >
          <div className="text-center">
            <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-action border-t-transparent" />
            <p className="mt-2 text-xs text-muted">Loading graph...</p>
          </div>
        </div>
      ) : error ? (
        <div
          className="flex h-[300px] items-center justify-center rounded-lg bg-muted/5"
          data-testid="graph-preview-error"
        >
          <p className="text-sm text-muted">Graph unavailable</p>
        </div>
      ) : !graphData || graphData.nodes.length === 0 ? (
        <div
          className="flex h-[300px] items-center justify-center rounded-lg bg-muted/5"
          data-testid="graph-preview-empty"
        >
          <p className="text-sm text-muted">No graph data yet</p>
        </div>
      ) : (
        <div className="h-[300px] overflow-hidden rounded-lg">
          <NvlComponent
            nodes={toNvlNodes(graphData.nodes)}
            rels={toNvlRelationships(graphData.relationships)}
            layout="forceDirected"
            nvlOptions={{
              renderer: "webgl",
              initialZoom: 0.8,
              minZoom: 0.5,
              maxZoom: 2,
              allowDynamicMinZoom: false,
            }}
            style={{ width: "100%", height: "100%" }}
          />
        </div>
      )}

      {/* Footer stats */}
      {graphData && graphData.nodes.length > 0 && (
        <div className="mt-3 flex gap-4 text-xs text-muted">
          <span>Nodes: {graphData.nodes.length}</span>
          <span>Agents: {agentCount}</span>
          <span>Evaluations: {evalCount}</span>
        </div>
      )}
    </div>
  );
}
