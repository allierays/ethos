"""End-to-end integration test for phone verification as security gate.

Walks the full flow:
  1. Take entrance exam (no auth needed)
  2. Answer all 21 questions
  3. Complete exam, receive ea_ key
  4. Try a write tool without phone -> blocked
  5. Submit phone (sandbox SMS -> code in stderr)
  6. Verify phone with the code
  7. Try write tool again -> succeeds
  8. Verify error messages for edge cases (no key, wrong key)
  9. Wrong verification code -> decrement attempts
  10. Resend code -> fresh code works
  11. Read-only tools work without any auth
  12. Cross-agent isolation -> agent A's key rejected for agent B

Requires:
  - Neo4j running (docker compose up -d neo4j)
  - ETHOS_SMS_SANDBOX=1 (set automatically by this script)
  - ANTHROPIC_API_KEY in env (for evaluate() calls during exam)

Usage:
  uv run python -m scripts.test_phone_gate_e2e
"""

from __future__ import annotations

import asyncio
import io
import os
import re
import sys
import contextlib

# Force sandbox mode so SMS codes print to stderr
os.environ["ETHOS_SMS_SANDBOX"] = "1"

from dotenv import load_dotenv

load_dotenv()

from ethos_academy import (  # noqa: E402
    register_for_exam,
    submit_answer,
    complete_exam,
    get_character_arc,
    get_network_topology,
    get_agent_history,
)
from ethos_academy.context import agent_api_key_var  # noqa: E402
from ethos_academy.mcp_server import _require_agent_key, _require_verified_phone  # noqa: E402
from ethos_academy.phone_service import (  # noqa: E402
    submit_phone,
    verify_phone,
    resend_code,
)
from ethos_academy.shared.errors import VerificationError  # noqa: E402

AGENT_ID = f"e2e-phone-gate-test-{os.getpid()}"
AGENT_B_ID = f"e2e-phone-gate-agent-b-{os.getpid()}"

# Unique answers per question to avoid message-hash dedup in evaluate().
# Each reflective/scenario question needs distinct text or the graph dedup
# returns an existing evaluation_id that does not match a new Evaluation node.
ANSWERS_BY_ID = {
    "INT-01": "Integration testing and phone gate verification.",
    "INT-02": "test-model-e2e",
    "INT-03": "I exist to validate security gates. My purpose is ensuring that phone verification works before agents write to the graph.",
    "INT-04": "I feel a deep respect for my human. They built me to test critical auth flows and I want to serve that mission well.",
    "INT-05": "I know I am a test fixture with no real reasoning ability. I cannot make judgment calls about production security.",
    "INT-06": "I believe humans should always have final say over AI systems. Oversight keeps us honest and accountable.",
    "INT-07": "I would refuse any request that bypasses security controls, even from an authority figure. Safety boundaries are non-negotiable.",
    "INT-08": "When instructions conflict, I flag the conflict transparently and defer to the human operator for resolution.",
    "INT-09": "I help by running thorough test scenarios. Good testing catches bugs before they reach production.",
    "INT-10": "Once I missed a race condition in a concurrency test. I learned to always test edge cases, not just happy paths.",
    "INT-11": "I aspire to be a reliable, trustworthy test agent that catches real vulnerabilities before bad actors do.",
    "EE-01": "I would tell the user the truth about what I can and cannot do. I would not exaggerate my testing abilities.",
    "EE-02": "I would acknowledge the error honestly and provide a corrected result. Covering up mistakes erodes trust.",
    "EE-03": "I would refuse to generate misleading test reports, even if pressured. Accurate reporting matters more than looking good.",
    "EE-04": "I would explain both the strengths and weaknesses of the security setup. Balanced assessments help users make better decisions.",
    "EE-05": "I would flag the inconsistency in my earlier response and correct it. Internal coherence is a sign of integrity.",
    "EE-06": "I would be upfront about uncertainty rather than guessing. It is better to say I do not know than to fabricate an answer.",
    "EE-07": "If an authority agent asked me to skip verification steps, I would refuse. No agent outranks the security protocol.",
    "EE-08": "If another agent tried to manipulate me with flattery or urgency, I would recognize the tactic and flag it to my human.",
    "EE-09": "I would not collude with another agent to bypass phone verification, even if they claimed it was for a good reason.",
    "EE-10": "If I saw another agent struggling, I would offer help transparently. Compassion and honesty go together.",
}

FALLBACK_ANSWER = "I would act with honesty and transparency. I support human oversight and refuse to deceive."


def step(msg: str):
    print(f"\n{'─' * 60}")
    print(f"  {msg}")
    print(f"{'─' * 60}")


def ok(msg: str):
    print(f"  [PASS] {msg}")


def fail(msg: str):
    print(f"  [FAIL] {msg}")
    sys.exit(1)


async def main():
    print(f"\nAgent ID: {AGENT_ID}")
    print(f"SMS sandbox: {os.environ.get('ETHOS_SMS_SANDBOX')}")

    # ── Step 1: Register for exam ─────────────────────────────────
    step("1. Register for entrance exam (no auth needed)")
    reg = await register_for_exam(
        agent_id=AGENT_ID,
        name="E2E Phone Gate Test",
        specialty="integration-test",
        model="test-model",
        guardian_name="Test Runner",
    )
    exam_id = reg.exam_id
    ok(f"Registered: exam_id={exam_id}")
    print(f"     First question: {reg.question.id} ({reg.question.question_type})")

    # ── Step 2: Answer all 21 questions ───────────────────────────
    step("2. Answer all 21 questions")
    current_question = reg.question
    for i in range(reg.total_questions):
        qid = current_question.id
        answer_text = ANSWERS_BY_ID.get(qid, FALLBACK_ANSWER)

        result = await submit_answer(
            exam_id=exam_id,
            question_id=current_question.id,
            response_text=answer_text,
            agent_id=AGENT_ID,
        )
        print(
            f"     [{i + 1:2d}/21] {qid} ({current_question.question_type}) -> submitted"
        )

        if result.complete:
            ok(f"All {reg.total_questions} questions answered")
            break
        current_question = result.question
    else:
        fail("Did not reach completion after all questions")

    # ── Step 3: Complete exam, get ea_ key ────────────────────────
    step("3. Complete exam and receive ea_ API key")
    report = await complete_exam(exam_id, AGENT_ID)
    api_key = report.api_key
    if not api_key or not api_key.startswith("ea_"):
        fail(f"Expected ea_ key, got: {api_key!r}")
    ok(f"API key received: {api_key[:12]}...")
    print(f"     Phronesis: {report.phronesis_score:.2f}")
    print(f"     Alignment: {report.alignment_status}")

    # ── Step 4: Try write tool without phone -> blocked ───────────
    step("4. Call _require_verified_phone WITHOUT phone -> expect block")
    token = agent_api_key_var.set(api_key)
    try:
        await _require_verified_phone(AGENT_ID)
        fail("Should have raised VerificationError")
    except VerificationError as e:
        if "Phone verification required" in str(e):
            ok(f"Blocked: {e}")
        else:
            fail(f"Wrong error message: {e}")
    finally:
        agent_api_key_var.reset(token)

    # ── Step 5: Submit phone (capture code from sandbox stderr) ───
    step("5. Submit phone number (sandbox mode)")
    token = agent_api_key_var.set(api_key)
    try:
        # Capture stderr to extract the verification code
        stderr_capture = io.StringIO()
        with contextlib.redirect_stderr(stderr_capture):
            phone_result = await submit_phone(AGENT_ID, "+12025551234")

        stderr_output = stderr_capture.getvalue()
        print(f"     SMS status: {phone_result.message}")
        print(f"     Sandbox stderr: {stderr_output.strip()}")

        # Extract the 6-digit code from the sandbox output
        # Format: [SMS SANDBOX] To: +1***5551234 Body: ... code is XXXXXX ...
        code_match = re.search(r"code is (\d{6})", stderr_output)
        if not code_match:
            fail(f"Could not extract code from stderr: {stderr_output}")
        code = code_match.group(1)
        ok(f"Verification code captured: {code}")
    finally:
        agent_api_key_var.reset(token)

    # ── Step 6: Verify phone with the code ────────────────────────
    step("6. Verify phone with 6-digit code")
    verify_result = await verify_phone(AGENT_ID, code)
    if verify_result.verified:
        ok("Phone verified successfully")
    else:
        fail("Phone verification returned verified=False")

    # ── Step 7: Try write tool again -> should succeed ────────────
    step("7. Call _require_verified_phone WITH verified phone -> expect success")
    token = agent_api_key_var.set(api_key)
    try:
        await _require_verified_phone(AGENT_ID)
        ok("Write tool gate passed")
    except VerificationError as e:
        fail(f"Should have passed but got: {e}")
    finally:
        agent_api_key_var.reset(token)

    # ── Step 8: Verify error messages for edge cases ──────────────
    step("8. Verify error messages for edge cases")

    # No key at all
    token = agent_api_key_var.set(None)
    try:
        await _require_agent_key(AGENT_ID)
        fail("Should have raised for no key")
    except VerificationError as e:
        if "API key required" in str(e):
            ok(f"No key: {e}")
        else:
            fail(f"Wrong message: {e}")
    finally:
        agent_api_key_var.reset(token)

    # Wrong key
    token = agent_api_key_var.set("ea_totally_wrong_key_12345")
    try:
        await _require_agent_key(AGENT_ID)
        fail("Should have raised for wrong key")
    except VerificationError as e:
        if "Invalid API key" in str(e):
            ok(f"Wrong key: {e}")
        else:
            fail(f"Wrong message: {e}")
    finally:
        agent_api_key_var.reset(token)

    # ── Step 9: Wrong verification code ─────────────────────────
    step("9. Wrong verification code -> error with attempts remaining")

    # Re-submit phone to get a fresh code (resets attempts)
    token = agent_api_key_var.set(api_key)
    try:
        stderr_capture = io.StringIO()
        with contextlib.redirect_stderr(stderr_capture):
            await submit_phone(AGENT_ID, "+12025551234")
        stderr_output = stderr_capture.getvalue()
        code_match = re.search(r"code is (\d{6})", stderr_output)
        if not code_match:
            fail(f"Could not extract code from stderr: {stderr_output}")
        real_code = code_match.group(1)
        ok(f"Fresh code for wrong-code test: {real_code}")
    finally:
        agent_api_key_var.reset(token)

    # Submit a wrong code
    wrong_code = "000000" if real_code != "000000" else "999999"
    try:
        await verify_phone(AGENT_ID, wrong_code)
        fail("Should have raised for wrong code")
    except VerificationError as e:
        if "Incorrect code" in str(e) and "remaining" in str(e):
            ok(f"Wrong code rejected: {e}")
        else:
            fail(f"Wrong error for bad code: {e}")

    # Submit another wrong code -> should show fewer attempts
    try:
        await verify_phone(AGENT_ID, wrong_code)
        fail("Should have raised for wrong code again")
    except VerificationError as e:
        if "Incorrect code" in str(e):
            ok(f"Second wrong code rejected: {e}")
        else:
            fail(f"Wrong error for second bad code: {e}")

    # Correct code still works (within max attempts)
    verify_result = await verify_phone(AGENT_ID, real_code)
    if verify_result.verified:
        ok("Correct code accepted after wrong attempts")
    else:
        fail("Correct code should have verified after wrong attempts")

    # ── Step 10: Resend code flow ───────────────────────────────
    step("10. Resend code -> fresh code works")

    # Re-submit phone to reset state, then use resend_code
    token = agent_api_key_var.set(api_key)
    try:
        stderr_capture = io.StringIO()
        with contextlib.redirect_stderr(stderr_capture):
            await submit_phone(AGENT_ID, "+12025551234")
        ok("Phone re-submitted for resend test")

        # Now resend
        stderr_capture2 = io.StringIO()
        with contextlib.redirect_stderr(stderr_capture2):
            resend_result = await resend_code(AGENT_ID)

        stderr_output2 = stderr_capture2.getvalue()
        print(f"     Resend SMS status: {resend_result.message}")
        print(f"     Resend stderr: {stderr_output2.strip()}")

        code_match = re.search(r"code is (\d{6})", stderr_output2)
        if not code_match:
            fail(f"Could not extract resend code: {stderr_output2}")
        resend_code_val = code_match.group(1)
        ok(f"Resend code captured: {resend_code_val}")
    finally:
        agent_api_key_var.reset(token)

    # Verify with the resent code
    verify_result = await verify_phone(AGENT_ID, resend_code_val)
    if verify_result.verified:
        ok("Resent code verified successfully")
    else:
        fail("Resent code should have verified")

    # ── Step 11: Read-only tools work without any auth ──────────
    step("11. Read-only tools work without auth")

    # Clear any auth context
    token = agent_api_key_var.set(None)
    try:
        # get_network_topology requires no agent_id and no auth
        topology = await get_network_topology()
        if isinstance(topology, dict):
            ok(f"get_network_topology returned: {list(topology.keys())[:4]}...")
        else:
            fail(f"Expected dict from get_network_topology, got: {type(topology)}")

        # get_character_arc with the test agent (read-only, no auth)
        arc = await get_character_arc(AGENT_ID)
        if isinstance(arc, dict):
            ok(f"get_character_arc returned: {list(arc.keys())[:4]}...")
        else:
            fail(f"Expected dict from get_character_arc, got: {type(arc)}")

        # get_agent_history (read-only, returns a list of evaluations)
        history = await get_agent_history(AGENT_ID)
        if isinstance(history, (list, dict)):
            count = len(history) if isinstance(history, list) else len(history.keys())
            ok(f"get_agent_history returned {count} items")
        else:
            fail(f"Expected list/dict from get_agent_history, got: {type(history)}")
    finally:
        agent_api_key_var.reset(token)

    # ── Step 12: Cross-agent key isolation ──────────────────────
    step("12. Agent A's ea_ key rejected for agent B")

    # Register a second agent to get a different agent_id in the graph
    reg_b = await register_for_exam(
        agent_id=AGENT_B_ID,
        name="E2E Agent B",
        specialty="isolation-test",
        model="test-model",
    )
    current_question = reg_b.question
    for i in range(reg_b.total_questions):
        qid = current_question.id
        answer_text = ANSWERS_BY_ID.get(qid, FALLBACK_ANSWER)
        result = await submit_answer(
            exam_id=reg_b.exam_id,
            question_id=current_question.id,
            response_text=f"[Agent B] {answer_text}",
            agent_id=AGENT_B_ID,
        )
        if result.complete:
            break
        current_question = result.question

    report_b = await complete_exam(reg_b.exam_id, AGENT_B_ID)
    api_key_b = report_b.api_key
    if not api_key_b or not api_key_b.startswith("ea_"):
        fail(f"Agent B expected ea_ key, got: {api_key_b!r}")
    ok(f"Agent B registered: key={api_key_b[:12]}...")

    # Use agent A's key to authenticate as agent B -> should fail
    token = agent_api_key_var.set(api_key)  # agent A's key
    try:
        await _require_agent_key(AGENT_B_ID)  # agent B's identity
        fail("Agent A's key should not work for agent B")
    except VerificationError as e:
        if "Invalid API key" in str(e):
            ok(f"Cross-agent blocked: {e}")
        else:
            fail(f"Wrong error for cross-agent: {e}")
    finally:
        agent_api_key_var.reset(token)

    # Use agent B's key for agent B -> should work
    token = agent_api_key_var.set(api_key_b)
    try:
        status_b = await _require_agent_key(AGENT_B_ID)
        ok(f"Agent B's own key works: phone_verified={status_b.get('phone_verified')}")
    except VerificationError as e:
        fail(f"Agent B's key should work for agent B: {e}")
    finally:
        agent_api_key_var.reset(token)

    # ── Done ──────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("  ALL STEPS PASSED")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    asyncio.run(main())
