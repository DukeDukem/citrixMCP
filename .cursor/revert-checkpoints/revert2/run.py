"""
Skill 2: Read email in Sprinklr — watch Fall # and auto-extract for Cursor RE.

Default (RE): watches h1 Fall #; on change, prints email for 7-step RE processing.
Single-shot (legacy): uv run python .../run.py --once

  uv run python .cursor/skills/sprinklr-read-answer-email/run.py
"""
import os
import subprocess
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SKILL_DIR.parent.parent.parent

def main() -> int:
    os.chdir(_REPO_ROOT)
    runner = _REPO_ROOT / ".cursor" / "skills" / "sprinklr-email-automation" / "run_sprinklr_email_automation.py"
    if not runner.exists():
        print(f"Runner not found: {runner}", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["SPRINKLR_CDP_ENDPOINT"] = "http://127.0.0.1:9222"

    argv = [sys.executable, str(runner), "--process-current-only"]
    if "--once" in sys.argv:
        argv.append("--extract-only")
    else:
        argv.append("--watch-fall-re")

    return subprocess.call(argv, cwd=str(_REPO_ROOT), env=env)

if __name__ == "__main__":
    sys.exit(main())
