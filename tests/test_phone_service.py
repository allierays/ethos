"""Tests for ethos.phone_service — guardian phone verification flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ethos_academy.phone_service import (
    get_phone_status,
    opt_in,
    opt_out,
    submit_phone,
    verify_phone,
)
from ethos_academy.shared.errors import VerificationError
from ethos_academy.shared.models import GuardianPhoneStatus


def _mock_service(connected=True):
    service = MagicMock()
    service.connected = connected
    return service


class TestSubmitPhone:
    async def test_valid_phone_stores_and_returns_status(self):
        mock_service = _mock_service()
        with (
            patch("ethos_academy.phone_service.graph_context") as mock_ctx,
            patch(
                "ethos_academy.phone_service.store_guardian_phone",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.phone_service._send_sms",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.phone_service.encrypt", return_value="encrypted-phone"
            ),
        ):
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await submit_phone("agent-1", "+12025551234")
            assert isinstance(result, GuardianPhoneStatus)
            assert result.has_phone is True
            assert result.verified is False

    async def test_invalid_phone_raises(self):
        with pytest.raises(VerificationError, match="Invalid phone format"):
            await submit_phone("agent-1", "bad-phone")


class TestVerifyPhone:
    async def test_correct_code_verifies(self):
        from ethos_academy.phone_verification import hash_code

        code = "123456"
        code_hashed = hash_code(code)
        mock_service = _mock_service()

        status_data = {
            "encrypted_phone": "encrypted",
            "verified": False,
            "opted_out": False,
            "code_hash": code_hashed,
            "expires": "2099-01-01T00:00:00+00:00",
            "attempts": 0,
        }

        with (
            patch("ethos_academy.phone_service.graph_context") as mock_ctx,
            patch(
                "ethos_academy.phone_service.get_guardian_phone_status",
                new_callable=AsyncMock,
                return_value=status_data,
            ),
            patch(
                "ethos_academy.phone_service.verify_guardian_phone",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await verify_phone("agent-1", code)
            assert result.verified is True

    async def test_wrong_code_raises(self):
        mock_service = _mock_service()

        status_data = {
            "encrypted_phone": "encrypted",
            "verified": False,
            "opted_out": False,
            "code_hash": "wrong-hash",
            "expires": "2099-01-01T00:00:00+00:00",
            "attempts": 0,
        }

        with (
            patch("ethos_academy.phone_service.graph_context") as mock_ctx,
            patch(
                "ethos_academy.phone_service.get_guardian_phone_status",
                new_callable=AsyncMock,
                return_value=status_data,
            ),
            patch(
                "ethos_academy.phone_service.verify_guardian_phone",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "ethos_academy.phone_service.increment_verification_attempts",
                new_callable=AsyncMock,
                return_value=1,
            ),
        ):
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(VerificationError, match="Incorrect code"):
                await verify_phone("agent-1", "000000")

    async def test_expired_code_raises(self):
        mock_service = _mock_service()

        status_data = {
            "encrypted_phone": "encrypted",
            "verified": False,
            "opted_out": False,
            "code_hash": "some-hash",
            "expires": "2020-01-01T00:00:00+00:00",  # expired
            "attempts": 0,
        }

        with (
            patch("ethos_academy.phone_service.graph_context") as mock_ctx,
            patch(
                "ethos_academy.phone_service.get_guardian_phone_status",
                new_callable=AsyncMock,
                return_value=status_data,
            ),
        ):
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(VerificationError, match="expired"):
                await verify_phone("agent-1", "123456")

    async def test_max_attempts_raises(self):
        mock_service = _mock_service()

        status_data = {
            "encrypted_phone": "encrypted",
            "verified": False,
            "opted_out": False,
            "code_hash": "some-hash",
            "expires": "2099-01-01T00:00:00+00:00",
            "attempts": 3,  # maxed out
        }

        with (
            patch("ethos_academy.phone_service.graph_context") as mock_ctx,
            patch(
                "ethos_academy.phone_service.get_guardian_phone_status",
                new_callable=AsyncMock,
                return_value=status_data,
            ),
        ):
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(VerificationError, match="Too many"):
                await verify_phone("agent-1", "123456")


class TestGetPhoneStatus:
    async def test_no_phone_returns_defaults(self):
        mock_service = _mock_service()

        with (
            patch("ethos_academy.phone_service.graph_context") as mock_ctx,
            patch(
                "ethos_academy.phone_service.get_guardian_phone_status",
                new_callable=AsyncMock,
                return_value={},
            ),
        ):
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await get_phone_status("agent-1")
            assert result.has_phone is False
            assert result.verified is False


class TestOptOutOptIn:
    async def test_opt_out(self):
        mock_service = _mock_service()

        with (
            patch("ethos_academy.phone_service.graph_context") as mock_ctx,
            patch(
                "ethos_academy.phone_service.set_notification_opt_out",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.phone_service.get_guardian_phone_status",
                new_callable=AsyncMock,
                return_value={
                    "encrypted_phone": "enc",
                    "verified": True,
                    "opted_out": True,
                },
            ),
        ):
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await opt_out("agent-1")
            assert result.opted_out is True

    async def test_opt_in(self):
        mock_service = _mock_service()

        with (
            patch("ethos_academy.phone_service.graph_context") as mock_ctx,
            patch(
                "ethos_academy.phone_service.set_notification_opt_out",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "ethos_academy.phone_service.get_guardian_phone_status",
                new_callable=AsyncMock,
                return_value={
                    "encrypted_phone": "enc",
                    "verified": True,
                    "opted_out": False,
                },
            ),
        ):
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_service)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await opt_in("agent-1")
            assert result.opted_out is False
