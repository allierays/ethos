import EvaluatorPanel from "../components/EvaluatorPanel";
import AgentTimeline from "../components/AgentTimeline";
import CohortPanel from "../components/CohortPanel";

export default function Home() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted">
          Score AI agent messages for honesty, accuracy, and intent.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <Card title="Evaluate" description="Score an incoming message across 12 behavioral traits." />
        <Card title="Reflect" description="Examine your own agent's outgoing messages over time." />
        <Card title="Insights" description="Opus-powered behavioral analysis and pattern detection." />
      </div>

      <EvaluatorPanel />

      <AgentTimeline />

      <CohortPanel />
    </div>
  );
}

function Card({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl border border-border bg-white p-5">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-muted">{description}</p>
    </div>
  );
}
