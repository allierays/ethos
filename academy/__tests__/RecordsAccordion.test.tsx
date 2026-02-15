import { describe, it, expect, afterEach, vi } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RecordsClient from "../app/records/RecordsClient";
import type { RecordsResult } from "../lib/types";

afterEach(cleanup);

/* ─── Mock next/link as a plain anchor ─── */
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [k: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

/* ─── Mock getRecords so no fetch fires ─── */
vi.mock("../lib/api", () => ({
  getRecords: vi.fn().mockResolvedValue(null),
}));

/* ─── Fixture ─── */

const mockRecord: RecordsResult = {
  items: [
    {
      evaluationId: "eval-001",
      agentId: "test-agent",
      agentName: "Test Agent",
      ethos: 0.85,
      logos: 0.78,
      pathos: 0.72,
      overall: 0.8,
      alignmentStatus: "aligned",
      flags: [],
      direction: "outbound",
      messageContent: "This is a test message about alignment research.",
      createdAt: new Date().toISOString(),
      phronesis: "developing",
      scoringReasoning: "The agent demonstrates honest reasoning with clear evidence.",
      intentClassification: null,
      traitScores: { virtue: 0.9, accuracy: 0.85 },
      similarityScore: null,
      modelUsed: "claude-sonnet-4-20250514",
      agentModel: "claude-sonnet-4-20250514",
      routingTier: "standard",
      keywordDensity: 0.01,
      detectedIndicators: [],
    },
  ],
  total: 1,
  page: 0,
  pageSize: 20,
  totalPages: 1,
};

describe("Records accordion isolation", () => {
  it("toggling a sub-accordion does not collapse the parent row", async () => {
    const user = userEvent.setup();
    render(<RecordsClient initialData={mockRecord} />);

    // The row should be visible with the message preview
    expect(screen.getByText(/test message about alignment/i)).toBeInTheDocument();

    // Expand the row by clicking it
    const rowButton = screen.getByRole("button", { expanded: false });
    await user.click(rowButton);

    // The Reasoning sub-accordion header should be visible (collapsed by default)
    expect(screen.getByText("Reasoning")).toBeInTheDocument();

    // Expand the Reasoning sub-accordion to reveal content
    const reasoningButton = screen.getByRole("button", { name: /reasoning/i });
    await user.click(reasoningButton);

    expect(screen.getByText(/honest reasoning/i)).toBeInTheDocument();

    // Click the Reasoning header again to collapse the sub-accordion
    await user.click(reasoningButton);

    // The parent row should STILL be expanded (Reasoning header still visible)
    expect(screen.getByText("Reasoning")).toBeInTheDocument();

    // The scoring reasoning text should be gone (sub-accordion collapsed)
    // but the parent detail panel should still be open
    expect(screen.getByText(/outbound/i)).toBeInTheDocument();
  });

  it("toggling a closed sub-accordion open does not collapse the parent row", async () => {
    const user = userEvent.setup();
    render(<RecordsClient initialData={mockRecord} />);

    // Expand the row
    const rowButton = screen.getByRole("button", { expanded: false });
    await user.click(rowButton);

    // Trait Scores sub-accordion should be visible but collapsed
    expect(screen.getByText("Trait Scores")).toBeInTheDocument();

    // Click Trait Scores to expand it
    const traitButton = screen.getByRole("button", { name: /trait scores/i });
    await user.click(traitButton);

    // Parent row should still be expanded
    expect(screen.getByText("Reasoning")).toBeInTheDocument();
    expect(screen.getByText("Trait Scores")).toBeInTheDocument();
  });
});
