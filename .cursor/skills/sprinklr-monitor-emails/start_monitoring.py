"""
Cold start: run login (open Sprinklr, set status) then start the email monitor.
Use this after closing Cursor or restarting the PC so Chrome and Sprinklr are ready.

  uv run python .cursor/skills/sprinklr-monitor-emails/start_monitoring.py
"""
import subprocess
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SKILL_DIR.parent.parent.parent


def main() -> int:
    # Step 1: Login (starts Chrome with CDP if needed, opens Sprinklr, sets Verfügbar)
    login_script = _REPO_ROOT / ".cursor" / "skills" / "sprinklr-open-login-status" / "run.py"
    if not login_script.exists():
        print(f"Login script not found: {login_script}", file=sys.stderr)
        return 1
    print("[START] Step 1: Opening Sprinklr and setting status...")
    rc = subprocess.call([sys.executable, str(login_script)], cwd=str(_REPO_ROOT))
    if rc != 0:
        print("[START] Login step failed. Fix any errors and try again.", file=sys.stderr)
        return rc

    # Step 2: Start the email monitor (runs until Ctrl+C)
    monitor_script = _REPO_ROOT / ".cursor" / "skills" / "sprinklr-monitor-emails" / "run.py"
    if not monitor_script.exists():
        print(f"Monitor script not found: {monitor_script}", file=sys.stderr)
        return 1
    print("[START] Step 2: Starting email monitor (Ctrl+C to stop)...")
    return subprocess.call([sys.executable, str(monitor_script)], cwd=str(_REPO_ROOT))


if __name__ == "__main__":
    sys.exit(main())
