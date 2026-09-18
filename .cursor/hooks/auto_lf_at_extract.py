#!/usr/bin/env python3
"""DEPRECATED for EMAIL — Auto-LF now runs once after the full 7-step
(see auto_lf_after_re.py via re_auto_lf_hook text detection).

This module refuses EMAIL channel runs so stale callers cannot double-fill
Case Tracker at extract. Prefer auto_lf_after_re.py.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_STATE = _REPO / ".cursor" / "state"
_LOG = _STATE / "auto_lf_at_extract.log"
_DONE = _STATE / "auto_lf_done.json"
_FILL = _REPO / ".cursor" / "skills" / "fill-microsoft-form" / "fill_case_tracker.py"
_RUN = _REPO / ".cursor" / "skills" / "sprinklr-read-answer-email" / "run.py"
_SESSION = _STATE / "email_session_active.json"
_PENDING = _STATE / "extract_lf_pending.json"


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
                age = datetime.now(timezone.utc).timestamp() - _DONE.stat().st_mtime
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
                "source": "auto_lf_at_extract",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    if _PENDING.exists():
        try:
            _PENDING.unlink()
        except Exception:
            pass


def write_lf_pending(case_id: str, channel: str = "EMAIL") -> None:
    _STATE.mkdir(parents=True, exist_ok=True)
    _PENDING.write_text(
        json.dumps(
            {
                "case_id": _norm_case(case_id),
                "channel": channel,
                "at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _parse_transfer_from_fill_out(out: str) -> tuple[str, str]:
    m = re.search(r"\[CASE TRACKER\] Transfer:\s*Ja\s*->\s*(\S+)", out)
    if m:
        return "1", m.group(1).strip()
    if re.search(r"\[CASE TRACKER\] Transfer:\s*Ja\b", out):
        return "1", ""
    return "0", ""


def _run_fill(case_id: str, channel: str) -> tuple[int, str, str]:
    cmd = [sys.executable, str(_FILL), "--case-id", case_id]
    if (channel or "").upper() == "CALL":
        cmd.extend(["--channel", "voice"])
    _log(f"FILL_CMD {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(_REPO), capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    for line in out.splitlines():
        if line.strip():
            print(line, flush=True)
    transfer, target = _parse_transfer_from_fill_out(out)
    return proc.returncode, transfer, target


def _run_closeout(channel: str, transfer: str, target: str) -> int:
    if (channel or "").upper() == "CALL":
        flag = (
            "--closeout-extern"
            if transfer == "1" and target and "@" in target
            else ("--closeout-weiter" if transfer == "1" else "--closeout-next")
        )
    else:
        flag = (
            "--closeout-extern"
            if transfer == "1" and target and "@" in target
            else ("--closeout-weiter" if transfer == "1" else "--closeout-anwenden")
        )
    cmd = [sys.executable, str(_RUN), flag]
    _log(f"CLOSEOUT_CMD {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(_REPO))


def run_for_case(case_id: str, channel: str = "EMAIL") -> int:
    case_id = _norm_case(case_id)
    if not case_id:
        _log("run_abort no_case_id")
        return 1
    # EMAIL Auto-LF is post-7-step only — refuse extract-time fills
    if (channel or "EMAIL").upper() != "CALL":
        _log(
            f"run_skip DISABLED_FOR_EMAIL case={case_id} "
            f"(use auto_lf_after_re after 7-step)"
        )
        print(
            f"AUTO_LF_AT_EXTRACT_DISABLED case={case_id} — wait for 7-step",
            flush=True,
        )
        return 0
    if not _email_session_active():
        _log("run_skip session_inactive")
        return 0
    if _already_filed(case_id):
        _log(f"run_skip already_filed {case_id}")
        return 0

    write_lf_pending(case_id, channel)
    _log(f"AUTO_LF_AT_EXTRACT_START case={case_id} channel={channel}")
    rc, transfer, target = _run_fill(case_id, channel)
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

    closeout = (
        "extern"
        if transfer == "1" and target and "@" in target
        else ("weiter" if transfer == "1" else ("next" if (channel or "").upper() == "CALL" else "anwenden"))
    )
    _mark_done(case_id, transfer=transfer, target=target, closeout=closeout)
    crc = _run_closeout(channel, transfer, target)
    _log(f"AUTO_LF_AT_EXTRACT_DONE case={case_id} closeout={closeout} closeout_rc={crc}")
    if transfer == "1":
        print(f"LF TR done for {case_id}", flush=True)
    else:
        print(f"LF done for {case_id} — armed, awaiting PR or Anwenden.", flush=True)
    return 0 if crc == 0 else crc


def spawn(case_id: str, channel: str = "EMAIL") -> int | None:
    case_id = _norm_case(case_id)
    if not case_id:
        return None
    if (channel or "EMAIL").upper() != "CALL":
        _log(f"spawn_skip DISABLED_FOR_EMAIL case={case_id}")
        print(
            f"AUTO_LF_AT_EXTRACT_DISABLED case={case_id} — wait for 7-step",
            flush=True,
        )
        return None
    write_lf_pending(case_id, channel)
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000 | 0x00000200  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    cmd = [sys.executable, str(Path(__file__).resolve()), "--run", "--case-id", case_id, "--channel", channel]
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
    _log(f"AUTO_LF_AT_EXTRACT_SPAWNED pid={proc.pid} case={case_id} channel={channel}")
    print(f"AUTO_LF_REQUIRED case={case_id}", flush=True)
    print(f"AUTO_LF_AT_EXTRACT_SPAWNED case={case_id}", flush=True)
    return proc.pid


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-LF at extract (Turn A safety net)")
    ap.add_argument("--spawn", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--case-id", required=True)
    ap.add_argument("--channel", default="EMAIL")
    args = ap.parse_args()
    if args.spawn:
        spawn(args.case_id, args.channel)
        return 0
    if args.run:
        return run_for_case(args.case_id, args.channel)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
