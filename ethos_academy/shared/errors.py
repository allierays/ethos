"""Custom exception hierarchy for Ethos.

All exceptions inherit from EthosError so callers can catch broadly or specifically.
"""


class EthosError(Exception):
    """Base exception for all Ethos errors."""


class GraphUnavailableError(EthosError):
    """Raised when Neo4j is unreachable or a graph operation fails."""


class EvaluationError(EthosError):
    """Raised when the evaluation pipeline fails."""


class ConfigError(EthosError):
    """Raised when configuration is missing or invalid."""


class ParseError(EthosError):
    """Raised when Claude's response cannot be parsed."""


class EnrollmentError(EthosError):
    """Raised when enrollment or exam operations fail."""


class VerificationError(EthosError):
    """Raised when phone verification fails (bad code, expired, max attempts)."""
