#!/usr/bin/env python3
"""Print the latest visible 7-step RE backup (when chat UI collapsed it to background trays)."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_PATH = _REPO / ".cursor" / "state" / "latest_re_visible.md"
_EXTRACT = _REPO / ".cursor" / "state" / "latest_extract.md"


def main() -> int:
    if _PATH.is_file():
        print("LATEST_RE_VISIBLE", flush=True)
        print("=" * 80, flush=True)
        print(_PATH.read_text(encoding="utf-8"), flush=True)
        return 0
    if _EXTRACT.is_file():
        print("LATEST_RE_VISIBLE_MISSING — showing latest_extract.md instead", flush=True)
        print("=" * 80, flush=True)
        print(_EXTRACT.read_text(encoding="utf-8"), flush=True)
        return 0
    print("ERROR: No latest_re_visible.md or latest_extract.md in .cursor/state/", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
