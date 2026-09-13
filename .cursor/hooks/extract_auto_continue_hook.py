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
    extract_file = str(_STATE / "latest_extract.md")

    if ch == "CALL":
        # CALL: agent must run LF + arm (sound hook does not handle CALL)
        return (
            f"[AUTO_PIPELINE]\n"
            f"CHANNEL: CALL — {cid}. Do all of this in ONE response, no operator input:\n"
            f"1. TOOL: uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py "
            f"--case-id \"{cid}\" --channel voice\n"
            f"2. TOOL: uv run python .cursor/skills/sprinklr-read-answer-email/run.py --closeout-next\n"
            f"3. TEXT: 'LF done for {cid} — armed. Click Next.'\n"
            f"DO NOT run email 7-step. DO NOT PR."
        )

    # EMAIL: agent writes text ONLY — no LF/closeout tools.
    # The re_complete_sound_hook detects section 7, saves latest_re_visible.md, and
    # spawns auto_lf_after_re.py which handles fill_case_tracker + closeout arm.
    # Agent running LF tools causes Cursor to collapse the 7-step into a background
    # tasks dropdown once the long-running --closeout-anwenden tool completes.
    return (
        f"[AUTO_PIPELINE]\n"
        f"CHANNEL: EMAIL — {cid}. TWO PHASES ONLY. NO SHELL TOOLS AFTER PHASE 2.\n\n"
        f"PHASE 1 — TOOL (fast file read only):\n"
        f"  Read file: {extract_file}\n"
        f"  (if missing: uv run python .cursor/skills/sprinklr-read-answer-email/run.py --pickup)\n\n"
        f"PHASE 2 — PLAIN VISIBLE TEXT (write this after Phase 1, then STOP — no more tools):\n"
        f"  Write: CHANNEL: EMAIL / Fall {cid} / full 7-step RE sections 1-7 as plain markdown.\n"
        f"  End with: 'Auto-LF filing now. (Background: sound hook handles LF + arm.)'\n\n"
        f"*** STOP AFTER PHASE 2. DO NOT call fill_case_tracker. DO NOT run --closeout-*. ***\n"
        f"*** DO NOT use Task/explore subagents. DO NOT ask operator anything. ***\n"
        f"The re_complete_sound_hook fires on section 7 and auto-files LF + arms Anwenden.\n"
        f"Running LF tools here collapses the 7-step into a hidden dropdown — FORBIDDEN."
    )


def _followup_turn_c(case_id: str) -> str:
    return (
        f"[AUTO_PIPELINE_TURN_C - do not wait for operator input]\n"
        f"7-step RE for {case_id or 'visible case'} is already visible (or in latest_re_visible.md).\n"
        f"Turn B done — run Turn C NOW (tools only):\n"
        f"1) uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py "
        f"--case-id \"{case_id or '#FALL'}\"  (add --transfer/--target if §3 says Ja)\n"
        f"2) Then --closeout-anwenden OR --closeout-weiter OR --closeout-extern\n"
        f"3) Quote LF done / LF TR done. Skip if auto_lf_done.json already has this Fall #.\n"
        f"Forbidden: re-pasting full 7-step; asking operator for LF; idling."
    )


def _needs_turn_c_followup() -> tuple[bool, str]:
    """True if latest RE has section 7 / filing note but Auto-LF not done for that case."""
    latest = _STATE / "latest_re_visible.md"
    done = _STATE / "auto_lf_done.json"
    if not latest.exists():
        return False, ""
    try:
        text = latest.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False, ""
    if "7." not in text or "Summary of response" not in text:
        return False, ""
    if "Auto-LF filing now" not in text and "Transfer eligible" not in text:
        return False, ""
    import re

    m = re.search(r"Fall\s*#\s*(\d{5,})", text, re.I)
    case_id = f"#{m.group(1)}" if m else ""
    if not case_id:
        return False, ""
    if done.exists():
        try:
            d = json.loads(done.read_text(encoding="utf-8"))
            digits = re.sub(r"\D", "", str(d.get("case_id") or ""))
            if digits == m.group(1):
                # Already LF'd this case
                return False, case_id
        except Exception:
            pass
    return True, case_id


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

    if loop_count >= _LOOP_LIMIT:
        _log("loop_limit_reached")
        sys.stdout.write("{}\n")
        sys.stdout.flush()
        return 0

    if str(_READ_SKILL) not in sys.path:
        sys.path.insert(0, str(_READ_SKILL))

    try:
        from extract_ready_state import (
            is_pending_pickup,
            is_monitoring_armed,
            read_extract_ready,
            mark_consumed,
        )
    except Exception as e:
        _log(f"import_failed={e!r}")
        sys.stdout.write("{}\n")
        sys.stdout.flush()
        return 0

    # Path A: new extract ready (monitoring window) → Turn B followup
    try:
        monitoring = is_monitoring_armed()
    except Exception:
        monitoring = True

    if monitoring and is_pending_pickup():
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

    # Path B: Turn B done, Turn C missing (outside monitoring — after RE paste)
    need_c, case_id = _needs_turn_c_followup()
    if need_c:
        dispatched = _load_dispatched()
        turn_c_key = f"turn_c:{case_id}"
        if dispatched.get("turn_c_case") == case_id:
            _log(f"turn_c already_dispatched case={case_id}")
            sys.stdout.write("{}\n")
            sys.stdout.flush()
            return 0
        # Also try spawn Auto-LF immediately so LF files even if agent is slow
        try:
            auto_lf = Path(__file__).resolve().parent / "auto_lf_after_re.py"
            latest = _STATE / "latest_re_visible.md"
            if auto_lf.exists() and latest.exists():
                import subprocess

                creationflags = 0
                if sys.platform == "win32":
                    creationflags = 0x08000000 | 0x00000200
                subprocess.Popen(
                    [sys.executable, str(auto_lf), "--spawn", "--text-file", str(latest)],
                    cwd=str(_REPO),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                    close_fds=False if sys.platform == "win32" else True,
                )
                _log(f"turn_c auto_lf spawn case={case_id}")
        except Exception as e:
            _log(f"turn_c spawn failed={e!r}")

        try:
            _STATE.mkdir(parents=True, exist_ok=True)
            _DISPATCHED.write_text(
                json.dumps(
                    {
                        "turn_c_case": case_id,
                        "at": datetime.now(timezone.utc).isoformat(),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

        msg = _followup_turn_c(case_id)
        _log(f"followup_turn_c case={case_id}")
        sys.stdout.write(json.dumps({"followup_message": msg}, ensure_ascii=False) + "\n")
        sys.stdout.flush()
        return 0

    _log("no_pending_extract_and_no_turn_c")
    sys.stdout.write("{}\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
