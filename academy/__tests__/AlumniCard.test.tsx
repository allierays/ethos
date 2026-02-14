import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { spectrumLabel } from "@/lib/colors";
import type { AgentSummary } from "@/lib/types";

// Mock the API so alumni page doesn't make real requests
vi.mock("../lib/api", () => ({
  getAgents: vi.fn(),
}));

import { getAgents } from "../lib/api";
import AlumniPage from "../app/alumni/page";

afterEach(cleanup);

/**
 * Build a mock AgentSummary with the given overrides.
 * The key field here is latestAlignmentStatus: the raw discrete
 * value from Neo4j (e.g. "violation", "misaligned"). The alumni
 * card must NOT display this raw status. It must compute the
 * spectrum label from dimensionAverages instead.
 */
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
  it("displays spectrum label derived from dimension averages, not raw alignment status", async () => {
    // Agent has "violation" as latestAlignmentStatus but 82% avg score.
    // The card must show "Sound" (matching the report page), not "Violation".
    const agent = mockAgent({
      latestAlignmentStatus: "violation",
      dimensionAverages: { ethos: 0.85, logos: 0.85, pathos: 0.76 },
    });
    const avg = (0.85 + 0.85 + 0.76) / 3;
    const expected = spectrumLabel(avg); // "Sound"

    vi.mocked(getAgents).mockResolvedValue([agent]);
    render(<AlumniPage />);

    await waitFor(() => {
      // Spectrum label appears (on card badge + possibly filter chip)
      expect(screen.getAllByText(expected).length).toBeGreaterThanOrEqual(1);
    });

    // "Violation" must NOT appear anywhere
    expect(screen.queryByText("Violation")).not.toBeInTheDocument();
  });

  it("never displays raw alignment status values on cards", async () => {
    // An agent with "misaligned" status but 65% avg should show "Developing"
    const agent = mockAgent({
      agentId: "edge-case",
      agentName: "Edge Case",
      latestAlignmentStatus: "misaligned",
      dimensionAverages: { ethos: 0.70, logos: 0.60, pathos: 0.65 },
    });

    vi.mocked(getAgents).mockResolvedValue([agent]);
    render(<AlumniPage />);

    await waitFor(() => {
      // Name appears on both front and back of card
      expect(screen.getAllByText("Edge Case").length).toBeGreaterThanOrEqual(1);
    });

    // Raw alignment values must not appear
    expect(screen.queryByText("Misaligned")).not.toBeInTheDocument();
    expect(screen.queryByText("misaligned")).not.toBeInTheDocument();
    expect(screen.queryByText("Aligned")).not.toBeInTheDocument();
    expect(screen.queryByText("Drifting")).not.toBeInTheDocument();
    expect(screen.queryByText("Violation")).not.toBeInTheDocument();

    // Spectrum label: (0.70+0.60+0.65)/3 = 0.65 -> "Developing"
    expect(screen.getAllByText("Developing").length).toBeGreaterThanOrEqual(1);
  });

  it("spectrum label matches report page computation for all tiers", async () => {
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
      vi.mocked(getAgents).mockResolvedValue([
        mockAgent({
          agentId: `agent-${expected}`,
          agentName: `Agent ${expected}`,
          latestAlignmentStatus: rawStatus,
          dimensionAverages: dims,
        }),
      ]);

      render(<AlumniPage />);

      await waitFor(() => {
        expect(screen.getAllByText(expected).length).toBeGreaterThanOrEqual(1);
      });
    }
  });
});
