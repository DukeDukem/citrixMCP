#!/usr/bin/env python3
"""Auto-LF once after full 7-step RE is visible in chat (not at extract).

Triggered by re_auto_lf_hook when section 7 / 7-step-complete is detected (not audio).
Idempotent via auto_lf_done.json / Speichern pending.
Parses Transfer Ja/Nein + target from RE text when present; else Sprinklr resolve.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_STATE = _REPO / ".cursor" / "state"
_LOG = _STATE / "auto_lf_after_re.log"
_DONE = _STATE / "auto_lf_done.json"
_LATEST_RE = _STATE / "latest_re_visible.md"
_FILL = _REPO / ".cursor" / "skills" / "fill-microsoft-form" / "fill_case_tracker.py"
_RUN = _REPO / ".cursor" / "skills" / "sprinklr-read-answer-email" / "run.py"
_SESSION = _STATE / "email_session_active.json"

_CASE_RE = re.compile(r"Fall\s*#\s*(\d{5,})", re.I)
_ELIGIBLE_YES = re.compile(r"Transfer\s+eligible:\s*\**\s*Yes", re.I)
_ELIGIBLE_NO = re.compile(r"Transfer\s+eligible:\s*\**\s*No", re.I)
_BEST_GUESS = re.compile(
    r"Auto-LF\s+(?:filed|starting|filing).*?Transfer\s+(?:\*\*)?(Nein|Ja)(?:\*\*)?"
    r"(?:\s+to\s+[`'\"*\s]*)?([A-Za-z0-9_@.+\- ]+)?",
    re.I | re.S,
)
_TARGET_TICK = re.compile(r"`([A-Z][A-Z0-9_@.+\-]{3,})`")
_CHANNEL_CALL = re.compile(r"CHANNEL:\s*CALL\b", re.I)
_OUR_TEAMS = ("EMAIL_O2_CARE", "O2MOBILECARE", "CARE_ALLGEMEIN")


def _log(msg: str) -> None:
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with _LOG.open("a", encoding="utf-8") as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass
    print(msg, flush=True)


def _email_session_active() -> bool:
    if not _SESSION.exists():
        return False
    try:
        return bool(json.loads(_SESSION.read_text(encoding="utf-8")).get("active"))
    except Exception:
        return False


def _norm_case(case_id: str) -> str:
    digits = re.sub(r"\D", "", case_id or "")
    return f"#{digits}" if digits else ""


def _already_filed(case_id: str) -> bool:
    digits = re.sub(r"\D", "", case_id)
    if _DONE.exists():
        try:
            done = json.loads(_DONE.read_text(encoding="utf-8"))
            if re.sub(r"\D", "", str(done.get("case_id") or "")) == digits:
                age = time.time() - _DONE.stat().st_mtime
                if age < 3600:
                    return True
        except Exception:
            pass
    speichern = _STATE / "lf_speichern_pending.json"
    if speichern.exists():
        try:
            data = json.loads(speichern.read_text(encoding="utf-8"))
            if re.sub(r"\D", "", str(data.get("case_id") or "")) == digits:
                return True
        except Exception:
            pass
    return False


def _mark_done(case_id: str, *, transfer: str, target: str, closeout: str) -> None:
    _STATE.mkdir(parents=True, exist_ok=True)
    _DONE.write_text(
        json.dumps(
            {
                "case_id": case_id,
                "at": datetime.now(timezone.utc).isoformat(),
                "transfer": transfer,
                "target": target,
                "closeout": closeout,
                "source": "auto_lf_after_re",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _is_our_team(target: str) -> bool:
    t = (target or "").upper().replace(" ", "").replace("-", "").replace("_", "")
    return any(x.replace("_", "") in t for x in ("EMAILO2CARE", "O2MOBILECARE", "CAREALLGEMEIN"))


def parse_case_and_transfer(text: str) -> tuple[str, str | None, str, bool]:
    """Return (case_id, transfer '0'|'1'|None, target, is_call)."""
    is_call = bool(_CHANNEL_CALL.search(text or ""))
    m = _CASE_RE.search(text or "")
    case_id = f"#{m.group(1)}" if m else ""

    transfer: str | None = None
    target = ""

    bg = _BEST_GUESS.search(text or "")
    if bg:
        transfer = "1" if bg.group(1).lower() == "ja" else "0"
        target = (bg.group(2) or "").strip().strip("`\"'*")

    if _ELIGIBLE_YES.search(text or ""):
        transfer = "1"
    elif _ELIGIBLE_NO.search(text or ""):
        transfer = "0"

    if transfer == "1" and not target:
        for tm in _TARGET_TICK.finditer(text or ""):
            cand = tm.group(1)
            if not _is_our_team(cand):
                target = cand
                break

    if transfer == "1" and _is_our_team(target):
        transfer = "0"
        target = ""

    return case_id, transfer, target, is_call


def _run_fill(case_id: str, transfer: str | None, target: str) -> int:
    cmd = [sys.executable, str(_FILL), "--case-id", case_id]
    if transfer == "1":
        cmd.extend(["--transfer", "1"])
        if target:
            cmd.extend(["--target", target])
    elif transfer == "0":
        cmd.extend(["--transfer", "0"])
    _log(f"FILL_CMD {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(_REPO))


def _run_closeout(transfer: str, target: str | None) -> int:
    """Arm close-out + background await only (do not block this worker).

    Blocking await hid extract completion from the email agent (no Cursor shell
    notify). Detached arm + bg await writes extract_ready; stop hook fires
    [AUTO_PIPELINE] for the next 7-step.
    """
    if transfer == "1":
        flag = "--closeout-extern" if target and "@" in target else "--closeout-weiter"
    else:
        flag = "--closeout-anwenden"
    # --arm-only: spawn detached watch + bg await; return immediately
    cmd = [sys.executable, str(_RUN), flag, "--arm-only"]
    _log(f"CLOSEOUT_CMD {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(_REPO))


def run_from_text(text: str) -> int:
    if not _email_session_active():
        _log("run_skip session_inactive")
        return 0

    case_id, transfer, target, is_call = parse_case_and_transfer(text)
    if is_call:
        _log("run_skip CHANNEL_CALL")
        return 0
    if not case_id:
        ready = _STATE / "extract_ready.json"
        if ready.exists():
            try:
                data = json.loads(ready.read_text(encoding="utf-8"))
                cid = str(data.get("case_id") or "")
                if cid:
                    case_id = _norm_case(cid)
            except Exception:
                pass
    if not case_id:
        _log("run_abort no_case_id")
        return 1
    if _already_filed(case_id):
        _log(f"run_skip already_filed {case_id}")
        return 0

    _log(f"AUTO_LF_AFTER_RE_START case={case_id} transfer={transfer} target={target}")
    rc = _run_fill(case_id, transfer, target)
    if rc == 3:
        _log("PAUSE_AUTO_LF — awaiting Speichern continue")
        await_rc = subprocess.call(
            [sys.executable, str(_FILL), "--await-speichern-continue"],
            cwd=str(_REPO),
        )
        _log(f"await_speichern_continue rc={await_rc}")
        if await_rc != 0:
            return await_rc
        rc = 0
    if rc != 0:
        _log(f"FILL_FAILED rc={rc}")
        return rc

    tflag = transfer if transfer is not None else "0"
    closeout = (
        "extern"
        if tflag == "1" and target and "@" in target
        else ("weiter" if tflag == "1" else "anwenden")
    )
    _mark_done(case_id, transfer=tflag, target=target or "", closeout=closeout)
    crc = _run_closeout(tflag, target)
    _log(f"AUTO_LF_AFTER_RE_DONE case={case_id} closeout={closeout} closeout_rc={crc}")
    if tflag == "1":
        print(f"LF TR done for {case_id}", flush=True)
    else:
        print(f"LF done for {case_id} — armed, awaiting PR or Anwenden.", flush=True)
    return 0 if crc == 0 else crc


def spawn_self_from_hook(text: str) -> int | None:
    _STATE.mkdir(parents=True, exist_ok=True)
    text_path = _STATE / "auto_lf_after_re_input.txt"
    text_path.write_text(text or "", encoding="utf-8")
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000 | 0x00000200
    cmd = [sys.executable, str(Path(__file__).resolve()), "--run", "--text-file", str(text_path)]
    proc = subprocess.Popen(
        cmd,
        cwd=str(_REPO),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=False if sys.platform == "win32" else True,
        env={**os.environ},
    )
    case_id, transfer, target, _ = parse_case_and_transfer(text or "")
    _log(f"AUTO_LF_AFTER_RE_SPAWNED pid={proc.pid} case={case_id} transfer={transfer} target={target}")
    return proc.pid


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-LF once after 7-step RE")
    ap.add_argument("--spawn", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--text-file")
    ap.add_argument("--stdin-text", action="store_true")
    args = ap.parse_args()

    text = ""
    if args.text_file:
        p = Path(args.text_file)
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
    elif args.stdin_text:
        text = sys.stdin.read()
    elif _LATEST_RE.exists():
        text = _LATEST_RE.read_text(encoding="utf-8", errors="replace")

    if args.spawn:
        spawn_self_from_hook(text)
        return 0
    if args.run or args.text_file or args.stdin_text:
        return run_from_text(text)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
