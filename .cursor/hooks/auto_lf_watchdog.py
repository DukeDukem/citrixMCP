#!/usr/bin/env python3
"""Detached watchdog: if a Fall # has a finished 7-step in the transcript but
Auto-LF was never filed, spawn auto_lf_after_re.

Covers Cursor turns where afterAgentResponse/stop hooks never fire or get empty text.
Polls every few seconds while email_session_active.json is active.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_STATE = _REPO / ".cursor" / "state"
_HOOK = Path(__file__).resolve().parent / "re_auto_lf_hook.py"
_LOG = _STATE / "auto_lf_watchdog.log"
_SESSION = _STATE / "email_session_active.json"
_EXTRACT = _STATE / "extract_ready.json"
_DONE = _STATE / "auto_lf_done.json"
_META = _STATE / "auto_lf_watchdog.json"
_POLL_S = 4.0


def _log(msg: str) -> None:
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with _LOG.open("a", encoding="utf-8") as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass


def _active() -> bool:
    if not _SESSION.exists():
        return False
    try:
        return bool(json.loads(_SESSION.read_text(encoding="utf-8")).get("active"))
    except Exception:
        return False


def _need_case() -> str:
    if not _EXTRACT.exists():
        return ""
    try:
        data = json.loads(_EXTRACT.read_text(encoding="utf-8"))
    except Exception:
        return ""
    case_id = str(data.get("case_id") or "")
    if not case_id or str(data.get("channel") or "").upper() == "CALL":
        return ""
    dig = "".join(c for c in case_id if c.isdigit())
    if _DONE.exists():
        try:
            done = json.loads(_DONE.read_text(encoding="utf-8"))
            if "".join(c for c in str(done.get("case_id") or "") if c.isdigit()) == dig:
                return ""
        except Exception:
            pass
    spe = _STATE / "lf_speichern_pending.json"
    if spe.exists():
        try:
            s = json.loads(spe.read_text(encoding="utf-8"))
            if "".join(c for c in str(s.get("case_id") or "") if c.isdigit()) == dig:
                return ""
        except Exception:
            pass
    return case_id if case_id.startswith("#") else f"#{dig}"


def _tick() -> None:
    """Invoke hook logic via a synthetic stop payload with transcript hint."""
    need = _need_case()
    if not need:
        return
    # Prefer owner conversation transcript
    owner = _STATE / "pipeline_chat_owner.json"
    conv = ""
    try:
        if owner.exists():
            conv = str(json.loads(owner.read_text(encoding="utf-8")).get("conversation_id") or "")
    except Exception:
        pass
    transcript = ""
    if conv:
        base = (
            Path.home()
            / ".cursor"
            / "projects"
            / "c-Users-PC-ENTER-Desktop-Citrix"
            / "agent-transcripts"
            / conv
        )
        if base.is_dir():
            transcript = str(base)
        elif (base.with_suffix(".jsonl")).is_file():
            transcript = str(base.with_suffix(".jsonl"))
    payload = {
        "hook_event_name": "stop",
        "status": "completed",
        "loop_count": 0,
        "conversation_id": conv,
        "transcript_path": transcript,
        "text": "",
    }
    _log(f"tick need={need} transcript={'yes' if transcript else 'no'}")
    proc = subprocess.run(
        [sys.executable, str(_HOOK)],
        input=json.dumps(payload).encode("utf-8"),
        cwd=str(_REPO),
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        _log(f"hook_rc={proc.returncode} err={proc.stderr[:200]!r}")


def _write_meta(pid: int) -> None:
    _STATE.mkdir(parents=True, exist_ok=True)
    _META.write_text(
        json.dumps({"pid": pid, "at": datetime.now(timezone.utc).isoformat()}, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    if "--once" in sys.argv:
        if _active():
            _tick()
        return 0

    _write_meta(os_getpid())
    _log(f"WATCHDOG_START pid={os_getpid()}")
    idle_rounds = 0
    while True:
        if not _active():
            idle_rounds += 1
            if idle_rounds > 30:  # ~2 min inactive → exit
                _log("WATCHDOG_STOP session_inactive")
                return 0
            time.sleep(_POLL_S)
            continue
        idle_rounds = 0
        try:
            _tick()
        except Exception as e:
            _log(f"tick_error={e!r}")
        time.sleep(_POLL_S)


def os_getpid() -> int:
    import os

    return os.getpid()


def spawn_detached() -> int:
    """Start watchdog in background (CREATE_NO_WINDOW)."""
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000 | 0x00000200
    _STATE.mkdir(parents=True, exist_ok=True)
    log_f = open(_LOG, "a", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve())],
        cwd=str(_REPO),
        stdin=subprocess.DEVNULL,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
        close_fds=False if sys.platform == "win32" else True,
    )
    _write_meta(proc.pid)
    print(f"AUTO_LF_WATCHDOG_SPAWNED pid={proc.pid}", flush=True)
    return 0


if __name__ == "__main__":
    if "--spawn" in sys.argv:
        raise SystemExit(spawn_detached())
    raise SystemExit(main())
