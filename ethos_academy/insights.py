"""Re-export shim for `from ethos_academy.insights import insights`.

The insights function moved to ethos.reflection.insights during the DDD
restructure. This module preserves the import path for scripts and docs
that reference the old location.
"""

from ethos_academy.reflection.insights import _parse_insights_response, insights  # noqa: F401
