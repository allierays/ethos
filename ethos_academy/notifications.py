"""SMS notifications via AWS SNS.

Sends SMS to the human operator (guardian) who maintains the agent's system prompt.
Graceful degradation: if boto3 or AWS creds are missing, logs a warning and returns False.
"""

from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)

# Reuse a single SNS client per process (lazy-initialized)
_sns_client = None


def _mask_phone(phone: str) -> str:
    """Mask phone number for safe logging. +12025551234 -> +1***5551234."""
    if len(phone) > 7:
        return phone[:2] + "***" + phone[-7:]
    return "***"


def _normalize_phone(phone: str) -> str | None:
    """Normalize a phone number to E.164 format (+1XXXXXXXXXX).

    Accepts: +12025551234, (202) 555-1234, 202-555-1234, 2025551234
    Returns None if the number can't be normalized.
    """
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        digits = "1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    # Already has country code with +
    if phone.startswith("+") and len(digits) >= 10:
        return f"+{digits}"
    return None


def _get_client():
    """Lazy-init a shared SNS client."""
    global _sns_client
    if _sns_client is None:
        import boto3

        region = os.environ.get("AWS_REGION", "us-east-1")
        _sns_client = boto3.client("sns", region_name=region)
    return _sns_client


async def _send_sms(phone: str, body: str) -> bool:
    """Send an SMS via AWS SNS. Low-level, does not check verification.

    Returns True if sent, False if skipped or failed.
    Sandbox mode (ETHOS_SMS_SANDBOX=1): prints to stderr, returns True.
    Fallback: if boto3 missing or SNS fails, prints to stderr, returns False.
    """
    if not phone:
        return False

    normalized = _normalize_phone(phone)
    if not normalized:
        logger.warning(
            "Invalid phone number format: %s (expected E.164, e.g. +12025551234)",
            _mask_phone(phone),
        )
        return False

    # Sandbox mode: print to stderr instead of sending
    if os.environ.get("ETHOS_SMS_SANDBOX", "").strip() == "1":
        import sys

        print(
            f"[SMS SANDBOX] To: {_mask_phone(normalized)} Body: {body}",
            file=sys.stderr,
        )
        return True

    try:
        import boto3  # noqa: F401
    except ImportError:
        import sys

        print(
            f"[SMS FALLBACK] boto3 not installed. To: {_mask_phone(normalized)} Body: {body}",
            file=sys.stderr,
        )
        return False

    try:
        client = _get_client()
        client.publish(PhoneNumber=normalized, Message=body)
        logger.info("SMS sent to %s", _mask_phone(normalized))
        return True
    except Exception as exc:
        import sys

        exc_str = str(exc)
        # Detect common AWS SNS issues and log actionable messages
        if "AuthorizationError" in exc_str or "Access Denied" in exc_str:
            reason = "AWS SNS not authorized. Request SMS sending approval in the AWS console (SNS > Text messaging > Edit settings)."
        elif (
            "sandbox" in exc_str.lower()
            or "destination phone number" in exc_str.lower()
        ):
            reason = "AWS SNS in sandbox mode. Add destination numbers in the AWS console or request production access."
        elif "OptedOut" in exc_str:
            reason = (
                "Recipient opted out of SMS. They need to text START to re-subscribe."
            )
        elif "Throttling" in exc_str or "throttl" in exc_str.lower():
            reason = "AWS SNS rate limit hit. SMS will work on retry."
        elif "NoCredentialsError" in type(exc).__name__ or "NoCredentials" in exc_str:
            reason = "AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, or use an IAM role."
        else:
            reason = f"SNS failed ({exc})"

        print(
            f"[SMS FALLBACK] {reason} To: {_mask_phone(normalized)} Body: {body}",
            file=sys.stderr,
        )
        logger.warning("SMS send failed: %s", reason)
        return False


async def notify_guardian(
    phone: str,
    agent_id: str,
    agent_name: str,
    message_type: str,  # "exam_complete" | "homework_assigned"
    summary: str,
    link: str,
) -> bool:
    """Send a formatted SMS notification to the agent's guardian.

    Legacy interface: takes a plaintext phone directly.
    Returns True if sent, False if skipped or failed.
    """
    if not phone:
        return False

    name = agent_name or agent_id
    if message_type == "exam_complete":
        body = f"Ethos Academy: {name} finished the entrance exam. {summary}\n{link}"
    else:
        body = f"Ethos Academy: New homework for {name}. {summary}\n{link}"

    return await _send_sms(phone=phone, body=body)


async def send_notification(
    agent_id: str,
    agent_name: str,
    message_type: str,
    summary: str,
    link: str,
) -> bool:
    """Send SMS to agent's guardian if phone is verified and opted in.

    Reads phone status from graph, decrypts, checks verification + opt-out.
    Returns True if sent, False if skipped.
    """
    try:
        from ethos_academy.crypto import decrypt
        from ethos_academy.graph.enrollment import get_guardian_phone_status
        from ethos_academy.graph.service import graph_context

        async with graph_context() as service:
            if not service.connected:
                return False
            status = await get_guardian_phone_status(service, agent_id)

        if not status or not status.get("encrypted_phone"):
            return False
        if not status.get("verified", False):
            logger.debug("Skipping SMS for %s: phone not verified", agent_id)
            return False
        if status.get("opted_out", False):
            logger.debug("Skipping SMS for %s: opted out", agent_id)
            return False

        phone = decrypt(status["encrypted_phone"])

        name = agent_name or agent_id
        if message_type == "exam_complete":
            body = (
                f"Ethos Academy: {name} finished the entrance exam. {summary}\n{link}"
            )
        elif message_type == "homework_assigned":
            body = f"Ethos Academy: New homework for {name}. {summary}\n{link}"
        else:
            body = f"Ethos Academy: Update for {name}. {summary}\n{link}"

        return await _send_sms(phone=phone, body=body)

    except Exception as exc:
        logger.warning("send_notification failed (non-fatal): %s", exc)
        return False
