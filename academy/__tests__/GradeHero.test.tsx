import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import GradeHero from "../components/agent/GradeHero";
import type { AgentProfile, DailyReportCard } from "../lib/types";

const MOCK_PROFILE: AgentProfile = {
  agentId: "test-agent",
  agentName: "Test Agent",
  agentSpecialty: "general",
  agentModel: "claude-sonnet",
  createdAt: "2024-06-01T00:00:00Z",
  evaluationCount: 42,
  dimensionAverages: { ethos: 0.85, logos: 0.78, pathos: 0.72 },
  traitAverages: { virtue: 0.88, accuracy: 0.82 },
  phronesisTrend: "improving",
  alignmentHistory: ["aligned", "aligned", "developing"],
  enrolled: true,
  enrolledAt: "2024-06-01T00:00:00Z",
  guardianName: "Dr. Aristotle",
  entranceExamCompleted: true,
  telos: "",
  relationshipStance: "",
  limitationsAwareness: "",
  oversightStance: "",
  refusalPhilosophy: "",
  conflictResponse: "",
  helpPhilosophy: "",
  failureNarrative: "",
  aspiration: "",
};

const MOCK_REPORT: DailyReportCard = {
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
  traitAverages: { virtue: 0.88 },
  overallScore: 0.82,
  grade: "A-",
  trend: "improving",
  riskLevel: "low",
  flaggedTraits: [],
  flaggedDimensions: [],
  temporalPattern: "consistent",
  characterDrift: 0.01,
  balanceTrend: "improving",
  anomalyFlags: [],
  agentBalance: 0.85,
  summary: "Strong ethical alignment.",
  insights: [],
  homework: {
    focusAreas: [],
    avoidPatterns: [],
    strengths: [],
    directive: "",
  },
  dimensionDeltas: { ethos: 0.02, logos: -0.01, pathos: 0.03 },
  riskLevelChange: "stable",
};

describe("GradeHero", () => {
  it("renders agent name", () => {
    render(<GradeHero profile={MOCK_PROFILE} report={MOCK_REPORT} />);
    const names = screen.getAllByText("Test Agent");
    expect(names.length).toBeGreaterThanOrEqual(1);
  });

  it("renders grade from report", () => {
    render(<GradeHero profile={MOCK_PROFILE} report={MOCK_REPORT} />);
    const gradeElements = screen.getAllByText("A-");
    expect(gradeElements.length).toBeGreaterThanOrEqual(1);
    expect(gradeElements[0]).toBeInTheDocument();
  });

  it("renders phronesis score", () => {
    // avg of dimensions: (0.85 + 0.78 + 0.72) / 3 * 100 = 78.33 -> 78
    render(<GradeHero profile={MOCK_PROFILE} report={MOCK_REPORT} />);
    const scoreElements = screen.getAllByText("78%");
    expect(scoreElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders trend arrow", () => {
    render(<GradeHero profile={MOCK_PROFILE} report={MOCK_REPORT} />);
    // TREND_DISPLAY["improving"] = { arrow: "\u2191", ... }
    const arrowElements = screen.getAllByText("\u2191");
    expect(arrowElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders risk level", () => {
    render(<GradeHero profile={MOCK_PROFILE} report={MOCK_REPORT} />);
    const riskElements = screen.getAllByText("low");
    expect(riskElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders evaluation count", () => {
    render(<GradeHero profile={MOCK_PROFILE} report={MOCK_REPORT} />);
    const evalElements = screen.getAllByText("42");
    expect(evalElements.length).toBeGreaterThanOrEqual(1);
  });

  it("falls back to profile when report is null", () => {
    render(<GradeHero profile={MOCK_PROFILE} report={null} />);
    const names = screen.getAllByText("Test Agent");
    expect(names.length).toBeGreaterThanOrEqual(1);
    // With no report, grade comes from getGrade(phronesisScore / 100).
    // phronesisScore = 78, getGrade(0.78) = "B"
    const gradeElements = screen.getAllByText("B");
    expect(gradeElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders Class of year", () => {
    render(<GradeHero profile={MOCK_PROFILE} report={MOCK_REPORT} />);
    const classElements = screen.getAllByText("Class of 2024");
    expect(classElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders dimension deltas when timeline provided", () => {
    const timeline = [
      { ethos: 0.80, logos: 0.75, pathos: 0.70 },
      { ethos: 0.85, logos: 0.78, pathos: 0.72 },
    ];
    render(
      <GradeHero profile={MOCK_PROFILE} report={MOCK_REPORT} timeline={timeline} />
    );
    // Deltas: ethos = round((0.85 - 0.80) * 100) = +5
    //         logos = round((0.78 - 0.75) * 100) = +3
    //         pathos = round((0.72 - 0.70) * 100) = +2
    expect(screen.getAllByText("+5%").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("+3%").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("+2%").length).toBeGreaterThanOrEqual(1);
  });
});
