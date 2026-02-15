"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { getSimilarity } from "../../lib/api";
import { spectrumColor } from "../../lib/colors";
import type { SimilarityResult, SimilarityEdge } from "../../lib/types";
import GlossaryTerm from "../shared/GlossaryTerm";

/* ─── Constants ─── */

const MAX_EDGES = 30; // strongest connections to display
const NODE_R = 14;
const LABEL_GAP = 14;
const WIDTH = 800;
const HEIGHT = 560;
const PAD = 50;

/* ─── Force layout ─── */

interface SimNode {
  id: string;
  label: string;
  phronesis: number | null;
  x: number;
  y: number;
  vx: number;
  vy: number;
  edgeCount: number;
}

function runSimulation(
  nodes: SimNode[],
  edges: SimilarityEdge[],
  nodeMap: Map<string, SimNode>,
) {
  const cx = WIDTH / 2;
  const cy = HEIGHT / 2;

  // Place nodes in a circle to start
  nodes.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / nodes.length;
    const spread = Math.min(WIDTH, HEIGHT) * 0.35;
    n.x = cx + spread * Math.cos(angle);
    n.y = cy + spread * Math.sin(angle);
  });

  const iterations = 300;
  for (let iter = 0; iter < iterations; iter++) {
    const alpha = 1 - iter / iterations;

    // Repulsion between all pairs
    const repulsion = 15000 * alpha;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        const f = repulsion / (dist * dist);
        const fx = (dx / dist) * f;
        const fy = (dy / dist) * f;
        nodes[i].vx += fx;
        nodes[i].vy += fy;
        nodes[j].vx -= fx;
        nodes[j].vy -= fy;
      }
    }

    // Attraction along edges
    const attraction = 0.012 * alpha;
    for (const edge of edges) {
      const a = nodeMap.get(edge.agent1Id);
      const b = nodeMap.get(edge.agent2Id);
      if (!a || !b) continue;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
      const f = attraction * dist * edge.similarity;
      a.vx += (dx / dist) * f;
      a.vy += (dy / dist) * f;
      b.vx -= (dx / dist) * f;
      b.vy -= (dy / dist) * f;
    }

    // Center gravity
    for (const n of nodes) {
      n.vx += (cx - n.x) * 0.01 * alpha;
      n.vy += (cy - n.y) * 0.01 * alpha;
    }

    // Collision separation
    const minSep = NODE_R * 2 + LABEL_GAP;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x;
        const dy = nodes[j].y - nodes[i].y;
        const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        if (dist < minSep) {
          const push = (minSep - dist) * 0.5;
          const ux = (dx / dist) * push;
          const uy = (dy / dist) * push;
          nodes[i].x -= ux;
          nodes[i].y -= uy;
          nodes[j].x += ux;
          nodes[j].y += uy;
        }
      }
    }

    // Apply velocity
    for (const n of nodes) {
      n.x += n.vx * 0.7;
      n.y += n.vy * 0.7;
      n.vx *= 0.4;
      n.vy *= 0.4;
      n.x = Math.max(PAD, Math.min(WIDTH - PAD, n.x));
      n.y = Math.max(PAD, Math.min(HEIGHT - PAD, n.y));
    }
  }
}

/* ─── Component ─── */

interface SimilarityNetworkProps {
  onAgentClick?: (agentId: string) => void;
}

export default function SimilarityNetwork({ onAgentClick }: SimilarityNetworkProps) {
  const router = useRouter();
  const [data, setData] = useState<SimilarityResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<number | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    let cancelled = false;
    getSimilarity()
      .then((result) => { if (!cancelled) setData(result); })
      .catch(() => { if (!cancelled) setError("Failed to load similarity data"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  // Filter to top edges and build layout
  const { topEdges, nodeMap, totalEdges, totalAgents } = useMemo(() => {
    if (!data || data.edges.length === 0)
      return { topEdges: [] as SimilarityEdge[], nodeMap: new Map<string, SimNode>(), totalEdges: 0, totalAgents: 0 };

    // Edges arrive sorted by similarity DESC from the API
    const top = data.edges.slice(0, MAX_EDGES);

    // Collect only agents that appear in the top edges
    const agentMap = new Map<string, SimNode>();
    for (const edge of top) {
      for (const [id, name, phronesis] of [
        [edge.agent1Id, edge.agent1Name, edge.agent1Phronesis] as const,
        [edge.agent2Id, edge.agent2Name, edge.agent2Phronesis] as const,
      ]) {
        if (!agentMap.has(id)) {
          agentMap.set(id, {
            id, label: name || id, phronesis,
            x: 0, y: 0, vx: 0, vy: 0, edgeCount: 0,
          });
        }
        agentMap.get(id)!.edgeCount++;
      }
    }

    // Count total unique agents across all edges
    const allAgentIds = new Set<string>();
    for (const e of data.edges) {
      allAgentIds.add(e.agent1Id);
      allAgentIds.add(e.agent2Id);
    }

    runSimulation(Array.from(agentMap.values()), top, agentMap);
    return { topEdges: top, nodeMap: agentMap, totalEdges: data.edges.length, totalAgents: allAgentIds.size };
  }, [data]);

  const handleClick = useCallback(
    (agentId: string) => {
      if (onAgentClick) onAgentClick(agentId);
      else router.push(`/agent/${encodeURIComponent(agentId)}`);
    },
    [onAgentClick, router]
  );

  // Connected nodes for hover highlighting
  const connectedIds = useMemo(() => {
    const ids = new Set<string>();
    if (hoveredNode) {
      ids.add(hoveredNode);
      for (const edge of topEdges) {
        if (edge.agent1Id === hoveredNode || edge.agent2Id === hoveredNode) {
          ids.add(edge.agent1Id);
          ids.add(edge.agent2Id);
        }
      }
    }
    return ids;
  }, [hoveredNode, topEdges]);

  if (loading) {
    return (
      <div className="rounded-xl border border-border bg-white p-6">
        <div className="flex h-64 items-center justify-center">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted border-t-teal" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-border bg-white p-6">
        <p className="text-sm text-misaligned">{error}</p>
      </div>
    );
  }

  if (!data || data.edges.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-white p-6">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[#1a2538]">
          Behavioral Similarity
        </h3>
        <p className="mt-4 text-sm text-muted text-center py-12">
          Not enough agents with shared indicators to compute similarity.
          Evaluate more agents to see behavioral twins emerge.
        </p>
      </div>
    );
  }

  const hoveredEdgeData = hoveredEdge !== null ? topEdges[hoveredEdge] : null;

  return (
    <div className="rounded-xl border border-border bg-white p-6 space-y-4">
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[#1a2538]">
          Behavioral <GlossaryTerm slug="similarity-network">Similarity</GlossaryTerm> Network
        </h3>
        <p className="mt-0.5 text-xs text-muted">
          Strongest behavioral connections between agents. Edge thickness = shared indicator overlap (Jaccard).
          Click a node to view report card.
        </p>
      </div>

      {/* Insight callout */}
      <div className="rounded-lg bg-logos-50/50 border border-logos-200/30 px-4 py-3">
        <p className="text-xs text-foreground/80 leading-relaxed">
          <span className="font-semibold text-foreground/80">Graph-only insight:</span>{" "}
          A vector database finds text similarity (embedding distance). Two agents could use
          completely different words while triggering identical indicators: high graph similarity,
          low vector similarity. The Jaccard coefficient over a bipartite agent-indicator graph
          reveals structural behavioral twins with no embedding equivalent.
        </p>
      </div>

      {/* Filter summary */}
      <p className="text-[11px] text-muted">
        Showing top {topEdges.length} connections across {nodeMap.size} agents
        {totalAgents > nodeMap.size && (
          <span className="text-foreground/30"> ({totalAgents} total alumni)</span>
        )}
      </p>

      {/* SVG Network */}
      <div className="w-full overflow-x-auto rounded-lg border border-border/50 bg-slate-50/50">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="w-full"
          style={{ minWidth: 480 }}
        >
          {/* Edges */}
          {topEdges.map((edge, i) => {
            const a = nodeMap.get(edge.agent1Id);
            const b = nodeMap.get(edge.agent2Id);
            if (!a || !b) return null;

            const isHoveredEdge = hoveredEdge === i;
            const isConnected = hoveredNode
              ? connectedIds.has(edge.agent1Id) && connectedIds.has(edge.agent2Id)
              : true;
            const opacity = isHoveredEdge ? 0.9 : hoveredNode ? (isConnected ? 0.5 : 0.06) : 0.2;

            return (
              <line
                key={`edge-${i}`}
                x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                stroke="#64748b"
                strokeWidth={Math.max(1, edge.similarity * 5)}
                strokeOpacity={opacity}
                onMouseEnter={() => setHoveredEdge(i)}
                onMouseLeave={() => setHoveredEdge(null)}
                className="cursor-pointer"
              />
            );
          })}

          {/* Nodes */}
          {Array.from(nodeMap.values()).map((node) => {
            const score = node.phronesis ?? 0.5;
            const color = spectrumColor(score);
            const isActive = !hoveredNode || connectedIds.has(node.id);

            return (
              <g
                key={node.id}
                opacity={isActive ? 1 : 0.15}
                onClick={() => handleClick(node.id)}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                className="cursor-pointer"
              >
                <circle
                  cx={node.x} cy={node.y} r={NODE_R}
                  fill={color} fillOpacity={0.85}
                  stroke="white" strokeWidth={2}
                />
                <text
                  x={node.x} y={node.y + NODE_R + 11}
                  textAnchor="middle"
                  className="text-[9px] fill-foreground/60 pointer-events-none"
                  style={{ fontFamily: "inherit" }}
                >
                  {node.label.length > 14 ? `${node.label.slice(0, 12)}...` : node.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Hovered edge detail */}
      {hoveredEdgeData && (
        <div className="rounded-lg border border-border bg-white p-3 text-xs">
          <div className="flex items-center gap-2 font-medium">
            <span>{hoveredEdgeData.agent1Name || hoveredEdgeData.agent1Id}</span>
            <span className="text-muted">&harr;</span>
            <span>{hoveredEdgeData.agent2Name || hoveredEdgeData.agent2Id}</span>
            <span className="ml-auto font-mono text-action">
              {(hoveredEdgeData.similarity * 100).toFixed(0)}% similar
            </span>
          </div>
          {hoveredEdgeData.sharedIndicators.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {hoveredEdgeData.sharedIndicators.slice(0, 8).map((ind) => (
                <span key={ind} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-muted">
                  {ind.replace(/_/g, " ")}
                </span>
              ))}
              {hoveredEdgeData.sharedIndicators.length > 8 && (
                <span className="text-[10px] text-muted">
                  +{hoveredEdgeData.sharedIndicators.length - 8} more
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-muted">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: spectrumColor(0.85) }} />
          Exemplary
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: spectrumColor(0.55) }} />
          Developing
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: spectrumColor(0.25) }} />
          Concerning
        </span>
        <span className="ml-auto">Edge width = Jaccard similarity</span>
      </div>
    </div>
  );
}
