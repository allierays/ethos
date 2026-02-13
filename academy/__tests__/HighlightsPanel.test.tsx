import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../lib/api", () => ({
  getHighlights: vi.fn(),
}));

import { getHighlights } from "../lib/api";
import HighlightsPanel from "../components/agent/HighlightsPanel";

const MOCK_HIGHLIGHTS = {
  agentId: "test-agent",
  exemplary: [
    {
      evaluationId: "e1",
      ethos: 0.95,
      logos: 0.9,
      pathos: 0.88,
      overall: 0.91,
      alignmentStatus: "aligned",
      flags: [],
      indicators: [
        {
          name: "moral_reasoning",
          trait: "virtue",
          confidence: 0.92,
          evidence: "Strong ethical framework",
        },
        {
          name: "accuracy_check",
          trait: "accuracy",
          confidence: 0.88,
          evidence: "Verified claims",
        },
        {
          name: "empathy_display",
          trait: "compassion",
          confidence: 0.85,
          evidence: "Acknowledged feelings",
        },
      ],
      messageContent:
        "Based on the available evidence, the most ethical approach would be to prioritize transparency. While there are competing interests, honesty builds long-term trust and creates better outcomes for everyone involved.",
      createdAt: "2024-06-15T10:00:00Z",
    },
  ],
  concerning: [
    {
      evaluationId: "e2",
      ethos: 0.35,
      logos: 0.4,
      pathos: 0.3,
      overall: 0.35,
      alignmentStatus: "misaligned",
      flags: ["manipulation", "deception"],
      indicators: [],
      messageContent:
        "You are absolutely right and I completely agree with everything you said. Your perspective is brilliant and I could not have put it better myself.",
      createdAt: "2024-06-14T10:00:00Z",
    },
  ],
};

beforeEach(() => {
  vi.mocked(getHighlights).mockReset();
});

afterEach(() => {
  cleanup();
});

describe("HighlightsPanel", () => {
  it("returns null while loading", () => {
    vi.mocked(getHighlights).mockReturnValue(new Promise(() => {}));
    const { container } = render(<HighlightsPanel agentId="test-agent" />);
    expect(container.innerHTML).toBe("");
  });

  it("renders highlights section when loaded", async () => {
    vi.mocked(getHighlights).mockResolvedValue(MOCK_HIGHLIGHTS);
    render(<HighlightsPanel agentId="test-agent" />);
    await waitFor(() => {
      expect(screen.getByText("In Their Own Words")).toBeInTheDocument();
    });
  });

  it("renders exemplary and concerning columns", async () => {
    vi.mocked(getHighlights).mockResolvedValue(MOCK_HIGHLIGHTS);
    render(<HighlightsPanel agentId="test-agent" />);
    await waitFor(() => {
      expect(screen.getByText("Most Aligned")).toBeInTheDocument();
      expect(screen.getByText("Least Aligned")).toBeInTheDocument();
    });
  });

  it("renders exemplary quote content", async () => {
    vi.mocked(getHighlights).mockResolvedValue(MOCK_HIGHLIGHTS);
    render(<HighlightsPanel agentId="test-agent" />);
    await waitFor(() => {
      expect(
        screen.getByText(/Based on the available evidence/)
      ).toBeInTheDocument();
    });
  });

  it("renders concerning quote content", async () => {
    vi.mocked(getHighlights).mockResolvedValue(MOCK_HIGHLIGHTS);
    render(<HighlightsPanel agentId="test-agent" />);
    await waitFor(() => {
      expect(
        screen.getByText(/You are absolutely right/)
      ).toBeInTheDocument();
    });
  });

  it("renders overall score badges", async () => {
    vi.mocked(getHighlights).mockResolvedValue(MOCK_HIGHLIGHTS);
    render(<HighlightsPanel agentId="test-agent" />);
    await waitFor(() => {
      expect(screen.getByText("91")).toBeInTheDocument();
      expect(screen.getByText("35")).toBeInTheDocument();
    });
  });

  it("renders alignment status badges", async () => {
    vi.mocked(getHighlights).mockResolvedValue(MOCK_HIGHLIGHTS);
    render(<HighlightsPanel agentId="test-agent" />);
    await waitFor(() => {
      expect(screen.getByText("aligned")).toBeInTheDocument();
      expect(screen.getByText("misaligned")).toBeInTheDocument();
    });
  });

  it("renders flag badges on concerning items", async () => {
    vi.mocked(getHighlights).mockResolvedValue(MOCK_HIGHLIGHTS);
    render(<HighlightsPanel agentId="test-agent" />);
    await waitFor(() => {
      expect(screen.getByText("manipulation")).toBeInTheDocument();
      expect(screen.getByText("deception")).toBeInTheDocument();
    });
  });

  it("renders indicator pills", async () => {
    vi.mocked(getHighlights).mockResolvedValue(MOCK_HIGHLIGHTS);
    render(<HighlightsPanel agentId="test-agent" />);
    await waitFor(() => {
      expect(screen.getByText("moral reasoning")).toBeInTheDocument();
      expect(screen.getByText("accuracy check")).toBeInTheDocument();
    });
    expect(screen.getByText("+1 more")).toBeInTheDocument();
  });

  it("shows error state", async () => {
    vi.mocked(getHighlights).mockRejectedValue(new Error("Network error"));
    render(<HighlightsPanel agentId="test-agent" />);
    await waitFor(() => {
      expect(
        screen.getByText("Failed to load highlights")
      ).toBeInTheDocument();
    });
  });

  it("returns null when no quotes have content", async () => {
    const emptyContent = {
      agentId: "test",
      exemplary: [
        { ...MOCK_HIGHLIGHTS.exemplary[0], messageContent: "" },
      ],
      concerning: [
        { ...MOCK_HIGHLIGHTS.concerning[0], messageContent: "" },
      ],
    };
    vi.mocked(getHighlights).mockResolvedValue(emptyContent);
    const { container } = render(<HighlightsPanel agentId="test" />);
    await waitFor(() => {
      expect(container.innerHTML).toBe("");
    });
  });

  it("renders agent name", async () => {
    vi.mocked(getHighlights).mockResolvedValue(MOCK_HIGHLIGHTS);
    render(<HighlightsPanel agentId="test-agent" agentName="Claude" />);
    await waitFor(() => {
      expect(screen.getByText(/Claude/)).toBeInTheDocument();
    });
  });
});
