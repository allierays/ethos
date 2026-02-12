"""Backward compatibility — scanner renamed to instinct.

All imports from ethos.evaluation.scanner still work.
New code should import from ethos.evaluation.instinct.
"""

from ethos.evaluation.instinct import (  # noqa: F401
    KEYWORD_LEXICON,
    scan,
    scan_keywords,
)
from ethos.shared.models import InstinctResult as KeywordScanResult  # noqa: F401
