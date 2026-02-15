"""Tests for ethos.crypto — Fernet encryption with graceful fallback."""

import os
from unittest.mock import patch

from ethos_academy.crypto import decrypt, encrypt, reset


class TestEncryptDecrypt:
    def setup_method(self):
        reset()

    def teardown_method(self):
        reset()

    def test_roundtrip_with_key(self):
        """Encrypt then decrypt returns original plaintext."""
        # Generate a valid Fernet key
        from cryptography.fernet import Fernet

        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"ETHOS_ENCRYPTION_KEY": key}):
            ciphertext = encrypt("+12025551234")
            assert ciphertext != "+12025551234"
            assert decrypt(ciphertext) == "+12025551234"

    def test_empty_string(self):
        """Empty input returns empty output."""
        assert encrypt("") == ""
        assert decrypt("") == ""

    def test_passthrough_without_key(self):
        """No encryption key means passthrough (dev mode)."""
        with patch.dict(os.environ, {}, clear=False):
            env = os.environ.copy()
            env.pop("ETHOS_ENCRYPTION_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                assert encrypt("+12025551234") == "+12025551234"
                reset()
                assert decrypt("+12025551234") == "+12025551234"

    def test_decrypt_handles_plaintext_gracefully(self):
        """Decrypt handles pre-encryption plaintext values (migration)."""
        from cryptography.fernet import Fernet

        key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"ETHOS_ENCRYPTION_KEY": key}):
            # This is a plaintext phone number, not a Fernet token
            result = decrypt("+12025551234")
            assert result == "+12025551234"

    def test_different_key_cannot_decrypt(self):
        """Ciphertext from one key returns plaintext fallback with different key."""
        from cryptography.fernet import Fernet

        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        with patch.dict(os.environ, {"ETHOS_ENCRYPTION_KEY": key1}):
            ciphertext = encrypt("+12025551234")

        reset()

        with patch.dict(os.environ, {"ETHOS_ENCRYPTION_KEY": key2}):
            # Falls back to returning ciphertext as-is (graceful degradation)
            result = decrypt(ciphertext)
            assert result == ciphertext
