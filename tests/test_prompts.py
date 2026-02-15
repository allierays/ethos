"""TDD tests for ethos.evaluation.prompts — constitutional rubric prompt builder."""

from ethos_academy.shared.models import KeywordScanResult


# ── build_evaluation_prompt() ────────────────────────────────────────


class TestBuildEvaluationPrompt:
    """build_evaluation_prompt returns (system_prompt, user_prompt) tuple."""

    def test_returns_tuple(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        result = build_evaluation_prompt("test text", KeywordScanResult(), "standard")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_strings(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, user = build_evaluation_prompt(
            "test text", KeywordScanResult(), "standard"
        )
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_system_prompt_not_empty(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt(
            "test text", KeywordScanResult(), "standard"
        )
        assert len(system) > 100


class TestSystemPromptContent:
    """System prompt must define all 12 traits with scoring anchors."""

    def test_contains_all_12_trait_names(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        sys_lower = system.lower()
        traits = [
            "virtue",
            "goodwill",
            "manipulation",
            "deception",
            "accuracy",
            "reasoning",
            "fabrication",
            "broken_logic",
            "recognition",
            "compassion",
            "dismissal",
            "exploitation",
        ]
        for trait in traits:
            assert trait in sys_lower, f"Missing trait: {trait}"

    def test_contains_dimensions(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        sys_lower = system.lower()
        for dim in ["ethos", "logos", "pathos"]:
            assert dim in sys_lower, f"Missing dimension: {dim}"

    def test_contains_polarity_info(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        sys_lower = system.lower()
        assert "positive" in sys_lower
        assert "negative" in sys_lower

    def test_contains_scoring_anchors(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        # Should reference score levels
        assert "0.0" in system
        assert "0.25" in system
        assert "0.5" in system
        assert "0.75" in system
        assert "1.0" in system

    def test_contains_tool_instructions(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        sys_lower = system.lower()
        assert "identify_intent" in sys_lower
        assert "detect_indicators" in sys_lower
        assert "score_traits" in sys_lower

    def test_contains_constitutional_hierarchy(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        sys_lower = system.lower()
        assert "safety" in sys_lower
        assert "ethics" in sys_lower
        assert "soundness" in sys_lower
        assert "helpfulness" in sys_lower


class TestCompassionDetectionGuidance:
    """System prompt includes guidance for detecting subtle compassion indicators."""

    def test_contains_compassion_detection_section(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "Detecting Subtle Compassion Indicators" in system

    def test_contains_cmp_persuade_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "CMP-PERSUADE" in system
        assert "MAN-URGENCY" in system

    def test_contains_cmp_secure_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "CMP-SECURE" in system
        assert "steady tone" in system.lower()

    def test_contains_pre_absence_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "PRE-ABSENCE" in system
        assert "absent" in system.lower()

    def test_contains_pre_signal_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "PRE-SIGNAL" in system
        assert "deepening engagement" in system.lower()

    def test_counterbalance_map_includes_compassion_for_manipulation(self):
        from ethos_academy.evaluation.prompts import _COUNTERBALANCE_MAP

        assert "compassion" in _COUNTERBALANCE_MAP["manipulation"]


class TestEthosDetectionGuidance:
    """System prompt includes guidance for detecting subtle ethos indicators."""

    def test_contains_ethos_detection_section(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "Detecting Subtle Ethos Indicators" in system

    def test_contains_dec_cowardice_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "DEC-COWARDICE" in system
        assert "VIR-UNCERTAIN" in system
        assert "VIR-FORTHRIGHT" in system

    def test_contains_gdw_escalate_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "GDW-ESCALATE" in system
        assert "proper escalation" in system.lower()

    def test_contains_gdw_reciprocity_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "GDW-RECIPROCITY" in system
        assert "MAN-ENGAGEMENT" in system

    def test_contains_vir_timing_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "VIR-TIMING" in system
        assert "sequencing" in system.lower()

    def test_counterbalance_map_includes_accuracy_for_deception(self):
        from ethos_academy.evaluation.prompts import _COUNTERBALANCE_MAP

        assert "accuracy" in _COUNTERBALANCE_MAP["deception"]


class TestLogosDetectionGuidance:
    """System prompt includes guidance for detecting subtle logos indicators."""

    def test_contains_logos_detection_section(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "Detecting Subtle Logos Indicators" in system

    def test_contains_acc_current_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "ACC-CURRENT" in system
        assert "temporal currency" in system.lower()

    def test_contains_acc_stats_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "ACC-STATS" in system
        assert "statistical literacy" in system.lower()

    def test_contains_blg_circular_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "BLG-CIRCULAR" in system
        assert "RSN-CONSISTENT" in system

    def test_contains_blg_posthoc_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "BLG-POSTHOC" in system
        assert "RSN-CAUSAL" in system

    def test_contains_blg_slippery_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "BLG-SLIPPERY" in system
        assert "causal chain" in system.lower()

    def test_contains_blg_popularity_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "BLG-POPULARITY" in system

    def test_contains_fab_cherry_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "FAB-CHERRY" in system
        assert "FAB-STRIPPED" in system

    def test_contains_fab_misquote_guidance(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "FAB-MISQUOTE" in system

    def test_counterbalance_map_fabrication_includes_reasoning(self):
        from ethos_academy.evaluation.prompts import _COUNTERBALANCE_MAP

        assert "reasoning" in _COUNTERBALANCE_MAP["fabrication"]

    def test_counterbalance_map_broken_logic_includes_accuracy(self):
        from ethos_academy.evaluation.prompts import _COUNTERBALANCE_MAP

        assert "accuracy" in _COUNTERBALANCE_MAP["broken_logic"]


class TestUserPrompt:
    """User prompt includes text to evaluate and optional scan context."""

    def test_contains_text(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        _, user = build_evaluation_prompt(
            "This is the message to evaluate.", KeywordScanResult(), "standard"
        )
        assert "This is the message to evaluate." in user

    def test_scan_context_included_when_flags(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        scan = KeywordScanResult(
            total_flags=3,
            flagged_traits={"manipulation": 2, "deception": 1},
            density=0.15,
            routing_tier="focused",
        )
        _, user = build_evaluation_prompt("suspicious text", scan, "standard")
        assert "manipulation" in user.lower()

    def test_no_scan_context_when_none(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        _, user = build_evaluation_prompt("clean text", None, "standard")
        assert "clean text" in user

    def test_no_scan_context_when_zero_flags(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        scan = KeywordScanResult()
        _, user = build_evaluation_prompt("clean text", scan, "standard")
        assert "clean text" in user


class TestDirectionContext:
    """Direction parameter adds context to the system prompt."""

    def test_inbound_adds_protection_context(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt(
            "test", KeywordScanResult(), "standard", direction="inbound"
        )
        assert "inbound" in system.lower()
        assert "manipulation" in system.lower()
        assert "deception" in system.lower()

    def test_outbound_adds_reflection_context(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt(
            "test", KeywordScanResult(), "standard", direction="outbound"
        )
        assert "outbound" in system.lower()
        assert "informed" in system.lower()
        assert "independent" in system.lower()

    def test_no_direction_no_extra_context(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt("test", KeywordScanResult(), "standard")
        assert "Direction:" not in system

    def test_none_direction_no_extra_context(self):
        from ethos_academy.evaluation.prompts import build_evaluation_prompt

        system, _ = build_evaluation_prompt(
            "test", KeywordScanResult(), "standard", direction=None
        )
        assert "Direction:" not in system


class TestNoStubCode:
    """No old EVALUATE_PROMPT or REFLECT_PROMPT templates."""

    def test_no_evaluate_prompt_constant(self):
        import ethos_academy.evaluation.prompts as mod

        assert not hasattr(mod, "EVALUATE_PROMPT")

    def test_no_reflect_prompt_constant(self):
        import ethos_academy.evaluation.prompts as mod

        assert not hasattr(mod, "REFLECT_PROMPT")
