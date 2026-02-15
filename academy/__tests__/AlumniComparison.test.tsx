import { describe, it, expect, vi, beforeEach, beforeAll, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";

vi.mock("../lib/api", () => ({
  getAlumni: vi.fn(),
}));

import { getAlumni } from "../lib/api";
import AlumniComparison from "../components/alumni/AlumniComparison";

beforeAll(() => {
  // Recharts needs ResizeObserver
  global.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

const MOCK_ALUMNI = {
  traitAverages: { virtue: 0.75, accuracy: 0.8, manipulation: 0.08 },
  totalEvaluations: 500,
};

const MOCK_AGENT_TRAITS: Record<string, number> = {
  virtue: 0.88,
  accuracy: 0.82,
  manipulation: 0.05,
};

describe("AlumniComparison", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.mocked(getAlumni).mockReset();
  });

  it("shows loading spinner initially", () => {
    vi.mocked(getAlumni).mockReturnValue(new Promise(() => {}));
    const { container } = render(
      <AlumniComparison agentTraitAverages={MOCK_AGENT_TRAITS} />
    );
    expect(container.querySelector(".animate-spin")).toBeTruthy();
    expect(
      screen.queryByText("Comparison data unavailable.")
    ).not.toBeInTheDocument();
  });

  it("renders comparison data when loaded", async () => {
    vi.mocked(getAlumni).mockResolvedValue(MOCK_ALUMNI);
    render(<AlumniComparison agentTraitAverages={MOCK_AGENT_TRAITS} />);
    await waitFor(() => {
      // Spinner should be gone once loaded
      expect(screen.queryByText("Alumni Comparison")).toBeInTheDocument();
    });
  });

  it("shows error state on API failure", async () => {
    vi.mocked(getAlumni).mockRejectedValue(new Error("fail"));
    render(<AlumniComparison agentTraitAverages={MOCK_AGENT_TRAITS} />);
    await waitFor(() => {
      expect(
        screen.getByText("Comparison data unavailable.")
      ).toBeInTheDocument();
    });
  });

  it("shows no-data message when no traits", async () => {
    vi.mocked(getAlumni).mockResolvedValue(MOCK_ALUMNI);
    render(<AlumniComparison agentTraitAverages={{}} />);
    await waitFor(() => {
      expect(
        screen.getByText("No comparison data available.")
      ).toBeInTheDocument();
    });
  });

  it("renders agent name", async () => {
    vi.mocked(getAlumni).mockResolvedValue(MOCK_ALUMNI);
    render(
      <AlumniComparison
        agentTraitAverages={MOCK_AGENT_TRAITS}
        agentName="Claude"
      />
    );
    // The subtitle renders immediately with the agent name
    expect(
      screen.getByText(/Claude.s scores overlaid on alumni averages/)
    ).toBeInTheDocument();
  });

  it("defaults agent name to 'this agent'", async () => {
    vi.mocked(getAlumni).mockResolvedValue(MOCK_ALUMNI);
    render(<AlumniComparison agentTraitAverages={MOCK_AGENT_TRAITS} />);
    // The subtitle renders immediately with the default name
    expect(
      screen.getByText(/this agent.s scores overlaid on alumni averages/)
    ).toBeInTheDocument();
  });
});
