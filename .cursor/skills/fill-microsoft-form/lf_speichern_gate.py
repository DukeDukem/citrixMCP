"""Speichern gate between Case Tracker LFs for different Fall #s.

After Auto-LF fill (without --submit), listeners mark Speichern in
page localStorage (survives navigation / dead watches). The next LF for a
*different* case is blocked until that mark is seen.
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
CONTINUE_LOG = _STATE_DIR / "lf_speichern_continue.log"
CDP_ENDPOINT = "http://127.0.0.1:9222"
_WATCH_TIMEOUT_S = 86_400  # 24h
_CONTINUE_DONE_MARKERS = (
    "CONTINUE_LF_DONE",
    "CONTINUE_LF_ERROR",
)

# Document-level capture + localStorage — must NOT depend on data-lf-speichern-watch
# (that attribute previously blocked re-arming the real notify handler).
_ARM_SPEICHERN_JS = """
(caseId) => {
  const cid = String(caseId || '').replace(/\\D/g, '');
  window.__lf_speichern_case = cid;
  try {
    localStorage.setItem('lf_speichern_pending', cid);
    // Do not clear lf_speichern_seen here if it already matches cid (re-arm after click)
    const seen = localStorage.getItem('lf_speichern_seen') || '';
    if (seen && seen !== cid) {
      localStorage.removeItem('lf_speichern_seen');
      localStorage.removeItem('lf_speichern_at');
    }
  } catch (e) {}

  const mark = (ev) => {
    const t = ev && ev.target;
    let hit = false;
    if (ev && ev.type === 'submit') {
      hit = true;
    } else if (t) {
      const el = (t.closest && t.closest('input[type="submit"][value="Speichern"]')) || t;
      if (el && el.matches && el.matches('input[type="submit"][value="Speichern"]')) {
        hit = true;
      }
    }
    if (!hit) return;
    const useCid = window.__lf_speichern_case || (localStorage.getItem('lf_speichern_pending') || '');
    window.__lf_speichern_clicked = true;
    try {
      if (useCid) localStorage.setItem('lf_speichern_seen', String(useCid).replace(/\\D/g, ''));
      localStorage.setItem('lf_speichern_at', String(Date.now()));
    } catch (e) {}
    try { if (typeof window.lfSpeichernNotify === 'function') window.lfSpeichernNotify(); } catch (e) {}
  };

  if (!window.__lfSpeichernDocArmed) {
    window.__lfSpeichernDocArmed = true;
    document.addEventListener('click', mark, true);
    document.addEventListener('submit', mark, true);
  }

  // Also stamp the button (debug / user inspection) without blocking re-arm
  const btn = document.querySelector('input[type="submit"][value="Speichern"]');
  if (btn) btn.setAttribute('data-lf-speichern-watch', '1');

  return {
    pending: (localStorage.getItem('lf_speichern_pending') || ''),
    seen: (localStorage.getItem('lf_speichern_seen') || ''),
    clicked: !!window.__lf_speichern_clicked,
  };
}
"""

_READ_SPEICHERN_MARKS_JS = """
() => {
  let pending = '';
  let seen = '';
  let at = '';
  try {
    pending = localStorage.getItem('lf_speichern_pending') || '';
    seen = localStorage.getItem('lf_speichern_seen') || '';
    at = localStorage.getItem('lf_speichern_at') || '';
  } catch (e) {}
  return {
    pending,
    seen,
    at,
    clicked: !!window.__lf_speichern_clicked,
    sikas: ((document.querySelector('input[name="sikas"]') || {}).value || '').replace(/\\D/g, ''),
  };
}
"""

_CLEAR_PAGE_SPEICHERN_JS = """
() => {
  try {
    localStorage.removeItem('lf_speichern_pending');
    localStorage.removeItem('lf_speichern_seen');
    localStorage.removeItem('lf_speichern_at');
  } catch (e) {}
  window.__lf_speichern_clicked = false;
  return true;
}
"""

# Survives Case Tracker reloads after Speichern — captures click even if detached watch died.
_INIT_SPEICHERN_CAPTURE_JS = """
() => {
  if (window.__lfSpeichernInitCapture) return true;
  window.__lfSpeichernInitCapture = true;
  const mark = (ev) => {
    const t = ev && ev.target;
    let hit = false;
    if (ev && ev.type === 'submit') hit = true;
    else if (t) {
      const el = (t.closest && t.closest('input[type="submit"][value="Speichern"]')) || t;
      if (el && el.matches && el.matches('input[type="submit"][value="Speichern"]')) hit = true;
    }
    if (!hit) return;
    let useCid = '';
    try {
      useCid = String(window.__lf_speichern_case || localStorage.getItem('lf_speichern_pending') || '')
        .replace(/\\D/g, '');
    } catch (e) {}
    window.__lf_speichern_clicked = true;
    try {
      if (useCid) localStorage.setItem('lf_speichern_seen', useCid);
      localStorage.setItem('lf_speichern_at', String(Date.now()));
    } catch (e) {}
  };
  document.addEventListener('click', mark, true);
  document.addEventListener('submit', mark, true);
  return true;
}
"""


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


def ensure_speichern_init_capture(page) -> None:
    """Install durable Speichern capture that survives Case Tracker reloads."""
    if page is None:
        return
    try:
        page.add_init_script(_INIT_SPEICHERN_CAPTURE_JS)
    except Exception:
        pass
    try:
        page.evaluate(_INIT_SPEICHERN_CAPTURE_JS)
    except Exception:
        pass


def arm_speichern_for_case(page, case_id: str) -> dict:
    """Install durable Speichern capture for this Fall # (localStorage + document listeners)."""
    digits = normalise_case_id(case_id)
    try:
        ensure_speichern_init_capture(page)
        result = page.evaluate(_ARM_SPEICHERN_JS, digits)
        print(
            f"[CASE TRACKER] Speichern armed case=#{digits} "
            f"ls_pending={result.get('pending') if isinstance(result, dict) else ''} "
            f"ls_seen={result.get('seen') if isinstance(result, dict) else ''}",
            flush=True,
        )
        return result if isinstance(result, dict) else {}
    except Exception as e:
        print(f"[WARN] Could not arm Speichern listener: {e}", flush=True)
        return {}


def install_speichern_listener(page, case_id: str | None = None) -> bool:
    """Backward-compatible wrapper; prefer arm_speichern_for_case with explicit case_id."""
    st = read_speichern_state() or {}
    cid = case_id or st.get("case_id") or ""
    if not cid:
        return False
    return bool(arm_speichern_for_case(page, str(cid)))


def read_page_speichern_marks(page) -> dict:
    try:
        ensure_speichern_init_capture(page)
        result = page.evaluate(_READ_SPEICHERN_MARKS_JS)
        return result if isinstance(result, dict) else {}
    except Exception:
        return {}


def clear_page_speichern_marks(page) -> None:
    try:
        page.evaluate(_CLEAR_PAGE_SPEICHERN_JS)
    except Exception:
        pass


def page_speichern_clicked(page) -> bool:
    marks = read_page_speichern_marks(page)
    return bool(marks.get("clicked")) or bool(normalise_case_id(str(marks.get("seen") or "")))


def sync_speichern_from_page(page, expected_case: str) -> bool:
    """
    If the page shows Speichern already happened for expected_case, mark file state seen.
    Survives belated clicks after the Python watch died (localStorage lf_speichern_seen).
    Call this on every Auto-LF retry / --check-speichern — do not keep pausing after belated Speichern.
    """
    prev = normalise_case_id(expected_case)
    if not prev or page is None:
        return False

    ensure_speichern_init_capture(page)
    # Re-arm listeners for prev WITHOUT wiping lf_speichern_seen when it already matches prev
    # (arm JS only clears seen when seen is set and differs from cid).
    arm_speichern_for_case(page, prev)
    marks = read_page_speichern_marks(page)
    seen = normalise_case_id(str(marks.get("seen") or ""))
    clicked = bool(marks.get("clicked"))
    sikas = normalise_case_id(str(marks.get("sikas") or ""))
    ls_pending = normalise_case_id(str(marks.get("pending") or ""))
    print(
        f"[CASE TRACKER] Speichern sync check expected=#{prev} "
        f"ls_seen={seen or '-'} ls_pending={ls_pending or '-'} "
        f"clicked={int(clicked)} sikas={sikas or '-'}",
        flush=True,
    )

    if seen == prev:
        mark_speichern_seen(prev, source="localStorage")
        return True

    if clicked and (seen == prev or not seen):
        mark_speichern_seen(prev, source="live_flag")
        return True

    # Heuristic: form no longer holds the previous Case # after a successful Speichern
    if sikas != prev:
        st = read_speichern_state()
        if st and normalise_case_id(str(st.get("case_id") or "")) == prev and not st.get("speichern_seen"):
            if ls_pending == prev:
                mark_speichern_seen(prev, source="sikas_cleared")
                return True

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
                arm_speichern_for_case(page, digits)
                if sync_speichern_from_page(page, digits):
                    marked["done"] = True
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
        if tracker_page is not None:
            clear_page_speichern_marks(tracker_page)
        clear_speichern_state()
        return None

    # Belated Speichern: localStorage / sikas / live flag (works even if watch died)
    if tracker_page is not None:
        try:
            if sync_speichern_from_page(tracker_page, prev):
                clear_page_speichern_marks(tracker_page)
                clear_speichern_state()
                print(
                    f"[CASE TRACKER] Previous Speichern detected for #{prev} — gate cleared; continuing Auto-LF on #{nxt}.",
                    flush=True,
                )
                return None
        except Exception as e:
            print(f"[WARN] Speichern live sync failed: {e}", flush=True)

    st = read_speichern_state()
    if st and st.get("speichern_seen") and normalise_case_id(str(st.get("case_id") or "")) == prev:
        if tracker_page is not None:
            clear_page_speichern_marks(tracker_page)
        clear_speichern_state()
        return None

    print(
        f"ERROR: PREVIOUS_LF_SPEICHERN_PENDING previous=#{prev} next=#{nxt}",
        flush=True,
    )
    print(
        'Click Speichern on Case Tracker for the previous LF '
        '(<input type="submit" value="Speichern">). '
        f"Auto-LF for #{nxt} will continue automatically after that click.",
        flush=True,
    )
    print("PAUSE_AUTO_LF", flush=True)
    return 2


def build_continue_lf_args(
    *,
    case_id: str,
    channel: str = "em_care",
    transfer: str | None = None,
    target: str | None = None,
    salcus: str | None = None,
    cdp: str = CDP_ENDPOINT,
) -> dict:
    return {
        "case_id": normalise_case_id(case_id),
        "channel": channel or "em_care",
        "transfer": transfer,
        "target": (target or "").strip() or None,
        "salcus": (salcus or "").strip() or None,
        "cdp": cdp or CDP_ENDPOINT,
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }


def spawn_continue_after_speichern(continue_args: dict) -> int | None:
    """Detached: wait for previous Speichern, then Auto-LF the queued current case."""
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        CONTINUE_LOG.write_text("", encoding="utf-8")
    except Exception:
        pass

    st = read_speichern_state() or {}
    prev = normalise_case_id(str(st.get("case_id") or ""))
    nxt = normalise_case_id(str(continue_args.get("case_id") or ""))
    st["continue_lf"] = continue_args
    st["continue_previous"] = prev
    write_speichern_state(st)

    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000 | 0x00000200

    script = Path(__file__).resolve().parent / "fill_case_tracker.py"
    log_f = open(CONTINUE_LOG, "a", encoding="utf-8", errors="replace")
    try:
        proc = subprocess.Popen(
            [
                sys.executable,
                str(script),
                "--continue-after-speichern",
                "--cdp",
                str(continue_args.get("cdp") or CDP_ENDPOINT),
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
        print(f"[WARN] Could not spawn continue-after-Speichern: {e}", flush=True)
        return None

    st = read_speichern_state() or {}
    st["continue_pid"] = proc.pid
    write_speichern_state(st)

    print(f"LF_CONTINUE_AFTER_SPEICHERN_ARMED previous=#{prev} next=#{nxt} pid={proc.pid}", flush=True)
    print(f"LF_CONTINUE_LOG {CONTINUE_LOG}", flush=True)
    print("READY_FOR_YOUR_CLICK: Speichern (previous LF) — then Auto-LF continues for current case", flush=True)
    return proc.pid


def run_continue_after_speichern(*, cdp: str = CDP_ENDPOINT) -> int:
    """Wait for belated Speichern on previous case, then fill the queued current case."""
    if sync_playwright is None:
        print("CONTINUE_LF_ERROR reason=no_playwright", flush=True)
        return 1

    st = read_speichern_state() or {}
    cont = st.get("continue_lf") if isinstance(st.get("continue_lf"), dict) else None
    prev = normalise_case_id(str(st.get("continue_previous") or st.get("case_id") or ""))
    if not cont or not prev:
        print("CONTINUE_LF_ERROR reason=missing_continue_payload", flush=True)
        return 1

    nxt = normalise_case_id(str(cont.get("case_id") or ""))
    cdp_url = str(cont.get("cdp") or cdp or CDP_ENDPOINT)
    print(f"MODE: --continue-after-speichern previous=#{prev} next=#{nxt}", flush=True)
    print("Waiting for belated Speichern on previous LF…", flush=True)

    deadline = time.time() + _WATCH_TIMEOUT_S
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(cdp_url)
        except Exception as e:
            print(f"CONTINUE_LF_ERROR reason=cdp_connect {e}", flush=True)
            return 1
        ctx = browser.contexts[0] if browser.contexts else None
        if not ctx:
            print("CONTINUE_LF_ERROR reason=no_context", flush=True)
            return 1

        while time.time() < deadline:
            st_now = read_speichern_state() or {}
            # User cleared pending entirely — abort continue
            if not st_now:
                print("CONTINUE_LF_ERROR reason=state_cleared", flush=True)
                return 1
            # Continue payload removed/changed
            cont_now = st_now.get("continue_lf") if isinstance(st_now.get("continue_lf"), dict) else None
            if not cont_now or normalise_case_id(str(cont_now.get("case_id") or "")) != nxt:
                print("CONTINUE_LF_ERROR reason=continue_payload_changed", flush=True)
                return 1

            if st_now.get("speichern_seen") and normalise_case_id(str(st_now.get("case_id") or "")) == prev:
                break

            page = find_case_tracker_page(ctx)
            if page:
                try:
                    try:
                        page.expose_function(
                            "lfSpeichernNotify",
                            lambda: mark_speichern_seen(prev, source="continue_watch"),
                        )
                    except Exception:
                        pass
                    arm_speichern_for_case(page, prev)
                    if sync_speichern_from_page(page, prev):
                        break
                except Exception:
                    pass
            time.sleep(0.4)
        else:
            print(f"CONTINUE_LF_ERROR reason=timeout previous=#{prev}", flush=True)
            return 1

    # Snapshot continue args, clear previous gate, fill current case
    cont = (read_speichern_state() or {}).get("continue_lf") or cont
    page = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url)
            ctx = browser.contexts[0] if browser.contexts else None
            page = find_case_tracker_page(ctx) if ctx else None
            if page:
                clear_page_speichern_marks(page)
    except Exception:
        pass

    clear_speichern_state()
    print(f"LF_SPEICHERN_GATE_CLEARED previous=#{prev} — starting Auto-LF on #{nxt}", flush=True)

    script = Path(__file__).resolve().parent / "fill_case_tracker.py"
    cmd = [
        sys.executable,
        str(script),
        "--case-id",
        f"#{nxt}",
        "--cdp",
        cdp_url,
        "--channel",
        str(cont.get("channel") or "em_care"),
    ]
    if cont.get("transfer") in ("0", "1"):
        cmd.extend(["--transfer", str(cont["transfer"])])
    if cont.get("target"):
        cmd.extend(["--target", str(cont["target"])])
    if cont.get("salcus"):
        cmd.extend(["--salcus", str(cont["salcus"])])

    print(f"CONTINUE_LF_FILL_START case=#{nxt}", flush=True)
    try:
        rc = subprocess.call(cmd, cwd=str(REPO_ROOT))
    except Exception as e:
        print(f"CONTINUE_LF_ERROR reason=fill_spawn {e}", flush=True)
        return 1

    if rc != 0:
        print(f"CONTINUE_LF_ERROR reason=fill_exit_code_{rc} case=#{nxt}", flush=True)
        return rc if isinstance(rc, int) else 1

    print(f"CONTINUE_LF_DONE case=#{nxt} previous_speichern=#{prev}", flush=True)
    return 0


def await_speichern_continue(*, timeout_s: float = 1800.0, poll_s: float = 1.0) -> int:
    """Poll continue log until Auto-LF for the paused current case finishes."""
    print(f"MODE: --await-speichern-continue (polling {CONTINUE_LOG})", flush=True)
    print("AWAITING_SPEICHERN_THEN_AUTO_LF", flush=True)
    print(
        "Click Speichern for the previous LF when ready — Auto-LF for the current case continues automatically.",
        flush=True,
    )
    deadline = time.time() + max(30.0, timeout_s)
    last_size = -1
    while time.time() < deadline:
        if CONTINUE_LOG.exists():
            try:
                text = CONTINUE_LOG.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = ""
            size = len(text)
            if size != last_size and size:
                for line in text.strip().splitlines()[-5:]:
                    if any(
                        k in line
                        for k in (
                            "Waiting for",
                            "LF_SPEICHERN",
                            "CONTINUE_LF",
                            "CASE TRACKER",
                            "READY_FOR",
                        )
                    ):
                        print(line, flush=True)
                last_size = size
            if "CONTINUE_LF_DONE" in text:
                print("\n" + "=" * 80, flush=True)
                print("SPEICHERN_CONTINUE_LF_READY", flush=True)
                print("=" * 80, flush=True)
                print(text[-12000:], flush=True)
                print("AWAIT_SPEICHERN_CONTINUE_DONE", flush=True)
                return 0
            if "CONTINUE_LF_ERROR" in text:
                print("\n" + "=" * 80, flush=True)
                print("SPEICHERN_CONTINUE_LF_FAILED", flush=True)
                print("=" * 80, flush=True)
                print(text[-8000:], flush=True)
                return 1
        time.sleep(max(0.3, poll_s))

    print("ERROR: AWAIT_SPEICHERN_CONTINUE_TIMEOUT", flush=True)
    return 1


def check_speichern_status(*, cdp: str = CDP_ENDPOINT, sync_live: bool = True) -> int:
    st = read_speichern_state()
    if not st:
        print("LF_SPEICHERN_STATUS clear", flush=True)
        return 0
    cid = normalise_case_id(str(st.get("case_id") or ""))
    if st.get("speichern_seen"):
        print(f"LF_SPEICHERN_STATUS seen case=#{cid}", flush=True)
        return 0

    if sync_live and sync_playwright is not None:
        try:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(cdp)
                ctx = browser.contexts[0] if browser.contexts else None
                page = find_case_tracker_page(ctx) if ctx else None
                if page and sync_speichern_from_page(page, cid):
                    st2 = read_speichern_state() or {}
                    if st2.get("continue_lf"):
                        # Keep continue payload — detached continue-after-Speichern will fill next
                        print(
                            f"LF_SPEICHERN_STATUS synced_seen case=#{cid} continue_armed=1",
                            flush=True,
                        )
                        return 0
                    clear_page_speichern_marks(page)
                    clear_speichern_state()
                    print(f"LF_SPEICHERN_STATUS synced_seen case=#{cid}", flush=True)
                    return 0
        except Exception as e:
            print(f"[WARN] Speichern live check failed: {e}", flush=True)

    st = read_speichern_state()
    if st and st.get("speichern_seen"):
        print(f"LF_SPEICHERN_STATUS seen case=#{cid}", flush=True)
        return 0

    print(f"LF_SPEICHERN_STATUS pending case=#{cid}", flush=True)
    print("PAUSE_AUTO_LF", flush=True)
    return 2
