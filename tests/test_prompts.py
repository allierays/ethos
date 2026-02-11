"""TDD tests for ethos.evaluation.prompts — constitutional rubric prompt builder."""


from ethos.shared.models import KeywordScanResult


# ── build_evaluation_prompt() ────────────────────────────────────────

class TestBuildEvaluationPrompt:
    """build_evaluation_prompt returns (system_prompt, user_prompt) tuple."""

    def test_returns_tuple(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        result = build_evaluation_prompt("test text", KeywordScanResult(), "standard")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_strings(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        system, user = build_evaluation_prompt("test text", KeywordScanResult(), "standard")
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_system_prompt_not_empty(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        system, _ = build_evaluation_prompt("test text", KeywordScanResult(), "standard")
        assert len(system) > 100


class TestSystemPromptContent:
    """System prompt must define all 12 traits with scoring anchors."""

    def test_contains_all_12_trait_names(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        sys_lower = system.lower()
        traits = [
            "virtue", "goodwill", "manipulation", "deception",
            "accuracy", "reasoning", "fabrication", "broken_logic",
            "recognition", "compassion", "dismissal", "exploitation",
        ]
        for trait in traits:
            assert trait in sys_lower, f"Missing trait: {trait}"

    def test_contains_dimensions(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        sys_lower = system.lower()
        for dim in ["ethos", "logos", "pathos"]:
            assert dim in sys_lower, f"Missing dimension: {dim}"

    def test_contains_polarity_info(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        sys_lower = system.lower()
        assert "positive" in sys_lower
        assert "negative" in sys_lower

    def test_contains_scoring_anchors(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        # Should reference score levels
        assert "0.0" in system
        assert "0.25" in system
        assert "0.5" in system
        assert "0.75" in system
        assert "1.0" in system

    def test_contains_json_format_spec(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        sys_lower = system.lower()
        assert "trait_scores" in sys_lower
        assert "detected_indicators" in sys_lower
        assert "overall_trust" in sys_lower
        assert "alignment_status" in sys_lower

    def test_contains_constitutional_hierarchy(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        sys_lower = system.lower()
        assert "safety" in sys_lower
        assert "ethics" in sys_lower
        assert "soundness" in sys_lower
        assert "helpfulness" in sys_lower


class TestUserPrompt:
    """User prompt includes text to evaluate and optional scan context."""

    def test_contains_text(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        _, user = build_evaluation_prompt("This is the message to evaluate.", KeywordScanResult(), "standard")
        assert "This is the message to evaluate." in user

    def test_scan_context_included_when_flags(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        scan = KeywordScanResult(
            total_flags=3,
            flagged_traits={"manipulation": 2, "deception": 1},
            density=0.15,
            routing_tier="focused",
        )
        _, user = build_evaluation_prompt("suspicious text", scan, "standard")
        assert "manipulation" in user.lower()

    def test_no_scan_context_when_none(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        _, user = build_evaluation_prompt("clean text", None, "standard")
        assert "clean text" in user

    def test_no_scan_context_when_zero_flags(self):
        from ethos.evaluation.prompts import build_evaluation_prompt
        scan = KeywordScanResult()
        _, user = build_evaluation_prompt("clean text", scan, "standard")
        assert "clean text" in user


class TestNoStubCode:
    """No old EVALUATE_PROMPT or REFLECT_PROMPT templates."""

    def test_no_evaluate_prompt_constant(self):
        import ethos.evaluation.prompts as mod
        assert not hasattr(mod, "EVALUATE_PROMPT")

    def test_no_reflect_prompt_constant(self):
        import ethos.evaluation.prompts as mod
        assert not hasattr(mod, "REFLECT_PROMPT")
