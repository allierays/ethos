"use client";

import { useEffect, useRef } from "react";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: false,
  theme: "base",
  themeVariables: {
    primaryColor: "#e8f4f3",
    primaryTextColor: "#1a2538",
    primaryBorderColor: "#389590",
    lineColor: "#389590",
    secondaryColor: "#fef3d0",
    tertiaryColor: "#f5f0eb",
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
    fontSize: "13px",
  },
  flowchart: {
    curve: "basis",
    padding: 16,
    nodeSpacing: 30,
    rankSpacing: 40,
    htmlLabels: true,
  },
});

interface MermaidDiagramProps {
  chart: string;
  id: string;
}

export default function MermaidDiagram({ chart, id }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;
    el.innerHTML = "";

    const render = async () => {
      try {
        const { svg } = await mermaid.render(`mermaid-${id}`, chart);
        el.innerHTML = svg;
        // Make SVG responsive
        const svgEl = el.querySelector("svg");
        if (svgEl) {
          svgEl.removeAttribute("height");
          svgEl.style.maxWidth = "100%";
          svgEl.style.height = "auto";
          // Add background behind subgraph labels so arrows don't obscure text
          svgEl.querySelectorAll(".cluster-label").forEach((label) => {
            const text = label.querySelector("text, foreignObject");
            if (!text) return;
            const bbox = (text as SVGGraphicsElement).getBBox?.();
            if (!bbox) return;
            const pad = 4;
            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", String(bbox.x - pad));
            rect.setAttribute("y", String(bbox.y - pad));
            rect.setAttribute("width", String(bbox.width + pad * 2));
            rect.setAttribute("height", String(bbox.height + pad * 2));
            rect.setAttribute("fill", "#f5f0eb");
            rect.setAttribute("rx", "3");
            label.insertBefore(rect, text);
          });
        }
      } catch {
        el.innerHTML = `<pre class="text-xs text-red-400">${chart}</pre>`;
      }
    };

    render();
  }, [chart, id]);

  return <div ref={containerRef} className="overflow-x-auto" />;
}
