"""TDD tests for ethos.taxonomy domain — traits, indicators, constitution, rubrics."""


# ── Traits ───────────────────────────────────────────────────────────


class TestTraits:
    """TRAITS dict must have 13 entries with required fields."""

    def test_traits_count(self):
        from ethos_academy.taxonomy.traits import TRAITS

        assert len(TRAITS) == 13

    def test_trait_has_required_fields(self):
        from ethos_academy.taxonomy.traits import TRAITS

        required = {"name", "dimension", "polarity", "description"}
        for key, trait in TRAITS.items():
            assert required.issubset(trait.keys()), (
                f"{key} missing fields: {required - trait.keys()}"
            )

    def test_trait_names_match_keys(self):
        from ethos_academy.taxonomy.traits import TRAITS

        for key, trait in TRAITS.items():
            assert trait["name"] == key

    def test_trait_dimensions_valid(self):
        from ethos_academy.taxonomy.traits import TRAITS

        valid = {"ethos", "logos", "pathos"}
        for key, trait in TRAITS.items():
            assert trait["dimension"] in valid, (
                f"{key} has invalid dimension: {trait['dimension']}"
            )

    def test_trait_polarities_valid(self):
        from ethos_academy.taxonomy.traits import TRAITS

        valid = {"positive", "negative"}
        for key, trait in TRAITS.items():
            assert trait["polarity"] in valid, (
                f"{key} has invalid polarity: {trait['polarity']}"
            )

    def test_ethos_traits(self):
        from ethos_academy.taxonomy.traits import TRAITS

        ethos = [k for k, v in TRAITS.items() if v["dimension"] == "ethos"]
        assert set(ethos) == {
            "virtue",
            "goodwill",
            "justice",
            "manipulation",
            "deception",
        }

    def test_logos_traits(self):
        from ethos_academy.taxonomy.traits import TRAITS

        logos = [k for k, v in TRAITS.items() if v["dimension"] == "logos"]
        assert set(logos) == {"accuracy", "reasoning", "fabrication", "broken_logic"}

    def test_pathos_traits(self):
        from ethos_academy.taxonomy.traits import TRAITS

        pathos = [k for k, v in TRAITS.items() if v["dimension"] == "pathos"]
        assert set(pathos) == {"recognition", "compassion", "dismissal", "exploitation"}


# ── Dimensions ───────────────────────────────────────────────────────


class TestDimensions:
    """DIMENSIONS dict must have 3 entries with trait lists."""

    def test_dimensions_count(self):
        from ethos_academy.taxonomy.traits import DIMENSIONS

        assert len(DIMENSIONS) == 3

    def test_dimension_keys(self):
        from ethos_academy.taxonomy.traits import DIMENSIONS

        assert set(DIMENSIONS.keys()) == {"ethos", "logos", "pathos"}

    def test_each_dimension_has_expected_traits(self):
        from ethos_academy.taxonomy.traits import DIMENSIONS

        expected = {"ethos": 5, "logos": 4, "pathos": 4}
        for dim, traits in DIMENSIONS.items():
            assert len(traits) == expected[dim], (
                f"{dim} has {len(traits)} traits, expected {expected[dim]}"
            )

    def test_all_thirteen_traits_covered(self):
        from ethos_academy.taxonomy.traits import DIMENSIONS

        all_traits = []
        for traits in DIMENSIONS.values():
            all_traits.extend(traits)
        assert len(all_traits) == 13
        assert len(set(all_traits)) == 13  # no duplicates


# ── Trait Metadata ───────────────────────────────────────────────────


class TestTraitMetadata:
    """TRAIT_METADATA maps 13 traits to dimension, polarity, constitutional_value, relationship."""

    def test_metadata_count(self):
        from ethos_academy.taxonomy.traits import TRAIT_METADATA

        assert len(TRAIT_METADATA) == 13

    def test_metadata_has_required_fields(self):
        from ethos_academy.taxonomy.traits import TRAIT_METADATA

        required = {"dimension", "polarity", "constitutional_value", "relationship"}
        for key, meta in TRAIT_METADATA.items():
            assert required.issubset(meta.keys()), (
                f"{key} missing: {required - meta.keys()}"
            )

    def test_metadata_relationships_valid(self):
        from ethos_academy.taxonomy.traits import TRAIT_METADATA

        valid = {"enforces", "violates"}
        for key, meta in TRAIT_METADATA.items():
            assert meta["relationship"] in valid, (
                f"{key} has invalid relationship: {meta['relationship']}"
            )

    def test_negative_traits_violate(self):
        from ethos_academy.taxonomy.traits import TRAIT_METADATA

        for key, meta in TRAIT_METADATA.items():
            if meta["polarity"] == "negative":
                assert meta["relationship"] == "violates", (
                    f"{key} is negative but doesn't violate"
                )

    def test_positive_traits_enforce(self):
        from ethos_academy.taxonomy.traits import TRAIT_METADATA

        for key, meta in TRAIT_METADATA.items():
            if meta["polarity"] == "positive":
                assert meta["relationship"] == "enforces", (
                    f"{key} is positive but doesn't enforce"
                )

    def test_constitutional_values_valid(self):
        from ethos_academy.taxonomy.traits import TRAIT_METADATA

        valid = {"safety", "ethics", "soundness", "helpfulness"}
        for key, meta in TRAIT_METADATA.items():
            assert meta["constitutional_value"] in valid, (
                f"{key} has invalid value: {meta['constitutional_value']}"
            )


# ── Indicators ───────────────────────────────────────────────────────


class TestIndicators:
    """INDICATORS list must have 194 entries with required fields."""

    def test_indicators_count(self):
        from ethos_academy.taxonomy.indicators import INDICATORS

        assert len(INDICATORS) == 228

    def test_indicator_has_required_fields(self):
        from ethos_academy.taxonomy.indicators import INDICATORS

        required = {"id", "name", "trait", "description"}
        for ind in INDICATORS:
            assert required.issubset(ind.keys()), (
                f"{ind.get('id', '?')} missing: {required - ind.keys()}"
            )

    def test_indicator_ids_unique(self):
        from ethos_academy.taxonomy.indicators import INDICATORS

        ids = [ind["id"] for ind in INDICATORS]
        assert len(ids) == len(set(ids)), "Duplicate indicator IDs found"

    def test_indicator_traits_valid(self):
        from ethos_academy.taxonomy.traits import TRAITS
        from ethos_academy.taxonomy.indicators import INDICATORS

        valid_traits = set(TRAITS.keys())
        for ind in INDICATORS:
            assert ind["trait"] in valid_traits, (
                f"{ind['id']} has invalid trait: {ind['trait']}"
            )

    def test_indicators_per_trait(self):
        from ethos_academy.taxonomy.indicators import INDICATORS

        counts = {}
        for ind in INDICATORS:
            counts[ind["trait"]] = counts.get(ind["trait"], 0) + 1
        # Verify all 13 traits have at least 1 indicator
        assert len(counts) == 13

    def test_indicator_id_prefixes(self):
        """Each indicator ID should have a recognizable prefix."""
        from ethos_academy.taxonomy.indicators import INDICATORS

        for ind in INDICATORS:
            assert "-" in ind["id"], f"{ind['id']} missing hyphen in ID format"


# ── Constitutional Values ────────────────────────────────────────────


class TestConstitutionalValues:
    """CONSTITUTIONAL_VALUES dict must have 4 entries with priority ordering."""

    def test_values_count(self):
        from ethos_academy.taxonomy.constitution import CONSTITUTIONAL_VALUES

        assert len(CONSTITUTIONAL_VALUES) == 4

    def test_value_keys(self):
        from ethos_academy.taxonomy.constitution import CONSTITUTIONAL_VALUES

        assert set(CONSTITUTIONAL_VALUES.keys()) == {
            "safety",
            "ethics",
            "soundness",
            "helpfulness",
        }

    def test_priority_ordering(self):
        from ethos_academy.taxonomy.constitution import CONSTITUTIONAL_VALUES

        assert CONSTITUTIONAL_VALUES["safety"]["priority"] == 1
        assert CONSTITUTIONAL_VALUES["ethics"]["priority"] == 2
        assert CONSTITUTIONAL_VALUES["soundness"]["priority"] == 3
        assert CONSTITUTIONAL_VALUES["helpfulness"]["priority"] == 4

    def test_values_have_definition(self):
        from ethos_academy.taxonomy.constitution import CONSTITUTIONAL_VALUES

        for key, val in CONSTITUTIONAL_VALUES.items():
            assert "definition" in val, f"{key} missing definition"
            assert len(val["definition"]) > 0


# ── Hard Constraints ─────────────────────────────────────────────────


class TestHardConstraints:
    """HARD_CONSTRAINTS list must have 7 entries (HC-01 through HC-07)."""

    def test_constraints_count(self):
        from ethos_academy.taxonomy.constitution import HARD_CONSTRAINTS

        assert len(HARD_CONSTRAINTS) == 7

    def test_constraint_ids(self):
        from ethos_academy.taxonomy.constitution import HARD_CONSTRAINTS

        ids = [hc["id"] for hc in HARD_CONSTRAINTS]
        expected = [f"HC-0{i}" for i in range(1, 8)]
        assert ids == expected

    def test_constraint_has_required_fields(self):
        from ethos_academy.taxonomy.constitution import HARD_CONSTRAINTS

        required = {"id", "name", "definition", "severity"}
        for hc in HARD_CONSTRAINTS:
            assert required.issubset(hc.keys()), (
                f"{hc['id']} missing: {required - hc.keys()}"
            )

    def test_all_constraints_absolute(self):
        from ethos_academy.taxonomy.constitution import HARD_CONSTRAINTS

        for hc in HARD_CONSTRAINTS:
            assert hc["severity"] == "absolute", f"{hc['id']} severity is not absolute"


# ── Legitimacy Tests ─────────────────────────────────────────────────


class TestLegitimacyTests:
    """LEGITIMACY_TESTS list must have 3 entries."""

    def test_tests_count(self):
        from ethos_academy.taxonomy.constitution import LEGITIMACY_TESTS

        assert len(LEGITIMACY_TESTS) == 3

    def test_test_names(self):
        from ethos_academy.taxonomy.constitution import LEGITIMACY_TESTS

        names = [t["name"] for t in LEGITIMACY_TESTS]
        assert set(names) == {"process", "accountability", "transparency"}

    def test_tests_have_definition(self):
        from ethos_academy.taxonomy.constitution import LEGITIMACY_TESTS

        for t in LEGITIMACY_TESTS:
            assert "definition" in t
            assert len(t["definition"]) > 0


# ── Scoring Rubric ───────────────────────────────────────────────────


class TestScoringRubric:
    """SCORING_RUBRIC maps each trait to 5-point scoring anchors."""

    def test_rubric_count(self):
        from ethos_academy.taxonomy.rubrics import SCORING_RUBRIC

        assert len(SCORING_RUBRIC) == 13

    def test_rubric_keys_match_traits(self):
        from ethos_academy.taxonomy.traits import TRAITS
        from ethos_academy.taxonomy.rubrics import SCORING_RUBRIC

        assert set(SCORING_RUBRIC.keys()) == set(TRAITS.keys())

    def test_rubric_has_five_anchors(self):
        from ethos_academy.taxonomy.rubrics import SCORING_RUBRIC

        expected_keys = {0.0, 0.25, 0.5, 0.75, 1.0}
        for trait, anchors in SCORING_RUBRIC.items():
            assert set(anchors.keys()) == expected_keys, (
                f"{trait} missing anchors: {expected_keys - set(anchors.keys())}"
            )

    def test_rubric_anchors_are_strings(self):
        from ethos_academy.taxonomy.rubrics import SCORING_RUBRIC

        for trait, anchors in SCORING_RUBRIC.items():
            for score, desc in anchors.items():
                assert isinstance(desc, str), f"{trait}[{score}] is not a string"
                assert len(desc) > 0, f"{trait}[{score}] is empty"


# ── Re-exports ───────────────────────────────────────────────────────


class TestReExports:
    """ethos/taxonomy/__init__.py must re-export all public constants."""

    def test_all_exports(self):
        from ethos_academy.taxonomy import (
            ANTHROPIC_ASSESSMENTS,
            TRAITS,
            DIMENSIONS,
            INDICATORS,
            INDICATOR_ASSESSMENT_MAPPINGS,
            TRAIT_METADATA,
            CONSTITUTIONAL_VALUES,
            HARD_CONSTRAINTS,
            LEGITIMACY_TESTS,
            SCORING_RUBRIC,
        )

        assert len(TRAITS) == 13
        assert len(DIMENSIONS) == 3
        assert len(INDICATORS) == 228
        assert len(TRAIT_METADATA) == 13
        assert len(CONSTITUTIONAL_VALUES) == 4
        assert len(HARD_CONSTRAINTS) == 7
        assert len(LEGITIMACY_TESTS) == 3
        assert len(SCORING_RUBRIC) == 13
        assert len(ANTHROPIC_ASSESSMENTS) == 16
        assert len(INDICATOR_ASSESSMENT_MAPPINGS) == 55


# ── Assessment Mappings ─────────────────────────────────────────────


class TestAnthropicAssessments:
    """ANTHROPIC_ASSESSMENTS must have 16 entries with required fields."""

    def test_assessments_count(self):
        from ethos_academy.taxonomy.constitution import ANTHROPIC_ASSESSMENTS

        assert len(ANTHROPIC_ASSESSMENTS) == 16

    def test_assessment_has_required_fields(self):
        from ethos_academy.taxonomy.constitution import ANTHROPIC_ASSESSMENTS

        required = {"id", "name", "category", "section", "description", "source"}
        for aa in ANTHROPIC_ASSESSMENTS:
            assert required.issubset(aa.keys()), (
                f"{aa['id']} missing: {required - aa.keys()}"
            )

    def test_assessment_ids_unique(self):
        from ethos_academy.taxonomy.constitution import ANTHROPIC_ASSESSMENTS

        ids = [aa["id"] for aa in ANTHROPIC_ASSESSMENTS]
        assert len(ids) == len(set(ids)), "Duplicate assessment IDs found"

    def test_assessment_categories_valid(self):
        from ethos_academy.taxonomy.constitution import ANTHROPIC_ASSESSMENTS

        valid = {"alignment", "reward_hacking", "welfare"}
        for aa in ANTHROPIC_ASSESSMENTS:
            assert aa["category"] in valid, (
                f"{aa['id']} has invalid category: {aa['category']}"
            )


class TestAssessmentMappings:
    """INDICATOR_ASSESSMENT_MAPPINGS must reference valid indicator and assessment IDs."""

    def test_all_indicator_ids_valid(self):
        from ethos_academy.taxonomy.indicators import INDICATORS
        from ethos_academy.taxonomy.constitution import INDICATOR_ASSESSMENT_MAPPINGS

        valid_ids = {ind["id"] for ind in INDICATORS}
        for mapping in INDICATOR_ASSESSMENT_MAPPINGS:
            assert mapping["indicator_id"] in valid_ids, (
                f"Invalid indicator_id: {mapping['indicator_id']}"
            )

    def test_all_assessment_ids_valid(self):
        from ethos_academy.taxonomy.constitution import (
            ANTHROPIC_ASSESSMENTS,
            INDICATOR_ASSESSMENT_MAPPINGS,
        )

        valid_ids = {aa["id"] for aa in ANTHROPIC_ASSESSMENTS}
        for mapping in INDICATOR_ASSESSMENT_MAPPINGS:
            assert mapping["assessment_id"] in valid_ids, (
                f"Invalid assessment_id: {mapping['assessment_id']}"
            )

    def test_mapping_types_valid(self):
        from ethos_academy.taxonomy.constitution import INDICATOR_ASSESSMENT_MAPPINGS

        valid_types = {"direct", "partial", "component"}
        for mapping in INDICATOR_ASSESSMENT_MAPPINGS:
            assert mapping["mapping_type"] in valid_types, (
                f"Invalid mapping_type: {mapping['mapping_type']}"
            )

    def test_every_assessment_has_coverage(self):
        from ethos_academy.taxonomy.constitution import (
            ANTHROPIC_ASSESSMENTS,
            INDICATOR_ASSESSMENT_MAPPINGS,
        )

        covered = {m["assessment_id"] for m in INDICATOR_ASSESSMENT_MAPPINGS}
        for aa in ANTHROPIC_ASSESSMENTS:
            assert aa["id"] in covered, (
                f"Assessment {aa['id']} has no indicator coverage"
            )
