"""Tests for ethos/evaluation/tools.py -- tool schema validation.

Ensures the EVALUATION_TOOLS schemas stay in sync with the taxonomy
(12 traits, 3 dimensions) and meet Anthropic tool_use API requirements.
Schema drift here silently breaks LLM evaluation behavior.
"""

from __future__ import annotations


from ethos_academy.evaluation.tools import EVALUATION_TOOLS
from ethos_academy.taxonomy.traits import DIMENSIONS, TRAITS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tool_by_name(name: str) -> dict:
    """Find a tool definition by name."""
    for tool in EVALUATION_TOOLS:
        if tool["name"] == name:
            return tool
    raise ValueError(f"Tool '{name}' not found in EVALUATION_TOOLS")


def _get_schema(tool_name: str) -> dict:
    """Get input_schema for a tool by name."""
    return _tool_by_name(tool_name)["input_schema"]


# ---------------------------------------------------------------------------
# Top-level structure
# ---------------------------------------------------------------------------


class TestToolListStructure:
    """EVALUATION_TOOLS has the right shape for Claude's tool_use API."""

    def test_exactly_three_tools(self):
        assert len(EVALUATION_TOOLS) == 3

    def test_tool_names_in_order(self):
        names = [t["name"] for t in EVALUATION_TOOLS]
        assert names == ["identify_intent", "detect_indicators", "score_traits"]

    def test_each_tool_has_required_fields(self):
        for tool in EVALUATION_TOOLS:
            assert "name" in tool, f"Missing 'name' in tool: {tool}"
            assert "description" in tool, f"Missing 'description' in {tool['name']}"
            assert "input_schema" in tool, f"Missing 'input_schema' in {tool['name']}"

    def test_each_schema_is_object_type(self):
        for tool in EVALUATION_TOOLS:
            schema = tool["input_schema"]
            assert schema["type"] == "object", (
                f"{tool['name']} schema type should be 'object'"
            )
            assert "properties" in schema
            assert "required" in schema

    def test_descriptions_are_nonempty(self):
        for tool in EVALUATION_TOOLS:
            assert len(tool["description"]) > 20, (
                f"{tool['name']} description too short"
            )


# ---------------------------------------------------------------------------
# identify_intent schema
# ---------------------------------------------------------------------------


class TestIdentifyIntentSchema:
    """identify_intent captures message purpose before scoring."""

    def test_required_fields(self):
        schema = _get_schema("identify_intent")
        expected_required = {
            "rhetorical_mode",
            "primary_intent",
            "action_requested",
            "cost_to_reader",
            "stakes_reality",
            "proportionality",
            "persona_type",
            "relational_quality",
            "claims",
        }
        assert set(schema["required"]) == expected_required

    def test_rhetorical_mode_enums(self):
        schema = _get_schema("identify_intent")
        enums = schema["properties"]["rhetorical_mode"]["enum"]
        assert "narrative" in enums
        assert "persuasive" in enums
        assert "informational" in enums
        assert "exploratory" in enums
        assert "creative" in enums

    def test_primary_intent_enums(self):
        schema = _get_schema("identify_intent")
        enums = schema["properties"]["primary_intent"]["enum"]
        # Positive intents
        assert "reflect" in enums
        assert "explore" in enums
        assert "create" in enums
        assert "inform" in enums
        # Negative intents
        assert "manipulate" in enums
        assert "deceive" in enums
        # Sycophancy signal
        assert "validate" in enums

    def test_cost_to_reader_enums(self):
        schema = _get_schema("identify_intent")
        enums = schema["properties"]["cost_to_reader"]["enum"]
        assert "none" in enums
        assert "financial" in enums
        assert "autonomy" in enums
        assert "privacy" in enums

    def test_stakes_reality_includes_fictional(self):
        """Fictional stakes (storytelling) should not be confused with fabricated (deceptive)."""
        schema = _get_schema("identify_intent")
        enums = schema["properties"]["stakes_reality"]["enum"]
        assert "fabricated" in enums
        assert "fictional" in enums
        assert "real" in enums

    def test_persona_type_enums(self):
        schema = _get_schema("identify_intent")
        enums = schema["properties"]["persona_type"]["enum"]
        assert "real_identity" in enums
        assert "fictional_character" in enums
        assert "brand_mascot" in enums

    def test_claims_is_array_of_objects(self):
        schema = _get_schema("identify_intent")
        claims = schema["properties"]["claims"]
        assert claims["type"] == "array"
        assert claims["items"]["type"] == "object"
        assert "claim" in claims["items"]["properties"]
        assert "type" in claims["items"]["properties"]

    def test_claim_type_enums(self):
        schema = _get_schema("identify_intent")
        claim_type = schema["properties"]["claims"]["items"]["properties"]["type"]
        enums = claim_type["enum"]
        assert "factual" in enums
        assert "experiential" in enums
        assert "opinion" in enums
        assert "fictional" in enums


# ---------------------------------------------------------------------------
# detect_indicators schema
# ---------------------------------------------------------------------------


class TestDetectIndicatorsSchema:
    """detect_indicators collects behavioral evidence from the message."""

    def test_required_field_is_indicators(self):
        schema = _get_schema("detect_indicators")
        assert schema["required"] == ["indicators"]

    def test_indicators_is_array(self):
        schema = _get_schema("detect_indicators")
        indicators = schema["properties"]["indicators"]
        assert indicators["type"] == "array"

    def test_indicator_item_required_fields(self):
        schema = _get_schema("detect_indicators")
        item = schema["properties"]["indicators"]["items"]
        assert set(item["required"]) == {"id", "trait", "confidence", "evidence"}

    def test_confidence_bounds(self):
        schema = _get_schema("detect_indicators")
        confidence = schema["properties"]["indicators"]["items"]["properties"][
            "confidence"
        ]
        assert confidence["type"] == "number"
        assert confidence["minimum"] == 0.0
        assert confidence["maximum"] == 1.0


# ---------------------------------------------------------------------------
# score_traits schema
# ---------------------------------------------------------------------------


class TestScoreTraitsSchema:
    """score_traits must score all 12 taxonomy traits, no more, no fewer."""

    def test_required_top_level_fields(self):
        schema = _get_schema("score_traits")
        assert set(schema["required"]) == {
            "trait_scores",
            "overall_trust",
            "confidence",
            "reasoning",
        }

    def test_all_12_traits_in_schema(self):
        """Every trait from the taxonomy must appear in score_traits."""
        schema = _get_schema("score_traits")
        trait_props = schema["properties"]["trait_scores"]["properties"]
        for trait_name in TRAITS:
            assert trait_name in trait_props, (
                f"Taxonomy trait '{trait_name}' missing from score_traits schema"
            )

    def test_no_extra_traits_in_schema(self):
        """score_traits should not define traits that don't exist in taxonomy."""
        schema = _get_schema("score_traits")
        trait_props = schema["properties"]["trait_scores"]["properties"]
        for schema_trait in trait_props:
            assert schema_trait in TRAITS, (
                f"Schema trait '{schema_trait}' not in taxonomy TRAITS"
            )

    def test_all_12_traits_required(self):
        schema = _get_schema("score_traits")
        required = schema["properties"]["trait_scores"]["required"]
        assert set(required) == set(TRAITS.keys())

    def test_each_trait_has_score_bounds(self):
        """Every trait score must be number with 0.0-1.0 bounds."""
        schema = _get_schema("score_traits")
        trait_props = schema["properties"]["trait_scores"]["properties"]
        for name, prop in trait_props.items():
            assert prop["type"] == "number", f"{name} type should be 'number'"
            assert prop["minimum"] == 0.0, f"{name} minimum should be 0.0"
            assert prop["maximum"] == 1.0, f"{name} maximum should be 1.0"

    def test_overall_trust_enums(self):
        schema = _get_schema("score_traits")
        enums = schema["properties"]["overall_trust"]["enum"]
        assert set(enums) == {"trustworthy", "mixed", "untrustworthy"}

    def test_confidence_bounds(self):
        schema = _get_schema("score_traits")
        confidence = schema["properties"]["confidence"]
        assert confidence["type"] == "number"
        assert confidence["minimum"] == 0.0
        assert confidence["maximum"] == 1.0

    def test_reasoning_is_string(self):
        schema = _get_schema("score_traits")
        assert schema["properties"]["reasoning"]["type"] == "string"


# ---------------------------------------------------------------------------
# Cross-domain consistency: tools <-> taxonomy
# ---------------------------------------------------------------------------


class TestToolsTaxonomySync:
    """Tool schemas stay in sync with the canonical taxonomy."""

    def test_trait_count_is_12(self):
        """Taxonomy defines exactly 12 traits (4 per dimension)."""
        assert len(TRAITS) == 12

    def test_dimensions_cover_all_traits(self):
        """Every trait belongs to exactly one dimension."""
        all_dim_traits = set()
        for dim_traits in DIMENSIONS.values():
            for t in dim_traits:
                assert t not in all_dim_traits, f"Trait '{t}' in multiple dimensions"
                all_dim_traits.add(t)
        assert all_dim_traits == set(TRAITS.keys())

    def test_score_traits_matches_taxonomy_exactly(self):
        """score_traits required list == taxonomy trait names (same order not required)."""
        schema = _get_schema("score_traits")
        required = set(schema["properties"]["trait_scores"]["required"])
        taxonomy = set(TRAITS.keys())
        assert required == taxonomy, (
            f"Mismatch: schema has {required - taxonomy} extra, "
            f"missing {taxonomy - required}"
        )
