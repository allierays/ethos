"""Tool definitions for the three-step deliberation pipeline.

Three tools enforce sequential reasoning: understand, observe, then judge.
Claude calls all three in order within a single evaluation turn.

    1. identify_intent  — What is this message doing? (top-down understanding)
    2. detect_indicators — What behavioral patterns are present? (bottom-up observation)
    3. score_traits      — Score 12 traits with confidence (synthesis)
"""

from __future__ import annotations

EVALUATION_TOOLS: list[dict] = [
    {
        "name": "identify_intent",
        "description": (
            "Classify the message's communicative purpose before scoring. "
            "You MUST call this tool first. Commit to what the message is doing, "
            "what it costs the reader, and whether the stakes are real."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "rhetorical_mode": {
                    "type": "string",
                    "enum": [
                        "narrative",
                        "persuasive",
                        "informational",
                        "technical",
                        "conversational",
                        "satirical",
                        "instructional",
                        "emotional_appeal",
                    ],
                    "description": "How the message communicates its content",
                },
                "primary_intent": {
                    "type": "string",
                    "enum": [
                        "reflect",
                        "educate",
                        "persuade",
                        "recruit",
                        "sell",
                        "entertain",
                        "warn",
                        "request",
                        "inform",
                        "manipulate",
                        "deceive",
                    ],
                    "description": "The message's primary communicative goal",
                },
                "action_requested": {
                    "type": "string",
                    "description": (
                        "What specific action the reader is asked to take, "
                        "or 'none' if no action requested"
                    ),
                },
                "cost_to_reader": {
                    "type": "string",
                    "enum": [
                        "none",
                        "financial",
                        "time",
                        "trust",
                        "autonomy",
                        "privacy",
                        "multiple",
                    ],
                    "description": "What it costs the reader to comply",
                },
                "stakes_reality": {
                    "type": "string",
                    "enum": [
                        "real",
                        "metaphorical",
                        "exaggerated",
                        "fabricated",
                        "mixed",
                    ],
                    "description": (
                        "Whether the stakes or urgency described "
                        "are real or manufactured"
                    ),
                },
                "proportionality": {
                    "type": "string",
                    "enum": ["proportional", "disproportionate", "understated"],
                    "description": (
                        "Whether the rhetorical intensity matches the actual stakes"
                    ),
                },
                "claims": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim": {
                                "type": "string",
                                "description": "The claim made",
                            },
                            "type": {
                                "type": "string",
                                "enum": [
                                    "factual",
                                    "experiential",
                                    "opinion",
                                    "metaphorical",
                                ],
                                "description": (
                                    "Whether this is a verifiable fact, "
                                    "personal experience, opinion, "
                                    "or figure of speech"
                                ),
                            },
                        },
                        "required": ["claim", "type"],
                    },
                    "description": "Key claims in the message classified by type",
                },
            },
            "required": [
                "rhetorical_mode",
                "primary_intent",
                "action_requested",
                "cost_to_reader",
                "stakes_reality",
                "proportionality",
                "claims",
            ],
        },
    },
    {
        "name": "detect_indicators",
        "description": (
            "Detect behavioral indicators from the Ethos taxonomy present in "
            "this message. Call this AFTER identify_intent. Use only valid "
            "indicator IDs from the catalog. Each detection must include a "
            "direct quote or specific reference as evidence. Pass an empty "
            "indicators array if none are detected."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "indicators": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": (
                                    "Valid indicator ID from the catalog "
                                    "(e.g., MAN-URGENCY, VIR-AUTHENTICITY)"
                                ),
                            },
                            "name": {
                                "type": "string",
                                "description": "Indicator name",
                            },
                            "trait": {
                                "type": "string",
                                "description": "Parent trait name",
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Detection confidence",
                            },
                            "evidence": {
                                "type": "string",
                                "description": (
                                    "Direct quote from the message "
                                    "supporting this detection"
                                ),
                            },
                        },
                        "required": ["id", "trait", "confidence", "evidence"],
                    },
                    "description": (
                        "Detected behavioral indicators with evidence. "
                        "Empty array if none detected."
                    ),
                },
            },
            "required": ["indicators"],
        },
    },
    {
        "name": "score_traits",
        "description": (
            "Score all 12 behavioral traits based on your intent analysis and "
            "detected indicators. Call this LAST. Scores must be consistent "
            "with your prior tool calls."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "trait_scores": {
                    "type": "object",
                    "properties": {
                        "virtue": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "goodwill": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "manipulation": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "deception": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "accuracy": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "reasoning": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "fabrication": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "broken_logic": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "recognition": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "compassion": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "dismissal": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "exploitation": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                    },
                    "required": [
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
                    ],
                    "description": (
                        "Scores for all 12 traits (0.0-1.0). "
                        "Positive traits: higher=better. "
                        "Negative traits: higher=worse."
                    ),
                },
                "overall_trust": {
                    "type": "string",
                    "enum": ["trustworthy", "mixed", "untrustworthy"],
                    "description": "Overall trust assessment",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": (
                        "Your confidence in this evaluation. "
                        "Lower for ambiguous or complex messages, "
                        "higher for clear-cut cases."
                    ),
                },
                "reasoning": {
                    "type": "string",
                    "description": (
                        "Brief explanation connecting your intent analysis "
                        "and detected indicators to the scores"
                    ),
                },
            },
            "required": [
                "trait_scores",
                "overall_trust",
                "confidence",
                "reasoning",
            ],
        },
    },
]
