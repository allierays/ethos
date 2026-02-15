"""TDD tests for ethos.config domain — EthosConfig, priorities, thresholds."""

import pytest

from ethos_academy.shared.errors import ConfigError
from ethos_academy.shared.models import Priority


# ── EthosConfig ──────────────────────────────────────────────────────


class TestEthosConfig:
    """EthosConfig dataclass with from_env() classmethod."""

    def test_config_has_required_fields(self):
        from ethos_academy.config.config import EthosConfig

        cfg = EthosConfig(anthropic_api_key="sk-test")
        assert cfg.anthropic_api_key == "sk-test"
        assert cfg.neo4j_uri == "bolt://localhost:7694"
        assert cfg.neo4j_user == "neo4j"
        assert cfg.neo4j_password == "password"
        assert isinstance(cfg.priorities, dict)

    def test_config_custom_values(self):
        from ethos_academy.config.config import EthosConfig

        cfg = EthosConfig(
            anthropic_api_key="sk-custom",
            neo4j_uri="bolt://custom:7687",
            neo4j_user="admin",
            neo4j_password="secret",
        )
        assert cfg.anthropic_api_key == "sk-custom"
        assert cfg.neo4j_uri == "bolt://custom:7687"
        assert cfg.neo4j_user == "admin"
        assert cfg.neo4j_password == "secret"


class TestFromEnv:
    """from_env() classmethod loads from environment variables."""

    def test_from_env_with_api_key(self, monkeypatch):
        from ethos_academy.config.config import EthosConfig

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-env")
        monkeypatch.delenv("NEO4J_URI", raising=False)
        monkeypatch.delenv("NEO4J_USER", raising=False)
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
        cfg = EthosConfig.from_env()
        assert cfg.anthropic_api_key == "sk-from-env"
        assert cfg.neo4j_uri == "bolt://localhost:7694"
        assert cfg.neo4j_user == "neo4j"
        assert cfg.neo4j_password == "password"

    def test_from_env_with_all_vars(self, monkeypatch):
        from ethos_academy.config.config import EthosConfig

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-full")
        monkeypatch.setenv("NEO4J_URI", "bolt://prod:7687")
        monkeypatch.setenv("NEO4J_USER", "produser")
        monkeypatch.setenv("NEO4J_PASSWORD", "prodsecret")
        cfg = EthosConfig.from_env()
        assert cfg.anthropic_api_key == "sk-full"
        assert cfg.neo4j_uri == "bolt://prod:7687"
        assert cfg.neo4j_user == "produser"
        assert cfg.neo4j_password == "prodsecret"

    def test_from_env_missing_api_key_raises(self, monkeypatch):
        from ethos_academy.config.config import EthosConfig

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ConfigError):
            EthosConfig.from_env()

    def test_from_env_error_message(self, monkeypatch):
        from ethos_academy.config.config import EthosConfig

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
            EthosConfig.from_env()


class TestConfigImmutability:
    """Config should be immutable after creation."""

    def test_frozen(self):
        from ethos_academy.config.config import EthosConfig

        cfg = EthosConfig(anthropic_api_key="sk-test")
        with pytest.raises(Exception):
            cfg.anthropic_api_key = "changed"


# ── Priority Thresholds ──────────────────────────────────────────────


class TestPriorityThresholds:
    """PRIORITY_THRESHOLDS maps Priority levels to float thresholds."""

    def test_thresholds_count(self):
        from ethos_academy.config.priorities import PRIORITY_THRESHOLDS

        assert len(PRIORITY_THRESHOLDS) == 3  # LOW is not in dict

    def test_critical_threshold(self):
        from ethos_academy.config.priorities import PRIORITY_THRESHOLDS

        assert PRIORITY_THRESHOLDS["critical"] == 0.25

    def test_high_threshold(self):
        from ethos_academy.config.priorities import PRIORITY_THRESHOLDS

        assert PRIORITY_THRESHOLDS["high"] == 0.50

    def test_standard_threshold(self):
        from ethos_academy.config.priorities import PRIORITY_THRESHOLDS

        assert PRIORITY_THRESHOLDS["standard"] == 0.75

    def test_low_not_in_thresholds(self):
        from ethos_academy.config.priorities import PRIORITY_THRESHOLDS

        assert "low" not in PRIORITY_THRESHOLDS


class TestGetThreshold:
    """get_threshold() returns the float threshold or None for LOW."""

    def test_critical(self):
        from ethos_academy.config.priorities import get_threshold

        assert get_threshold(Priority.CRITICAL) == 0.25

    def test_high(self):
        from ethos_academy.config.priorities import get_threshold

        assert get_threshold(Priority.HIGH) == 0.50

    def test_standard(self):
        from ethos_academy.config.priorities import get_threshold

        assert get_threshold(Priority.STANDARD) == 0.75

    def test_low_returns_none(self):
        from ethos_academy.config.priorities import get_threshold

        assert get_threshold(Priority.LOW) is None


# ── Re-exports ───────────────────────────────────────────────────────


class TestReExports:
    """ethos/config/__init__.py must re-export public API."""

    def test_all_exports(self):
        from ethos_academy.config import EthosConfig, PRIORITY_THRESHOLDS, get_threshold

        assert EthosConfig is not None
        assert PRIORITY_THRESHOLDS is not None
        assert get_threshold is not None
