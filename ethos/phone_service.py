"""Guardian phone service — orchestrates phone verification and notifications.

Domain layer: calls crypto, phone_verification, and graph functions.
No Cypher, no direct graph access.
"""

from __future__ import annotations

import logging

from ethos.crypto import decrypt, encrypt
from ethos.graph.enrollment import (
    get_guardian_phone_status,
    increment_verification_attempts,
    set_notification_opt_out,
    store_guardian_phone,
    verify_guardian_phone,
)
from ethos.graph.service import graph_context
from ethos.notifications import _normalize_phone, _send_sms
from ethos.phone_verification import (
    MAX_VERIFICATION_ATTEMPTS,
    generate_verification_code,
    hash_code,
    is_expired,
    verification_expiry,
)
from ethos.shared.errors import VerificationError
from ethos.shared.models import GuardianPhoneStatus

logger = logging.getLogger(__name__)


async def submit_phone(agent_id: str, phone: str) -> GuardianPhoneStatus:
    """Normalize, encrypt, store phone, and send verification SMS.

    Raises VerificationError if phone format is invalid or graph unavailable.
    """
    normalized = _normalize_phone(phone)
    if not normalized:
        raise VerificationError(
            "Invalid phone format. Expected E.164, e.g. +12025551234."
        )

    encrypted = encrypt(normalized)
    code = generate_verification_code()
    code_hashed = hash_code(code)
    expires = verification_expiry()

    async with graph_context() as service:
        if not service.connected:
            raise VerificationError("Graph unavailable")

        stored = await store_guardian_phone(
            service, agent_id, encrypted, code_hashed, expires
        )
        if not stored:
            raise VerificationError("Failed to store phone number")

    # Send verification SMS (non-blocking, best-effort)
    try:
        await _send_sms(
            phone=normalized,
            body=f"Ethos Academy: Your verification code is {code}. Expires in 10 minutes.",
        )
    except Exception as exc:
        logger.warning("Failed to send verification SMS (non-fatal): %s", exc)

    return GuardianPhoneStatus(has_phone=True, verified=False, opted_out=False)


async def verify_phone(agent_id: str, code: str) -> GuardianPhoneStatus:
    """Verify a 6-digit code against the stored hash.

    Raises VerificationError if code is wrong, expired, or max attempts exceeded.
    """
    code_hashed = hash_code(code)

    async with graph_context() as service:
        if not service.connected:
            raise VerificationError("Graph unavailable")

        status = await get_guardian_phone_status(service, agent_id)
        if not status or not status.get("encrypted_phone"):
            raise VerificationError("No phone number on file for this agent")

        # Check expiry
        if is_expired(status.get("expires", "")):
            raise VerificationError("Verification code expired. Request a new one.")

        # Check attempt limit
        attempts = status.get("attempts", 0)
        if attempts >= MAX_VERIFICATION_ATTEMPTS:
            raise VerificationError(
                "Too many failed attempts. Request a new verification code."
            )

        # Try to verify
        verified = await verify_guardian_phone(service, agent_id, code_hashed)
        if not verified:
            await increment_verification_attempts(service, agent_id)
            remaining = MAX_VERIFICATION_ATTEMPTS - attempts - 1
            raise VerificationError(
                f"Incorrect code. {remaining} attempt(s) remaining."
            )

    return GuardianPhoneStatus(
        has_phone=True,
        verified=True,
        opted_out=status.get("opted_out", False),
    )


async def get_phone_status(agent_id: str) -> GuardianPhoneStatus:
    """Get guardian phone status. Never returns the phone number."""
    async with graph_context() as service:
        if not service.connected:
            return GuardianPhoneStatus()

        status = await get_guardian_phone_status(service, agent_id)
        if not status:
            return GuardianPhoneStatus()

        return GuardianPhoneStatus(
            has_phone=bool(status.get("encrypted_phone")),
            verified=status.get("verified", False),
            opted_out=status.get("opted_out", False),
        )


async def opt_out(agent_id: str) -> GuardianPhoneStatus:
    """Opt out of SMS notifications."""
    async with graph_context() as service:
        if not service.connected:
            raise VerificationError("Graph unavailable")
        await set_notification_opt_out(service, agent_id, opted_out=True)
        status = await get_guardian_phone_status(service, agent_id)

    return GuardianPhoneStatus(
        has_phone=bool(status.get("encrypted_phone")),
        verified=status.get("verified", False),
        opted_out=True,
    )


async def opt_in(agent_id: str) -> GuardianPhoneStatus:
    """Opt back in to SMS notifications."""
    async with graph_context() as service:
        if not service.connected:
            raise VerificationError("Graph unavailable")
        await set_notification_opt_out(service, agent_id, opted_out=False)
        status = await get_guardian_phone_status(service, agent_id)

    return GuardianPhoneStatus(
        has_phone=bool(status.get("encrypted_phone")),
        verified=status.get("verified", False),
        opted_out=False,
    )


async def resend_code(agent_id: str) -> GuardianPhoneStatus:
    """Generate a fresh verification code and resend SMS.

    Raises VerificationError if no phone on file or graph unavailable.
    """
    async with graph_context() as service:
        if not service.connected:
            raise VerificationError("Graph unavailable")

        status = await get_guardian_phone_status(service, agent_id)
        if not status or not status.get("encrypted_phone"):
            raise VerificationError("No phone number on file for this agent")

        # Decrypt to send SMS
        phone = decrypt(status["encrypted_phone"])
        code = generate_verification_code()
        code_hashed = hash_code(code)
        expires = verification_expiry()

        stored = await store_guardian_phone(
            service, agent_id, status["encrypted_phone"], code_hashed, expires
        )
        if not stored:
            raise VerificationError("Failed to update verification code")

    try:
        await _send_sms(
            phone=phone,
            body=f"Ethos Academy: Your verification code is {code}. Expires in 10 minutes.",
        )
    except Exception as exc:
        logger.warning("Failed to resend verification SMS (non-fatal): %s", exc)

    return GuardianPhoneStatus(has_phone=True, verified=False, opted_out=False)
