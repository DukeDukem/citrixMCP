"""Speichern gate between Case Tracker LFs for different Fall #s.

After Auto-LF fill (without --submit), a detached watch listens for
<input type="submit" value="Speichern">. The next LF for a *different*
case is blocked until that click is registered.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[3]
_STATE_DIR = REPO_ROOT / ".cursor" / "state"
SPEICHERN_STATE = _STATE_DIR / "lf_speichern_pending.json"
SPEICHERN_LOG = _STATE_DIR / "lf_speichern_watch.log"
CDP_ENDPOINT = "http://127.0.0.1:9222"
_WATCH_TIMEOUT_S = 86_400  # 24h


def normalise_case_id(case_id: str) -> str:
    case_id = (case_id or "").strip()
    if case_id.startswith("#"):
        case_id = case_id[1:]
    digits = "".join(ch for ch in case_id if ch.isdigit())
    return digits or case_id


def read_speichern_state() -> dict | None:
    if not SPEICHERN_STATE.exists():
        return None
    try:
        data = json.loads(SPEICHERN_STATE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def write_speichern_state(data: dict) -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    SPEICHERN_STATE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def clear_speichern_state() -> None:
    try:
        if SPEICHERN_STATE.exists():
            SPEICHERN_STATE.unlink()
    except Exception:
        pass


def mark_speichern_seen(case_id: str, *, source: str) -> None:
    digits = normalise_case_id(case_id)
    prev = read_speichern_state() or {}
    write_speichern_state(
        {
            "case_id": digits,
            "filled_at": prev.get("filled_at"),
            "speichern_seen": True,
            "speichern_at": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "watch_pid": prev.get("watch_pid"),
        }
    )
    print(f"LF_SPEICHERN_SEEN case=#{digits} source={source}", flush=True)


def set_speichern_pending(case_id: str, *, watch_pid: int | None = None) -> None:
    digits = normalise_case_id(case_id)
    write_speichern_state(
        {
            "case_id": digits,
            "filled_at": datetime.now(timezone.utc).isoformat(),
            "speichern_seen": False,
            "watch_pid": watch_pid,
        }
    )
    print(f"LF_SPEICHERN_PENDING case=#{digits}", flush=True)


def find_case_tracker_page(ctx):
    for p in ctx.pages:
        if "roberta.yoummday.com/casetracker" in (p.url or "").lower():
            return p
    return None


def page_speichern_clicked(page) -> bool:
    try:
        return bool(page.evaluate("() => !!window.__lf_speichern_clicked"))
    except Exception:
        return False


def install_speichern_listener(page) -> bool:
    try:
        page.evaluate(
            """() => {
          window.__lf_speichern_clicked = window.__lf_speichern_clicked || false;
          const mark = () => { window.__lf_speichern_clicked = true; };
          const arm = () => {
            const btn = document.querySelector('input[type="submit"][value="Speichern"]');
            const form = (btn && btn.form) || document.querySelector('form');
            if (btn && !btn.dataset.lfSpeichernWatch) {
              btn.dataset.lfSpeichernWatch = '1';
              btn.addEventListener('click', mark, true);
            }
            if (form && !form.dataset.lfSpeichernWatch) {
              form.dataset.lfSpeichernWatch = '1';
              form.addEventListener('submit', mark, true);
            }
          };
          arm();
          if (!window.__lfSpeichernObs) {
            window.__lfSpeichernObs = new MutationObserver(arm);
            window.__lfSpeichernObs.observe(document.documentElement, { childList: true, subtree: true });
          }
          return true;
        }"""
        )
        return True
    except Exception as e:
        print(f"[WARN] Could not install Speichern listener: {e}", flush=True)
        return False


def spawn_speichern_watch(case_id: str) -> int | None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        SPEICHERN_LOG.write_text("", encoding="utf-8")
    except Exception:
        pass

    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000 | 0x00000200  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP

    script = Path(__file__).resolve().parent / "fill_case_tracker.py"
    log_f = open(SPEICHERN_LOG, "a", encoding="utf-8", errors="replace")
    try:
        proc = subprocess.Popen(
            [
                sys.executable,
                str(script),
                "--watch-speichern",
                "--case-id",
                f"#{normalise_case_id(case_id)}",
            ],
            cwd=str(REPO_ROOT),
            stdout=log_f,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=False if sys.platform == "win32" else True,
            env=os.environ.copy(),
        )
    except Exception as e:
        log_f.close()
        print(f"[WARN] Could not spawn Speichern watch: {e}", flush=True)
        return None

    digits = normalise_case_id(case_id)
    print(f"LF_SPEICHERN_WATCH_ARMED case=#{digits} pid={proc.pid}", flush=True)
    print(f"LF_SPEICHERN_WATCH_LOG {SPEICHERN_LOG}", flush=True)
    print("READY_FOR_YOUR_CLICK: Speichern (Case Tracker)", flush=True)
    return proc.pid


def run_speichern_watch(case_id: str, cdp: str = CDP_ENDPOINT) -> int:
    if sync_playwright is None:
        print("ERROR: playwright not available for Speichern watch", flush=True)
        return 1

    digits = normalise_case_id(case_id)
    print(f"MODE: --watch-speichern case=#{digits}", flush=True)
    marked = {"done": False}

    def _notify_from_page() -> None:
        if marked["done"]:
            return
        marked["done"] = True
        mark_speichern_seen(digits, source="watch")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(cdp)
        except Exception as e:
            print(f"ERROR: Speichern watch cannot connect to Chrome at {cdp}: {e}", flush=True)
            return 1
        ctx = browser.contexts[0] if browser.contexts else None
        if not ctx:
            print("ERROR: No browser context for Speichern watch.", flush=True)
            return 1

        deadline = time.time() + _WATCH_TIMEOUT_S
        while time.time() < deadline:
            st = read_speichern_state()
            if not st:
                print("LF_SPEICHERN_WATCH_STOP reason=state_cleared", flush=True)
                return 0
            st_case = normalise_case_id(str(st.get("case_id") or ""))
            if st_case and st_case != digits:
                print(
                    f"LF_SPEICHERN_WATCH_STOP reason=case_changed watched=#{digits} state=#{st_case}",
                    flush=True,
                )
                return 0
            if st.get("speichern_seen"):
                print(f"LF_SPEICHERN_SEEN case=#{digits} source=state", flush=True)
                return 0

            page = find_case_tracker_page(ctx)
            if not page:
                time.sleep(0.5)
                continue

            try:
                try:
                    page.expose_function("lfSpeichernNotify", lambda: _notify_from_page())
                except Exception:
                    pass
                page.evaluate(
                    """() => {
                  const notify = () => {
                    window.__lf_speichern_clicked = true;
                    try { if (window.lfSpeichernNotify) window.lfSpeichernNotify(); } catch (e) {}
                  };
                  const arm = () => {
                    const btn = document.querySelector('input[type="submit"][value="Speichern"]');
                    const form = (btn && btn.form) || document.querySelector('form');
                    if (btn && !btn.dataset.lfSpeichernWatch) {
                      btn.dataset.lfSpeichernWatch = '1';
                      btn.addEventListener('click', notify, true);
                    }
                    if (form && !form.dataset.lfSpeichernWatch) {
                      form.dataset.lfSpeichernWatch = '1';
                      form.addEventListener('submit', notify, true);
                    }
                  };
                  arm();
                  if (!window.__lfSpeichernObs) {
                    window.__lfSpeichernObs = new MutationObserver(arm);
                    window.__lfSpeichernObs.observe(document.documentElement, { childList: true, subtree: true });
                  }
                  return true;
                }"""
                )
                if page_speichern_clicked(page):
                    _notify_from_page()
                    return 0
            except Exception:
                if marked["done"]:
                    return 0

            if marked["done"]:
                return 0
            time.sleep(0.35)

        print(f"ERROR: Speichern watch timed out for case=#{digits}", flush=True)
        return 1


def gate_previous_speichern(next_case_id: str, tracker_page, *, ignore: bool) -> int | None:
    """
    Block Auto-LF for a different case when previous LF Speichern was not registered.
    Returns None to continue, or exit code 2 to abort.
    """
    if ignore:
        print("[CASE TRACKER] Speichern gate ignored (--ignore-speichern-gate).", flush=True)
        return None

    st = read_speichern_state()
    if not st:
        return None

    prev = normalise_case_id(str(st.get("case_id") or ""))
    nxt = normalise_case_id(next_case_id)
    if not prev:
        return None
    if prev == nxt:
        return None

    if st.get("speichern_seen"):
        clear_speichern_state()
        return None

    if tracker_page is not None:
        try:
            install_speichern_listener(tracker_page)
            if page_speichern_clicked(tracker_page):
                mark_speichern_seen(prev, source="live_flag")
                clear_speichern_state()
                return None
        except Exception:
            pass

    st = read_speichern_state()
    if st and st.get("speichern_seen") and normalise_case_id(str(st.get("case_id") or "")) == prev:
        clear_speichern_state()
        return None

    print(
        f"ERROR: PREVIOUS_LF_SPEICHERN_PENDING previous=#{prev} next=#{nxt}",
        flush=True,
    )
    print(
        'Click Speichern on Case Tracker for the previous LF '
        '(<input type="submit" value="Speichern">) before Auto-LF on '
        f"#{nxt}.",
        flush=True,
    )
    print("PAUSE_AUTO_LF", flush=True)
    print(
        "After Speichern: re-run Auto-LF for the new case "
        "(or --check-speichern then fill). "
        "If you already saved: --clear-speichern-pending then retry.",
        flush=True,
    )
    return 2


def check_speichern_status() -> int:
    st = read_speichern_state()
    if not st:
        print("LF_SPEICHERN_STATUS clear", flush=True)
        return 0
    cid = normalise_case_id(str(st.get("case_id") or ""))
    if st.get("speichern_seen"):
        print(f"LF_SPEICHERN_STATUS seen case=#{cid}", flush=True)
        return 0
    print(f"LF_SPEICHERN_STATUS pending case=#{cid}", flush=True)
    print("PAUSE_AUTO_LF", flush=True)
    return 2
