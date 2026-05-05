#!/usr/bin/env python3
"""Compatibility wrapper for the v0.7 template prototype module.

All source-of-truth geometry now lives in the ``cardboxgen`` package. Imports
from this module still work, but callers should migrate to ``cardboxgen.api``.
"""

from __future__ import annotations

import warnings

from cardboxgen.api import generate_svg
from cardboxgen.cli import main
from cardboxgen.models import WarningMsg
from cardboxgen.panels import Panel
from cardboxgen.version import __version__

warnings.warn(
    "cardboxgen_v0_7_templates is deprecated; use cardboxgen.api.generate_svg",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["__version__", "Panel", "WarningMsg", "generate_svg", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
