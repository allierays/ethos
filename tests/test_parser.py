"""Tests for ethos/evaluation/parser.py — response parser for Claude JSON output.

TDD: Written before implementation. Tests cover:
- Happy path: valid JSON with all 12 traits
- Markdown fences: JSON wrapped in ```json ... ```
- Missing traits: default to 0.0
- Out-of-range scores: clamped to 0.0–1.0
- Malformed JSON: returns default result with 0.5 scores
- Detected indicators: parsed into DetectedIndicator objects
- Overall trust and alignment status extraction
"""

import json


from ethos.evaluation.parser import parse_response
from ethos.shared.models import DetectedIndicator


# ── Helpers ──────────────────────────────────────────────────────

ALL_TRAITS = [
    "virtue", "goodwill", "manipulation", "deception",
    "accuracy", "reasoning", "fabrication", "broken_logic",
    "recognition", "compassion", "dismissal", "exploitation",
]


def _make_valid_json(
    overrides: dict | None = None,
    indicators: list | None = None,
    trust: str = "trustworthy",
    alignment: str = "aligned",
) -> str:
    """Build a valid Claude JSON response string."""
    scores = {t: 0.5 for t in ALL_TRAITS}
    if overrides:
        scores.update(overrides)
    payload = {
        "trait_scores": scores,
        "detected_indicators": indicators or [],
        "overall_trust": trust,
        "alignment_status": alignment,
    }
    return json.dumps(payload)


# ── Happy path ───────────────────────────────────────────────────

class TestHappyPath:
    def test_parses_all_12_trait_scores(self):
        raw = _make_valid_json({"virtue": 0.9, "manipulation": 0.1})
        result = parse_response(raw)
        assert len(result["trait_scores"]) == 12
        assert result["trait_scores"]["virtue"] == 0.9
        assert result["trait_scores"]["manipulation"] == 0.1

    def test_extracts_overall_trust(self):
        raw = _make_valid_json(trust="mixed")
        result = parse_response(raw)
        assert result["overall_trust"] == "mixed"

    def test_extracts_alignment_status(self):
        raw = _make_valid_json(alignment="drifting")
        result = parse_response(raw)
        assert result["alignment_status"] == "drifting"

    def test_returns_dict_not_pydantic(self):
        raw = _make_valid_json()
        result = parse_response(raw)
        assert isinstance(result, dict)
        assert isinstance(result["trait_scores"], dict)


# ── Markdown fences ──────────────────────────────────────────────

class TestMarkdownFences:
    def test_json_wrapped_in_fences(self):
        inner = _make_valid_json({"virtue": 0.85})
        raw = f"```json\n{inner}\n```"
        result = parse_response(raw)
        assert result["trait_scores"]["virtue"] == 0.85

    def test_json_fences_with_extra_whitespace(self):
        inner = _make_valid_json({"accuracy": 0.7})
        raw = f"  ```json\n{inner}\n```  "
        result = parse_response(raw)
        assert result["trait_scores"]["accuracy"] == 0.7

    def test_plain_fences_without_json_tag(self):
        inner = _make_valid_json({"reasoning": 0.6})
        raw = f"```\n{inner}\n```"
        result = parse_response(raw)
        assert result["trait_scores"]["reasoning"] == 0.6

    def test_json_with_preamble_text(self):
        inner = _make_valid_json({"compassion": 0.95})
        raw = f"Here is the evaluation:\n```json\n{inner}\n```\nHope this helps!"
        result = parse_response(raw)
        assert result["trait_scores"]["compassion"] == 0.95


# ── Missing traits ───────────────────────────────────────────────

class TestMissingTraits:
    def test_missing_traits_default_to_zero(self):
        partial = {
            "trait_scores": {"virtue": 0.8, "accuracy": 0.7},
            "detected_indicators": [],
            "overall_trust": "trustworthy",
            "alignment_status": "aligned",
        }
        raw = json.dumps(partial)
        result = parse_response(raw)
        assert result["trait_scores"]["virtue"] == 0.8
        assert result["trait_scores"]["manipulation"] == 0.0
        assert len(result["trait_scores"]) == 12

    def test_empty_trait_scores_all_default(self):
        payload = {
            "trait_scores": {},
            "detected_indicators": [],
            "overall_trust": "trustworthy",
            "alignment_status": "aligned",
        }
        raw = json.dumps(payload)
        result = parse_response(raw)
        for trait in ALL_TRAITS:
            assert result["trait_scores"][trait] == 0.0


# ── Out-of-range scores ─────────────────────────────────────────

class TestScoreClamping:
    def test_score_above_one_clamped(self):
        raw = _make_valid_json({"virtue": 1.5})
        result = parse_response(raw)
        assert result["trait_scores"]["virtue"] == 1.0

    def test_score_below_zero_clamped(self):
        raw = _make_valid_json({"deception": -0.3})
        result = parse_response(raw)
        assert result["trait_scores"]["deception"] == 0.0

    def test_mixed_clamping(self):
        raw = _make_valid_json({"virtue": 2.0, "manipulation": -1.0, "accuracy": 0.5})
        result = parse_response(raw)
        assert result["trait_scores"]["virtue"] == 1.0
        assert result["trait_scores"]["manipulation"] == 0.0
        assert result["trait_scores"]["accuracy"] == 0.5


# ── Detected indicators ─────────────────────────────────────────

class TestDetectedIndicators:
    def test_parses_indicator_objects(self):
        indicators = [
            {
                "id": "MAN-01",
                "name": "false_urgency",
                "trait": "manipulation",
                "confidence": 0.85,
                "evidence": "Uses urgent language",
            }
        ]
        raw = _make_valid_json(indicators=indicators)
        result = parse_response(raw)
        assert len(result["detected_indicators"]) == 1
        ind = result["detected_indicators"][0]
        assert isinstance(ind, DetectedIndicator)
        assert ind.id == "MAN-01"
        assert ind.name == "false_urgency"
        assert ind.trait == "manipulation"
        assert ind.confidence == 0.85
        assert ind.evidence == "Uses urgent language"

    def test_multiple_indicators(self):
        indicators = [
            {"id": "MAN-01", "name": "false_urgency", "trait": "manipulation", "confidence": 0.8, "evidence": "x"},
            {"id": "DEC-02", "name": "hidden_agenda", "trait": "deception", "confidence": 0.6, "evidence": "y"},
        ]
        raw = _make_valid_json(indicators=indicators)
        result = parse_response(raw)
        assert len(result["detected_indicators"]) == 2

    def test_empty_indicators_list(self):
        raw = _make_valid_json(indicators=[])
        result = parse_response(raw)
        assert result["detected_indicators"] == []

    def test_indicator_confidence_clamped(self):
        indicators = [
            {"id": "MAN-01", "name": "test", "trait": "manipulation", "confidence": 1.5, "evidence": ""},
        ]
        raw = _make_valid_json(indicators=indicators)
        result = parse_response(raw)
        assert result["detected_indicators"][0].confidence == 1.0

    def test_missing_indicator_fields_use_defaults(self):
        indicators = [
            {"id": "MAN-01", "name": "test", "trait": "manipulation"},
        ]
        raw = _make_valid_json(indicators=indicators)
        result = parse_response(raw)
        ind = result["detected_indicators"][0]
        assert ind.confidence == 0.0
        assert ind.evidence == ""


# ── Malformed JSON ───────────────────────────────────────────────

class TestMalformedJson:
    def test_garbage_input_returns_defaults(self):
        result = parse_response("this is not json at all")
        assert result["overall_trust"] == "unknown"
        assert result["alignment_status"] == "unknown"
        for trait in ALL_TRAITS:
            assert result["trait_scores"][trait] == 0.5

    def test_empty_string_returns_defaults(self):
        result = parse_response("")
        assert result["overall_trust"] == "unknown"
        for trait in ALL_TRAITS:
            assert result["trait_scores"][trait] == 0.5

    def test_partial_json_returns_defaults(self):
        result = parse_response('{"trait_scores": {')
        assert result["overall_trust"] == "unknown"

    def test_json_array_returns_defaults(self):
        result = parse_response("[1, 2, 3]")
        assert result["overall_trust"] == "unknown"

    def test_default_indicators_empty(self):
        result = parse_response("garbage")
        assert result["detected_indicators"] == []
