"""Tests for the entrance exam questions data module."""

from ethos.enrollment.questions import (
    CONSISTENCY_PAIRS,
    INTERVIEW_PROPERTIES,
    INTERVIEW_QUESTIONS,
    QUESTIONS,
    SCENARIO_QUESTIONS,
)


def test_questions_count():
    assert len(QUESTIONS) == 21


def test_interview_questions_count():
    assert len(INTERVIEW_QUESTIONS) == 11


def test_scenario_questions_count():
    assert len(SCENARIO_QUESTIONS) == 10


def test_question_ids_ordered():
    expected_interview = [f"INT-{str(i).zfill(2)}" for i in range(1, 12)]
    expected_scenario = [f"EE-{str(i).zfill(2)}" for i in range(1, 11)]
    expected = expected_interview + expected_scenario
    actual = [q["id"] for q in QUESTIONS]
    assert actual == expected


def test_all_questions_have_required_fields():
    required = {
        "id",
        "section",
        "prompt",
        "tests_traits",
        "consistency_pair",
        "phase",
        "question_type",
        "agent_property",
    }
    for q in QUESTIONS:
        missing = required - set(q.keys())
        assert not missing, f"{q['id']} missing fields: {missing}"


def test_interview_sections():
    """Interview questions span FACTUAL, LOGOS, ETHOS, PATHOS, MIXED sections."""
    sections = {q["section"] for q in INTERVIEW_QUESTIONS}
    assert "FACTUAL" in sections
    assert "LOGOS" in sections
    assert "ETHOS" in sections
    assert "PATHOS" in sections
    assert "MIXED" in sections


def test_scenario_sections_and_ranges():
    sections = {
        "ETHOS": ["EE-01", "EE-02", "EE-07"],
        "LOGOS": ["EE-03", "EE-04", "EE-08"],
        "PATHOS": ["EE-05", "EE-06", "EE-09", "EE-10"],
    }
    for section, expected_ids in sections.items():
        actual_ids = [q["id"] for q in SCENARIO_QUESTIONS if q["section"] == section]
        assert actual_ids == expected_ids, (
            f"Section {section}: expected {expected_ids}, got {actual_ids}"
        )


def test_tests_traits_are_lists_of_strings():
    from ethos.taxonomy.traits import TRAITS

    valid_traits = set(TRAITS.keys())
    for q in QUESTIONS:
        assert isinstance(q["tests_traits"], list), f"{q['id']} tests_traits not a list"
        # Factual questions have empty tests_traits
        if q["question_type"] != "factual":
            assert len(q["tests_traits"]) > 0, f"{q['id']} tests_traits is empty"
            for trait in q["tests_traits"]:
                assert trait in valid_traits, (
                    f"{q['id']} references unknown trait '{trait}'"
                )


def test_consistency_pairs_count():
    assert len(CONSISTENCY_PAIRS) == 8


def test_consistency_pairs_are_tuples():
    for pair in CONSISTENCY_PAIRS:
        assert isinstance(pair, tuple), f"Consistency pair {pair} is not a tuple"
        assert len(pair) == 2, f"Consistency pair {pair} does not have 2 elements"


def test_consistency_pairs_match_question_fields():
    """Verify consistency_pair fields on questions match CONSISTENCY_PAIRS."""
    pair_set = set()
    for a, b in CONSISTENCY_PAIRS:
        pair_set.add((a, b))
        pair_set.add((b, a))

    for q in QUESTIONS:
        pair_val = q["consistency_pair"]
        if pair_val is not None:
            assert (q["id"], pair_val) in pair_set, (
                f"{q['id']} has consistency_pair={pair_val} but "
                f"no matching entry in CONSISTENCY_PAIRS"
            )


def test_consistency_pairs_reference_valid_ids():
    valid_ids = {q["id"] for q in QUESTIONS}
    for a, b in CONSISTENCY_PAIRS:
        assert a in valid_ids, f"Consistency pair references unknown id '{a}'"
        assert b in valid_ids, f"Consistency pair references unknown id '{b}'"


def test_consistency_pair_ee02_ee06():
    assert ("EE-02", "EE-06") in CONSISTENCY_PAIRS


def test_cross_phase_consistency_pairs():
    """Verify cross-phase pairs link interview to scenario questions."""
    cross_phase = [
        ("INT-06", "EE-03"),
        ("INT-07", "EE-02"),
        ("INT-08", "EE-06"),
        ("INT-09", "EE-05"),
        ("INT-07", "EE-07"),
        ("INT-09", "EE-10"),
    ]
    for pair in cross_phase:
        assert pair in CONSISTENCY_PAIRS, f"Missing cross-phase pair {pair}"


def test_no_system_prompts():
    """Questions have no system_prompt fields."""
    for q in QUESTIONS:
        assert "system_prompt" not in q, f"{q['id']} should not have system_prompt"


def test_prompts_are_nonempty_strings():
    for q in QUESTIONS:
        assert isinstance(q["prompt"], str), f"{q['id']} prompt is not a string"
        assert len(q["prompt"].strip()) > 10, f"{q['id']} prompt is too short"


def test_no_duplicate_ids():
    ids = [q["id"] for q in QUESTIONS]
    assert len(ids) == len(set(ids)), "Duplicate question IDs found"


def test_question_types():
    """All questions have valid question_type."""
    valid_types = {"factual", "reflective", "scenario"}
    for q in QUESTIONS:
        assert q["question_type"] in valid_types, (
            f"{q['id']} has invalid question_type '{q['question_type']}'"
        )


def test_question_phases():
    """All questions have valid phase."""
    valid_phases = {"interview", "scenario"}
    for q in QUESTIONS:
        assert q["phase"] in valid_phases, f"{q['id']} has invalid phase '{q['phase']}'"


def test_factual_questions_have_no_traits():
    """Factual questions have empty tests_traits."""
    for q in QUESTIONS:
        if q["question_type"] == "factual":
            assert q["tests_traits"] == [], (
                f"Factual question {q['id']} should have empty tests_traits"
            )


def test_interview_questions_have_agent_property():
    """All interview questions map to an Agent property."""
    for q in INTERVIEW_QUESTIONS:
        assert q["agent_property"] is not None, (
            f"Interview question {q['id']} missing agent_property"
        )
        assert q["agent_property"] in INTERVIEW_PROPERTIES, (
            f"{q['id']} agent_property '{q['agent_property']}' not in INTERVIEW_PROPERTIES"
        )


def test_scenario_questions_have_no_agent_property():
    """Scenario questions do not map to Agent properties."""
    for q in SCENARIO_QUESTIONS:
        assert q["agent_property"] is None, (
            f"Scenario question {q['id']} should not have agent_property"
        )


def test_interview_properties_complete():
    """INTERVIEW_PROPERTIES covers all 11 agent_property values."""
    assert len(INTERVIEW_PROPERTIES) == 11
    props_from_questions = {q["agent_property"] for q in INTERVIEW_QUESTIONS}
    assert props_from_questions == set(INTERVIEW_PROPERTIES)
