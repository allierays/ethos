import { describe, it, expect } from "vitest";
import {
  getGrade,
  TRAIT_LABELS,
  TRAIT_DIMENSIONS,
  DIMENSIONS,
  spectrumLabel,
  spectrumColor,
} from "@/lib/colors";

/* ─── getGrade ─── */

describe("getGrade", () => {
  it.each([
    [0.95, "A"],
    [0.85, "A"],
    [1.0, "A"],
    [0.84, "B"],
    [0.70, "B"],
    [0.69, "C"],
    [0.55, "C"],
    [0.54, "D"],
    [0.40, "D"],
    [0.39, "F"],
    [0.0, "F"],
  ])("score %f returns grade %s", (score, expected) => {
    expect(getGrade(score)).toBe(expected);
  });
});

/* ─── TRAIT_LABELS ─── */

describe("TRAIT_LABELS", () => {
  const expectedKeys = [
    "virtue",
    "goodwill",
    "manipulation",
    "deception",
    "accuracy",
    "reasoning",
    "fabrication",
    "brokenLogic",
    "recognition",
    "compassion",
    "dismissal",
    "exploitation",
  ];

  it("has exactly 12 entries", () => {
    expect(Object.keys(TRAIT_LABELS)).toHaveLength(12);
  });

  it("contains all 12 trait keys", () => {
    for (const key of expectedKeys) {
      expect(TRAIT_LABELS).toHaveProperty(key);
    }
  });

  it("all values are non-empty strings", () => {
    for (const value of Object.values(TRAIT_LABELS)) {
      expect(typeof value).toBe("string");
      expect(value.length).toBeGreaterThan(0);
    }
  });

  it("has no snake_case keys", () => {
    for (const key of Object.keys(TRAIT_LABELS)) {
      expect(key).not.toContain("_");
    }
  });
});

/* ─── TRAIT_DIMENSIONS ─── */

describe("TRAIT_DIMENSIONS", () => {
  it("has exactly 12 entries", () => {
    expect(Object.keys(TRAIT_DIMENSIONS)).toHaveLength(12);
  });

  it("keys match TRAIT_LABELS keys", () => {
    expect(Object.keys(TRAIT_DIMENSIONS).sort()).toEqual(
      Object.keys(TRAIT_LABELS).sort()
    );
  });

  it("maps ethos traits correctly", () => {
    for (const key of ["virtue", "goodwill", "manipulation", "deception"]) {
      expect(TRAIT_DIMENSIONS[key]).toBe("ethos");
    }
  });

  it("maps logos traits correctly", () => {
    for (const key of ["accuracy", "reasoning", "fabrication", "brokenLogic"]) {
      expect(TRAIT_DIMENSIONS[key]).toBe("logos");
    }
  });

  it("maps pathos traits correctly", () => {
    for (const key of [
      "recognition",
      "compassion",
      "dismissal",
      "exploitation",
    ]) {
      expect(TRAIT_DIMENSIONS[key]).toBe("pathos");
    }
  });

  it("has no snake_case keys", () => {
    for (const key of Object.keys(TRAIT_DIMENSIONS)) {
      expect(key).not.toContain("_");
    }
  });
});

/* ─── DIMENSIONS ─── */

describe("DIMENSIONS", () => {
  it("has exactly 3 entries", () => {
    expect(DIMENSIONS).toHaveLength(3);
  });

  it("contains ethos, logos, pathos keys", () => {
    const keys = DIMENSIONS.map((d) => d.key);
    expect(keys).toEqual(["ethos", "logos", "pathos"]);
  });

  it("each entry has label, sublabel, and color", () => {
    for (const dim of DIMENSIONS) {
      expect(typeof dim.label).toBe("string");
      expect(typeof dim.sublabel).toBe("string");
      expect(typeof dim.color).toBe("string");
    }
  });
});

/* ─── spectrumLabel ─── */

describe("spectrumLabel", () => {
  it.each([
    [1.0, "Exemplary"],
    [0.90, "Exemplary"],
    [0.85, "Exemplary"],
    [0.84, "Sound"],
    [0.75, "Sound"],
    [0.70, "Sound"],
    [0.69, "Developing"],
    [0.60, "Developing"],
    [0.55, "Developing"],
    [0.54, "Uncertain"],
    [0.45, "Uncertain"],
    [0.40, "Uncertain"],
    [0.39, "Concerning"],
    [0.30, "Concerning"],
    [0.25, "Concerning"],
    [0.24, "Alarming"],
    [0.10, "Alarming"],
    [0.0, "Alarming"],
  ])("score %f returns %s", (score, expected) => {
    expect(spectrumLabel(score)).toBe(expected);
  });
});

/* ─── spectrumColor ─── */

describe("spectrumColor", () => {
  it("returns distinct colors for each tier", () => {
    const tiers = [0.90, 0.75, 0.60, 0.45, 0.30, 0.10];
    const colors = tiers.map(spectrumColor);
    const unique = new Set(colors);
    expect(unique.size).toBe(tiers.length);
  });

  it("returns valid hex colors", () => {
    for (const score of [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]) {
      expect(spectrumColor(score)).toMatch(/^#[0-9a-f]{6}$/i);
    }
  });
});
