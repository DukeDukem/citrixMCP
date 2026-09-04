"""
End-of-day stop for Sprinklr email automation.

Stops Anwenden-RE / watch / related RE shells. Does not close Chrome or log out of Sprinklr.

Usage:
  uv run python .cursor/skills/sprinklr-email-automation/done_for_today.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO = _SCRIPT_DIR.parent.parent.parent

# Command-line substrings that identify automation processes to stop (not the IDE itself).
_KILL_CMDLINE_MARKERS = (
    "watch-anwenden-re",
    "watch-weiter-re",
    "sprinklr-read-answer-email" + os.sep + "run.py",
    "sprinklr-read-answer-email/run.py",
    "run_sprinklr_email_automation.py",
    "email_automation.py",
    "monitor_emails",
    "wait-next-extract-only",
    "watch-fall-re",
)

# Never kill ourselves or the Cursor host by broad matches alone.
_SAFE_SKIP = (
    "done_for_today.py",
    "Cursor.exe",
)


def _clear_session_flags() -> None:
    state_dir = _REPO / ".cursor" / "state"
    for name in ("re_pending_sound.json", "fall_watch_primed.json", "first_re_once.json"):
        path = state_dir / name
        if path.exists():
            try:
                path.unlink()
                print(f"CLEARED {path.name}")
            except Exception as e:
                print(f"[WARN] Could not clear {path.name}: {e}")


def _list_python_pids_windows() -> list[tuple[int, str]]:
    """Return (pid, commandline) for python processes via PowerShell CIM."""
    ps = r"""
Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" |
  ForEach-Object { '{0}|{1}' -f $_.ProcessId, ($_.CommandLine -replace '[\r\n]+',' ') }
"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as e:
        print(f"[WARN] Process list failed: {e}")
        return []
    out = []
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        pid_s, cmd = line.split("|", 1)
        try:
            out.append((int(pid_s), cmd))
        except ValueError:
            continue
    return out


def _should_kill(cmdline: str) -> bool:
    cl = cmdline or ""
    cl_l = cl.lower()
    my_pid = os.getpid()
    if any(s.lower() in cl_l for s in _SAFE_SKIP if s.endswith(".py")):
        if "done_for_today.py" in cl_l:
            return False
    if not any(m.lower() in cl_l for m in _KILL_CMDLINE_MARKERS):
        return False
    return True


def stop_automation() -> int:
    print("DONE_FOR_TODAY: stopping Anwenden RE / watch / related shells...")
    killed = 0
    my_pid = os.getpid()
    if sys.platform == "win32":
        for pid, cmd in _list_python_pids_windows():
            if pid == my_pid:
                continue
            if not _should_kill(cmd):
                continue
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                print(f"STOPPED pid={pid}")
                print(f"  cmd: {cmd[:180]}{'…' if len(cmd) > 180 else ''}")
                killed += 1
            except Exception as e:
                print(f"[WARN] Could not stop pid={pid}: {e}")
    else:
        print("[WARN] Non-Windows: stop watch shells manually (Ctrl+C).")

    _clear_session_flags()
    print(f"DONE_FOR_TODAY_OK stopped={killed}")
    print("Session paused until next login. Do not arm RE/PR/LF until then.")
    return 0


if __name__ == "__main__":
    raise SystemExit(stop_automation())
