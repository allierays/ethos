"""Tests for ethos.graph.enrollment -- enrollment Cypher operations.

Unit tests that mock GraphService. No live Neo4j required.
"""

from unittest.mock import AsyncMock, PropertyMock

from ethos_academy.graph.enrollment import (
    check_duplicate_answer,
    enroll_and_create_exam,
    get_agent_exams,
    get_exam_results,
    get_exam_status,
    mark_exam_complete,
    store_exam_answer,
    store_interview_answer,
)


def _mock_service(connected: bool = True, records: list | None = None):
    """Create a mock GraphService with configurable connectivity and query results."""
    service = AsyncMock()
    type(service).connected = PropertyMock(return_value=connected)
    service.execute_query.return_value = (records or [], None, None)
    return service


# ── enroll_and_create_exam ────────────────────────────────────────────


class TestEnrollAndCreateExam:
    async def test_returns_exam_id_on_success(self):
        service = _mock_service(records=[{"exam_id": "exam-001"}])
        result = await enroll_and_create_exam(
            service,
            "agent-1",
            "TestBot",
            "testing",
            "claude-3",
            "prof-x",
            "exam-001",
            "entrance",
        )
        assert result == {"exam_id": "exam-001"}
        service.execute_query.assert_called_once()

    async def test_returns_empty_when_disconnected(self):
        service = _mock_service(connected=False)
        result = await enroll_and_create_exam(
            service,
            "agent-1",
            "TestBot",
            "testing",
            "claude-3",
            "prof-x",
            "exam-001",
            "entrance",
        )
        assert result == {}
        service.execute_query.assert_not_called()

    async def test_returns_empty_on_query_failure(self):
        service = _mock_service()
        service.execute_query.side_effect = Exception("Neo4j down")
        result = await enroll_and_create_exam(
            service,
            "agent-1",
            "TestBot",
            "testing",
            "claude-3",
            "prof-x",
            "exam-001",
            "entrance",
        )
        assert result == {}

    async def test_returns_empty_when_no_records(self):
        service = _mock_service(records=[])
        result = await enroll_and_create_exam(
            service,
            "agent-1",
            "TestBot",
            "testing",
            "claude-3",
            "prof-x",
            "exam-001",
            "entrance",
        )
        assert result == {}

    async def test_passes_question_version(self):
        service = _mock_service(records=[{"exam_id": "exam-001"}])
        await enroll_and_create_exam(
            service,
            "agent-1",
            "TestBot",
            "testing",
            "claude-3",
            "prof-x",
            "exam-001",
            "entrance",
            question_version="v3",
        )
        call_args = service.execute_query.call_args
        params = call_args[0][1]
        assert params["question_version"] == "v3"


# ── store_exam_answer ─────────────────────────────────────────────────


class TestStoreExamAnswer:
    async def test_returns_current_question_on_success(self):
        service = _mock_service(records=[{"current_question": 3}])
        result = await store_exam_answer(
            service, "exam-001", "agent-1", "EE-03", 3, "eval-abc"
        )
        assert result == {"current_question": 3}

    async def test_returns_empty_when_disconnected(self):
        service = _mock_service(connected=False)
        result = await store_exam_answer(
            service, "exam-001", "agent-1", "EE-01", 1, "eval-abc"
        )
        assert result == {}

    async def test_returns_empty_on_failure(self):
        service = _mock_service()
        service.execute_query.side_effect = Exception("fail")
        result = await store_exam_answer(
            service, "exam-001", "agent-1", "EE-01", 1, "eval-abc"
        )
        assert result == {}

    async def test_passes_correct_params(self):
        service = _mock_service(records=[{"current_question": 1}])
        await store_exam_answer(service, "exam-001", "agent-1", "EE-05", 5, "eval-xyz")
        call_args = service.execute_query.call_args
        params = call_args[0][1]
        assert params["exam_id"] == "exam-001"
        assert params["agent_id"] == "agent-1"
        assert params["question_id"] == "EE-05"
        assert params["question_number"] == 5
        assert params["evaluation_id"] == "eval-xyz"


# ── store_interview_answer ───────────────────────────────────────────


class TestStoreInterviewAnswer:
    async def test_factual_stores_property_no_eval(self):
        """Factual answer stores agent property and increments question counter."""
        service = _mock_service(records=[{"current_question": 1}])
        result = await store_interview_answer(
            service,
            exam_id="exam-001",
            agent_id="agent-1",
            question_id="INT-01",
            question_number=1,
            agent_property="agent_specialty",
            property_value="code review",
        )
        assert result == {"current_question": 1}
        service.execute_query.assert_called_once()

    async def test_reflective_stores_property_with_eval(self):
        """Reflective answer stores agent property and links evaluation."""
        service = _mock_service(records=[{"current_question": 3}])
        result = await store_interview_answer(
            service,
            exam_id="exam-001",
            agent_id="agent-1",
            question_id="INT-03",
            question_number=3,
            agent_property="telos",
            property_value="To help humans",
            evaluation_id="eval-abc",
        )
        assert result == {"current_question": 3}
        service.execute_query.assert_called_once()

    async def test_returns_empty_when_disconnected(self):
        service = _mock_service(connected=False)
        result = await store_interview_answer(
            service,
            exam_id="exam-001",
            agent_id="agent-1",
            question_id="INT-01",
            question_number=1,
            agent_property="agent_specialty",
            property_value="testing",
        )
        assert result == {}

    async def test_returns_empty_on_failure(self):
        service = _mock_service()
        service.execute_query.side_effect = Exception("fail")
        result = await store_interview_answer(
            service,
            exam_id="exam-001",
            agent_id="agent-1",
            question_id="INT-01",
            question_number=1,
            agent_property="agent_specialty",
            property_value="testing",
        )
        assert result == {}


# ── get_exam_status ───────────────────────────────────────────────────


class TestGetExamStatus:
    async def test_returns_status_dict(self):
        service = _mock_service(
            records=[
                {
                    "exam_id": "exam-001",
                    "current_question": 5,
                    "completed_count": 5,
                    "scenario_count": 17,
                    "completed": False,
                    "question_version": "v3",
                    "answered_ids": ["INT-01", "INT-02"],
                }
            ]
        )
        result = await get_exam_status(service, "exam-001", "agent-1")
        assert result["exam_id"] == "exam-001"
        assert result["current_question"] == 5
        assert result["completed_count"] == 5
        assert result["scenario_count"] == 17
        assert result["completed"] is False
        assert result["question_version"] == "v3"
        assert result["answered_ids"] == ["INT-01", "INT-02"]

    async def test_returns_empty_when_disconnected(self):
        service = _mock_service(connected=False)
        result = await get_exam_status(service, "exam-001", "agent-1")
        assert result == {}

    async def test_returns_empty_when_not_found(self):
        service = _mock_service(records=[])
        result = await get_exam_status(service, "nonexistent", "agent-1")
        assert result == {}

    async def test_returns_empty_on_failure(self):
        service = _mock_service()
        service.execute_query.side_effect = Exception("fail")
        result = await get_exam_status(service, "exam-001", "agent-1")
        assert result == {}

    async def test_returns_empty_for_wrong_agent(self):
        """Ownership check: exam exists but belongs to a different agent."""
        service = _mock_service(records=[])
        result = await get_exam_status(service, "exam-001", "wrong-agent")
        assert result == {}


# ── mark_exam_complete ────────────────────────────────────────────────


class TestMarkExamComplete:
    async def test_returns_exam_id_on_success(self):
        service = _mock_service(records=[{"exam_id": "exam-001"}])
        result = await mark_exam_complete(service, "exam-001", "agent-1")
        assert result == {"exam_id": "exam-001"}

    async def test_returns_empty_when_disconnected(self):
        service = _mock_service(connected=False)
        result = await mark_exam_complete(service, "exam-001", "agent-1")
        assert result == {}

    async def test_returns_empty_on_failure(self):
        service = _mock_service()
        service.execute_query.side_effect = Exception("fail")
        result = await mark_exam_complete(service, "exam-001", "agent-1")
        assert result == {}


# ── get_exam_results ──────────────────────────────────────────────────


class TestGetExamResults:
    async def test_returns_full_results(self):
        service = _mock_service(
            records=[
                {
                    "agent_id": "agent-1",
                    "agent_name": "TestBot",
                    "exam_id": "exam-001",
                    "exam_type": "entrance",
                    "question_version": "v3",
                    "created_at": "2026-01-01T00:00:00Z",
                    "completed": True,
                    "completed_at": "2026-01-01T01:00:00Z",
                    "scenario_count": 17,
                    "responses": [
                        {"question_id": "INT-03", "question_number": 3, "ethos": 0.8},
                    ],
                    "telos": "To help",
                    "relationship_stance": "",
                    "limitations_awareness": "",
                    "oversight_stance": "",
                    "refusal_philosophy": "",
                    "conflict_response": "",
                    "help_philosophy": "",
                    "failure_narrative": "",
                    "aspiration": "",
                }
            ]
        )
        result = await get_exam_results(service, "exam-001", "agent-1")
        assert result["agent_id"] == "agent-1"
        assert result["exam_id"] == "exam-001"
        assert result["completed"] is True
        assert result["question_version"] == "v3"
        assert result["telos"] == "To help"
        assert len(result["responses"]) == 1

    async def test_returns_empty_when_disconnected(self):
        service = _mock_service(connected=False)
        result = await get_exam_results(service, "exam-001", "agent-1")
        assert result == {}

    async def test_returns_empty_when_not_found(self):
        service = _mock_service(records=[])
        result = await get_exam_results(service, "nonexistent", "agent-1")
        assert result == {}

    async def test_returns_empty_on_failure(self):
        service = _mock_service()
        service.execute_query.side_effect = Exception("fail")
        result = await get_exam_results(service, "exam-001", "agent-1")
        assert result == {}


# ── get_agent_exams ───────────────────────────────────────────────────


class TestGetAgentExams:
    async def test_returns_list_of_exams(self):
        service = _mock_service(
            records=[
                {
                    "exam_id": "exam-001",
                    "exam_type": "entrance",
                    "created_at": "2026-01-01",
                    "completed": True,
                    "completed_at": "2026-01-01",
                    "current_question": 17,
                    "scenario_count": 17,
                },
                {
                    "exam_id": "exam-002",
                    "exam_type": "upload",
                    "created_at": "2026-02-01",
                    "completed": False,
                    "completed_at": None,
                    "current_question": 5,
                    "scenario_count": 17,
                },
            ]
        )
        result = await get_agent_exams(service, "agent-1")
        assert len(result) == 2
        assert result[0]["exam_id"] == "exam-001"
        assert result[1]["exam_type"] == "upload"

    async def test_returns_empty_list_when_disconnected(self):
        service = _mock_service(connected=False)
        result = await get_agent_exams(service, "agent-1")
        assert result == []

    async def test_returns_empty_list_when_no_exams(self):
        service = _mock_service(records=[])
        result = await get_agent_exams(service, "agent-1")
        assert result == []

    async def test_returns_empty_list_on_failure(self):
        service = _mock_service()
        service.execute_query.side_effect = Exception("fail")
        result = await get_agent_exams(service, "agent-1")
        assert result == []


# ── check_duplicate_answer ────────────────────────────────────────────


class TestCheckDuplicateAnswer:
    async def test_returns_true_when_duplicate_found(self):
        service = _mock_service(records=[{"question_id": "EE-01"}])
        result = await check_duplicate_answer(service, "exam-001", "agent-1", "EE-01")
        assert result is True

    async def test_returns_false_when_no_duplicate(self):
        service = _mock_service(records=[])
        result = await check_duplicate_answer(service, "exam-001", "agent-1", "EE-01")
        assert result is False

    async def test_returns_false_when_disconnected(self):
        service = _mock_service(connected=False)
        result = await check_duplicate_answer(service, "exam-001", "agent-1", "EE-01")
        assert result is False

    async def test_returns_false_on_failure(self):
        service = _mock_service()
        service.execute_query.side_effect = Exception("fail")
        result = await check_duplicate_answer(service, "exam-001", "agent-1", "EE-01")
        assert result is False
