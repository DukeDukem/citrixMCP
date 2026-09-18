#!/usr/bin/env python3
"""Non-audio hook: after full 7-step text → spawn auto_lf_after_re once.

Sounds (Prowler / book / Dexter) are NEVER processing triggers.
Arm + extract_ready + this text hook drive the pipeline.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_STATE = _REPO / ".cursor" / "state"
_LOG = _STATE / "re_auto_lf_hook.log"
_DEBOUNCE = _STATE / "re_auto_lf_debounce.json"
_LATEST_RE = _STATE / "latest_re_visible.md"
_SESSION = _STATE / "email_session_active.json"
_DEBOUNCE_SECONDS = 45.0

_SECTION7 = (
    re.compile(r"(?mi)7\.\s*Summary of response"),
    re.compile(r"(?mi)Summary of response\s*\(EN\)"),
)
_DONE_MARK = (
    re.compile(r"(?mi)7-step\s+complete"),
    re.compile(r"(?mi)Auto-LF\s+starts\s+after\s+this\s+message"),
)
_SECTION1 = (re.compile(r"(?mi)1\.\s*Customer(?:\s+case)?\s+summary"),)
_SECTION6 = (re.compile(r"(?mi)6\.\s*Your response to customer"),)


def _log(msg: str) -> None:
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with _LOG.open("a", encoding="utf-8") as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass


def _ok() -> int:
    try:
        sys.stdout.write("{}\n")
        sys.stdout.flush()
    except Exception:
        pass
    return 0


def _any(text: str, pats: tuple[re.Pattern, ...]) -> bool:
    return bool(text) and any(p.search(text) for p in pats)


def _session_active() -> bool:
    if not _SESSION.exists():
        return False
    try:
        return bool(json.loads(_SESSION.read_text(encoding="utf-8")).get("active"))
    except Exception:
        return False


def _extract_text(payload: dict) -> str:
    for key in ("text", "response", "message", "final_text", "assistant_message", "content"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def _is_full_re(text: str) -> bool:
    if not text:
        return False
    if _any(text, _DONE_MARK):
        return True
    if _any(text, _SECTION7) and (_any(text, _SECTION1) or _any(text, _SECTION6)):
        return True
    return False


def _debounce() -> bool:
    now = time.time()
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        if _DEBOUNCE.exists():
            data = json.loads(_DEBOUNCE.read_text(encoding="utf-8"))
            if now - float(data.get("at", 0)) < _DEBOUNCE_SECONDS:
                return False
        _DEBOUNCE.write_text(json.dumps({"at": now}, indent=2), encoding="utf-8")
        return True
    except Exception:
        return True


def _spawn(text: str) -> None:
    worker = Path(__file__).resolve().parent / "auto_lf_after_re.py"
    if not worker.exists():
        _log("auto_lf_after_re.py missing")
        return
    _STATE.mkdir(parents=True, exist_ok=True)
    text_path = _STATE / "auto_lf_after_re_input.txt"
    payload = (text or "").strip()
    if not payload and _LATEST_RE.exists():
        payload = _LATEST_RE.read_text(encoding="utf-8", errors="replace")
    if not payload:
        _log("spawn aborted — no RE text")
        return
    text_path.write_text(payload, encoding="utf-8")
    try:
        _LATEST_RE.write_text(payload.strip() + "\n", encoding="utf-8")
    except Exception:
        pass
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000 | 0x00000200
    err_log = _STATE / "auto_lf_after_re_spawn.err"
    with err_log.open("a", encoding="utf-8") as err_f:
        err_f.write(f"\n--- re_auto_lf_hook {datetime.now(timezone.utc).isoformat()} ---\n")
        err_f.flush()
        proc = subprocess.Popen(
            [sys.executable, str(worker), "--run", "--text-file", str(text_path)],
            cwd=str(_REPO),
            stdin=subprocess.DEVNULL,
            stdout=err_f,
            stderr=err_f,
            creationflags=creationflags,
            close_fds=False if sys.platform == "win32" else True,
        )
    _log(f"spawned pid={proc.pid} text_len={len(payload)}")


def main() -> int:
    try:
        raw = sys.stdin.buffer.read()
        payload = json.loads(raw.decode("utf-8-sig", errors="replace")) if raw.strip() else {}
    except Exception as e:
        _log(f"json_error={e!r}")
        return _ok()

    if not isinstance(payload, dict):
        return _ok()
    if not _session_active():
        _log("skip session_inactive")
        return _ok()

    event = payload.get("hook_event_name") or payload.get("event") or ""
    text = _extract_text(payload)
    _log(f"event={event!r} text_len={len(text)}")

    if text and _is_full_re(text):
        if not _debounce():
            _log("debounced")
            return _ok()
        _spawn(text)
        return _ok()

    # stop often has empty text — use latest_re only if very fresh (<20s) and not yet filed
    if (not text) and str(event).lower() == "stop" and _LATEST_RE.exists():
        try:
            age = time.time() - _LATEST_RE.stat().st_mtime
            if age < 20:
                saved = _LATEST_RE.read_text(encoding="utf-8", errors="replace")
                if _is_full_re(saved) and _debounce():
                    _log(f"stop_fresh_re age={age:.1f}s")
                    _spawn(saved)
                    return _ok()
        except Exception as e:
            _log(f"stop_check_failed={e!r}")

    return _ok()


if __name__ == "__main__":
    raise SystemExit(main())
