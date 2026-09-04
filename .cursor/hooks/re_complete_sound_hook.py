#!/usr/bin/env python3
"""Cursor afterAgentResponse hook: play RE complete sound after section 7."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SKILLS = _REPO / ".cursor" / "skills" / "sprinklr-email-automation"
if str(_SKILLS) not in sys.path:
    sys.path.insert(0, str(_SKILLS))

from re_complete_sound import play_re_complete_sound  # noqa: E402
from re_pending_sound import clear_re_pending_sound, is_re_pending_sound  # noqa: E402

_SECTION7_PATTERNS = (
    re.compile(r"(?mi)^\s*#{0,3}\s*\*{0,2}\s*7\.\s*Summary of response"),
    re.compile(r"(?mi)7\.\s*Summary of response"),
)


def _has_section7(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in _SECTION7_PATTERNS)


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    text = payload.get("text") or ""
    if is_re_pending_sound() and _has_section7(text):
        play_re_complete_sound()
        clear_re_pending_sound()

    # afterAgentResponse: no stdout action required
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
