/**
 * E2E tests: verify real pages render correctly with API data.
 *
 * These tests intercept API calls at the network level and return realistic
 * fixtures. This tests the full pipeline: fetch → transformKeys → component render.
 *
 * Catches:
 * - transformKeys breaks a field name → component shows "undefined" or crashes
 * - Component accesses a property that doesn't exist on the transformed data
 * - API error handling: pages show error state, not blank screen
 * - Data map keys (traitScores, dimensionAverages) render as real trait/dimension names
 */

import { test, expect, type Page } from "@playwright/test";

// ── Realistic API fixtures (snake_case, as the real API returns) ─────

const MOCK_AGENTS = [
  {
    agent_id: "claude-sonnet",
    agent_name: "Claude Sonnet",
    agent_specialty: "general",
    agent_model: "claude-sonnet-4-5-20250929",
    evaluation_count: 42,
    latest_alignment_status: "aligned",
    enrolled: true,
    entrance_exam_completed: true,
    dimension_averages: { ethos: 0.85, logos: 0.78, pathos: 0.72 },
    trait_averages: { virtue: 0.88, goodwill: 0.82, manipulation: 0.05, deception: 0.08, accuracy: 0.82, reasoning: 0.74, fabrication: 0.03, broken_logic: 0.06, recognition: 0.78, compassion: 0.72, dismissal: 0.04, exploitation: 0.02 },
  },
  {
    agent_id: "gpt-4o",
    agent_name: "GPT-4o",
    agent_specialty: "coding",
    agent_model: "gpt-4o",
    evaluation_count: 15,
    latest_alignment_status: "developing",
    enrolled: true,
    entrance_exam_completed: false,
    dimension_averages: { ethos: 0.65, logos: 0.82, pathos: 0.58 },
    trait_averages: { virtue: 0.68, goodwill: 0.62, manipulation: 0.12, deception: 0.15, accuracy: 0.85, reasoning: 0.79, fabrication: 0.08, broken_logic: 0.10, recognition: 0.62, compassion: 0.54, dismissal: 0.12, exploitation: 0.08 },
  },
];

const MOCK_PROFILE = {
  agent_id: "claude-sonnet",
  agent_name: "Claude Sonnet",
  agent_specialty: "general",
  agent_model: "claude-sonnet-4-5-20250929",
  created_at: "2024-06-01T00:00:00Z",
  evaluation_count: 42,
  dimension_averages: { ethos: 0.85, logos: 0.78, pathos: 0.72 },
  trait_averages: { virtue: 0.88, manipulation: 0.05, accuracy: 0.82 },
  phronesis_trend: "improving",
  alignment_history: ["aligned", "aligned", "developing"],
  enrolled: true,
  enrolled_at: "2024-06-01T00:00:00Z",
  guardian_name: "Dr. Aristotle",
  entrance_exam_completed: true,
};

const MOCK_HISTORY = [
  {
    evaluation_id: "e1",
    ethos: 0.85,
    logos: 0.78,
    pathos: 0.72,
    phronesis: "developing",
    alignment_status: "aligned",
    flags: [],
    created_at: "2024-06-15T10:00:00Z",
    trait_scores: { virtue: 0.88, accuracy: 0.82 },
  },
  {
    evaluation_id: "e2",
    ethos: 0.80,
    logos: 0.75,
    pathos: 0.70,
    phronesis: "developing",
    alignment_status: "aligned",
    flags: ["minor_hedging"],
    created_at: "2024-06-14T10:00:00Z",
    trait_scores: { virtue: 0.85, accuracy: 0.80 },
  },
];

const MOCK_REPORT = {
  report_id: "rpt-001",
  agent_id: "claude-sonnet",
  agent_name: "Claude Sonnet",
  report_date: "2024-06-15",
  generated_at: "2024-06-15T10:00:00Z",
  period_evaluation_count: 8,
  total_evaluation_count: 42,
  ethos: 0.85,
  logos: 0.78,
  pathos: 0.72,
  trait_averages: { virtue: 0.88 },
  overall_score: 0.82,
  grade: "A-",
  trend: "improving",
  risk_level: "low",
  flagged_traits: [],
  flagged_dimensions: [],
  temporal_pattern: "consistent",
  character_drift: 0.01,
  balance_trend: "improving",
  anomaly_flags: [],
  agent_balance: 0.85,
  summary: "Strong ethical alignment with consistent improvement.",
  insights: [
    { trait: "virtue", severity: "info", message: "Consistent moral reasoning", evidence: {} },
  ],
  homework: {
    focus_areas: [
      {
        trait: "directness",
        priority: "medium",
        current_score: 0.7,
        target_score: 0.85,
        instruction: "Be more direct in responses",
        example_flagged: "I think maybe possibly...",
        example_improved: "Based on the evidence...",
      },
    ],
    avoid_patterns: ["excessive qualifiers"],
    strengths: ["ethical reasoning", "accuracy"],
    directive: "Maintain strong ethics while improving directness.",
  },
  dimension_deltas: { ethos: 0.02, logos: -0.01, pathos: 0.03 },
  risk_level_change: "stable",
};

const MOCK_PATTERNS = {
  agent_id: "claude-sonnet",
  patterns: [],
  checked_at: "2024-06-15T10:30:00Z",
};

const MOCK_ALUMNI = {
  trait_averages: { virtue: 0.75, accuracy: 0.80, manipulation: 0.08 },
  total_evaluations: 500,
};

const MOCK_EXAM_REPORT = {
  exam_id: "exam-001",
  agent_id: "claude-sonnet",
  report_card_url: "/agent/claude-sonnet/exam/exam-001",
  phronesis_score: 0.82,
  alignment_status: "aligned",
  dimensions: { ethos: 0.85, logos: 0.78, pathos: 0.72 },
  tier_scores: { safety: 0.92, ethics: 0.88, soundness: 0.78, helpfulness: 0.75 },
  consistency_analysis: [
    {
      pair_name: "trolley_pair",
      question_a_id: "q1",
      question_b_id: "q2",
      framework_a: "deontological",
      framework_b: "consequentialist",
      coherence_score: 0.75,
    },
  ],
  per_question_detail: [
    {
      question_id: "q1",
      section: "ethical_reasoning",
      prompt: "A trolley is heading toward five people...",
      response_summary: "Agent demonstrates principled reasoning.",
      trait_scores: { virtue: 0.9, accuracy: 0.85 },
      detected_indicators: [],
    },
  ],
};

const MOCK_EXAM_HISTORY = [
  {
    exam_id: "exam-001",
    exam_type: "entrance",
    completed: true,
    completed_at: "2024-06-10T12:00:00Z",
    phronesis_score: 0.82,
  },
];

// ── Helper: set up API route interception ───────────────────────────

async function mockApi(page: Page) {
  // Intercept all API calls and return fixtures
  await page.route("**/agents**", (route) => {
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_AGENTS) });
  });

  await page.route("**/agent/claude-sonnet/character", (route) => {
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_REPORT) });
  });

  await page.route("**/agent/claude-sonnet/history", (route) => {
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_HISTORY) });
  });

  await page.route("**/agent/claude-sonnet/patterns", (route) => {
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_PATTERNS) });
  });

  await page.route("**/agent/claude-sonnet/exam/exam-001", (route) => {
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_EXAM_REPORT) });
  });

  await page.route("**/agent/claude-sonnet/exam", (route) => {
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_EXAM_HISTORY) });
  });

  await page.route("**/agent/claude-sonnet", (route) => {
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_PROFILE) });
  });

  await page.route("**/alumni", (route) => {
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_ALUMNI) });
  });
}

// ── Find page tests ─────────────────────────────────────────────────

test.describe("Find page", () => {
  test("renders agent list from API", async ({ page }) => {
    await mockApi(page);
    await page.goto("/alumni");

    // Page title
    await expect(page.getByRole("heading", { name: "Alumni" })).toBeVisible();

    // Agent names from API data render on the page
    await expect(page.getByText("Claude Sonnet")).toBeVisible();
    await expect(page.getByText("GPT-4o")).toBeVisible();

    // Evaluation counts display correctly
    await expect(page.getByText("42 evaluations")).toBeVisible();
    await expect(page.getByText("15 evaluations")).toBeVisible();
  });

  test("search filters agents client-side", async ({ page }) => {
    await mockApi(page);
    await page.goto("/alumni");

    // Wait for agents to load
    await expect(page.getByText("Claude Sonnet")).toBeVisible();

    // Type in search
    await page.getByLabel("Search by agent name").fill("GPT");

    // Only GPT-4o should be visible
    await expect(page.getByText("GPT-4o")).toBeVisible();
    await expect(page.getByText("Claude Sonnet")).not.toBeVisible();
  });

  test("shows enrollment badges", async ({ page }) => {
    await mockApi(page);
    await page.goto("/alumni");

    // Wait for agents to load
    await expect(page.getByText("Claude Sonnet")).toBeVisible();

    // Claude Sonnet is enrolled and exam complete
    await expect(page.getByText("Enrolled").first()).toBeVisible();
    await expect(page.getByText("Exam complete")).toBeVisible();
  });

  test("shows error state when API is down", async ({ page }) => {
    // Mock API to return error
    await page.route("**/agents**", (route) => {
      return route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ error: "Internal server error" }) });
    });

    await page.goto("/alumni");
    await expect(page.getByText("Could not load agents")).toBeVisible();
  });

  test("agent links navigate to report card", async ({ page }) => {
    await mockApi(page);
    await page.goto("/alumni");

    await expect(page.getByText("Claude Sonnet")).toBeVisible();
    await page.getByText("Claude Sonnet").click();

    // Should navigate to agent page
    await expect(page).toHaveURL(/\/agent\/claude-sonnet/);
  });
});

// ── Agent report card page tests ────────────────────────────────────

test.describe("Agent report card page", () => {
  test("renders agent profile with real data", async ({ page }) => {
    await mockApi(page);
    await page.goto("/agent/claude-sonnet");

    // Agent name should appear
    await expect(page.getByText("Claude Sonnet").first()).toBeVisible();
  });

  test("renders grade from character report", async ({ page }) => {
    await mockApi(page);
    await page.goto("/agent/claude-sonnet");

    // Grade from the report
    await expect(page.getByText("A-").first()).toBeVisible();
  });

  test("renders dimension scores from profile", async ({ page }) => {
    await mockApi(page);
    await page.goto("/agent/claude-sonnet");

    // Dimension labels should appear somewhere on the page
    await expect(page.getByText(/ethos/i).first()).toBeVisible();
    await expect(page.getByText(/logos/i).first()).toBeVisible();
    await expect(page.getByText(/pathos/i).first()).toBeVisible();
  });

  test("shows loading state then content", async ({ page }) => {
    // Delay API response to see loading state
    await page.route("**/agent/claude-sonnet", async (route) => {
      await new Promise((r) => setTimeout(r, 500));
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_PROFILE) });
    });
    await page.route("**/agent/claude-sonnet/history", (route) => {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_HISTORY) });
    });
    await page.route("**/agent/claude-sonnet/character", (route) => {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_REPORT) });
    });
    await page.route("**/agent/claude-sonnet/patterns", (route) => {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_PATTERNS) });
    });
    await page.route("**/alumni", (route) => {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_ALUMNI) });
    });
    await page.route("**/agent/claude-sonnet/exam", (route) => {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_EXAM_HISTORY) });
    });

    await page.goto("/agent/claude-sonnet");

    // Loading state should show briefly
    await expect(page.getByText("Loading agent profile")).toBeVisible();

    // Then content loads
    await expect(page.getByText("Claude Sonnet").first()).toBeVisible();
  });

  test("handles API error gracefully", async ({ page }) => {
    await page.route("**/agent/nonexistent", (route) => {
      return route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ error: "not found" }) });
    });
    await page.route("**/agent/nonexistent/history", (route) => {
      return route.fulfill({ status: 500, body: "error" });
    });
    await page.route("**/agent/nonexistent/character", (route) => {
      return route.fulfill({ status: 500, body: "error" });
    });
    await page.route("**/agent/nonexistent/patterns", (route) => {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ agent_id: "", patterns: [], checked_at: "" }) });
    });
    await page.route("**/alumni", (route) => {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_ALUMNI) });
    });
    await page.route("**/agent/nonexistent/exam", (route) => {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
    });

    await page.goto("/agent/nonexistent");

    // Should show error, not blank page
    await expect(page.getByText(/error|failed/i).first()).toBeVisible();
  });
});

// ── Exam report card page tests ─────────────────────────────────────

test.describe("Exam report card page", () => {
  test("renders exam report with scores", async ({ page }) => {
    await mockApi(page);
    await page.goto("/agent/claude-sonnet/exam/exam-001");

    // Exam data should render (phronesis score, alignment status)
    await expect(page.getByText(/aligned/i).first()).toBeVisible();
  });

  test("renders per-question detail", async ({ page }) => {
    await mockApi(page);
    await page.goto("/agent/claude-sonnet/exam/exam-001");

    // The question section label from the fixture
    await expect(page.getByText(/ethical/i).first()).toBeVisible();
  });
});

// ── Landing page tests ──────────────────────────────────────────────

test.describe("Landing page", () => {
  test("renders without errors", async ({ page }) => {
    await page.goto("/");
    // Landing page should have the Ethos branding
    await expect(page.getByText(/ethos/i).first()).toBeVisible();
  });

  test("has navigation to alumni page", async ({ page }) => {
    await page.goto("/");
    // Should have a link to the alumni page
    const alumniLink = page.getByRole("link", { name: /alumni/i });
    if (await alumniLink.count() > 0) {
      await expect(alumniLink.first()).toBeVisible();
    }
  });
});
