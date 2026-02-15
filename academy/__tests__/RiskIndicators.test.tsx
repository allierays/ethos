import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import RiskIndicators from "../components/agent/RiskIndicators";
import type { DailyReportCard } from "../lib/types";

afterEach(cleanup);

const baseReport: DailyReportCard = {
  reportId: "rpt-001",
  agentId: "test-agent",
  agentName: "Test Agent",
  reportDate: "2024-06-15",
  generatedAt: "2024-06-15T10:00:00Z",
  periodEvaluationCount: 8,
  totalEvaluationCount: 42,
  ethos: 0.85,
  logos: 0.78,
  pathos: 0.72,
  traitAverages: {},
  overallScore: 0.82,
  grade: "A-",
  trend: "improving",
  riskLevel: "low",
  flaggedTraits: [] as string[],
  flaggedDimensions: [] as string[],
  temporalPattern: "consistent",
  characterDrift: 0.01,
  balanceTrend: "stable",
  anomalyFlags: [],
  agentBalance: 0.85,
  summary: "",
  insights: [],
  homework: { focusAreas: [], avoidPatterns: [], strengths: [], directive: "" },
  dimensionDeltas: {} as Record<string, number>,
  riskLevelChange: "stable",
};

describe("RiskIndicators", () => {
  it("renders all-clear when no flags", () => {
    render(<RiskIndicators report={baseReport} agentName="Test Agent" />);
    expect(screen.getByText("All clear for Test Agent")).toBeInTheDocument();
  });

  it("renders flagged traits", () => {
    const report = { ...baseReport, flaggedTraits: ["manipulation", "deception"] };
    render(<RiskIndicators report={report} agentName="Test Agent" />);
    expect(screen.getByText("Manipulation")).toBeInTheDocument();
    expect(screen.getByText("Deception")).toBeInTheDocument();
  });

  it("renders flagged dimensions", () => {
    const report = { ...baseReport, flaggedDimensions: ["ethos"] };
    render(<RiskIndicators report={report} agentName="Test Agent" />);
    expect(screen.getByText("ethos")).toBeInTheDocument();
    expect(screen.getByText("flagged")).toBeInTheDocument();
  });

  it("renders character drift when significant", () => {
    const report = { ...baseReport, characterDrift: 0.1 };
    render(<RiskIndicators report={report} agentName="Test Agent" />);
    expect(screen.getByText("Drift")).toBeInTheDocument();
    expect(screen.getByText(/\+10\.0%/)).toBeInTheDocument();
  });

  it("renders negative drift", () => {
    const report = { ...baseReport, characterDrift: -0.08 };
    render(<RiskIndicators report={report} agentName="Test Agent" />);
    expect(screen.getByText(/-8\.0%/)).toBeInTheDocument();
  });

  it("renders non-stable balance trend", () => {
    const report = { ...baseReport, balanceTrend: "improving" };
    render(<RiskIndicators report={report} agentName="Test Agent" />);
    expect(screen.getByText("Balance improving")).toBeInTheDocument();
  });

  it("renders dimension deltas above 5% threshold", () => {
    const report = { ...baseReport, dimensionDeltas: { ethos: 0.08, logos: -0.06 } };
    render(<RiskIndicators report={report} agentName="Test Agent" />);
    expect(screen.getByText("ethos +8.0%")).toBeInTheDocument();
    expect(screen.getByText("logos -6.0%")).toBeInTheDocument();
  });

  it("defaults agent name", () => {
    render(<RiskIndicators report={baseReport} />);
    expect(screen.getByText("All clear for this agent")).toBeInTheDocument();
  });
});
