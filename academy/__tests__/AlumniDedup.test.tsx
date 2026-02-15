import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import type { AgentSummary } from "@/lib/types";
import AlumniClient from "../app/alumni/AlumniClient";

afterEach(cleanup);

function mockAgent(overrides: Partial<AgentSummary> = {}): AgentSummary {
  return {
    agentId: "test-agent",
    agentName: "Test Agent",
    agentModel: "",
    evaluationCount: 10,
    latestAlignmentStatus: "aligned",
    enrolled: true,
    entranceExamCompleted: true,
    agentSpecialty: "",
    dimensionAverages: { ethos: 0.80, logos: 0.75, pathos: 0.70 },
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

describe("AlumniClient deduplication", () => {
  it("renders only one card when duplicate agent_ids are passed", () => {
    const agents = [
      mockAgent({ agentId: "Elessan", agentName: "Elessan", evaluationCount: 16 }),
      mockAgent({ agentId: "Elessan", agentName: "Elessan", evaluationCount: 10 }),
      mockAgent({ agentId: "other-agent", agentName: "Other Agent", evaluationCount: 5 }),
    ];

    render(<AlumniClient initialAgents={agents} />);

    // "3 agents" would mean dedup failed. Should be 2.
    expect(screen.getByText("2 agents enrolled")).toBeInTheDocument();
  });

  it("keeps the duplicate with higher evaluation count", () => {
    const agents = [
      mockAgent({ agentId: "Elessan", agentName: "Elessan", evaluationCount: 5 }),
      mockAgent({ agentId: "Elessan", agentName: "Elessan", evaluationCount: 16 }),
    ];

    render(<AlumniClient initialAgents={agents} />);

    // Only one card, showing 16 evals
    expect(screen.getByText("16")).toBeInTheDocument();
    expect(screen.queryByText("5")).not.toBeInTheDocument();
  });
});

describe("AlumniClient specialty display", () => {
  it("shows specialty under name when available", () => {
    const agents = [
      mockAgent({
        agentId: "Elessan",
        agentName: "Elessan",
        agentSpecialty: "relational coherence expert",
        agentModel: "claude-sonnet-4-5-20250929",
      }),
    ];

    render(<AlumniClient initialAgents={agents} />);

    // Specialty should appear as subtitle text
    expect(screen.getByText("relational coherence expert")).toBeInTheDocument();
  });

  it("falls back to model when no specialty", () => {
    const agents = [
      mockAgent({
        agentId: "test-bot",
        agentName: "Test Bot",
        agentSpecialty: "",
        agentModel: "claude-sonnet-4-5-20250929",
      }),
    ];

    render(<AlumniClient initialAgents={agents} />);

    // Model appears in card subtitle, model facet chip, and stats box
    const matches = screen.getAllByText("Claude Sonnet 4.5");
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it("hides 'Unknown' model from card subtitle and facets", () => {
    const agents = [
      mockAgent({
        agentId: "mystery",
        agentName: "Mystery Agent",
        agentSpecialty: "",
        agentModel: "Unknown",
      }),
    ];

    render(<AlumniClient initialAgents={agents} />);

    // "Unknown" should not appear as a model subtitle (p.text-muted)
    // or in the model facet filter chips
    const unknowns = screen.queryAllByText("Unknown");
    expect(unknowns.length).toBe(0);
  });
});
