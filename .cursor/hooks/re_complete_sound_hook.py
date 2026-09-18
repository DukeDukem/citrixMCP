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
_DEBOUNCE_SECONDS = 15.0  # align with play_pr_lf_done_sound shared Dexter debounce

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
_LATEST_RE_VISIBLE = _STATE / "latest_re_visible.md"
_CLOSEOUT_DONE_PATTERNS = (
    re.compile(r"(?mi)\bPR\s*LF\s+done\s+for\s+#?\d+"),
    re.compile(r"(?mi)^\s*#{0,3}\s*\*{0,2}\s*PR\s*LF\s+done\b"),
    re.compile(r"(?mi)\bLF\s*TR\s+done\s+for\s+#?\d+"),
    re.compile(r"(?mi)^\s*#{0,3}\s*\*{0,2}\s*LF\s*TR\s+done\b"),
    re.compile(r"(?mi)\bLFTR\s+done\s+for\s+#?\d+"),
    re.compile(r"(?mi)\bLF\s+done\s+for\s+#?\d+"),
    re.compile(r"(?mi)^\s*#{0,3}\s*\*{0,2}\s*LF\s+done\s+for\s+#?\d+"),
)
# Do NOT match READY_FOR_YOUR_CLICK / PR_LF_DONE_SOUND — run.py --arm* already plays Dexter.
# Matching those caused a second Dexter when the finishing quote also fired this hook.


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
    for key in (
        "text",
        "response",
        "message",
        "final_text",
        "assistant_message",
        "agent_response",
        "output",
        "content",
        "result",
    ):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
        if isinstance(val, list):
            parts = []
            for item in val:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    t = item.get("text") or item.get("content") or ""
                    if isinstance(t, str):
                        parts.append(t)
            joined = "\n".join(parts).strip()
            if joined:
                return joined
    for nest in ("data", "result", "output", "payload", "body"):
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


def _save_latest_re_visible(text: str) -> None:
    """Backup full agent RE to disk when section 7 is present (UI collapse fallback)."""
    if not text or not _any(text, _SECTION7_PATTERNS):
        return
    if not (_any(text, _SECTION1_PATTERNS) or _any(text, _SECTION6_PATTERNS)):
        return
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        _LATEST_RE_VISIBLE.write_text(text.strip() + "\n", encoding="utf-8")
        _log(f"latest_re_visible saved len={len(text)} path={_LATEST_RE_VISIBLE}")
    except Exception as e:
        _log(f"latest_re_visible save failed: {e!r}")


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


def _read_stdin_payload() -> dict:
    """Read Cursor hook JSON; tolerate empty stdin / UTF-8 BOM."""
    try:
        raw_b = sys.stdin.buffer.read()
    except Exception:
        raw_b = b""
    if not raw_b:
        try:
            raw = sys.stdin.read()
        except Exception:
            raw = ""
        raw_b = raw.encode("utf-8", errors="replace") if raw else b""
    if not raw_b.strip():
        return {}
    # Strip BOM (Windows hooks often prepend EF BB BF)
    text = raw_b.decode("utf-8-sig", errors="replace").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        _log(f"json_error={e!r} raw_prefix={text[:120]!r}")
        return {}


def _spawn_auto_lf_after_re(text: str) -> None:
    """One Auto-LF after full 7-step is visible — never at extract."""
    try:
        import subprocess

        worker = Path(__file__).resolve().parent / "auto_lf_after_re.py"
        if not worker.exists():
            _log("auto_lf_after_re.py missing")
            return
        creationflags = 0
        if sys.platform == "win32":
            creationflags = 0x08000000 | 0x00000200
        # Prefer saved latest_re_visible; also pass text via spawn's write
        subprocess.Popen(
            [sys.executable, str(worker), "--spawn", "--text-file", str(_LATEST_RE_VISIBLE)],
            cwd=str(_REPO),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=False if sys.platform == "win32" else True,
        )
        _log("auto_lf_after_re spawn requested")
    except Exception as e:
        _log(f"auto_lf_after_re spawn failed: {e!r}")


def main() -> int:
    # Always emit empty JSON decision object so Cursor does not treat hook as failed
    def _ok() -> int:
        try:
            sys.stdout.write("{}\n")
            sys.stdout.flush()
        except Exception:
            pass
        return 0

    payload = _read_stdin_payload()
    event = payload.get("hook_event_name") or payload.get("event") or ""
    text = _extract_text(payload)
    _log(
        f"event={event!r} text_len={len(text)} pending={is_re_pending_sound()} "
        f"keys={list(payload.keys())[:12]}"
    )

    if _any(text, _CLOSEOUT_DONE_PATTERNS):
        if not _debounce_allow("closeout"):
            _log("closeout_dexter debounced")
            return _ok()
        ok = play_pr_lf_done_sound()
        _log(f"closeout_dexter ok={ok}")
        return _ok()

    if _should_play_re_ready(text):
        _save_latest_re_visible(text)
        if not _debounce_allow("re_ready"):
            _log("re_ready_book debounced (skip sound + skip duplicate auto_lf spawn)")
            return _ok()
        # Primary Auto-LF path: once after section 7 is in chat (not at extract)
        _spawn_auto_lf_after_re(text)
        ok = play_re_ready_sound()
        clear_re_pending_sound()
        _log(f"re_ready_book ok={ok}")
        return _ok()

    _log("no_sound_match")
    return _ok()


if __name__ == "__main__":
    raise SystemExit(main())
