#!/usr/bin/env python3
"""Stop hook: fire [AUTO_PIPELINE] once per new extract — email chat only.

Triggers: arm → extract_ready (pending) + monitoring_armed.
Never: audio, PR stops, already-LF'd cases, wrong conversation, re-dispatch.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_STATE = _REPO / ".cursor" / "state"
_READ_SKILL = _REPO / ".cursor" / "skills" / "sprinklr-read-answer-email"
_LOG = _STATE / "extract_auto_continue_hook.log"
_DISPATCHED = _STATE / "auto_continue_dispatched.json"
_SESSION_FLAG = _STATE / "email_session_active.json"
_OWNER = _STATE / "pipeline_chat_owner.json"
_BIND_PENDING = _STATE / "pipeline_bind_pending.json"
_DONE = _STATE / "auto_lf_done.json"
_SPEICHERN = _STATE / "lf_speichern_pending.json"
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


def _digits(case_id: str) -> str:
    return re.sub(r"\D", "", case_id or "")


def _empty() -> int:
    sys.stdout.write("{}\n")
    sys.stdout.flush()
    return 0


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _mark_dispatched(case_id: str, extract_at: str = "") -> None:
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        _DISPATCHED.write_text(
            json.dumps(
                {
                    "case_id": case_id,
                    "extract_at": extract_at,
                    "at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception as e:
        _log(f"dispatch_mark_failed={e!r}")


def _maybe_bind_owner(conversation_id: str) -> None:
    """After login, first stop in that chat claims AUTO_PIPELINE ownership."""
    if not conversation_id or not _BIND_PENDING.exists():
        return
    try:
        pending = _load_json(_BIND_PENDING)
        if not pending.get("pending"):
            return
        _STATE.mkdir(parents=True, exist_ok=True)
        _OWNER.write_text(
            json.dumps(
                {
                    "conversation_id": conversation_id,
                    "bound_at": datetime.now(timezone.utc).isoformat(),
                    "source": "login_bind",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        _BIND_PENDING.unlink(missing_ok=True)
        _log(f"pipeline_owner_bound conversation_id={conversation_id}")
    except Exception as e:
        _log(f"bind_owner_failed={e!r}")


def _owner_allows(conversation_id: str) -> bool:
    """Only the email-processing chat may receive AUTO_PIPELINE."""
    if not conversation_id:
        _log("no_conversation_id in payload — skip")
        return False
    owner = _load_json(_OWNER)
    oid = str(owner.get("conversation_id") or "").strip()
    if not oid:
        # First legitimate fire (monitoring+pending already passed) claims this chat.
        # Run login / first AUTO_PIPELINE only from the email processing chat.
        try:
            _STATE.mkdir(parents=True, exist_ok=True)
            _OWNER.write_text(
                json.dumps(
                    {
                        "conversation_id": conversation_id,
                        "bound_at": datetime.now(timezone.utc).isoformat(),
                        "source": "first_followup_claim",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            _log(f"pipeline_owner_claimed conversation_id={conversation_id[:12]}…")
        except Exception as e:
            _log(f"claim_owner_failed={e!r}")
            return False
        return True
    if conversation_id != oid:
        _log(f"wrong_chat skip owner={oid[:8]}… got={conversation_id[:8]}…")
        return False
    return True


def _already_processed(case_id: str) -> bool:
    """True if this Fall # already had 7-step pipeline / LF / Speichern for this case."""
    dig = _digits(case_id)
    if not dig:
        return False

    done = _load_json(_DONE)
    if _digits(str(done.get("case_id") or "")) == dig:
        try:
            at = done.get("at") or ""
            # ISO timestamp — if within 6 hours, treat as done
            if at:
                return True
        except Exception:
            return True

    spe = _load_json(_SPEICHERN)
    if _digits(str(spe.get("case_id") or "")) == dig:
        return True

    dispatched = _load_json(_DISPATCHED)
    if _digits(str(dispatched.get("case_id") or "")) == dig:
        return True

    return False


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
        f"CHANNEL: EMAIL — {cid}. 7-STEP FIRST; Auto-LF ONCE AFTER section 7.\n"
        f"PHASE 1 (optional fast tool): Read .cursor/state/latest_extract.md if needed "
        f"(or run.py --pickup if missing).\n"
        f"PHASE 2 (PLAIN VISIBLE TEXT — ZERO LF tools, then STOP):\n"
        f"  Write: CHANNEL: EMAIL / Fall {cid} / full 7-step sections 1-7.\n"
        f"  End: '7-step complete — Auto-LF starts after this message.'\n"
        f"  Do NOT paste customer email body/Subject/From.\n"
        f"*** FORBIDDEN in this message: fill_case_tracker / --closeout-* / Auto-LF tools ***\n"
        f"*** FORBIDDEN: Auto-LF before the full 7-step is typed ***\n"
        f"Background: re_auto_lf_hook → auto_lf_after_re.py "
        f"(one LF + closeout from §3). No audio.\n"
        f"Forbidden: Task/explore; asking operator anything."
    )


def main() -> int:
    payload = _read_stdin_payload()
    event = payload.get("hook_event_name") or payload.get("event") or "stop"
    status = payload.get("status") or "completed"
    loop_count = int(payload.get("loop_count") or 0)
    conversation_id = str(payload.get("conversation_id") or "").strip()

    _log(
        f"event={event!r} status={status!r} loop_count={loop_count} "
        f"conv={(conversation_id[:12] + '…') if conversation_id else ''}"
    )

    if event != "stop" or status != "completed":
        return _empty()

    # Bind email chat after login (before any followup logic)
    _maybe_bind_owner(conversation_id)

    if not _SESSION_FLAG.exists():
        return _empty()
    try:
        if not json.loads(_SESSION_FLAG.read_text(encoding="utf-8")).get("active"):
            _log("email_session inactive — skip")
            return _empty()
    except Exception:
        pass

    if loop_count >= _LOOP_LIMIT:
        _log("loop_limit_reached")
        return _empty()

    # Never re-enter pipeline on the auto-followup turn itself
    if loop_count > 0:
        _log("loop_count>0 — skip (no re-fire after AUTO_PIPELINE/PR followups)")
        return _empty()

    if str(_READ_SKILL) not in sys.path:
        sys.path.insert(0, str(_READ_SKILL))

    try:
        from extract_ready_state import (
            is_monitoring_armed,
            is_pending_pickup,
            read_extract_ready,
            mark_consumed,
        )
    except Exception as e:
        _log(f"import_failed={e!r}")
        return _empty()

    # Hard gate: only during arm→extract window (write_extract_ready sets armed)
    if not is_monitoring_armed():
        _log("monitoring_not_armed — silent (blocks PR/idle/wrong re-fire)")
        return _empty()

    if not is_pending_pickup():
        return _empty()

    data = read_extract_ready() or {}
    case_id = str(data.get("case_id") or "")
    channel = str(data.get("channel") or "EMAIL")
    gate = str(data.get("gate") or "RE_TEXT_ONLY_GATE")
    extract_at = str(data.get("at") or "")

    if _already_processed(case_id):
        _log(f"already_processed case={case_id} — consume+skip")
        mark_consumed()
        return _empty()

    dispatched = _load_json(_DISPATCHED)
    if _digits(str(dispatched.get("case_id") or "")) == _digits(case_id) and case_id:
        # Same case already dispatched — only allow if extract_at is strictly newer
        if extract_at and extract_at == str(dispatched.get("extract_at") or ""):
            _log(f"already_dispatched same extract_at case={case_id}")
            mark_consumed()
            return _empty()
        if not extract_at or extract_at <= str(dispatched.get("extract_at") or ""):
            _log(f"already_dispatched case={case_id}")
            mark_consumed()
            return _empty()

    if not _owner_allows(conversation_id):
        # Leave pending+armed so the email chat can still pick it up
        return _empty()

    msg = _followup(case_id, channel, gate)
    mark_consumed()
    _mark_dispatched(case_id, extract_at)
    _log(f"followup case={case_id} channel={channel}")

    sys.stdout.write(json.dumps({"followup_message": msg}, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
