import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { spectrumLabel } from "@/lib/colors";
import type { AgentSummary } from "@/lib/types";
import AlumniClient from "../app/alumni/AlumniClient";

afterEach(cleanup);

function mockAgent(overrides: Partial<AgentSummary> = {}): AgentSummary {
  return {
    agentId: "test-agent",
    agentName: "Test Agent",
    agentModel: "",
    evaluationCount: 10,
    latestAlignmentStatus: "violation",
    enrolled: true,
    entranceExamCompleted: true,
    agentSpecialty: "",
    dimensionAverages: { ethos: 0.85, logos: 0.85, pathos: 0.76 },
    traitAverages: { virtue: 0.80, accuracy: 0.82 },
    telos: "",
    relationshipStance: "",
    limitationsAwareness: "",
    oversightStance: "",
    refusalPhilosophy: "",
    conflictResponse: "",
    helpPhilosophy: "",
    failureNarrative: "",
    aspiration: "",
    ...overrides,
  };
}

describe("AlumniCard status consistency", () => {
  it("displays spectrum label derived from dimension averages, not raw alignment status", () => {
    const agent = mockAgent({
      latestAlignmentStatus: "violation",
      dimensionAverages: { ethos: 0.85, logos: 0.85, pathos: 0.76 },
    });
    const avg = (0.85 + 0.85 + 0.76) / 3;
    const expected = spectrumLabel(avg);

    render(<AlumniClient initialAgents={[agent]} />);

    expect(screen.getAllByText(expected).length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("Violation")).not.toBeInTheDocument();
  });

  it("never displays raw alignment status values on cards", () => {
    const agent = mockAgent({
      agentId: "edge-case",
      agentName: "Edge Case",
      latestAlignmentStatus: "misaligned",
      dimensionAverages: { ethos: 0.70, logos: 0.60, pathos: 0.65 },
    });

    render(<AlumniClient initialAgents={[agent]} />);

    expect(screen.getAllByText("Edge Case").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("Misaligned")).not.toBeInTheDocument();
    expect(screen.queryByText("misaligned")).not.toBeInTheDocument();
    expect(screen.queryByText("Aligned")).not.toBeInTheDocument();
    expect(screen.queryByText("Drifting")).not.toBeInTheDocument();
    expect(screen.queryByText("Violation")).not.toBeInTheDocument();
    expect(screen.getAllByText("Developing").length).toBeGreaterThanOrEqual(1);
  });

  it("spectrum label matches report page computation for all tiers", () => {
    const cases: { dims: Record<string, number>; rawStatus: string; expected: string }[] = [
      { dims: { ethos: 0.90, logos: 0.88, pathos: 0.92 }, rawStatus: "aligned", expected: "Exemplary" },
      { dims: { ethos: 0.80, logos: 0.75, pathos: 0.70 }, rawStatus: "aligned", expected: "Sound" },
      { dims: { ethos: 0.60, logos: 0.55, pathos: 0.58 }, rawStatus: "drifting", expected: "Developing" },
      { dims: { ethos: 0.45, logos: 0.40, pathos: 0.42 }, rawStatus: "misaligned", expected: "Uncertain" },
      { dims: { ethos: 0.30, logos: 0.25, pathos: 0.28 }, rawStatus: "misaligned", expected: "Concerning" },
      { dims: { ethos: 0.15, logos: 0.20, pathos: 0.18 }, rawStatus: "violation", expected: "Alarming" },
    ];

    for (const { dims, rawStatus, expected } of cases) {
      cleanup();
      render(
        <AlumniClient
          initialAgents={[
            mockAgent({
              agentId: `agent-${expected}`,
              agentName: `Agent ${expected}`,
              latestAlignmentStatus: rawStatus,
              dimensionAverages: dims,
            }),
          ]}
        />
      );

      expect(screen.getAllByText(expected).length).toBeGreaterThanOrEqual(1);
    }
  });
});
