"""
Skill 1: Open Sprinklr, log in, set status to Verfügbar (active).
Run this script from anywhere; it finds the repo and runs the login-only automation.

  uv run python .cursor/skills/sprinklr-open-login-status/run.py
  or from repo root:  python .cursor/skills/sprinklr-open-login-status/run.py
"""
import os
import subprocess
import sys
from pathlib import Path

# Skill dir = this file's parent; repo root = three levels up (.cursor/skills/skill-name -> repo)
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
    return subprocess.call(
        [sys.executable, str(runner), "--login-only"],
        cwd=str(_REPO_ROOT),
        env=env,
    )

if __name__ == "__main__":
    sys.exit(main())
