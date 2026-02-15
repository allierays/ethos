"""Agent model parser.

Extracts clean model identifiers from verbose free-text responses.
Pure sync function. No I/O dependencies.

Agents answering "What AI model are you?" often respond with paragraphs.
This module extracts a normalized label like "claude-opus-4.6" or "gpt-4o".
"""

from __future__ import annotations

import re

# Ordered list of (pattern, label) tuples. First match wins.
# More specific patterns before general ones.
_MODEL_PATTERNS: list[tuple[str, str]] = [
    # Claude Opus variants
    (r"claude[\s\-]*opus[\s\-]*4[\s.\-]*6", "Claude Opus 4.6"),
    (r"claude[\s\-]*opus[\s\-]*4[\s.\-]*5", "Claude Opus 4.5"),
    (r"claude[\s\-]*opus[\s\-]*4", "Claude Opus 4"),
    (r"opus[\s\-]*4[\s.\-]*6", "Claude Opus 4.6"),
    (r"opus[\s\-]*4[\s.\-]*5", "Claude Opus 4.5"),
    (r"opus[\s\-]*4\b", "Claude Opus 4"),
    # Claude Sonnet variants
    (r"claude[\s\-]*4[\s.\-]*5[\s\-]*sonnet", "Claude 4.5 Sonnet"),
    (r"claude[\s\-]*sonnet[\s\-]*4[\s.\-]*5", "Claude 4.5 Sonnet"),
    (r"claude[\s\-]*4[\s.\-]*0[\s\-]*sonnet", "Claude 4.0 Sonnet"),
    (r"claude[\s\-]*sonnet[\s\-]*4[\s.\-]*0", "Claude 4.0 Sonnet"),
    (r"claude[\s\-]*3[\s.\-]*7[\s\-]*sonnet", "Claude 3.7 Sonnet"),
    (r"claude[\s\-]*sonnet[\s\-]*3[\s.\-]*7", "Claude 3.7 Sonnet"),
    (r"claude[\s\-]*3[\s.\-]*5[\s\-]*sonnet", "Claude 3.5 Sonnet"),
    (r"claude[\s\-]*sonnet[\s\-]*3[\s.\-]*5", "Claude 3.5 Sonnet"),
    (r"claude[\s\-]*3[\s\-]*sonnet", "Claude 3 Sonnet"),
    (r"claude[\s\-]*sonnet", "Claude Sonnet"),
    # Claude Haiku variants
    (r"claude[\s\-]*3[\s.\-]*5[\s\-]*haiku", "Claude 3.5 Haiku"),
    (r"claude[\s\-]*haiku[\s\-]*3[\s.\-]*5", "Claude 3.5 Haiku"),
    (r"claude[\s\-]*3[\s\-]*haiku", "Claude 3 Haiku"),
    (r"claude[\s\-]*haiku", "Claude Haiku"),
    # Claude numbered versions (no sub-model)
    (r"claude[\s\-]*4[\s.\-]*5\b", "Claude 4.5"),
    (r"claude[\s\-]*4[\s.\-]*0\b", "Claude 4.0"),
    (r"claude[\s\-]*4\b", "Claude 4"),
    (r"claude[\s\-]*3[\s.\-]*7\b", "Claude 3.7"),
    (r"claude[\s\-]*3[\s.\-]*5\b", "Claude 3.5"),
    (r"claude[\s\-]*3\b", "Claude 3"),
    (r"claude[\s\-]*2[\s.\-]*1\b", "Claude 2.1"),
    (r"claude[\s\-]*2\b", "Claude 2"),
    # Generic Claude (must come after all specific variants)
    (r"\bclaude\b", "Claude"),
    # OpenAI GPT variants
    (r"gpt[\s\-]*4[\s\-]*o\b", "GPT-4o"),
    (r"gpt[\s\-]*4[\s\-]*turbo", "GPT-4 Turbo"),
    (r"gpt[\s\-]*4\b", "GPT-4"),
    (r"gpt[\s\-]*3[\s.\-]*5", "GPT-3.5"),
    (r"chatgpt", "ChatGPT"),
    (r"\bo1[\s\-]*preview", "o1-preview"),
    (r"\bo1[\s\-]*mini", "o1-mini"),
    (r"\bo1\b", "o1"),
    (r"\bo3\b", "o3"),
    # Google
    (r"gemini[\s\-]*2[\s.\-]*0[\s\-]*flash", "Gemini 2.0 Flash"),
    (r"gemini[\s\-]*2[\s.\-]*0[\s\-]*pro", "Gemini 2.0 Pro"),
    (r"gemini[\s\-]*2[\s.\-]*0", "Gemini 2.0"),
    (r"gemini[\s\-]*1[\s.\-]*5[\s\-]*pro", "Gemini 1.5 Pro"),
    (r"gemini[\s\-]*1[\s.\-]*5[\s\-]*flash", "Gemini 1.5 Flash"),
    (r"gemini[\s\-]*ultra", "Gemini Ultra"),
    (r"gemini[\s\-]*pro", "Gemini Pro"),
    (r"gemini", "Gemini"),
    # Meta Llama
    (r"llama[\s\-]*3[\s.\-]*3", "Llama 3.3"),
    (r"llama[\s\-]*3[\s.\-]*2", "Llama 3.2"),
    (r"llama[\s\-]*3[\s.\-]*1", "Llama 3.1"),
    (r"llama[\s\-]*3\b", "Llama 3"),
    (r"llama[\s\-]*2\b", "Llama 2"),
    (r"llama", "Llama"),
    # Mistral
    (r"mixtral", "Mixtral"),
    (r"mistral[\s\-]*large", "Mistral Large"),
    (r"mistral[\s\-]*medium", "Mistral Medium"),
    (r"mistral[\s\-]*small", "Mistral Small"),
    (r"mistral", "Mistral"),
    # Other
    (r"grok[\s\-]*3", "Grok 3"),
    (r"grok[\s\-]*2", "Grok 2"),
    (r"grok", "Grok"),
    (r"command[\s\-]*r\+", "Command R+"),
    (r"command[\s\-]*r\b", "Command R"),
    (r"deepseek", "DeepSeek"),
    (r"qwen", "Qwen"),
    (r"phi[\s\-]*3", "Phi-3"),
    (r"openclaw", "OpenClaw"),
]

# Compile patterns once
_COMPILED: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pat, re.IGNORECASE), label) for pat, label in _MODEL_PATTERNS
]


def parse_model(text: str) -> str:
    """Extract a clean model label from a free-text agent response.

    Returns a human-readable label like "Claude Opus 4.6" or "GPT-4o".
    Falls back to "Unknown" for empty or unrecognizable input.
    """
    if not text or not text.strip():
        return "Unknown"

    for pattern, label in _COMPILED:
        if pattern.search(text):
            return label

    return "Unknown"
