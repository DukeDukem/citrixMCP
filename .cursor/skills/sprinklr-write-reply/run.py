"""
Skill: Write reply to Sprinklr email editor (clear existing content, then write the given reply).
Trigger when the user says "reply with ..." or "write the reply in the box".
Requires Skill 1 (login) and an open email case. Reply text must be in a file; pass the file path.

  uv run python .cursor/skills/sprinklr-write-reply/run.py <path-to-reply.txt>
  uv run python .cursor/skills/sprinklr-write-reply/run.py --reply-file=path/to/reply.txt
"""
import os
import subprocess
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SKILL_DIR.parent.parent.parent


def main() -> int:
    reply_file = None
    for arg in sys.argv[1:]:
        if arg.startswith("--reply-file="):
            reply_file = arg.split("=", 1)[1].strip().strip("'\"")
            break
    if not reply_file and len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        reply_file = sys.argv[1]
    if not reply_file:
        print("Usage: run.py <reply-file-path>   or   run.py --reply-file=<path>", file=sys.stderr)
        print("The file should contain the email body to write into the Sprinklr reply box.", file=sys.stderr)
        return 1
    reply_path = Path(reply_file)
    if not reply_path.is_absolute():
        reply_path = _REPO_ROOT / reply_file
    if not reply_path.exists():
        print(f"Reply file not found: {reply_path}", file=sys.stderr)
        return 1

    os.chdir(_REPO_ROOT)
    runner = _REPO_ROOT / ".cursor" / "skills" / "sprinklr-email-automation" / "run_sprinklr_email_automation.py"
    if not runner.exists():
        print(f"Runner not found: {runner}", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["SPRINKLR_CDP_ENDPOINT"] = "http://127.0.0.1:9222"
    return subprocess.call(
        [
            sys.executable,
            str(runner),
            "--write-reply-only",
            f"--reply-file={reply_path}",
            "--wait-next-extract-only",
        ],
        cwd=str(_REPO_ROOT),
        env=env,
    )


if __name__ == "__main__":
    sys.exit(main())
