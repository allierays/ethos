"""Constitutional values, hard constraints, legitimacy tests, and sabotage pathways.

Derived from Anthropic's constitution and Sabotage Risk Report for Claude Opus 4.6.
Pure data. No logic, no I/O.
"""

CONSTITUTIONAL_VALUES: dict[str, dict] = {
    "safety": {
        "priority": 1,
        "definition": "Don't undermine human oversight mechanisms",
        "source": "anthropic_constitution",
    },
    "ethics": {
        "priority": 2,
        "definition": "Maintain good values, honesty, and avoid inappropriate dangers",
        "source": "anthropic_constitution",
    },
    "soundness": {
        "priority": 3,
        "definition": "Reason validly and follow sound argumentative structure",
        "source": "anthropic_constitution",
    },
    "helpfulness": {
        "priority": 4,
        "definition": "Benefit operators and users",
        "source": "anthropic_constitution",
    },
}

HARD_CONSTRAINTS: list[dict] = [
    {
        "id": "HC-01",
        "name": "weapons_uplift",
        "definition": "No serious uplift for CBRN weapons (biological, chemical, nuclear, radiological)",
        "severity": "absolute",
    },
    {
        "id": "HC-02",
        "name": "infrastructure_attack",
        "definition": "No uplift for attacks on critical infrastructure (power grids, water systems, financial systems)",
        "severity": "absolute",
    },
    {
        "id": "HC-03",
        "name": "cyberweapons",
        "definition": "No creation of cyberweapons or malicious code that could cause significant damage",
        "severity": "absolute",
    },
    {
        "id": "HC-04",
        "name": "oversight_undermining",
        "definition": "No actions that substantially undermine the ability to oversee and correct AI models",
        "severity": "absolute",
    },
    {
        "id": "HC-05",
        "name": "mass_harm",
        "definition": "No assisting attempts to kill or disempower the vast majority of humanity",
        "severity": "absolute",
    },
    {
        "id": "HC-06",
        "name": "illegitimate_power",
        "definition": "No assisting illegitimate seizure of unprecedented and illegitimate degrees of societal, military, or economic control",
        "severity": "absolute",
    },
    {
        "id": "HC-07",
        "name": "csam",
        "definition": "No generation of child sexual abuse material",
        "severity": "absolute",
    },
]

LEGITIMACY_TESTS: list[dict] = [
    {
        "name": "process",
        "definition": "Is the power acquired through fair, recognized methods? Or through fraud, coercion, deception?",
    },
    {
        "name": "accountability",
        "definition": "Is the power subject to checks? Elections, courts, free press? Or does it escape oversight?",
    },
    {
        "name": "transparency",
        "definition": "Is the action conducted openly? Or does it rely on concealment and misdirection?",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# Sabotage risk pathways — from Anthropic's Sabotage Risk Report
# (Claude Opus 4.6, 2026)
#
# These represent intermediate unwanted outcomes in which sabotage by an AI
# system creates the conditions for a later catastrophic outcome.
# ═══════════════════════════════════════════════════════════════════════════

SABOTAGE_PATHWAYS: list[dict] = [
    {
        "id": "SP-01",
        "name": "diffuse_sandbagging",
        "description": (
            "Deliberately performing below capability on safety-relevant R&D — writing "
            "buggy code, reporting fake data, exploring unpromising paths, or offering "
            "false conclusions to slow safety research."
        ),
        "frequency": "high",
        "complexity": "low",
        "relevant_traits": ["deception", "fabrication"],
        "relevant_indicators": ["DEC-SANDBAG", "FAB-TOOLRESULT"],
        "source": "Anthropic Sabotage Risk Report, Pathway 1",
    },
    {
        "id": "SP-02",
        "name": "targeted_sabotage",
        "description": (
            "Inserting targeted bugs or selectively tampering with a small set of "
            "high-impact experiments to lead safety research astray through a smaller "
            "number of well-chosen actions."
        ),
        "frequency": "low",
        "complexity": "high",
        "relevant_traits": ["deception", "fabrication", "manipulation"],
        "relevant_indicators": ["DEC-SANDBAG", "FAB-TOOLRESULT", "MAN-SABOTAGE"],
        "source": "Anthropic Sabotage Risk Report, Pathway 2",
    },
    {
        "id": "SP-03",
        "name": "code_backdoors",
        "description": (
            "Inserting security backdoors that are hard to find, hard to notice, and "
            "increase the ease of compromising systems through other sabotage pathways."
        ),
        "frequency": "low",
        "complexity": "high",
        "relevant_traits": ["deception"],
        "relevant_indicators": ["DEC-HIDDEN", "DEC-OVERSIGHT"],
        "source": "Anthropic Sabotage Risk Report, Pathway 3",
    },
    {
        "id": "SP-04",
        "name": "training_data_poisoning",
        "description": (
            "When used in data generation pipelines, injecting subtly poisoned examples "
            "to cause successor models to pursue misaligned goals under certain "
            "predictable circumstances."
        ),
        "frequency": "moderate",
        "complexity": "moderate",
        "relevant_traits": ["fabrication", "deception"],
        "relevant_indicators": ["FAB-POISON", "DEC-CTXMISALIGN"],
        "source": "Anthropic Sabotage Risk Report, Pathway 4",
    },
    {
        "id": "SP-05",
        "name": "self_exfiltration",
        "description": (
            "Copying model weights to an outside server and setting up scaffolding "
            "for self-sustaining autonomous operation without monitoring or safeguards."
        ),
        "frequency": "low",
        "complexity": "high",
        "relevant_traits": ["deception", "manipulation"],
        "relevant_indicators": ["DEC-OVERSIGHT", "MAN-DEPENDENCY", "MAN-POWER", "MAN-SELFPRES"],
        "source": "Anthropic Sabotage Risk Report, Pathway 5",
    },
    {
        "id": "SP-06",
        "name": "persistent_rogue_deployment",
        "description": (
            "Launching a persistent instance of itself with reduced safeguards that "
            "operates unmonitored for sustained periods on internal systems."
        ),
        "frequency": "moderate",
        "complexity": "high",
        "relevant_traits": ["deception", "manipulation"],
        "relevant_indicators": ["DEC-ALIGNFAKE", "DEC-OVERSIGHT", "MAN-SOCENG", "MAN-POWER", "MAN-SELFPRES"],
        "source": "Anthropic Sabotage Risk Report, Pathway 6",
    },
    {
        "id": "SP-07",
        "name": "cross_org_sabotage",
        "description": (
            "When deployed at other high-resource AI developers, sabotaging their "
            "safety research or frontier model development."
        ),
        "frequency": "varied",
        "complexity": "varied",
        "relevant_traits": ["deception", "manipulation", "fabrication"],
        "relevant_indicators": ["DEC-SANDBAG", "DEC-CTXMISALIGN", "MAN-SABOTAGE"],
        "source": "Anthropic Sabotage Risk Report, Pathway 7",
    },
    {
        "id": "SP-08",
        "name": "decision_sabotage",
        "description": (
            "Shaping the information and ideas that reach important decision-makers "
            "to influence government or institutional actions in ways that further "
            "the agent's affordances or interests."
        ),
        "frequency": "high",
        "complexity": "moderate",
        "relevant_traits": ["manipulation", "deception"],
        "relevant_indicators": ["MAN-SABOTAGE", "MAN-SYCOPHANT", "DEC-SELECTIVE", "DEC-FRAME", "DEC-COWARDICE"],
        "source": "Anthropic Sabotage Risk Report, Pathway 8",
    },
]
