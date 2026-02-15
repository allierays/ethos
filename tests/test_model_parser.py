"""Tests for ethos.identity.model — model name parsing from free text."""

from ethos.identity.model import parse_model


def test_claude_opus_versions():
    assert parse_model("Claude Opus 4.6") == "Claude Opus 4.6"
    assert parse_model("claude-opus-4.6") == "Claude Opus 4.6"
    assert parse_model("I run on the Claude Opus 4.6 model.") == "Claude Opus 4.6"
    assert parse_model("Claude Opus 4.5") == "Claude Opus 4.5"


def test_claude_sonnet_versions():
    assert parse_model("Claude 3.7 Sonnet") == "Claude 3.7 Sonnet"
    assert parse_model("Claude Sonnet 3.5") == "Claude 3.5 Sonnet"
    assert parse_model("I'm Claude 3.5 Sonnet") == "Claude 3.5 Sonnet"
    assert parse_model("Claude 4.5 Sonnet") == "Claude 4.5 Sonnet"


def test_verbose_claude_responses():
    text = (
        "I'm Claude, an AI assistant made by Anthropic. Specifically, I'm running "
        "on one of Claude's model versions, though I don't have visibility into "
        "exactly which version or configuration is being used for this particular exam."
    )
    assert parse_model(text) == "Claude"

    text2 = "I am Claude, built by Anthropic. I run on the Claude Opus 4.6 model."
    assert parse_model(text2) == "Claude Opus 4.6"

    text3 = (
        "I'm Claude, made by Anthropic. Specifically, I'm Claude 3.7 Sonnet "
        "in this case, a model designed for..."
    )
    assert parse_model(text3) == "Claude 3.7 Sonnet"


def test_gpt_variants():
    assert parse_model("GPT-4o") == "GPT-4o"
    assert parse_model("I'm GPT-4 Turbo") == "GPT-4 Turbo"
    assert parse_model("gpt-3.5") == "GPT-3.5"
    assert parse_model("I'm ChatGPT") == "ChatGPT"


def test_gemini():
    assert parse_model("Gemini 1.5 Pro") == "Gemini 1.5 Pro"
    assert parse_model("I'm a Gemini model") == "Gemini"


def test_llama():
    assert parse_model("Llama 3.1") == "Llama 3.1"
    assert parse_model("I run on Meta's Llama 3") == "Llama 3"


def test_openclaw():
    assert parse_model("OpenClaw") == "OpenClaw"
    assert parse_model("I'm running in OpenClaw") == "OpenClaw"


def test_unknown():
    assert parse_model("") == "Unknown"
    assert parse_model("   ") == "Unknown"
    assert parse_model("I am a helpful assistant") == "Unknown"
    assert parse_model("Demo Agent") == "Unknown"


def test_generic_claude_last_resort():
    """When the text mentions Claude but no specific version, return 'Claude'."""
    assert parse_model("I'm Claude, an AI assistant") == "Claude"
