#!/usr/bin/env python3

"""Sync the generator into docs/ for the Pyodide web app.

Run from repo root:
  python3 tools/sync_docs.py
"""

from __future__ import annotations

import shutil
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "cardboxgen_v0_1.py"
    dst = root / "docs" / "cardboxgen_v0_1.py"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"Synced {src} -> {dst}")


if __name__ == "__main__":
    main()
