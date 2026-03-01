"""
Single entry point: start Chrome with remote debugging if needed, then run the
Sprinklr email automation. Used by Skill 1 (login) and Skill 2 (read/answer email).
Scripts live under .cursor/skills/sprinklr-email-automation/; repo root is found by walking up.

  uv run python .cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py [--login-only|--process-current-only]
"""
import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CDP_PORT = 9222
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"
CHROME_USER_DATA = SCRIPT_DIR / "chrome_debug_profile"


def find_repo_root() -> Path:
    d = SCRIPT_DIR
    for _ in range(10):
        if (d / "config.json").exists() or (d / ".cursor").is_dir():
            return d
        if d.parent == d:
            break
        d = d.parent
    return Path.cwd()


REPO_ROOT = find_repo_root()

CHROME_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]


def find_chrome() -> Path | None:
    for p in CHROME_PATHS:
        if p and p.is_file():
            return p
    return None


def is_cdp_listening() -> bool:
    try:
        import urllib.request
        req = urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=2)
        return req.status == 200
    except Exception:
        return False


def launch_chrome() -> bool:
    chrome = find_chrome()
    if not chrome:
        print("Chrome not found. Install Google Chrome.", file=sys.stderr)
        return False
    CHROME_USER_DATA.mkdir(parents=True, exist_ok=True)
    print("Launching Chrome with remote debugging (dedicated profile)...")
    subprocess.Popen(
        [
            str(chrome),
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={CHROME_USER_DATA}",
            "--no-first-run",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        cwd=str(REPO_ROOT),
    )
    for _ in range(35):
        time.sleep(1)
        if is_cdp_listening():
            print("Chrome is ready on port", CDP_PORT)
            return True
    print("Chrome did not become ready in time. Try closing other Chrome windows and run again.", file=sys.stderr)
    return False


def main() -> int:
    os.chdir(REPO_ROOT)
    if not is_cdp_listening():
        if not launch_chrome():
            return 1
        time.sleep(3)
    else:
        print("Chrome already running with remote debugging.")

    email_script = SCRIPT_DIR / "email_automation.py"
    if not email_script.exists():
        print(f"Not found: {email_script}", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["SPRINKLR_CDP_ENDPOINT"] = CDP_URL
    args = [sys.executable, str(email_script)]
    if "--login-only" in sys.argv:
        args.append("--login-only")
    if "--process-current-only" in sys.argv:
        args.append("--process-current-only")
    if "--chat-only" in sys.argv:
        args.append("--chat-only")
    if "--extract-only" in sys.argv:
        args.append("--extract-only")
    if "--write-reply-only" in sys.argv:
        args.append("--write-reply-only")
    if "--wait-next-extract-only" in sys.argv:
        args.append("--wait-next-extract-only")
    for a in sys.argv[1:]:
        if a.startswith("--reply-file="):
            args.append(a)
            break
    print("Starting email automation script...")
    return subprocess.call(args, cwd=str(REPO_ROOT), env=env)


if __name__ == "__main__":
    sys.exit(main())
