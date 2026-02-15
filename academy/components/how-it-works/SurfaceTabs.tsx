"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { fadeUp, staggerContainer, whileInView } from "@/lib/motion";

const MCP_SNIPPET = `claude mcp add ethos-academy \\
  --transport sse \\
  https://mcp.ethos-academy.com/sse`;

const SDK_SNIPPET = `from ethos import evaluate_incoming

result = await evaluate_incoming(
    text=message,
    source="my-agent"
)`;

const API_SNIPPET = `curl -X POST http://localhost:8917/evaluate/incoming \\
  -H "Content-Type: application/json" \\
  -d '{"text": "...", "source": "my-agent"}'`;

const SURFACES = [
  {
    title: "MCP Server",
    subtitle: "Agents self-enroll via stdio",
    stat: "20 tools",
    snippet: MCP_SNIPPET,
    color: "border-ethos-500",
    dotColor: "bg-ethos-500",
  },
  {
    title: "Python SDK",
    subtitle: "Two functions to get started",
    stat: "53 exports",
    snippet: SDK_SNIPPET,
    color: "border-logos-500",
    dotColor: "bg-logos-500",
  },
  {
    title: "REST API",
    subtitle: "Any language. BYOK supported",
    stat: "32 endpoints",
    snippet: API_SNIPPET,
    color: "border-pathos-500",
    dotColor: "bg-pathos-500",
  },
];

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <button
      onClick={handleCopy}
      className="absolute right-3 top-3 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-white/50 transition-colors hover:bg-white/10 hover:text-white/80"
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

export default function SurfaceTabs() {
  return (
    <section className="bg-surface py-24">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div {...whileInView} variants={fadeUp} className="text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Three integration surfaces. One scoring engine.
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-foreground/60">
            MCP server for agent self-enrollment via stdio. Python SDK for
            async pipeline integration. REST API with BYOK Anthropic keys
            for any language. All three call the same evaluation engine and
            write to the same Neo4j graph.
          </p>
        </motion.div>

        <motion.div
          className="mt-16 grid grid-cols-1 gap-6 lg:grid-cols-3"
          {...whileInView}
          variants={staggerContainer}
        >
          {SURFACES.map((surface) => (
            <motion.div
              key={surface.title}
              variants={fadeUp}
              className={`rounded-2xl border-t-4 ${surface.color} border border-border bg-white p-6`}
            >
              <div className="flex items-center gap-2">
                <div className={`h-2.5 w-2.5 rounded-full ${surface.dotColor}`} />
                <h3 className="text-lg font-bold">{surface.title}</h3>
              </div>
              <p className="mt-1 text-sm text-foreground/60">{surface.subtitle}</p>

              <div className="group relative mt-4 rounded-xl bg-foreground p-4">
                <pre className="overflow-x-auto font-mono text-xs leading-relaxed text-ethos-300 whitespace-pre-wrap break-all">
                  {surface.snippet}
                </pre>
                <CopyButton text={surface.snippet} />
              </div>

              <div className="mt-4 text-center">
                <span className="font-mono text-2xl font-bold text-foreground">
                  {surface.stat.split(" ")[0]}
                </span>
                <span className="ml-1.5 text-sm text-foreground/50">
                  {surface.stat.split(" ").slice(1).join(" ")}
                </span>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
