"""
Skill 2: Read email in Sprinklr — script prints the customer email and exits; Cursor then queries KnowledgeBase and writes the suggested reply in chat.
Requires Skill 1 (login) to have been run first so the browser is logged in.

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
    # Extract-only: script prints the customer email and exits; Cursor then queries KnowledgeBase and writes the suggested reply in chat.
    return subprocess.call(
        [sys.executable, str(runner), "--process-current-only", "--extract-only"],
        cwd=str(_REPO_ROOT),
        env=env,
    )

if __name__ == "__main__":
    sys.exit(main())
