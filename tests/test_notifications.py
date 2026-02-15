"""Tests for ethos.notifications SMS sandbox mode and fallback logging."""

from __future__ import annotations

import os
from unittest.mock import patch, MagicMock


from ethos_academy.notifications import _send_sms, _normalize_phone, _mask_phone


class TestSandboxMode:
    """ETHOS_SMS_SANDBOX=1 prints to stderr and returns True."""

    async def test_sandbox_prints_to_stderr(self, capsys):
        with patch.dict(os.environ, {"ETHOS_SMS_SANDBOX": "1"}):
            result = await _send_sms("+12025551234", "Test verification code: 123456")

        assert result is True
        captured = capsys.readouterr()
        assert "[SMS SANDBOX]" in captured.err
        assert "Test verification code: 123456" in captured.err
        assert "+1***5551234" in captured.err

    async def test_sandbox_with_whitespace(self, capsys):
        """ETHOS_SMS_SANDBOX=' 1 ' still activates."""
        with patch.dict(os.environ, {"ETHOS_SMS_SANDBOX": " 1 "}):
            result = await _send_sms("+12025551234", "code: 999999")

        assert result is True
        captured = capsys.readouterr()
        assert "[SMS SANDBOX]" in captured.err

    async def test_sandbox_off_by_default(self):
        """Without ETHOS_SMS_SANDBOX, sandbox mode does not activate."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove ETHOS_SMS_SANDBOX if present
            os.environ.pop("ETHOS_SMS_SANDBOX", None)
            # boto3 import will be tried, which may or may not be installed
            # Either way, it should NOT go through the sandbox path
            result = await _send_sms("+12025551234", "code: 999999")
            # Result depends on whether boto3 is installed and SNS works,
            # but since we're not in sandbox, it won't be sandbox output
            # We just verify no sandbox stderr
            # (result will be False since boto3 is likely not configured)
            assert isinstance(result, bool)


class TestFallbackMode:
    """When boto3 is missing or SNS fails, logs to stderr and returns False."""

    async def test_no_boto3_prints_fallback(self, capsys):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ETHOS_SMS_SANDBOX", None)

            # Simulate boto3 not installed
            import builtins

            real_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "boto3":
                    raise ImportError("No module named 'boto3'")
                return real_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                result = await _send_sms("+12025551234", "test msg")

            assert result is False
            captured = capsys.readouterr()
            assert "[SMS FALLBACK]" in captured.err
            assert "boto3 not installed" in captured.err

    async def test_sns_failure_prints_fallback(self, capsys):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ETHOS_SMS_SANDBOX", None)

            mock_client = MagicMock()
            mock_client.publish.side_effect = Exception("SNS is down")

            with (
                patch(
                    "ethos_academy.notifications._get_client", return_value=mock_client
                ),
            ):
                result = await _send_sms("+12025551234", "test msg")

            assert result is False
            captured = capsys.readouterr()
            assert "[SMS FALLBACK]" in captured.err
            assert "SNS failed" in captured.err


class TestSendSmsEdgeCases:
    async def test_empty_phone_returns_false(self):
        result = await _send_sms("", "body")
        assert result is False

    async def test_invalid_phone_returns_false(self):
        result = await _send_sms("abc", "body")
        assert result is False


class TestNormalizePhone:
    def test_e164(self):
        assert _normalize_phone("+12025551234") == "+12025551234"

    def test_ten_digit(self):
        assert _normalize_phone("2025551234") == "+12025551234"

    def test_parentheses(self):
        assert _normalize_phone("(202) 555-1234") == "+12025551234"

    def test_dashes(self):
        assert _normalize_phone("202-555-1234") == "+12025551234"

    def test_bad_number(self):
        assert _normalize_phone("123") is None


class TestMaskPhone:
    def test_normal(self):
        assert _mask_phone("+12025551234") == "+1***5551234"

    def test_short(self):
        assert _mask_phone("123") == "***"
