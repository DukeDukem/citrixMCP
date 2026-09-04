"""
Skill 2: Read email in Sprinklr.

Default (RE): arm Anwenden-gated auto-RE —
  wait for left-click on Anwenden (validateMacro / UNIVERSAL_CASE) →
  wait 3s → click collapsed-case-item → extract → exit for 7-step RE.

Manual current case:
  uv run python .cursor/skills/sprinklr-read-answer-email/run.py --once
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

    once = "--once" in sys.argv
    if once:
        # Legacy: extract currently open case immediately
        return subprocess.call(
            [sys.executable, str(runner), "--process-current-only", "--extract-only"],
            cwd=str(_REPO_ROOT),
            env=env,
        )

    # Default RE: Anwenden click → wait 3s → open next case → extract
    return subprocess.call(
        [sys.executable, str(runner), "--watch-anwenden-re"],
        cwd=str(_REPO_ROOT),
        env=env,
    )


if __name__ == "__main__":
    sys.exit(main())
