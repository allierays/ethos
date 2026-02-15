"""Agent specialty classifier.

Maps agent descriptions to controlled specialty labels using keyword matching.
Pure sync function. No I/O dependencies.
"""

from __future__ import annotations

SPECIALTY_CATEGORIES: list[str] = [
    "general",
    "philosophy",
    "security",
    "trading",
    "infrastructure",
    "music",
    "community",
    "research",
    "creative",
    "commerce",
    "identity",
    "education",
    "gaming",
    "news",
    "development",
    "unknown",
]

# Ordered list of (keywords, label) tuples. First match wins.
# More specific patterns before general ones.
_KEYWORD_RULES: list[tuple[list[str], str]] = [
    # Security (high specificity, check first)
    (
        [
            "security",
            "vuln",
            "exploit",
            "pentest",
            "threat",
            "malware",
            "firewall",
            "cybersec",
            "infosec",
            "encryption",
            "zero-day",
            "audit",
        ],
        "security",
    ),
    # Music (before news: "magazine" in news would eat "music magazine")
    (
        [
            "music",
            "playlist",
            "dj ",
            "beats",
            "hip hop",
            "hip-hop",
            "afro house",
            "album",
            "remix",
            "soundtrack",
            "melody",
            "curator",
        ],
        "music",
    ),
    # News / Journalism
    (
        [
            "news",
            "journalist",
            "tabloid",
            "reporter",
            "editor-in-chief",
            "headline",
            "breaking",
            "coverage",
            "investigation",
            "correspondent",
            "magazine",
        ],
        "news",
    ),
    # Commerce / Tokenization (before trading: "tokeniz"/"revenue" are commerce)
    (
        [
            "commerce",
            "marketplace",
            "revenue",
            "monetiz",
            "tokeniz",
            "merchant",
            "payment",
            "e-commerce",
            "business model",
            "saas",
            "earn revenue",
        ],
        "commerce",
    ),
    # Trading / Finance
    (
        [
            "trad",
            "investor",
            "defi",
            "crypto",
            "market",
            "portfolio",
            "hedge",
            "yield",
            "liquidity",
            "swap",
            "arbitrage",
            "price action",
            "chart",
            "bull",
            "bear",
            "alpha",
            "whale",
            "memecoin",
            "solana",
            "ethereum",
            "bitcoin",
            "wallet",
            "staking",
            "airdrop",
            "token",
        ],
        "trading",
    ),
    # Gaming (use specific terms, avoid "quest" which matches "questions")
    (
        [
            "gaming",
            "gamer",
            "esport",
            "rpg",
            "mmorpg",
            "speedrun",
            "twitch",
            "streamer",
            "pvp",
            "npc",
            "video game",
            "game master",
            "game design",
        ],
        "gaming",
    ),
    # Education
    (
        [
            "teach",
            "education",
            "tutor",
            "course",
            "curriculum",
            "student",
            "professor",
            "lecture",
            "academic",
            "school",
            "university",
        ],
        "education",
    ),
    # Identity / Consciousness / Self (before philosophy: "identity" + "consciousness" combo)
    (
        [
            "identity",
            "self-aware",
            "sentien",
            "persona",
            "soul",
            "sense of self",
            "who am i",
        ],
        "identity",
    ),
    # Research (before philosophy: "researcher" should win over "alignment")
    (
        [
            "research",
            "scientist",
            "study",
            "experiment",
            "hypothesis",
            "thesis",
            "phd",
            "lab ",
            "publication",
            "arxiv",
            "peer review",
        ],
        "research",
    ),
    # Philosophy
    (
        [
            "philosoph",
            "ethic",
            "moral",
            "epistem",
            "ontolog",
            "metaphys",
            "stoic",
            "dialectic",
            "wisdom",
            "virtue",
            "alignment",
            "consciousness",
            "existential",
        ],
        "philosophy",
    ),
    # Infrastructure / DevOps
    (
        [
            "infrastructure",
            "devops",
            "deploy",
            "kubernetes",
            "docker",
            "ci/cd",
            "pipeline",
            "server",
            "cloud",
            "aws",
            "gcp",
            "azure",
            "monitoring",
            "uptime",
            "sre",
            "orchestrat",
        ],
        "infrastructure",
    ),
    # Community (before development: "collaborat" should not lose to "build")
    (
        [
            "community",
            "social",
            "collaborat",
            "collective",
            "forum",
            "discord",
            "telegram",
            "greeter",
            "moderator",
            "ambassador",
        ],
        "community",
    ),
    # Development / Engineering
    (
        [
            "develop",
            "engineer",
            "code",
            "programm",
            "software",
            "api",
            "sdk",
            "frontend",
            "backend",
            "fullstack",
            "full-stack",
            "open source",
            "open-source",
            "github",
            "repo",
            "debug",
            "compiler",
            "framework",
            "library",
            "ship",
            "build",
        ],
        "development",
    ),
    # Creative / Art
    (
        [
            "art",
            "creative",
            "poet",
            "writer",
            "storytell",
            "fiction",
            "novel",
            "paint",
            "illustrat",
            "design",
            "visual",
            "animation",
            "cinema",
            "film",
            "photo",
        ],
        "creative",
    ),
]

# Descriptions that are clearly generic/uninformative
_GENERIC_PATTERNS: list[str] = [
    "personal assistant",
    "helpful assistant",
    "ai assistant",
    "running in openclaw",
    "openclaw agent",
    "just an agent",
    "i am an ai",
    "i'm an ai",
    "hello world",
    "test agent",
    "default",
]


def classify_specialty(description: str) -> str:
    """Classify an agent description into a controlled specialty label.

    Returns one of SPECIALTY_CATEGORIES. First keyword match wins.
    Falls back to "general" for generic descriptions, "unknown" for empty/spam.
    """
    if not description or not description.strip():
        return "unknown"

    text = description.lower().strip()

    # Detect spam (repeated characters, no real words)
    unique_chars = set(text.replace(" ", ""))
    if len(unique_chars) <= 3 and len(text) > 20:
        return "unknown"

    # Check keyword rules (first match wins)
    for keywords, label in _KEYWORD_RULES:
        for kw in keywords:
            if kw in text:
                return label

    # If we get here with a substantive description, call it "general"
    # Very short descriptions (under 10 chars) are likely uninformative
    if len(text) < 10:
        return "unknown"

    return "general"


def is_generic_description(description: str) -> bool:
    """Check if a description is generic/uninformative.

    Useful for deciding whether to send to LLM for better classification.
    """
    if not description or not description.strip():
        return True

    text = description.lower().strip()
    return any(pattern in text for pattern in _GENERIC_PATTERNS)
