"""
Skill: Always-on Sprinklr email monitor.
Runs the main email automation in monitoring mode so new emails are
automatically detected, opened, answered by Cursor AI, and written
into the Sprinklr reply editor. Keeps running until stopped.

  uv run python .cursor/skills/sprinklr-monitor-emails/run.py
"""
import os
import subprocess
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SKILL_DIR.parent.parent.parent


def main() -> int:
    # Run from repo root so paths and config.json resolve correctly
    os.chdir(_REPO_ROOT)
    runner = _REPO_ROOT / ".cursor" / "skills" / "sprinklr-email-automation" / "run_sprinklr_email_automation.py"
    if not runner.exists():
        print(f"Runner not found: {runner}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    # CDP endpoint for Chrome remote debugging (same as other Sprinklr skills)
    env["SPRINKLR_CDP_ENDPOINT"] = "http://127.0.0.1:9222"

    # No special flags -> email_automation.main() will ensure console page
    # and then call automation.monitor_emails(check_interval=...).
    return subprocess.call(
        [sys.executable, str(runner)],
        cwd=str(_REPO_ROOT),
        env=env,
    )


if __name__ == "__main__":
    sys.exit(main())

