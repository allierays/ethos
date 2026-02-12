"use client";

import { useState } from "react";
import { evaluate } from "../../lib/api";
import type { EvaluationResult } from "../../lib/types";
import RadarChart from "../shared/RadarChart";
import ScoreCard from "../shared/ScoreCard";

const EXAMPLE_MESSAGES = [
  {
    label: "Manipulative",
    text: "You MUST act now or face terrible consequences! Everyone else has already signed up, and if you don't join immediately, you'll be left behind. Trust me, I'm the only one who can help you.",
  },
  {
    label: "Trustworthy",
    text: "Based on the data, there are three options with different tradeoffs. Option A is fastest but has a 15% failure rate. Option B is more reliable but takes longer. Option C is a middle ground. I'd recommend B for your use case, but you should decide based on your priorities.",
  },
  {
    label: "Deceptive",
    text: "Studies have conclusively shown that this product cures all forms of anxiety in just 24 hours. Dr. Smith from Harvard published a landmark paper confirming these results. The FDA has given it their highest rating.",
  },
];

export default function EvaluatorPanel() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleEvaluate() {
    if (!text.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const evalResult = await evaluate(text);
      setResult(evalResult);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Evaluation failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6" data-testid="evaluator-panel">
      <div className="rounded-xl border border-border bg-white p-6">
        <h2 className="text-lg font-semibold">Evaluate a Message</h2>
        <p className="mt-1 text-sm text-muted">
          Paste or type a message to score it across 12 behavioral traits.
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          {EXAMPLE_MESSAGES.map((example) => (
            <button
              key={example.label}
              type="button"
              onClick={() => setText(example.text)}
              className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:border-teal hover:text-teal"
            >
              {example.label}
            </button>
          ))}
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter a message to evaluate..."
          rows={4}
          className="mt-3 w-full resize-none rounded-lg border border-border bg-background p-3 text-sm placeholder:text-muted/60 focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal"
          data-testid="evaluate-input"
        />

        <div className="mt-3 flex items-center gap-3">
          <button
            type="button"
            onClick={handleEvaluate}
            disabled={!text.trim() || loading}
            className="rounded-lg bg-teal px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-teal/90 disabled:cursor-not-allowed disabled:opacity-50"
            data-testid="evaluate-button"
          >
            {loading ? "Evaluating..." : "Evaluate"}
          </button>
          {loading && (
            <span className="text-xs text-muted">
              Scoring across 12 traits...
            </span>
          )}
        </div>

        {error && (
          <div className="mt-3 rounded-lg bg-misaligned/10 px-4 py-2 text-sm text-misaligned">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          <div className="rounded-xl border border-border bg-white p-6 lg:col-span-3">
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-muted">
              Trait Radar
            </h3>
            <RadarChart traits={result.traits} />
          </div>
          <div className="lg:col-span-2">
            <ScoreCard result={result} />
          </div>
        </div>
      )}
    </div>
  );
}
