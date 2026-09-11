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
  --pickup               agent-internal: replay extract if already done (not operator command)
  --closeout-anwenden    post-PR: arm Anwenden + block until next-case extract (background + notify)
  --closeout-weiter      post-transfer: arm Weiter + block until extract
  --closeout-extern      post-transfer: arm Extern + block until extract
  --closeout-next        post-CALL LF: arm Next + block until extract
  --background           with --await-arm: detached poll + write extract_ready (no console)
  --no-auto-await        with --arm*: do not spawn background --await-arm
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
_AWAIT_OUT = _STATE_DIR / "await_arm_out.txt"
_RUN_PY = Path(__file__).resolve()


def _configure_stdout_utf8() -> None:
    """Avoid cp1252 UnicodeEncodeError when replaying German extract to agent shell."""
    if sys.platform != "win32":
        return
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _safe_print(text: str) -> None:
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        print(text.encode(enc, errors="replace").decode(enc), flush=True)

# Await-arm must only complete on explicit *EXTRACT_DONE* lines written after the
# current arm session — never on RE_PENDING_SOUND / CHANNEL_CALL_DETECTED alone
# (those caused stale-log false positives when --await-arm raced --arm-next).
_EXTRACT_DONE_MARKERS = (
    "ANWENDEN_RE_EXTRACT_DONE",
    "WEITER_RE_EXTRACT_DONE",
    "EXTERN_RE_EXTRACT_DONE",
    "NEXT_RE_EXTRACT_DONE",
)
_FAIL_MARKERS = (
    "ERROR: NEXT CASE NOT OPEN",
    "ERROR: ANWENDEN WATCH DIED BEFORE EXTRACT",
)


def _print_re_text_only_gate() -> None:
    """Tell the agent to paste extract + 7-step as plain chat next (no one-liner)."""
    print("\n" + "=" * 80, flush=True)
    print("RE_TEXT_ONLY_GATE", flush=True)
    print("=" * 80, flush=True)
    print(
        "AGENT — EVERY EMAIL CASE, EVERY TIME: next chat message MUST PASTE this Fall #'s "
        "CUSTOMER EMAIL extract (Fall #, Subject, From, Body) AND the full 7-step RE "
        "(sections 1–7) as plain visible text. Do IMMEDIATELY — do not wait for the operator. "
        "New Fall # = paste again. Prior cases do not count.",
        flush=True,
    )
    print(
        "BANNED: one-liners like 'extracted — 7-step next' / 'writing RE…' without pasting "
        "extract + sections 1–7 in that same message.",
        flush=True,
    )
    print(
        "That turn-B message must have ZERO tool calls (no Shell, Grep, Task, Read, Write, "
        "play-ready, Auto-LF, arms).",
        flush=True,
    )
    print(
        "Do NOT read terminals/*.txt or spawn explore/Task subagents — that creates "
        "'Finished background tasks' menus and hides the RE.",
        flush=True,
    )
    print(
        "Do NOT tell the operator to open latest_extract.md instead of pasting the extract.",
        flush=True,
    )
    print(
        "After extract + 7-step are visible in chat, run play-ready + Auto-LF in a separate "
        "tools-only message.",
        flush=True,
    )
    print(
        "Operator backup if UI collapses: .cursor/state/latest_re_visible.md "
        "(written when section 7 is detected).",
        flush=True,
    )
    print("=" * 80 + "\n", flush=True)


def _print_call_lf_gate() -> None:
    """After CHANNEL: CALL extract — voice Auto-LF, no email 7-step."""
    print("\n" + "=" * 80, flush=True)
    print("CALL_LF_GATE", flush=True)
    print("=" * 80, flush=True)
    print(
        "AGENT — CHANNEL: CALL confirmed by script. Do NOT run email 7-step RE or PR.",
        flush=True,
    )
    print(
        "Same turn: Auto-LF --channel voice → --arm-next (or weiter/extern if transfer) → await.",
        flush=True,
    )
    print("=" * 80 + "\n", flush=True)


def _emit_post_extract_gate(combined_output: str) -> None:
    if "CHANNEL: CALL" in combined_output or "CHANNEL_CALL_DETECTED" in combined_output:
        _print_call_lf_gate()
        return
    if "Blocked empty CUSTOMER EMAIL" in combined_output:
        _print_call_lf_gate()
        return
    if "CUSTOMER EMAIL (for Cursor to read" in combined_output:
        body_marker = "Body:"
        idx = combined_output.rfind(body_marker)
        if idx >= 0:
            after_body = combined_output[idx + len(body_marker) : idx + len(body_marker) + 120]
            stripped = after_body.strip()
            if not stripped or stripped.startswith("=") or stripped.startswith("N/A"):
                if "CHANNEL: EMAIL" not in combined_output or "Subject: N/A" in combined_output:
                    _print_call_lf_gate()
                    print(
                        "WARNING: Empty CUSTOMER EMAIL body — use CALL_LF_GATE not RE.",
                        flush=True,
                    )
                    return
    if "CHANNEL: EMAIL" in combined_output or "CUSTOMER EMAIL (for Cursor to read" in combined_output:
        _print_re_text_only_gate()


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


def _closeout_listen(runner: Path, watch_flag: str, env: dict) -> int:
    """Arm detached watch, then block until extract — for post-PR/transfer/CALL close-out."""
    rc = _spawn_detached(runner, watch_flag, env, auto_await=False)
    if rc != 0:
        return rc
    print("CLOSEOUT_LISTEN_ACTIVE", flush=True)
    print(
        "Close-out listen running — operator clicks Sprinklr button only; "
        "agent continues on AWAIT_ARM_EXTRACT_DONE (no typed RE/NEXT).",
        flush=True,
    )
    return _await_arm(timeout_s=1800.0)


def _spawn_detached(runner: Path, watch_flag: str, env: dict, *, auto_await: bool = True) -> int:
    """Start watch in a new process group; parent returns immediately.

    Uses CREATE_NO_WINDOW (not DETACHED_PROCESS) so no black console pops up.
    CREATE_NEW_PROCESS_GROUP keeps the watch alive when Cursor aborts the parent shell.
    """
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime, timezone

    reset_ts = datetime.now(timezone.utc).isoformat()
    # Truncate + session marker so --await-arm ignores pre-arm log content
    _ARM_LOG.write_text(
        f"ARM_WATCH_RESET started_at={reset_ts} mode={watch_flag}\n",
        encoding="utf-8",
    )

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
    if auto_await:
        _spawn_detached_await_arm(env)
    # Do not wait on proc; leave log_f open for child on Windows
    return 0


def _spawn_detached_await_arm(env: dict) -> None:
    """Background poll so extract_ready.json exists even if agent forgets --await-arm."""
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    bg_log = _STATE_DIR / "await_arm_bg.log"
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000 | 0x00000200
    try:
        log_f = open(bg_log, "a", encoding="utf-8", errors="replace")
        subprocess.Popen(
            [sys.executable, str(_RUN_PY), "--await-arm", "--background"],
            cwd=str(_REPO_ROOT),
            env=env,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=False if sys.platform == "win32" else True,
        )
        print("AWAIT_ARM_BACKGROUND_SPAWNED", flush=True)
        print(
            "AGENT: after close-out click, run --await-arm OR type NEXT when Prowler plays.",
            flush=True,
        )
    except Exception as e:
        print(f"[WARN] background await-arm spawn failed: {e}", flush=True)


def _arm_log_segment_after_reset(text: str) -> str:
    """Return log content only from the latest ARM_WATCH_RESET (current arm session)."""
    reset_idx = text.rfind("ARM_WATCH_RESET")
    if reset_idx >= 0:
        return text[reset_idx:]
    return text


def _extract_payload_from_segment(segment: str) -> str:
    idx = segment.rfind("CUSTOMER EMAIL")
    if idx >= 0:
        return segment[idx:]
    if "CHANNEL: CALL" in segment:
        idx = segment.rfind("=" * 80 + "\nCHANNEL: CALL")
        if idx < 0:
            idx = segment.rfind("CHANNEL: CALL")
        if idx >= 0:
            return segment[idx:]
    return segment[-8000:]


def _marker_from_segment(segment: str) -> str:
    for m in _EXTRACT_DONE_MARKERS:
        if m in segment:
            return m
    return ""


def _persist_extract_ready(segment: str) -> None:
    try:
        if str(_SKILL_DIR) not in sys.path:
            sys.path.insert(0, str(_SKILL_DIR))
        from extract_ready_state import write_extract_ready

        write_extract_ready(segment, marker=_marker_from_segment(segment), source="await_arm")
    except Exception as e:
        print(f"[WARN] extract_ready persist failed: {e}", flush=True)


def _replay_arm_extract_segment(segment: str, *, write_out_file: bool = True) -> None:
    """Print extract payload from the current arm session for agent handling."""
    payload = _extract_payload_from_segment(segment)
    header = "\n" + "=" * 80 + "\nDETACHED_ARM_EXTRACT_READY\n" + "=" * 80 + "\n"
    block = header + payload + "\nAWAIT_ARM_EXTRACT_DONE\n"
    print("\n" + "=" * 80)
    print("DETACHED_ARM_EXTRACT_READY")
    print("=" * 80)
    _safe_print(payload)
    print("AWAIT_ARM_EXTRACT_DONE", flush=True)
    _emit_post_extract_gate(payload)
    _persist_extract_ready(segment)
    if write_out_file:
        try:
            _STATE_DIR.mkdir(parents=True, exist_ok=True)
            _AWAIT_OUT.write_text(block, encoding="utf-8")
        except Exception as e:
            print(f"[WARN] await_arm_out write failed: {e}", flush=True)


def _await_arm(
    timeout_s: float = 1800.0,
    poll_s: float = 1.0,
    *,
    background: bool = False,
) -> int:
    """Block until detached arm log shows extract done (or timeout)."""
    if background:
        print("MODE: --await-arm --background (detached poll)", flush=True)
    else:
        print(f"MODE: --await-arm (polling {_ARM_LOG})")
    print("AWAITING_ARM_EXTRACT", flush=True)
    print(
        "Watch already armed — you may click Anwenden / Weiter / Weiterleiten / Next anytime. "
        "This poll stays open until extract finishes.",
        flush=True,
    )
    deadline = time.time() + max(30.0, timeout_s)
    last_size = -1
    # Wait for current arm session reset line (avoids race if await starts before --arm*)
    bootstrap_deadline = time.time() + 20.0
    while time.time() < bootstrap_deadline:
        if _ARM_LOG.exists():
            try:
                boot = _ARM_LOG.read_text(encoding="utf-8", errors="replace")
            except Exception:
                boot = ""
            if "ARM_WATCH_RESET" in boot:
                break
        time.sleep(0.15)
    while time.time() < deadline:
        if _ARM_LOG.exists():
            try:
                text = _ARM_LOG.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = ""
            segment = _arm_log_segment_after_reset(text)
            size = len(text)
            if size != last_size and size:
                # Tail heartbeat for agent visibility
                tail = segment.strip().splitlines()[-3:]
                for line in tail:
                    if "Waiting for" in line or "CLICK_DETECTED" in line or "EXTRACT" in line:
                        print(line, flush=True)
                last_size = size
            if any(m in segment for m in _EXTRACT_DONE_MARKERS):
                _replay_arm_extract_segment(segment)
                return 0
            if any(m in segment for m in _FAIL_MARKERS):
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
    _configure_stdout_utf8()
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

    closeout_map = {
        "--closeout-anwenden": "--watch-anwenden-re",
        "--closeout-weiter": "--watch-weiter-re",
        "--closeout-extern": "--watch-extern-re",
        "--closeout-next": "--watch-next-re",
    }
    for closeout_flag, watch_flag in closeout_map.items():
        if closeout_flag in argv:
            return _closeout_listen(runner, watch_flag, env)

    if "--pickup" in argv:
        # Recovery when Prowler played but agent did not continue RE/LF
        if _ARM_LOG.exists():
            try:
                text = _ARM_LOG.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = ""
            segment = _arm_log_segment_after_reset(text)
            if any(m in segment for m in _EXTRACT_DONE_MARKERS):
                print("EXTRACT_PICKUP_IMMEDIATE", flush=True)
                _replay_arm_extract_segment(segment)
                return 0
        try:
            if str(_SKILL_DIR) not in sys.path:
                sys.path.insert(0, str(_SKILL_DIR))
            from extract_ready_state import is_pending_pickup, read_extract_ready

            if is_pending_pickup():
                data = read_extract_ready() or {}
                print(f"EXTRACT_READY_PENDING case={data.get('case_id')} gate={data.get('gate')}", flush=True)
        except Exception:
            pass
        print("EXTRACT_PICKUP_POLLING", flush=True)
        return _await_arm(timeout_s=120.0)

    if "--await-arm" in argv:
        return _await_arm(background="--background" in argv)

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
        proc = subprocess.run(
            [sys.executable, str(runner), "--process-current-only", "--extract-only"],
            cwd=str(_REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.stdout:
            print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n", flush=True)
        if proc.stderr:
            print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr, flush=True)
        _emit_post_extract_gate((proc.stdout or "") + (proc.stderr or ""))
        return proc.returncode

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
        return _spawn_detached(
            runner,
            watch_flag,
            env,
            auto_await="--no-auto-await" not in argv,
        )

    print(f"MODE: {watch_flag} ({label}, foreground)")
    return subprocess.call(
        [sys.executable, str(runner), watch_flag],
        cwd=str(_REPO_ROOT),
        env=env,
    )


if __name__ == "__main__":
    sys.exit(main())
