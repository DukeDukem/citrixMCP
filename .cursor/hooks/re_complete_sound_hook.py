#!/usr/bin/env python3
"""Cursor afterAgentResponse hook: RE ready (book) + PR LF done (Dexter)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SKILLS = _REPO / ".cursor" / "skills" / "sprinklr-email-automation"
if str(_SKILLS) not in sys.path:
    sys.path.insert(0, str(_SKILLS))

from re_complete_sound import play_pr_lf_done_sound, play_re_ready_sound  # noqa: E402
from re_pending_sound import clear_re_pending_sound, is_re_pending_sound  # noqa: E402

_SECTION7_PATTERNS = (
    re.compile(r"(?mi)^\s*#{0,3}\s*\*{0,2}\s*7\.\s*Summary of response"),
    re.compile(r"(?mi)7\.\s*Summary of response"),
)

# Agent finishing quote after PR + LF + Anwenden arm, e.g. "PR LF done for #55387859"
_PR_LF_DONE_PATTERNS = (
    re.compile(r"(?mi)\bPR\s*LF\s+done\s+for\s+#?\d+"),
    re.compile(r"(?mi)^\s*#{0,3}\s*\*{0,2}\s*PR\s*LF\s+done\b"),
)


def _has_section7(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in _SECTION7_PATTERNS)


def _has_pr_lf_done(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in _PR_LF_DONE_PATTERNS)


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    text = payload.get("text") or ""

    # Prefer PR LF done cue when that finishing quote is present.
    if _has_pr_lf_done(text):
        play_pr_lf_done_sound()
        return 0

    # After full 7-step RE: book-opening cue (ready to read / process case).
    if is_re_pending_sound() and _has_section7(text):
        play_re_ready_sound()
        clear_re_pending_sound()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
