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
    cid = case_id or "visible case"
    if ch == "CALL" or "CALL" in (gate or "").upper():
        return (
            f"[AUTO_PIPELINE - do not wait for operator input]\n"
            f"CHANNEL: CALL — {cid}.\n"
            f"SAME TURN tools: fill_case_tracker.py --case-id \"{cid}\" --channel voice "
            f"then --closeout-next (or weiter/extern if transfer).\n"
            f"No email 7-step. No PR. Quote LF done / LF TR done.\n"
            f"Forbidden: idle; asking operator for RE/NEXT/LF."
        )
    return (
        f"[AUTO_PIPELINE - do not wait for operator input]\n"
        f"CHANNEL: EMAIL — {cid}. TWO TURNS. EXACT ORDER.\n"
        f"TURN A (tools FIRST — do not skip even if AUTO_LF_AT_EXTRACT_SPAWNED):\n"
        f"  a) Confirm/run: uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py "
        f"--case-id \"{cid}\"\n"
        f"  b) Then: uv run python .cursor/skills/sprinklr-read-answer-email/run.py "
        f"--closeout-anwenden (or --closeout-weiter / --closeout-extern if Transfer Ja)\n"
        f"  Skip a/b only if auto_lf_done.json already has this Fall # / Speichern pending for it.\n"
        f"TURN B (next message — ZERO tools, plain visible chat):\n"
        f"  CHANNEL: EMAIL / Fall {cid} / full 7-step sections 1-7.\n"
        f"  End: 'Auto-LF filed at extract — best-guess: Transfer Nein/Ja to X.'\n"
        f"  Do NOT paste customer email body/Subject/From.\n"
        f"BANNED: 'Auto-LF filing now' without LF already done.\n"
        f"BANNED: 7-step before Turn A LF for this Fall #.\n"
        f"RE_TEXT_ONLY_GATE = Turn B text-only only — NOT permission to skip Turn A.\n"
        f"Forbidden: Task/explore; asking operator anything."
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
