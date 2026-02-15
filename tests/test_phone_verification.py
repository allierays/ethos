"""Tests for ethos.phone_verification — pure verification utilities."""

from datetime import datetime, timedelta, timezone

from ethos_academy.phone_verification import (
    MAX_VERIFICATION_ATTEMPTS,
    VERIFICATION_TTL_MINUTES,
    generate_verification_code,
    hash_code,
    is_expired,
    verification_expiry,
)


class TestGenerateCode:
    def test_returns_six_digits(self):
        code = generate_verification_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_codes_are_unique(self):
        codes = {generate_verification_code() for _ in range(100)}
        # With 6-digit codes and 100 samples, collisions are extremely unlikely
        assert len(codes) > 90

    def test_zero_padded(self):
        """Codes with leading zeros are properly padded."""
        # Run enough times to statistically encounter a leading-zero code
        codes = [generate_verification_code() for _ in range(1000)]
        assert all(len(c) == 6 for c in codes)


class TestHashCode:
    def test_deterministic(self):
        assert hash_code("123456") == hash_code("123456")

    def test_different_codes_different_hashes(self):
        assert hash_code("123456") != hash_code("654321")

    def test_returns_hex_string(self):
        result = hash_code("123456")
        assert len(result) == 64  # SHA-256 hex digest
        int(result, 16)  # Validates hex


class TestVerificationExpiry:
    def test_returns_future_datetime(self):
        expiry = verification_expiry()
        parsed = datetime.fromisoformat(expiry)
        assert parsed > datetime.now(timezone.utc)

    def test_approximately_ten_minutes(self):
        expiry = verification_expiry()
        parsed = datetime.fromisoformat(expiry)
        delta = parsed - datetime.now(timezone.utc)
        assert timedelta(minutes=9) < delta < timedelta(minutes=11)


class TestIsExpired:
    def test_future_not_expired(self):
        future = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        assert is_expired(future) is False

    def test_past_is_expired(self):
        past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        assert is_expired(past) is True

    def test_empty_string_expired(self):
        assert is_expired("") is True

    def test_invalid_string_expired(self):
        assert is_expired("not-a-date") is True

    def test_none_expired(self):
        assert is_expired(None) is True


class TestConstants:
    def test_ttl_is_ten_minutes(self):
        assert VERIFICATION_TTL_MINUTES == 10

    def test_max_attempts_is_three(self):
        assert MAX_VERIFICATION_ATTEMPTS == 3
