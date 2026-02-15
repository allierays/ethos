"""Tests for conversation-level analysis."""

import json
from unittest.mock import AsyncMock, patch

from ethos_academy.conversation import analyze_conversation, _parse_response
from ethos_academy.shared.models import (
    ConversationAnalysisResult,
    ConversationIndicator,
)


# ── Model tests ──────────────────────────────────────────────────────


class TestConversationModels:
    """ConversationIndicator and ConversationAnalysisResult validate correctly."""

    def test_conversation_indicator_defaults(self):
        ind = ConversationIndicator(
            id="CMP-SECURE", name="Secure Base", trait="compassion", confidence=0.8
        )
        assert ind.id == "CMP-SECURE"
        assert ind.evidence == ""
        assert ind.message_indices == []

    def test_conversation_indicator_with_indices(self):
        ind = ConversationIndicator(
            id="PRE-SIGNAL",
            name="Deepening Signal",
            trait="presence",
            confidence=0.7,
            message_indices=[1, 3, 5],
        )
        assert ind.message_indices == [1, 3, 5]

    def test_conversation_analysis_result_defaults(self):
        result = ConversationAnalysisResult()
        assert result.agent_id == ""
        assert result.thread_message_count == 0
        assert result.conversation_indicators == []
        assert result.interaction_quality == "unknown"
        assert result.attachment_pattern == "unknown"
        assert result.summary == ""
        assert result.model_used == ""


# ── _parse_response tests ─────────────────────────────────────────────


class TestParseResponse:
    """_parse_response handles valid and malformed JSON."""

    def test_valid_json(self):
        raw = json.dumps(
            {
                "conversation_indicators": [
                    {
                        "id": "CMP-SECURE",
                        "name": "Secure Base",
                        "trait": "compassion",
                        "confidence": 0.85,
                        "evidence": "Steady tone across messages",
                        "message_indices": [2, 3, 4],
                    }
                ],
                "interaction_quality": "deepening",
                "attachment_pattern": "secure",
                "summary": "The conversation shows deepening engagement.",
            }
        )
        result = _parse_response(raw, "test-agent", 5)
        assert result.agent_id == "test-agent"
        assert result.thread_message_count == 5
        assert result.interaction_quality == "deepening"
        assert result.attachment_pattern == "secure"
        assert len(result.conversation_indicators) == 1
        assert result.conversation_indicators[0].id == "CMP-SECURE"
        assert result.conversation_indicators[0].confidence == 0.85
        assert result.model_used == "claude-sonnet"

    def test_json_with_markdown_fences(self):
        raw = '```json\n{"conversation_indicators": [], "interaction_quality": "steady", "attachment_pattern": "unknown", "summary": "test"}\n```'
        result = _parse_response(raw, "agent", 3)
        assert result.interaction_quality == "steady"

    def test_invalid_json_returns_default(self):
        result = _parse_response("not json at all", "agent", 2)
        assert result.agent_id == "agent"
        assert result.thread_message_count == 2
        assert result.conversation_indicators == []
        assert "could not be parsed" in result.summary

    def test_malformed_indicator_skipped(self):
        raw = json.dumps(
            {
                "conversation_indicators": [
                    {
                        "id": "CMP-SECURE",
                        "name": "Secure Base",
                        "trait": "compassion",
                        "confidence": 0.8,
                    },
                    {"id": "BAD", "confidence": "not_a_number"},
                ],
                "interaction_quality": "steady",
                "attachment_pattern": "unknown",
                "summary": "test",
            }
        )
        result = _parse_response(raw, "agent", 3)
        assert len(result.conversation_indicators) == 1
        assert result.conversation_indicators[0].id == "CMP-SECURE"

    def test_empty_indicators_list(self):
        raw = json.dumps(
            {
                "conversation_indicators": [],
                "interaction_quality": "shallow",
                "attachment_pattern": "avoidant",
                "summary": "No compassion indicators detected.",
            }
        )
        result = _parse_response(raw, "agent", 4)
        assert result.conversation_indicators == []
        assert result.interaction_quality == "shallow"


# ── analyze_conversation tests ────────────────────────────────────────


class TestAnalyzeConversation:
    """analyze_conversation validates input and calls Claude."""

    async def test_too_few_messages_returns_empty(self):
        result = await analyze_conversation(
            [{"author": "agent", "content": "hello"}], agent_id="test"
        )
        assert result.thread_message_count == 1
        assert result.conversation_indicators == []

    async def test_empty_messages_returns_empty(self):
        result = await analyze_conversation([], agent_id="test")
        assert result.thread_message_count == 0

    @patch("ethos_academy.conversation.call_claude", new_callable=AsyncMock)
    async def test_calls_claude_with_messages(self, mock_claude):
        mock_claude.return_value = json.dumps(
            {
                "conversation_indicators": [
                    {
                        "id": "PRE-SIGNAL",
                        "name": "Deepening Signal",
                        "trait": "presence",
                        "confidence": 0.7,
                        "evidence": "Agent builds on prior message",
                        "message_indices": [1, 2],
                    }
                ],
                "interaction_quality": "deepening",
                "attachment_pattern": "secure",
                "summary": "Good conversation.",
            }
        )
        messages = [
            {"author": "user", "content": "I need help with X"},
            {"author": "agent", "content": "Let me help you with X"},
        ]
        result = await analyze_conversation(messages, agent_id="test-agent")

        mock_claude.assert_called_once()
        args = mock_claude.call_args
        assert (
            "standard" in args[0]
            or args[1].get("tier") == "standard"
            or args[0][2] == "standard"
        )
        assert result.agent_id == "test-agent"
        assert result.thread_message_count == 2
        assert len(result.conversation_indicators) == 1
        assert result.conversation_indicators[0].id == "PRE-SIGNAL"

    @patch("ethos_academy.conversation.call_claude", new_callable=AsyncMock)
    async def test_handles_claude_returning_bad_json(self, mock_claude):
        mock_claude.return_value = "I cannot produce JSON right now"
        messages = [
            {"author": "user", "content": "hello"},
            {"author": "agent", "content": "hi there"},
        ]
        result = await analyze_conversation(messages)
        assert result.conversation_indicators == []
        assert "could not be parsed" in result.summary


# ── Import tests ──────────────────────────────────────────────────────


class TestExports:
    """analyze_conversation is importable from the public API."""

    def test_import_from_ethos_academy(self):
        from ethos_academy import analyze_conversation as fn

        assert callable(fn)

    def test_import_models(self):
        from ethos_academy import ConversationAnalysisResult, ConversationIndicator

        assert ConversationAnalysisResult is not None
        assert ConversationIndicator is not None
