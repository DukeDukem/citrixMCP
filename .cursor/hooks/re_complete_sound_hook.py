#!/usr/bin/env python3
"""Cursor afterAgentResponse / stop hook: RE ready (book) + PR LF / LF TR done (Dexter)."""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SKILLS = _REPO / ".cursor" / "skills" / "sprinklr-email-automation"
_STATE = _REPO / ".cursor" / "state"
_LOG = _STATE / "sound_hook.log"
_DEBOUNCE = _STATE / "sound_hook_debounce.json"
_DEBOUNCE_SECONDS = 4.0

if str(_SKILLS) not in sys.path:
    sys.path.insert(0, str(_SKILLS))

from re_complete_sound import play_pr_lf_done_sound, play_re_ready_sound  # noqa: E402
from re_pending_sound import clear_re_pending_sound, is_re_pending_sound  # noqa: E402

_SECTION7_PATTERNS = (
    re.compile(r"(?mi)^\s*#{0,3}\s*\*{0,2}\s*7\.\s*Summary of response"),
    re.compile(r"(?mi)7\.\s*Summary of response"),
    re.compile(r"(?mi)Summary of response\s*\(EN\)"),
)
_SECTION1_PATTERNS = (
    re.compile(r"(?mi)^\s*#{0,3}\s*\*{0,2}\s*1\.\s*Customer(?:\s+case)?\s+summary"),
    re.compile(r"(?mi)1\.\s*Customer(?:\s+case)?\s+summary"),
)
_SECTION6_PATTERNS = (
    re.compile(r"(?mi)^\s*#{0,3}\s*\*{0,2}\s*6\.\s*Your response to customer"),
    re.compile(r"(?mi)6\.\s*Your response to customer"),
)
_CLOSEOUT_DONE_PATTERNS = (
    re.compile(r"(?mi)\bPR\s*LF\s+done\s+for\s+#?\d+"),
    re.compile(r"(?mi)^\s*#{0,3}\s*\*{0,2}\s*PR\s*LF\s+done\b"),
    re.compile(r"(?mi)\bLF\s*TR\s+done\s+for\s+#?\d+"),
    re.compile(r"(?mi)^\s*#{0,3}\s*\*{0,2}\s*LF\s*TR\s+done\b"),
    re.compile(r"(?mi)\bLFTR\s+done\s+for\s+#?\d+"),
)


def _log(msg: str) -> None:
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with _LOG.open("a", encoding="utf-8") as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass


def _any(text: str, patterns: tuple[re.Pattern, ...]) -> bool:
    return bool(text) and any(p.search(text) for p in patterns)


def _extract_text(payload: dict) -> str:
    for key in ("text", "response", "message", "final_text", "assistant_message"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
    for nest in ("data", "result", "output"):
        sub = payload.get(nest)
        if isinstance(sub, dict):
            t = _extract_text(sub)
            if t:
                return t
    return ""


def _should_play_re_ready(text: str) -> bool:
    if not _any(text, _SECTION7_PATTERNS):
        return False
    if is_re_pending_sound():
        return True
    return _any(text, _SECTION1_PATTERNS) or _any(text, _SECTION6_PATTERNS)


def _debounce_allow(kind: str) -> bool:
    """Avoid double-play when both afterAgentResponse and stop fire."""
    now = time.time()
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        if _DEBOUNCE.exists():
            data = json.loads(_DEBOUNCE.read_text(encoding="utf-8"))
            if (
                data.get("kind") == kind
                and now - float(data.get("at", 0)) < _DEBOUNCE_SECONDS
            ):
                return False
        _DEBOUNCE.write_text(
            json.dumps({"kind": kind, "at": now}, indent=2),
            encoding="utf-8",
        )
        return True
    except Exception:
        return True


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        _log(f"json_error={e!r}")
        payload = {}

    event = payload.get("hook_event_name") or payload.get("event") or ""
    text = _extract_text(payload)
    _log(
        f"event={event!r} text_len={len(text)} pending={is_re_pending_sound()} "
        f"keys={list(payload.keys())[:12]}"
    )

    if _any(text, _CLOSEOUT_DONE_PATTERNS):
        if not _debounce_allow("closeout"):
            _log("closeout_dexter debounced")
            return 0
        ok = play_pr_lf_done_sound()
        _log(f"closeout_dexter ok={ok}")
        return 0

    if _should_play_re_ready(text):
        if not _debounce_allow("re_ready"):
            _log("re_ready_book debounced")
            return 0
        ok = play_re_ready_sound()
        clear_re_pending_sound()
        _log(f"re_ready_book ok={ok}")
        return 0

    _log("no_sound_match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
