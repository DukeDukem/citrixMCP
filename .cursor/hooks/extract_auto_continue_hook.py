#!/usr/bin/env python3
"""Stop hook: auto-submit follow-up when armed extract is ready — zero operator input."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_STATE = _REPO / ".cursor" / "state"
_READ_SKILL = _REPO / ".cursor" / "skills" / "sprinklr-read-answer-email"
_LOG = _STATE / "extract_auto_continue_hook.log"
_DISPATCHED = _STATE / "auto_continue_dispatched.json"
_SESSION_FLAG = _STATE / "email_session_active.json"
_LOOP_LIMIT = 50


def _log(msg: str) -> None:
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with _LOG.open("a", encoding="utf-8") as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass


def _read_stdin_payload() -> dict:
    try:
        raw_b = sys.stdin.buffer.read()
    except Exception:
        raw_b = b""
    if not raw_b.strip():
        return {}
    text = raw_b.decode("utf-8-sig", errors="replace").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        _log(f"json_error={e!r}")
        return {}


def _load_dispatched() -> dict:
    if not _DISPATCHED.exists():
        return {}
    try:
        return json.loads(_DISPATCHED.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _mark_dispatched(case_id: str) -> None:
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        _DISPATCHED.write_text(
            json.dumps(
                {"case_id": case_id, "at": datetime.now(timezone.utc).isoformat()},
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception as e:
        _log(f"dispatch_mark_failed={e!r}")


def _followup(case_id: str, channel: str, gate: str) -> str:
    ch = (channel or "EMAIL").upper()
    return (
        f"[AUTO_PIPELINE - do not wait for operator input]\n"
        f"Armed extract ready for {case_id or 'visible case'} ({ch}).\n"
        f"Mandatory now:\n"
        f"1) If stdout/log not in thread: run "
        f"uv run python .cursor/skills/sprinklr-read-answer-email/run.py --pickup\n"
        f"2) EMAIL ({gate}): full 7-step RE as visible chat text (sections 1-7, zero tools in step 2), "
        f"then play-ready, then Auto-LF, then wait for PR only.\n"
        f"3) CALL (CALL_LF_GATE): Auto-LF voice + closeout arm - no email RE/PR.\n"
        f"Forbidden: idle after Prowler; asking operator to type RE/NEXT/LF."
    )


def main() -> int:
    payload = _read_stdin_payload()
    event = payload.get("hook_event_name") or payload.get("event") or "stop"
    status = payload.get("status") or "completed"
    loop_count = int(payload.get("loop_count") or 0)

    _log(f"event={event!r} status={status!r} loop_count={loop_count}")

    if event != "stop" or status != "completed":
        sys.stdout.write("{}\n")
        sys.stdout.flush()
        return 0

    # Only fire in the email processing session — not the instructions/rules chat
    if not _SESSION_FLAG.exists():
        sys.stdout.write("{}\n")
        sys.stdout.flush()
        return 0

    try:
        _sess = json.loads(_SESSION_FLAG.read_text(encoding="utf-8"))
        if not _sess.get("active"):
            _log("email_session inactive — skip")
            sys.stdout.write("{}\n")
            sys.stdout.flush()
            return 0
    except Exception:
        pass

    # Gate: monitoring window — only active between arm fire and mark_consumed().
    # Outside this window (waiting for PR, idle, between cases) the hook is silent.
    # Window: set True in _spawn_detached() → set False in mark_consumed().
    try:
        if str(_READ_SKILL) not in sys.path:
            sys.path.insert(0, str(_READ_SKILL))
        from extract_ready_state import is_monitoring_armed
        if not is_monitoring_armed():
            _log("monitoring_not_armed — hook silent (outside arm window)")
            sys.stdout.write("{}\n")
            sys.stdout.flush()
            return 0
    except Exception as e:
        _log(f"monitoring_armed_check_failed={e!r} — allowing (safe default)")

    if loop_count >= _LOOP_LIMIT:
        _log("loop_limit_reached")
        sys.stdout.write("{}\n")
        sys.stdout.flush()
        return 0

    if str(_READ_SKILL) not in sys.path:
        sys.path.insert(0, str(_READ_SKILL))

    try:
        from extract_ready_state import is_pending_pickup, read_extract_ready, mark_consumed
    except Exception as e:
        _log(f"import_failed={e!r}")
        sys.stdout.write("{}\n")
        sys.stdout.flush()
        return 0

    if not is_pending_pickup():
        sys.stdout.write("{}\n")
        sys.stdout.flush()
        return 0

    data = read_extract_ready() or {}
    case_id = str(data.get("case_id") or "")
    channel = str(data.get("channel") or "EMAIL")
    gate = str(data.get("gate") or "RE_TEXT_ONLY_GATE")

    dispatched = _load_dispatched()
    if dispatched.get("case_id") == case_id and case_id:
        _log(f"already_dispatched case={case_id}")
        sys.stdout.write("{}\n")
        sys.stdout.flush()
        return 0

    msg = _followup(case_id, channel, gate)
    mark_consumed()
    _mark_dispatched(case_id)
    _log(f"followup case={case_id} channel={channel}")

    sys.stdout.write(json.dumps({"followup_message": msg}, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
