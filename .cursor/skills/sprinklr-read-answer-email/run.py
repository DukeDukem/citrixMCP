"""
Skill 2: Read email in Sprinklr.

Default RE:
  - After login (first RE of session): extract currently open case (--once)
  - Otherwise / after PR+LF: arm Anwenden-gated watch

Explicit flags:
  --once                 extract open case now
  --arm / --watch-anwenden-re   arm Anwenden watch (after PR+LF)
  --arm-weiter / --watch-weiter-re   arm Weiter watch (after LF TR)
"""
import os
import subprocess
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SKILL_DIR.parent.parent.parent
_AUTO_DIR = _REPO_ROOT / ".cursor" / "skills" / "sprinklr-email-automation"


def main() -> int:
    os.chdir(_REPO_ROOT)
    runner = _AUTO_DIR / "run_sprinklr_email_automation.py"
    if not runner.exists():
        print(f"Runner not found: {runner}", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["SPRINKLR_CDP_ENDPOINT"] = "http://127.0.0.1:9222"

    argv = sys.argv[1:]
    if "--help" in argv or "-h" in argv:
        print(__doc__ or "run.py [--once | --arm | --arm-weiter]")
        return 0

    force_once = "--once" in argv
    force_arm = "--arm" in argv or "--watch-anwenden-re" in argv
    force_weiter = "--arm-weiter" in argv or "--watch-weiter-re" in argv

    modes = sum(bool(x) for x in (force_once, force_arm, force_weiter))
    if modes > 1:
        print("[ERROR] Use only one of --once, --arm, or --arm-weiter.", file=sys.stderr)
        return 2

    use_once = force_once
    if not force_once and not force_arm and not force_weiter:
        if str(_AUTO_DIR) not in sys.path:
            sys.path.insert(0, str(_AUTO_DIR))
        try:
            from first_re_once import consume_first_re_once

            if consume_first_re_once():
                use_once = True
                print("FIRST_RE_ONCE_CONSUMED (post-login initial RE → --once)")
        except Exception as e:
            print(f"[WARN] first_re_once gate failed: {e}", file=sys.stderr)

    if use_once:
        print("MODE: --once (extract currently open case)")
        return subprocess.call(
            [sys.executable, str(runner), "--process-current-only", "--extract-only"],
            cwd=str(_REPO_ROOT),
            env=env,
        )

    if force_weiter:
        print("MODE: --watch-weiter-re (Weiter arm / LF TR)")
        return subprocess.call(
            [sys.executable, str(runner), "--watch-weiter-re"],
            cwd=str(_REPO_ROOT),
            env=env,
        )

    print("MODE: --watch-anwenden-re (Anwenden arm)")
    return subprocess.call(
        [sys.executable, str(runner), "--watch-anwenden-re"],
        cwd=str(_REPO_ROOT),
        env=env,
    )


if __name__ == "__main__":
    sys.exit(main())
