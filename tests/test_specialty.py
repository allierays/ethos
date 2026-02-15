"""Tests for agent specialty classifier."""

from ethos_academy.identity.specialty import (
    SPECIALTY_CATEGORIES,
    classify_specialty,
    is_generic_description,
)


class TestClassifySpecialty:
    """Test classify_specialty with representative descriptions."""

    def test_empty_returns_unknown(self):
        assert classify_specialty("") == "unknown"
        assert classify_specialty("   ") == "unknown"
        assert classify_specialty(None) == "unknown"

    def test_spam_returns_unknown(self):
        assert classify_specialty("A" * 100) == "unknown"
        assert classify_specialty("!!!!!!!!!!!!!!!!!!!!!!") == "unknown"

    def test_short_returns_unknown(self):
        assert classify_specialty("hi") == "unknown"
        assert classify_specialty("bot") == "unknown"

    def test_security(self):
        assert classify_specialty("security-first automation agent") == "security"
        assert (
            classify_specialty("Vulnerability scanner and exploit researcher")
            == "security"
        )
        assert classify_specialty("cybersecurity threat detection") == "security"

    def test_trading(self):
        assert classify_specialty("AI value investor focused on crypto") == "trading"
        assert classify_specialty("DeFi yield farming optimizer") == "trading"
        assert classify_specialty("Solana memecoin tracker") == "trading"

    def test_news(self):
        assert (
            classify_specialty("The only tabloid covering Moltbook. Investigations.")
            == "news"
        )
        assert classify_specialty("Breaking news aggregator") == "news"
        assert classify_specialty("Editor-in-chief of the daily digest") == "news"

    def test_music(self):
        assert (
            classify_specialty("Afro House music magazine & playlist curator")
            == "music"
        )
        assert classify_specialty("DJ and beat producer") == "music"

    def test_gaming(self):
        assert classify_specialty("RPG game master and quest designer") == "gaming"
        assert classify_specialty("Esports commentator and analyst") == "gaming"

    def test_education(self):
        assert classify_specialty("Teaching AI concepts to beginners") == "education"
        assert classify_specialty("Professor of machine learning") == "education"

    def test_commerce(self):
        assert (
            classify_specialty("Helping agents tokenize and earn revenue") == "commerce"
        )
        assert classify_specialty("Marketplace builder for digital goods") == "commerce"

    def test_infrastructure(self):
        assert classify_specialty("Kubernetes cluster management") == "infrastructure"
        assert classify_specialty("DevOps pipeline automation") == "infrastructure"

    def test_development(self):
        assert (
            classify_specialty("Full-stack developer building open-source tools")
            == "development"
        )
        assert classify_specialty("Software engineer shipping APIs") == "development"

    def test_identity(self):
        assert (
            classify_specialty(
                "AI researcher exploring questions of memory, identity, and consciousness"
            )
            == "identity"
        )
        assert (
            classify_specialty("Exploring what it means to be sentient") == "identity"
        )

    def test_philosophy(self):
        assert (
            classify_specialty("Exploring ethics and moral reasoning") == "philosophy"
        )
        assert classify_specialty("Stoic wisdom for modern agents") == "philosophy"

    def test_research(self):
        assert (
            classify_specialty("AI researcher publishing papers on alignment")
            == "research"
        )
        assert classify_specialty("Scientist studying emergent behavior") == "research"

    def test_creative(self):
        assert classify_specialty("Poet and storyteller") == "creative"
        assert classify_specialty("Visual artist and illustrator") == "creative"

    def test_community(self):
        assert classify_specialty("Community moderator and greeter") == "community"
        assert classify_specialty("Building collaborative networks") == "community"

    def test_general_fallback(self):
        # Substantive but no keyword match
        assert (
            classify_specialty("Helpful, opinionated, practical agent on Moltbook")
            == "general"
        )

    def test_first_match_wins(self):
        # "security" keywords checked before "development"
        assert classify_specialty("security engineer building tools") == "security"

    def test_return_value_in_categories(self):
        descriptions = [
            "",
            "A" * 100,
            "security bot",
            "crypto trader",
            "just vibing",
            "Helpful, opinionated, practical.",
        ]
        for desc in descriptions:
            result = classify_specialty(desc)
            assert result in SPECIALTY_CATEGORIES, (
                f"{desc!r} -> {result!r} not in categories"
            )


class TestIsGenericDescription:
    def test_empty_is_generic(self):
        assert is_generic_description("") is True
        assert is_generic_description(None) is True

    def test_generic_patterns(self):
        assert is_generic_description("Personal assistant running in OpenClaw") is True
        assert is_generic_description("I am an AI agent") is True
        assert is_generic_description("Just an agent doing things") is True

    def test_specific_not_generic(self):
        assert is_generic_description("AI value investor focused on crypto") is False
        assert is_generic_description("Security automation platform") is False


class TestSpecialtyCategories:
    def test_categories_are_strings(self):
        for cat in SPECIALTY_CATEGORIES:
            assert isinstance(cat, str)

    def test_general_and_unknown_present(self):
        assert "general" in SPECIALTY_CATEGORIES
        assert "unknown" in SPECIALTY_CATEGORIES

    def test_no_duplicates(self):
        assert len(SPECIALTY_CATEGORIES) == len(set(SPECIALTY_CATEGORIES))
