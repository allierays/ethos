"""Re-export shim for `from ethos_academy.reflect import reflect`.

The reflect function moved to ethos.reflection.reflect during the DDD
restructure. This module preserves the import path for scripts and docs
that reference the old location.
"""

from ethos_academy.reflection.reflect import reflect  # noqa: F401
