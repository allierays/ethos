"""Backward compatibility — scanner renamed to instinct.

All imports from ethos_academy.evaluation.scanner still work.
New code should import from ethos_academy.evaluation.instinct.
"""

from ethos_academy.evaluation.instinct import (  # noqa: F401
    KEYWORD_LEXICON,
    scan,
    scan_keywords,
)
from ethos_academy.shared.models import InstinctResult as KeywordScanResult  # noqa: F401
