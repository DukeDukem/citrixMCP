"""
Skill 2: Read email in Sprinklr.

Default RE (typed RE / bare run.py):
  Always extract the currently open case (--once).
  Never arm Anwenden on typed RE — arm only after LF close-out via --arm*.

Explicit flags:
  --once                 extract open case now (same as default)
  --arm / --watch-anwenden-re   arm Anwenden watch (after EMAIL LF / PR LF)
  --arm-weiter / --watch-weiter-re   arm Weiter watch (after LF TR queue)
  --arm-extern / --watch-extern-re   arm Extern watch (after LF TR email)
  --arm-next / --watch-next-re   arm call disposition Next watch (after CALL LF)
  --await-arm            poll detached arm log until extract done (then exit 0)
  --foreground           do NOT detach (legacy blocking watch in this shell)

Detached by default on Windows for --arm / --arm-weiter / --arm-extern / --arm-next so Cursor
aborting the agent shell does not kill the watch (common cause of
ANWENDEN WATCH DIED BEFORE EXTRACT).
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SKILL_DIR.parent.parent.parent
_AUTO_DIR = _REPO_ROOT / ".cursor" / "skills" / "sprinklr-email-automation"
_STATE_DIR = _REPO_ROOT / ".cursor" / "state"
_ARM_LOG = _STATE_DIR / "arm_watch.log"
_ARM_META = _STATE_DIR / "arm_watch.json"

_EXTRACT_MARKERS = (
    "ANWENDEN_RE_EXTRACT_DONE",
    "WEITER_RE_EXTRACT_DONE",
    "EXTERN_RE_EXTRACT_DONE",
    "NEXT_RE_EXTRACT_DONE",
    "CUSTOMER EMAIL (for Cursor to read",
    "RE_PENDING_SOUND",
)
_FAIL_MARKERS = (
    "ERROR: NEXT CASE NOT OPEN",
    "ERROR: ANWENDEN WATCH DIED BEFORE EXTRACT",
)


def _print_re_text_only_gate() -> None:
    """Tell the agent to stop tooling and post the 7-step as plain chat next."""
    print("\n" + "=" * 80, flush=True)
    print("RE_TEXT_ONLY_GATE", flush=True)
    print("=" * 80, flush=True)
    print(
        "AGENT — mandatory next step: send a NEW chat message with the full 7-step RE "
        "(sections 1–7) as plain visible text ONLY.",
        flush=True,
    )
    print(
        "That 7-step message must have ZERO tool calls (no Shell, Grep, Task, Read, Write, "
        "play-ready, Auto-LF, arms).",
        flush=True,
    )
    print(
        "Do NOT read terminals/*.txt or spawn explore/Task subagents — that creates "
        "'Finished background tasks' menus and hides the RE.",
        flush=True,
    )
    print(
        "After the 7-step is visible in chat, run play-ready + Auto-LF in a separate "
        "tools-only message.",
        flush=True,
    )
    print(
        "Operator backup if UI collapses: .cursor/state/latest_re_visible.md "
        "(written when section 7 is detected).",
        flush=True,
    )
    print("=" * 80 + "\n", flush=True)


def _write_meta(mode: str, pid: int) -> None:
    import json
    from datetime import datetime, timezone

    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    _ARM_META.write_text(
        json.dumps(
            {
                "mode": mode,
                "pid": pid,
                "log": str(_ARM_LOG),
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _spawn_detached(runner: Path, watch_flag: str, env: dict) -> int:
    """Start watch in a new process group; parent returns immediately.

    Uses CREATE_NO_WINDOW (not DETACHED_PROCESS) so no black console pops up.
    CREATE_NEW_PROCESS_GROUP keeps the watch alive when Cursor aborts the parent shell.
    """
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    # Truncate previous log so await doesn't see stale EXTRACT_DONE
    _ARM_LOG.write_text("", encoding="utf-8")

    creationflags = 0
    if sys.platform == "win32":
        # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
        # Do NOT use DETACHED_PROCESS — that allocates a visible console for python.exe.
        creationflags = 0x08000000 | 0x00000200

    log_f = open(_ARM_LOG, "a", encoding="utf-8", errors="replace")
    try:
        proc = subprocess.Popen(
            [sys.executable, str(runner), watch_flag],
            cwd=str(_REPO_ROOT),
            env=env,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=False if sys.platform == "win32" else True,
        )
    except Exception:
        log_f.close()
        raise

    _write_meta(watch_flag, proc.pid)
    print(f"MODE: {watch_flag} (DETACHED)")
    print(f"ARM_WATCH_DETACHED pid={proc.pid}")
    print(f"ARM_WATCH_LOG {_ARM_LOG}")
    if "anwenden" in watch_flag:
        print("ANWENDEN_RE_ARMED")
        print("READY_FOR_YOUR_CLICK: Anwenden", flush=True)
        print(">>> CLICK Anwenden NOW — watch is armed <<<", flush=True)
    elif "weiter" in watch_flag:
        print("WEITER_RE_ARMED")
        print("READY_FOR_YOUR_CLICK: Weiter (step 4/4 only)", flush=True)
        print(">>> After transfer UI, CLICK exact Weiter NOW — watch is armed <<<", flush=True)
    elif "extern" in watch_flag:
        print("EXTERN_RE_ARMED")
        print("READY_FOR_YOUR_CLICK: Weiterleiten (after Externer Transfer)", flush=True)
        print(">>> After Externer Transfer, CLICK Weiterleiten NOW — watch is armed <<<", flush=True)
    elif "next" in watch_flag:
        print("NEXT_RE_ARMED")
        print("READY_FOR_YOUR_CLICK: Next (call disposition)", flush=True)
        print(">>> CLICK exact Next NOW — watch is armed <<<", flush=True)
    print(
        "Watch runs outside this shell (no console window). "
        "You may click now. Agent will await extract with: run.py --await-arm",
        flush=True,
    )
    # Dexter = close-out armed / safe to click (do not rely on Cursor hooks)
    try:
        if str(_AUTO_DIR) not in sys.path:
            sys.path.insert(0, str(_AUTO_DIR))
        from re_complete_sound import play_pr_lf_done_sound

        if play_pr_lf_done_sound():
            print("PR_LF_DONE_SOUND (armed — click when ready)", flush=True)
    except Exception as e:
        print(f"[WARN] close-out sound failed: {e}", flush=True)
    # Do not wait on proc; leave log_f open for child on Windows
    return 0


def _await_arm(timeout_s: float = 1800.0, poll_s: float = 1.0) -> int:
    """Block until detached arm log shows extract done (or timeout)."""
    print(f"MODE: --await-arm (polling {_ARM_LOG})")
    print("AWAITING_ARM_EXTRACT", flush=True)
    print(
        "Watch already armed — you may click Anwenden / Weiter / Weiterleiten / Next anytime. "
        "This poll stays open until extract finishes.",
        flush=True,
    )
    deadline = time.time() + max(30.0, timeout_s)
    last_size = -1
    while time.time() < deadline:
        if _ARM_LOG.exists():
            try:
                text = _ARM_LOG.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = ""
            size = len(text)
            if size != last_size and size:
                # Tail heartbeat for agent visibility
                tail = text.strip().splitlines()[-3:]
                for line in tail:
                    if "Waiting for" in line or "CLICK_DETECTED" in line or "EXTRACT" in line:
                        print(line, flush=True)
                last_size = size
            if any(m in text for m in _EXTRACT_MARKERS):
                # Replay extract portion for agent 7-step
                print("\n" + "=" * 80)
                print("DETACHED_ARM_EXTRACT_READY")
                print("=" * 80)
                # Print from last CUSTOMER EMAIL banner if present
                idx = text.rfind("CUSTOMER EMAIL")
                if idx >= 0:
                    print(text[idx:], flush=True)
                else:
                    print(text[-8000:], flush=True)
                print("AWAIT_ARM_EXTRACT_DONE", flush=True)
                _print_re_text_only_gate()
                return 0
            if any(m in text for m in _FAIL_MARKERS):
                print("\n" + "=" * 80, flush=True)
                print("DETACHED_ARM_EXTRACT_FAILED", flush=True)
                print("=" * 80, flush=True)
                # Show last failure lines
                for line in text.strip().splitlines()[-20:]:
                    print(line, flush=True)
                print(
                    "ERROR: NEXT CASE NOT OPEN — run run.py --once on the visible case.",
                    flush=True,
                )
                return 1
        time.sleep(poll_s)
    print("[ERROR] --await-arm timed out waiting for extract in ARM_WATCH_LOG", file=sys.stderr)
    print("ERROR: ANWENDEN WATCH DIED BEFORE EXTRACT", flush=True)
    return 1


def main() -> int:
    os.chdir(_REPO_ROOT)
    runner = _AUTO_DIR / "run_sprinklr_email_automation.py"
    if not runner.exists():
        print(f"Runner not found: {runner}", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["SPRINKLR_CDP_ENDPOINT"] = "http://127.0.0.1:9222"
    env["PYTHONIOENCODING"] = "utf-8"

    argv = sys.argv[1:]
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0

    if "--await-arm" in argv:
        return _await_arm()

    force_once = "--once" in argv
    force_arm = "--arm" in argv or "--watch-anwenden-re" in argv
    force_weiter = "--arm-weiter" in argv or "--watch-weiter-re" in argv
    force_extern = "--arm-extern" in argv or "--watch-extern-re" in argv
    force_next = "--arm-next" in argv or "--watch-next-re" in argv
    foreground = "--foreground" in argv

    modes = sum(
        bool(x) for x in (force_once, force_arm, force_weiter, force_extern, force_next)
    )
    if modes > 1:
        print(
            "[ERROR] Use only one of --once, --arm, --arm-weiter, --arm-extern, or --arm-next.",
            file=sys.stderr,
        )
        return 2

    # Typed RE / bare run.py = always extract open case now.
    # Anwenden/Weiter/Extern/Next ONLY via explicit --arm* after LF close-out.
    use_once = force_once or not (
        force_arm or force_weiter or force_extern or force_next
    )
    if use_once and not (force_arm or force_weiter or force_extern or force_next):
        if str(_AUTO_DIR) not in sys.path:
            sys.path.insert(0, str(_AUTO_DIR))
        try:
            from first_re_once import consume_first_re_once

            if consume_first_re_once():
                print("FIRST_RE_ONCE_CONSUMED (post-login initial RE → --once)")
            else:
                print("RE_ONCE_DEFAULT (typed RE / bare run.py → extract open case)")
        except Exception as e:
            print(f"[WARN] first_re_once gate failed: {e}", file=sys.stderr)
            print("RE_ONCE_DEFAULT (typed RE / bare run.py → extract open case)")

    if use_once:
        print("MODE: --once (extract currently open case)")
        rc = subprocess.call(
            [sys.executable, str(runner), "--process-current-only", "--extract-only"],
            cwd=str(_REPO_ROOT),
            env=env,
        )
        _print_re_text_only_gate()
        return rc

    watch_flag = None
    label = None
    if force_weiter:
        watch_flag, label = "--watch-weiter-re", "Weiter arm / LF TR queue"
    elif force_extern:
        watch_flag, label = "--watch-extern-re", "Extern arm / LF TR email"
    elif force_next:
        watch_flag, label = "--watch-next-re", "Next arm / CALL LF disposition"
    elif force_arm:
        watch_flag, label = "--watch-anwenden-re", "Anwenden arm"
    else:
        print("[ERROR] Internal: expected arm mode", file=sys.stderr)
        return 2

    assert watch_flag is not None

    if not foreground and sys.platform == "win32":
        return _spawn_detached(runner, watch_flag, env)

    print(f"MODE: {watch_flag} ({label}, foreground)")
    return subprocess.call(
        [sys.executable, str(runner), watch_flag],
        cwd=str(_REPO_ROOT),
        env=env,
    )


if __name__ == "__main__":
    sys.exit(main())
