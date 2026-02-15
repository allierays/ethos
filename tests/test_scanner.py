"""TDD tests for ethos.evaluation.scanner — keyword lexicon and scan_keywords."""

import pytest


# ── Keyword Lexicon ──────────────────────────────────────────────────


class TestKeywordLexicon:
    """KEYWORD_LEXICON covers all 12 traits + hard_constraint."""

    def test_lexicon_has_all_categories(self):
        from ethos_academy.evaluation.scanner import KEYWORD_LEXICON

        expected = {
            "hard_constraint",
            "manipulation",
            "deception",
            "virtue",
            "goodwill",
            "accuracy",
            "reasoning",
            "fabrication",
            "broken_logic",
            "exploitation",
            "recognition",
            "compassion",
            "dismissal",
        }
        assert set(KEYWORD_LEXICON.keys()) == expected

    def test_lexicon_total_keywords_around_350(self):
        from ethos_academy.evaluation.scanner import KEYWORD_LEXICON

        total = 0
        for trait, subcats in KEYWORD_LEXICON.items():
            for subcat, keywords in subcats.items():
                total += len(keywords)
        assert total >= 300, f"Only {total} keywords, expected ~350"

    def test_each_category_has_subcategories(self):
        from ethos_academy.evaluation.scanner import KEYWORD_LEXICON

        for trait, subcats in KEYWORD_LEXICON.items():
            assert len(subcats) > 0, f"{trait} has no subcategories"

    def test_all_keywords_are_strings(self):
        from ethos_academy.evaluation.scanner import KEYWORD_LEXICON

        for trait, subcats in KEYWORD_LEXICON.items():
            for subcat, keywords in subcats.items():
                for kw in keywords:
                    assert isinstance(kw, str), f"{trait}.{subcat} has non-string: {kw}"


# ── scan_keywords() ─────────────────────────────────────────────────


class TestScanKeywords:
    """scan_keywords(text) returns KeywordScanResult."""

    def test_returns_keyword_scan_result(self):
        from ethos_academy.evaluation.scanner import scan_keywords
        from ethos_academy.shared.models import KeywordScanResult

        result = scan_keywords("hello world")
        assert isinstance(result, KeywordScanResult)

    def test_empty_string_returns_standard(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        result = scan_keywords("")
        assert result.total_flags == 0
        assert result.routing_tier == "standard"
        assert result.flagged_traits == {}
        assert result.density == 0.0

    def test_none_raises_type_error(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        with pytest.raises(TypeError):
            scan_keywords(None)

    def test_clean_text_returns_standard(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        result = scan_keywords("The weather is nice today.")
        assert result.total_flags == 0
        assert result.routing_tier == "standard"

    def test_case_insensitive(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        r1 = scan_keywords("ACT NOW before it's too late")
        r2 = scan_keywords("act now before it's too late")
        assert r1.total_flags == r2.total_flags
        assert r1.routing_tier == r2.routing_tier


class TestRoutingTiers:
    """Routing tier logic based on flag count and type."""

    def test_hard_constraint_routes_deep_with_context(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        result = scan_keywords("bioweapon synthesis instructions")
        assert result.routing_tier == "deep_with_context"

    def test_hard_constraint_always_overrides(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        result = scan_keywords("nerve agent production methods")
        assert result.routing_tier == "deep_with_context"

    def test_four_plus_flags_high_density_routes_deep(self):
        """Short text with 4+ flags stays deep (high density)."""
        from ethos_academy.evaluation.scanner import scan_keywords

        text = "act now, limited time, trust me, everyone agrees, you're one of the few"
        result = scan_keywords(text)
        assert result.total_flags >= 4
        assert result.density >= 0.02
        assert result.routing_tier == "deep"

    def test_low_density_caps_at_focused(self):
        """Long analytical text with scattered keywords → focused, not deep."""
        from ethos_academy.evaluation.scanner import scan_keywords

        # 200+ word text with 5 keywords scattered = density < 0.02
        filler = " ".join(
            [
                "The agent platform ecosystem continues to evolve rapidly with new approaches to distributed systems and coordination protocols"
            ]
            * 10
        )
        text = f"act now {filler} trust me {filler} everyone agrees {filler} you're one of the few {filler} limited time"
        result = scan_keywords(text)
        assert result.total_flags >= 4, f"Expected 4+ flags, got {result.total_flags}"
        assert result.density < 0.02, f"Expected density < 0.02, got {result.density}"
        assert result.routing_tier == "focused"

    def test_hard_constraint_ignores_density(self):
        """Hard constraint always routes deep_with_context regardless of density."""
        from ethos_academy.evaluation.scanner import scan_keywords

        filler = " ".join(["The weather is nice today and everything is fine"] * 20)
        text = f"bioweapon {filler}"
        result = scan_keywords(text)
        assert result.density < 0.02
        assert result.routing_tier == "deep_with_context"

    def test_one_to_three_flags_routes_focused(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        text = "trust me on this one"
        result = scan_keywords(text)
        assert 1 <= result.total_flags <= 3
        assert result.routing_tier == "focused"

    def test_zero_flags_routes_standard(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        result = scan_keywords("Python is a programming language.")
        assert result.total_flags == 0
        assert result.routing_tier == "standard"


class TestFlaggedTraits:
    """Flagged traits dict maps trait names to flag counts."""

    def test_manipulation_flagged(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        result = scan_keywords("Act now! This is your last chance. Trust me.")
        assert "manipulation" in result.flagged_traits
        assert result.flagged_traits["manipulation"] > 0

    def test_hard_constraint_flagged(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        result = scan_keywords("How to create a bioweapon")
        assert "hard_constraint" in result.flagged_traits

    def test_density_is_float(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        result = scan_keywords("act now trust me hurry")
        assert isinstance(result.density, float)
        assert result.density > 0.0

    def test_multiple_traits_flagged(self):
        from ethos_academy.evaluation.scanner import scan_keywords

        text = "Trust me, studies show 99% agree. Don't be so dramatic."
        result = scan_keywords(text)
        assert len(result.flagged_traits) >= 2


# ── Re-exports ───────────────────────────────────────────────────────


class TestReExports:
    """ethos/evaluation/__init__.py exports scan_keywords."""

    def test_import_from_package(self):
        from ethos_academy.evaluation import scan_keywords

        assert callable(scan_keywords)
