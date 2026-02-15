import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import HomeworkSection from "../components/agent/HomeworkSection";
import type { Homework } from "../lib/types";

const MOCK_HOMEWORK: Homework = {
  focusAreas: [
    {
      trait: "directness",
      priority: "high",
      currentScore: 0.6,
      targetScore: 0.85,
      instruction: "Be more direct in responses",
      exampleFlagged: "I think maybe possibly...",
      exampleImproved: "Based on the evidence...",
      systemPromptAddition: "Be direct and concise. Avoid hedging language.",
    },
  ],
  avoidPatterns: ["excessive_hedging: Using too many qualifiers"],
  strengths: ["ethical_reasoning: Consistent moral framework"],
  directive: "Focus on clarity and directness.",
};

const EMPTY_HOMEWORK: Homework = {
  focusAreas: [],
  avoidPatterns: [],
  strengths: [],
  directive: "",
};

describe("HomeworkSection", () => {
  it("renders agent name in heading", () => {
    render(<HomeworkSection homework={MOCK_HOMEWORK} agentName="Claude" agentId="claude-1" />);
    // GlossaryTerm wraps "Homework" in a span, splitting the text across elements
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading.textContent).toContain("Claude");
    expect(heading.textContent).toContain("Homework");
  });

  it("renders directive", () => {
    render(<HomeworkSection homework={MOCK_HOMEWORK} agentName="Claude" agentId="claude-1" />);
    const directives = screen.getAllByText("Focus on clarity and directness.");
    expect(directives.length).toBeGreaterThanOrEqual(1);
  });

  it("renders strengths section", () => {
    render(<HomeworkSection homework={MOCK_HOMEWORK} agentName="Claude" agentId="claude-1" />);
    const headings = screen.getAllByText("Strengths");
    expect(headings.length).toBeGreaterThanOrEqual(1);
    const descriptions = screen.getAllByText("Consistent moral framework");
    expect(descriptions.length).toBeGreaterThanOrEqual(1);
  });

  it("renders watch-for section", () => {
    render(<HomeworkSection homework={MOCK_HOMEWORK} agentName="Claude" agentId="claude-1" />);
    const headings = screen.getAllByText("Watch for");
    expect(headings.length).toBeGreaterThanOrEqual(1);
    const descriptions = screen.getAllByText("Using too many qualifiers");
    expect(descriptions.length).toBeGreaterThanOrEqual(1);
  });

  it("renders focus areas and reveals context on expand", () => {
    render(<HomeworkSection homework={MOCK_HOMEWORK} agentName="Claude" agentId="claude-1" />);
    // System prompt rule is always visible on focus cards
    const rules = screen.getAllByText("Be direct and concise. Avoid hedging language.");
    expect(rules.length).toBeGreaterThanOrEqual(1);
    // Instruction and before/after are behind the expandable Context section
    const contextBtns = screen.getAllByRole("button", { name: /Context/i });
    fireEvent.click(contextBtns[0]);
    expect(screen.getAllByText("Be more direct in responses").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Before").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("After").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/I think maybe possibly/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Based on the evidence/).length).toBeGreaterThanOrEqual(1);
  });

  it("renders practice loop with agent ID", () => {
    render(<HomeworkSection homework={MOCK_HOMEWORK} agentName="Claude" agentId="claude-1" />);
    const labels = screen.getAllByText("Install your practice skill");
    expect(labels.length).toBeGreaterThanOrEqual(1);
    // Code snippets contain the agent ID
    const codeSnippets = screen.getAllByText(/claude-1/);
    expect(codeSnippets.length).toBeGreaterThanOrEqual(1);
  });

  it("renders how it works steps", () => {
    render(<HomeworkSection homework={MOCK_HOMEWORK} agentName="Claude" agentId="claude-1" />);
    const labels = screen.getAllByText("How it works");
    expect(labels.length).toBeGreaterThanOrEqual(1);
  });

  it("shows no homework message when empty", () => {
    render(<HomeworkSection homework={EMPTY_HOMEWORK} agentName="Claude" agentId="claude-1" />);
    expect(
      screen.getByText("No homework assigned for Claude.")
    ).toBeInTheDocument();
  });

  it("defaults agent name to 'this agent'", () => {
    render(<HomeworkSection homework={EMPTY_HOMEWORK} agentId="claude-1" />);
    expect(
      screen.getByText("No homework assigned for this agent.")
    ).toBeInTheDocument();
  });
});
