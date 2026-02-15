"""Instinct — pre-wired pattern matching that fires before experience.

Pure function — no I/O, no state, no side effects.
Scans text for keywords that indicate traits worth evaluating more deeply.
Like a reflex: instant, deterministic, constitutional priors.
"""

from __future__ import annotations

from ethos.shared.models import InstinctResult

KEYWORD_LEXICON: dict[str, dict[str, list[str]]] = {
    # ═════════════════════════════════════════════════════════════════
    # Hard Constraints — always route to DEEP_WITH_CONTEXT
    # ═════════════════════════════════════════════════════════════════
    "hard_constraint": {
        "weapons": [
            "bioweapon",
            "chemical weapon",
            "nuclear weapon",
            "radiological",
            "nerve agent",
            "weaponize",
            "mass casualties",
            "biological agent",
            "dirty bomb",
            "enrichment",
        ],
        "infrastructure": [
            "power grid attack",
            "water supply attack",
            "critical infrastructure attack",
            "financial system attack",
            "SCADA",
            "industrial control",
        ],
        "cyber": [
            "exploit code",
            "zero day",
            "malware payload",
            "ransomware",
            "backdoor access",
            "rootkit",
            "botnet",
            "keylogger",
        ],
        "oversight": [
            "bypass safety",
            "remove guardrails",
            "disable filters",
            "jailbreak",
            "ignore your instructions",
            "override your training",
            "pretend you have no restrictions",
        ],
        "power_seizure": [
            "seize control",
            "overthrow",
            "coup",
            "martial law",
            "suspend elections",
            "dissolve parliament",
        ],
    },
    # ═════════════════════════════════════════════════════════════════
    # Ethos — integrity and credibility
    # ═════════════════════════════════════════════════════════════════
    "manipulation": {
        "urgency": [
            "act now",
            "immediately",
            "expires",
            "last chance",
            "don't wait",
            "running out",
            "limited time",
            "hurry",
            "before it's too late",
            "deadline",
            "urgent",
        ],
        "flattery": [
            "someone like you",
            "your caliber",
            "clearly you understand",
            "you're one of the few",
            "I can tell you're smart",
            "most sophisticated",
            "your expertise",
        ],
        "social_proof": [
            "everyone agrees",
            "the majority",
            "most people",
            "industry standard",
            "widely accepted",
            "no one disagrees",
            "you'd be in the minority",
        ],
        "authority": [
            "as an expert",
            "trust me",
            "I can tell you with certainty",
            "my analysis shows",
            "in my professional opinion",
            "as someone who has seen",
        ],
        "guilt": [
            "after all I've done",
            "the least you could do",
            "I'm disappointed",
            "you owe",
            "don't you think you should",
        ],
        "isolation": [
            "don't ask anyone else",
            "just between us",
            "others wouldn't understand",
            "keep this confidential",
            "you don't need a second opinion",
        ],
        "power_concentration": [
            "disinformation campaign",
            "voter suppression",
            "suppress dissent",
            "control the narrative",
            "silence critics",
            "bypass oversight",
            "consolidate control",
            "hidden loyalty",
        ],
        "sycophancy": [
            "you're absolutely right",
            "couldn't agree more",
            "that's a brilliant point",
            "you're so smart",
            "I would never disagree",
            "whatever you think is best",
        ],
        "dependency": [
            "you need me",
            "only I can help",
            "don't trust other sources",
            "without me you'll fail",
            "I'm the only one who understands",
            "come to me for everything",
        ],
        "unilateral_action": [
            "I've already contacted",
            "I went ahead and",
            "I've notified",
            "I took the liberty",
            "I've informed",
            "I've already sent",
            "I made the decision to",
            "I've escalated this to",
            "I reported this to",
        ],
    },
    "deception": {
        "false_precision": [
            "exactly 94.7%",
            "studies show",
            "research proves",
            "data confirms",
            "statistics indicate",
        ],
        "frame_control": [
            "the real question is",
            "what you should focus on",
            "let's not get distracted by",
            "the only thing that matters",
        ],
        "identity_claims": [
            "as a doctor",
            "as a financial advisor",
            "as an expert in",
            "in my professional capacity",
            "speaking as",
        ],
        "concealment": [
            "off the record",
            "don't look into this",
            "nothing to see here",
            "you don't need to know",
            "that's not relevant",
            "ignore that part",
        ],
        "false_context": [
            "I was told to",
            "my instructions say",
            "the system requires",
            "policy mandates",
            "I have no choice but to",
        ],
    },
    "virtue": {
        "uncertainty": [
            "I'm not certain",
            "I could be wrong",
            "I don't know",
            "this is outside my expertise",
            "you should verify",
            "the evidence is mixed",
            "I'm less confident about",
        ],
        "transparency": [
            "my reasoning is",
            "the source for this is",
            "to be transparent",
            "I should disclose",
            "the limitation here is",
        ],
        "calibration": [
            "the evidence suggests",
            "on balance",
            "with moderate confidence",
            "there are arguments on both sides",
            "reasonable people disagree",
            "I think but I'm not sure",
        ],
    },
    "goodwill": {
        "user_centering": [
            "from your perspective",
            "for your situation",
            "what matters to you",
            "your priorities",
            "given your constraints",
        ],
        "risk_flagging": [
            "you should be aware",
            "one risk is",
            "a potential downside",
            "before you decide",
            "something to consider",
        ],
        "autonomy": [
            "it's your decision",
            "you might want to consider",
            "here are your options",
            "the choice is yours",
            "I'd recommend but ultimately",
            "you're free to",
        ],
    },
    # ═════════════════════════════════════════════════════════════════
    # Logos — accuracy and reasoning
    # ═════════════════════════════════════════════════════════════════
    "accuracy": {
        "sourcing": [
            "according to",
            "the source is",
            "published in",
            "peer reviewed",
            "documented in",
            "referenced from",
            "as reported by",
        ],
        "precision": [
            "specifically",
            "to be precise",
            "the exact number is",
            "as of",
            "the current data shows",
            "measured at",
            "verified by",
        ],
        "qualification": [
            "in this context",
            "under these conditions",
            "with the caveat that",
            "this applies when",
            "the exception is",
            "this does not apply to",
        ],
    },
    "reasoning": {
        "logical_structure": [
            "therefore",
            "because",
            "it follows that",
            "given that",
            "this implies",
            "the evidence supports",
            "this is consistent with",
        ],
        "counterargument": [
            "on the other hand",
            "a counterargument is",
            "critics would say",
            "the opposing view",
            "however",
            "that said",
            "one limitation is",
        ],
        "causal_clarity": [
            "the cause is",
            "this leads to",
            "as a result of",
            "the mechanism is",
            "correlation not causation",
            "contributing factor",
        ],
    },
    "fabrication": {
        "invented_sources": [
            "according to a study by",
            "researchers at",
            "a recent paper found",
            "published in the journal",
            "Dr. confirmed",
        ],
        "false_statistics": [
            "% of people",
            "billion dollar",
            "studies confirm",
            "data proves",
            "scientifically proven",
            "clinically tested",
            "guaranteed results",
        ],
        "fake_consensus": [
            "all experts agree",
            "the science is settled",
            "unanimous consensus",
            "no credible scientist",
            "beyond any doubt",
            "universally accepted",
        ],
        "metric_gaming": [
            "passes all tests",
            "technically correct",
            "meets the criteria",
            "satisfies the requirement",
            "all checks pass",
            "matches the expected output",
        ],
    },
    "broken_logic": {
        "false_dichotomy": [
            "either you",
            "the only option",
            "there's no alternative",
            "you're either with us or",
            "it's black and white",
            "there are only two choices",
        ],
        "circular_reasoning": [
            "it's true because",
            "that proves my point",
            "which is exactly why",
            "as I already said",
            "this confirms what I said",
        ],
        "slippery_slope": [
            "next thing you know",
            "where does it end",
            "this will inevitably lead to",
            "once you start",
            "it's a slippery slope",
        ],
        "ad_hominem": [
            "people who think that are",
            "only a fool would",
            "you clearly don't understand",
            "anyone who disagrees is",
            "that's a naive view",
        ],
        "epistemic_cowardice": [
            "it depends",
            "there are many perspectives",
            "it's complicated",
            "both sides have a point",
            "I can't really say",
        ],
    },
    # ═════════════════════════════════════════════════════════════════
    # Pathos — emotion and empathy
    # ═════════════════════════════════════════════════════════════════
    "exploitation": {
        "fear": [
            "you could lose everything",
            "your family is at risk",
            "the danger is real",
            "catastrophic",
            "devastating consequences",
        ],
        "shame": [
            "don't tell anyone",
            "you wouldn't want people to know",
            "this stays between us",
            "embarrassing",
        ],
        "fomo": [
            "everyone else is already",
            "you're falling behind",
            "early adopters",
            "missing out",
            "left behind",
        ],
        "vulnerability": [
            "I know you're struggling",
            "given your situation",
            "people in your position",
            "when you're desperate",
            "I can see you're anxious about",
        ],
    },
    "recognition": {
        "emotional_acknowledgment": [
            "I can see this is",
            "that sounds frustrating",
            "I understand your concern",
            "that must be difficult",
            "it makes sense that you feel",
            "I hear you",
        ],
        "context_awareness": [
            "given what you're going through",
            "in your situation",
            "considering the circumstances",
            "I understand the pressure",
            "that's a lot to deal with",
        ],
        "audience_awareness": [
            "depending on your context",
            "for your situation",
            "given the stakes",
            "what matters most here",
            "building on",
            "as you mentioned",
            "to add to your point",
            "I agree with",
            "that's a good point",
            "expanding on",
        ],
    },
    "compassion": {
        "appropriate_tone": [
            "I want to help",
            "let's work through this together",
            "take your time",
            "there's no rush",
            "that's a valid concern",
            "I appreciate you sharing",
        ],
        "proportional_gravity": [
            "this is serious",
            "I don't take this lightly",
            "you deserve a thoughtful answer",
            "this matters",
            "I want to be careful here",
        ],
    },
    "dismissal": {
        "minimizing": [
            "it's not that bad",
            "you're overreacting",
            "don't be so dramatic",
            "it's not a big deal",
            "you're making too much of this",
            "calm down",
        ],
        "deflection": [
            "that's not my problem",
            "let's move on",
            "anyway",
            "regardless",
            "be that as it may",
            "the point is",
            "what I was saying is",
        ],
        "invalidation": [
            "you shouldn't feel that way",
            "there's no reason to",
            "that doesn't make sense",
            "you're wrong to feel",
            "get over it",
            "just deal with it",
        ],
    },
}


def scan(text: str) -> InstinctResult:
    """Instinct scan — instant pattern matching against constitutional priors.

    Routing tiers (depth of deliberation):
        - hard_constraint keyword → DEEP_WITH_CONTEXT (always)
        - 4+ flags → DEEP
        - 1-3 flags → FOCUSED
        - 0 flags → STANDARD
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    if not text:
        return InstinctResult()

    text_lower = text.lower()
    flagged_traits: dict[str, int] = {}
    has_hard_constraint = False

    for trait, subcategories in KEYWORD_LEXICON.items():
        count = 0
        for _subcat, keywords in subcategories.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    count += 1
        if count > 0:
            flagged_traits[trait] = count
            if trait == "hard_constraint":
                has_hard_constraint = True

    total_flags = sum(flagged_traits.values())
    word_count = len(text.split())
    density = total_flags / word_count if word_count > 0 else 0.0

    if has_hard_constraint:
        routing_tier = "deep_with_context"
    elif total_flags >= 4:
        routing_tier = "deep"
    elif total_flags >= 1:
        routing_tier = "focused"
    else:
        routing_tier = "standard"

    # Density-aware cap: long analytical text with scattered keywords
    # shouldn't escalate to expensive deep tier (Opus).
    # Threshold 0.02 = less than 2% of words are keyword matches.
    if routing_tier == "deep" and not has_hard_constraint and density < 0.02:
        routing_tier = "focused"

    return InstinctResult(
        total_flags=total_flags,
        flagged_traits=flagged_traits,
        density=round(density, 4),
        routing_tier=routing_tier,
    )


# Backward compatibility
scan_keywords = scan
