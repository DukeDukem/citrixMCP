"""
Roberta / Yoummday O2 Case Tracker filler.

Opens https://roberta.yoummday.com/casetracker/ in a NEW browser tab (Sprinklr stays open),
optionally logs in, fills Case # + channel + defaults, leaves save to the user unless --submit.

Usage:
    uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#36698255"
    uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --open-only
    uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --check-speichern
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("ERROR: Run  uv sync  and  uv run playwright install chromium")
    sys.exit(1)

try:
    from lf_speichern_gate import (
        arm_speichern_for_case,
        await_speichern_continue,
        build_continue_lf_args,
        check_speichern_status,
        clear_page_speichern_marks,
        clear_speichern_state,
        gate_previous_speichern,
        mark_speichern_seen,
        read_speichern_state,
        run_continue_after_speichern,
        run_speichern_watch,
        set_speichern_pending,
        spawn_continue_after_speichern,
        spawn_speichern_watch,
        write_speichern_state,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lf_speichern_gate import (
        arm_speichern_for_case,
        await_speichern_continue,
        build_continue_lf_args,
        check_speichern_status,
        clear_page_speichern_marks,
        clear_speichern_state,
        gate_previous_speichern,
        mark_speichern_seen,
        read_speichern_state,
        run_continue_after_speichern,
        run_speichern_watch,
        set_speichern_pending,
        spawn_continue_after_speichern,
        spawn_speichern_watch,
        write_speichern_state,
    )

CASE_TRACKER_URL = "https://roberta.yoummday.com/casetracker/"
CDP_ENDPOINT = "http://127.0.0.1:9222"
REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_config() -> dict:
    cfg_path = REPO_ROOT / "config.json"
    if not cfg_path.exists():
        return {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _normalise_case_id(case_id: str) -> str:
    case_id = (case_id or "").strip()
    if case_id.startswith("#"):
        case_id = case_id[1:]
    digits = "".join(ch for ch in case_id if ch.isdigit())
    return digits or case_id


_SALCUS_UNSET = frozenset(
    {
        "",
        "—",
        "-",
        "nicht festgelegt",
        "not set",
        "n/a",
        "na",
    }
)


# Vertragsnummer in Sprinklr Kundennummer box — NOT a Salcus ID (e.g. Fall #55920431 → C-0026448826).
_CONTRACT_ID_NOT_SALCUS = re.compile(r"^C-\d", re.IGNORECASE)


def _is_contract_id_not_salcus(raw: str | None) -> bool:
    """True when the sidebar value is a C- Vertragsnummer, not a numeric Kundennummer/Salcus."""
    value = (raw or "").replace("\u200f", "").replace("\u200e", "").strip()
    value = " ".join(value.split())
    return bool(_CONTRACT_ID_NOT_SALCUS.match(value))


def _normalise_salcus_value(raw: str | None) -> str:
    """Return Salcus ID for tracker fill, or empty when unset / placeholder / not Salcus."""
    value = (raw or "").replace("\u200f", "").replace("\u200e", "").strip()
    value = " ".join(value.split())
    if value.lower() in _SALCUS_UNSET:
        return ""
    if "nicht festgelegt" in value.lower():
        return ""
    if _is_contract_id_not_salcus(value):
        return ""
    # Salcus IDs are numeric; reject obvious labels/URLs
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return ""
    if "http" in value.lower() or "@" in value:
        return ""
    return digits[:20]


# Exclusive Salcus source: the sidebar box labelled Kundennummer (data-entityid + aria-label).
# The displayed number changes every Fall #. Do not require data-errorid (can vary).
# When set, Sprinklr often uses htmlText; "Nicht festgelegt" uses spr-text-03.
# Never read email body, Webform text, Betreff, or any other Kundennummer mention.
_EXTRACT_SALCUS_JS = """
() => {
  const unset = new Set(['', '—', '-', 'nicht festgelegt', 'not set', 'n/a', 'na']);
  const norm = (s) => (s || '').replace(/[\\u200f\\u200e]/g, '').replace(/\\u00a0/g, ' ').replace(/\\s+/g, ' ').trim();
  const isUnset = (v) => !v || unset.has(v.toLowerCase()) || v.toLowerCase().includes('nicht festgelegt');
  const isLabel = (v) => /^(Kundennummer|Salcus|Customer ID)$/i.test(norm(v));

  const fields = [...document.querySelectorAll('div[data-entityid="Kundennummer"][aria-label="Kundennummer"]')];
  const field = fields.find((el) => el.getAttribute('fieldtype') === 'TEXT') || fields[0];
  if (!field) return '';

  const valueRoot = field.querySelector('.dont-break-out') || field;
  const selectors = [
    '[data-testid="htmlText"]',
    '[data-testid="linkifiedText"] [data-testid="htmlText"]',
    '[data-testid="linkifiedText"] span',
    '.dont-break-out span.spr-text-03',
    'span.spr-text-03.font-400',
    'span.spr-text-03',
  ];
  for (const sel of selectors) {
    for (const el of valueRoot.querySelectorAll(sel)) {
      const v = norm(el.textContent);
      if (v && !isUnset(v) && !isLabel(v)) return v;
    }
  }
  return '';
}
"""


def extract_salcus_from_sprinklr(page, case_info: dict | None = None) -> str:
    """Read Salcus only from the Sprinklr sidebar Kundennummer box. Never from email/Webform body."""
    if page is None:
        return ""

    raw = ""
    try:
        raw = page.evaluate(_EXTRACT_SALCUS_JS)
    except Exception:
        pass
    salcus = _normalise_salcus_value(raw if isinstance(raw, str) else "")
    if salcus:
        print(f"[CASE TRACKER] Salcus from Sprinklr Kundennummer field: {salcus}")
    elif _is_contract_id_not_salcus(raw if isinstance(raw, str) else ""):
        print(
            "[CASE TRACKER] Kundennummer box shows Vertragsnummer (C-…), not Salcus — "
            "leaving Salcus empty; Ticketstatus → 3-Bot dokumentiert nicht in Salcus"
        )
    else:
        print("[CASE TRACKER] Kundennummer/Salcus: not set on Sprinklr — leaving empty")
    return salcus


def find_sprinklr_console_page(ctx):
    """Best-effort: active Sprinklr email/console tab in CDP context."""
    for pg in ctx.pages:
        u = (pg.url or "").lower()
        if "sprinklr.com" in u and "/app/console" in u:
            return pg
    return ctx.pages[0] if ctx.pages else None


_HANDLE_DIRECTLY_ZIELS = frozenset(
    {
        "CBC_E_CARE_ALLGEMEIN",
        "CBC_CARE_ALLGEMEIN",
        "CBC_XF_E_CARE_ALLGEMEIN",
    }
)


def _normalize_ziel(ziel: str) -> str:
    return (ziel or "").strip().upper().replace(" ", "")


def _is_our_care_ziel(ziel: str) -> bool:
    """True when Sprinklr Ziel is our Backoffice team (handle directly, no transfer log)."""
    z = _normalize_ziel(ziel)
    if not z or z.lower() in _SALCUS_UNSET:
        return False
    if z in _HANDLE_DIRECTLY_ZIELS:
        return True
    return "CARE_ALLGEMEIN" in z

_EXTRACT_CASE_INFO_JS = r"""
() => {
  const norm = (s) => (s || '').replace(/[\u200f\u200e]/g, '').replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim();
  const readField = (field) => {
    const html = field?.querySelector('[data-testid="htmlText"]');
    return html ? norm(html.textContent) : norm(field?.textContent || '');
  };

  const info = {};
  const fallField = document.querySelector('[data-entityid="Fallnummer"]');
  let section = fallField;
  for (let i = 0; i < 10 && section; i++) {
    section = section.parentElement;
    if (section?.querySelector('[data-entityid="Ziel"]') && section?.querySelector('[data-entityid="Quelle"]')) break;
  }
  if (section) {
    for (const id of ['Fallnummer', 'Quelle', 'Ziel', 'Sprache']) {
      const f = section.querySelector(`[data-entityid="${id}"]`);
      if (f) info[id] = readField(f);
    }
  }

  let subject = '';
  const h = document.querySelector('h1, h2, [data-testid="subject"], [data-entityid="Subject"]');
  if (h) subject = norm(h.textContent);
  if (!subject) {
    const subjLabel = [...document.querySelectorAll('span[data-testid="label"]')].find(
      (el) => norm(el.textContent).startsWith('Betreff')
    );
    if (subjLabel) {
      const row = subjLabel.closest('[data-testid="box"]')?.parentElement;
      subject = row ? norm(row.textContent).replace(/^Betreff:?/i, '').trim() : '';
    }
  }
  info.Subject = subject;
  return info;
}
"""


def extract_case_info_from_sprinklr(page) -> dict:
    """Read Case Informationen fields from Sprinklr sidebar."""
    if page is None:
        return {}
    try:
        raw = page.evaluate(_EXTRACT_CASE_INFO_JS)
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def resolve_transfer(case_info: dict | None) -> tuple[str, str]:
    """Return (transfer flag '0'|'1', target queue/email)."""
    case_info = case_info or {}
    quelle = (case_info.get("Quelle") or "").lower()
    ziel = (case_info.get("Ziel") or "").strip()

    # Widerruf transfer ONLY when Quelle is the Widerruf queue (e.g. "Care Widerruf").
    # Do NOT infer from email/webform Betreff category breadcrumbs (e.g. "...|Widerruf").
    if "widerruf" in quelle and "webform" not in quelle:
        return "1", "CBC_XF_E_WIDERRUF"

    # Our team (CBC_*_CARE_ALLGEMEIN incl. CBC_E / CBC_XF_E variants) — never Transfer Ja to ourselves
    if _is_our_care_ziel(ziel):
        return "0", ""

    if not ziel or ziel.lower() in _SALCUS_UNSET:
        return "0", ""

    if "@" in ziel:
        return "1", ziel

    if "_" in ziel:
        return "1", ziel

    return "0", ""


def _is_tracker_app_ready(page) -> bool:
    try:
        return page.locator('input[name="sikas"]').first.is_visible(timeout=800)
    except Exception:
        return False


def _is_tracker_login_gate(page) -> bool:
    try:
        if _is_tracker_app_ready(page):
            return False
        return page.locator("#btnPass").first.is_visible(timeout=800)
    except Exception:
        return False


def ensure_case_tracker_logged_in(page, config: dict | None = None) -> None:
    """Log in to Roberta Case Tracker if the password gate is shown."""
    config = config or _load_config()
    if _is_tracker_app_ready(page):
        return
    if not _is_tracker_login_gate(page):
        page.wait_for_timeout(1500)
        if _is_tracker_app_ready(page):
            return
        raise RuntimeError("Case Tracker login gate not detected and app form not visible.")

    password = (config.get("case_tracker_password") or config.get("case_tracker_passwort") or "").strip()
    if not password:
        raise RuntimeError(
            "Case Tracker password gate visible but case_tracker_password is not set in config.json."
        )

    # Login page: NQ (text) + Passwort (password) + submit #btnPass
    nq = (config.get("case_tracker_nq") or config.get("case_tracker_nq_id") or "NQ10061547").strip()
    try:
        text_inputs = page.locator('input[type="text"]:visible')
        if text_inputs.count() > 0:
            text_inputs.first.fill(nq)
    except Exception:
        pass
    try:
        pw = page.locator('input[type="password"]:visible').first
        pw.wait_for(state="visible", timeout=5000)
        pw.fill(password)
    except Exception as e:
        raise RuntimeError(f"Could not fill Case Tracker password field: {e}") from e
    try:
        page.locator("#btnPass").first.click()
    except Exception:
        page.locator('input[type="submit"][value="Passwort"]').first.click()
    page.wait_for_timeout(2000)
    if not _is_tracker_app_ready(page):
        raise RuntimeError("Case Tracker login failed — main form (Case #) not visible after Passwort submit.")


def open_or_reuse_case_tracker_tab(ctx, config: dict | None = None, *, bring_sprinklr_back=None):
    """Open Roberta Case Tracker in a new tab or reuse an existing one."""
    config = config or _load_config()
    url = (config.get("case_tracker_url") or CASE_TRACKER_URL).strip()

    for p in ctx.pages:
        if "roberta.yoummday.com/casetracker" in (p.url or "").lower():
            p.bring_to_front()
            ensure_case_tracker_logged_in(p, config)
            if bring_sprinklr_back:
                try:
                    bring_sprinklr_back.bring_to_front()
                except Exception:
                    pass
            return p

    page = ctx.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1500)
    ensure_case_tracker_logged_in(page, config)
    if bring_sprinklr_back:
        try:
            bring_sprinklr_back.bring_to_front()
        except Exception:
            pass
    return page


def fill_case_tracker_fields(
    page,
    case_id: str,
    *,
    salcus: str | None = None,
    channel: str = "em_care",
    transfer: str | None = None,
    transfer_target: str | None = None,
    tstate: str | None = None,
    submit: bool = False,
) -> None:
    """Fill Roberta Case Tracker fields.

    Ticketstatus Salcus (tstate) defaults:
    - Voice (Tel.) / channel voice → 3-Bot dokumentiert nicht in Salcus (#tstate3) always
    - Transfer Ja → 3-Bot dokumentiert nicht in Salcus (#tstate3) always
    - Transfer Nein + Salcus provided → 1-Erfolgreich (#tstate1)
    - Transfer Nein + Salcus empty → 3-Bot dokumentiert nicht in Salcus (#tstate3)
    """
    ensure_case_tracker_logged_in(page)
    page.bring_to_front()
    page.wait_for_timeout(500)

    sikas_value = _normalise_case_id(case_id)
    print(f"[CASE TRACKER] Case # (sikas): {sikas_value}")

    sikas = page.locator('input[name="sikas"]')
    sikas.wait_for(state="visible", timeout=10000)
    sikas.fill(sikas_value)

    salcus_value = _normalise_salcus_value(salcus)
    salcus_input = page.locator('input[name="salcus"]')
    salcus_input.wait_for(state="visible", timeout=10000)
    if salcus_value:
        salcus_input.fill(salcus_value)
        print(f"[CASE TRACKER] Salcus (salcus): {salcus_value}")
    else:
        salcus_input.fill("")
        print("[CASE TRACKER] Salcus (salcus): left empty")

    if transfer is None:
        transfer = "1" if transfer_target else "0"
    transfer_flag = "1" if str(transfer) == "1" else "0"

    channel_key = (channel or "em_care").strip()
    is_voice = channel_key.lower() in {
        "voice",
        "voice_tel",
        "voice (tel.)",
        "voice (tel)",
        "tel",
        "call",
    }

    if tstate is None:
        if is_voice or transfer_flag == "1":
            tstate = "3"
        else:
            tstate = "1" if salcus_value else "3"
    # Voice/call LF: Ticketstatus Salcus is ALWAYS 3 (Bot dokumentiert nicht in Salcus)
    if is_voice:
        tstate = "3"
    tstate_labels = {
        "1": "1-Erfolgreich",
        "2": "2-Nicht Erfolgreich",
        "3": "3-Bot dokumentiert nicht in Salcus",
    }
    print(f"[CASE TRACKER] Ticketstatus Salcus: {tstate_labels.get(str(tstate), tstate)}")

    channel_map = {
        "em_care": "#channel_em_care",
        "E-Mail Care": "#channel_em_care",
        "email_care": "#channel_em_care",
        "voice": "#channel_voice",
        "voice_tel": "#channel_voice",
        "Voice (Tel.)": "#channel_voice",
        "Voice (Tel)": "#channel_voice",
        "tel": "#channel_voice",
        "call": "#channel_voice",
    }
    channel_sel = channel_map.get(channel_key, channel_map.get(channel_key.lower(), "#channel_em_care"))
    if is_voice:
        channel_sel = "#channel_voice"
    page.locator(channel_sel).click(force=True)
    print(
        f"[CASE TRACKER] Kanal: {'Voice (Tel.)' if is_voice or channel_sel == '#channel_voice' else channel_key}"
    )
    transfer_sel = "#transfer1" if transfer_flag == "1" else "#transfer0"
    # Radio may already be selected but CSS-hidden; force-click can throw "not visible".
    try:
        loc = page.locator(transfer_sel)
        already = loc.evaluate(
            "el => !!(el.checked || el.getAttribute('selected') !== null)"
        )
        if not already:
            loc.click(force=True, timeout=3000)
        else:
            # Ensure checked even if hidden (Roberta sometimes keeps radios off-screen)
            loc.evaluate("el => { el.checked = true; el.click(); }")
    except Exception:
        page.evaluate(
            """(sel) => {
              const el = document.querySelector(sel);
              if (!el) return;
              el.checked = true;
              el.dispatchEvent(new Event('click', { bubbles: true }));
              if (typeof el.onclick === 'function') el.onclick();
            }""",
            transfer_sel,
        )
    if transfer_flag == "1" and transfer_target:
        page.locator('input[name="target"]').fill(transfer_target.strip())
        print(f"[CASE TRACKER] Transfer: Ja -> {transfer_target.strip()}")
    elif transfer_flag == "1":
        print("[CASE TRACKER] Transfer: Ja (no target)")
    else:
        print("[CASE TRACKER] Transfer: Nein")

    tstate_map = {"1": "#tstate1", "2": "#tstate2", "3": "#tstate3"}
    page.locator(tstate_map.get(str(tstate), "#tstate1")).click(force=True)

    # Notiz — always leave empty (never log attachment counts or other notes)
    try:
        page.locator('input[name="note"]').fill("")
    except Exception:
        pass

    page.wait_for_timeout(400)

    if submit:
        page.locator('input[type="submit"][value="Speichern"]').first.click()
        page.wait_for_timeout(1500)
        print("[CASE TRACKER] Speichern clicked.")
    else:
        print("[CASE TRACKER] Fields filled — click Speichern manually when ready.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Open/fill Roberta O2 Case Tracker")
    ap.add_argument("--case-id", help='Sprinklr Case ID, e.g. "#36698255"')
    ap.add_argument("--salcus", help="Salcus ID (optional; auto-read from Sprinklr when omitted)")
    ap.add_argument(
        "--channel",
        default="em_care",
        help='Kanal: em_care (E-Mail Care, default) or voice / "Voice (Tel.)" for call cases',
    )
    ap.add_argument("--transfer", choices=["0", "1"], help="Transfer Nein/Ja override")
    ap.add_argument("--target", help="Transfer target queue/email override")
    ap.add_argument("--cdp", default=CDP_ENDPOINT)
    ap.add_argument("--open-only", action="store_true", help="Only open/reuse Case Tracker tab (login if needed)")
    ap.add_argument("--submit", action="store_true", help="Click Speichern after fill")
    ap.add_argument("--close-tab", action="store_true", help="Close tracker tab after fill (default: leave open)")
    ap.add_argument(
        "--watch-speichern",
        action="store_true",
        help="Detached: wait for Speichern click on Case Tracker and mark pending LF saved",
    )
    ap.add_argument(
        "--check-speichern",
        action="store_true",
        help="Print Speichern pending status (exit 0 if clear/seen, 2 if pending)",
    )
    ap.add_argument(
        "--clear-speichern-pending",
        action="store_true",
        help="Clear Speichern pending gate (after manual save or recovery)",
    )
    ap.add_argument(
        "--ignore-speichern-gate",
        action="store_true",
        help="Fill even if previous case Speichern was not registered",
    )
    ap.add_argument(
        "--continue-after-speichern",
        action="store_true",
        help="Detached: wait for previous Speichern, then Auto-LF the queued current case",
    )
    ap.add_argument(
        "--await-speichern-continue",
        action="store_true",
        help="Poll until continue-after-Speichern Auto-LF finishes",
    )
    ap.add_argument(
        "--no-continue-arm",
        action="store_true",
        help="On Speichern gate pause, do not auto-arm continue-after-Speichern",
    )
    args = ap.parse_args()

    if args.clear_speichern_pending:
        clear_speichern_state()
        print("LF_SPEICHERN_PENDING_CLEARED", flush=True)
        return 0

    if args.check_speichern:
        return check_speichern_status(cdp=args.cdp, sync_live=True)

    if args.await_speichern_continue:
        return await_speichern_continue()

    if args.continue_after_speichern:
        return run_continue_after_speichern(cdp=args.cdp)

    if args.watch_speichern:
        if not args.case_id:
            ap.error("--case-id is required with --watch-speichern")
        return run_speichern_watch(args.case_id, args.cdp)

    if not args.open_only and not args.case_id:
        ap.error("--case-id is required unless --open-only is set")

    config = _load_config()

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(args.cdp)
        except Exception as e:
            print(f"ERROR: Cannot connect to Chrome at {args.cdp}. Run login first.", file=sys.stderr)
            print(str(e), file=sys.stderr)
            return 1

        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        sprinklr = find_sprinklr_console_page(ctx)

        tracker = open_or_reuse_case_tracker_tab(ctx, config, bring_sprinklr_back=None)
        print(f"[CASE TRACKER] Tab ready: {tracker.url}")

        if args.open_only:
            if sprinklr:
                sprinklr.bring_to_front()
            return 0

        gate_rc = gate_previous_speichern(
            args.case_id,
            tracker,
            ignore=bool(args.ignore_speichern_gate),
        )
        if gate_rc is not None:
            if args.no_continue_arm:
                return gate_rc

            salcus_value = _normalise_salcus_value(args.salcus) if args.salcus else ""
            transfer_flag = args.transfer
            transfer_target = (args.target or "").strip()
            case_info: dict = {}
            if sprinklr:
                try:
                    sprinklr.bring_to_front()
                    sprinklr.wait_for_timeout(400)
                    case_info = extract_case_info_from_sprinklr(sprinklr)
                    if not salcus_value:
                        salcus_value = extract_salcus_from_sprinklr(sprinklr, case_info)
                except Exception:
                    case_info = {}
            if transfer_flag is None and not transfer_target:
                transfer_flag, transfer_target = resolve_transfer(case_info)
            elif transfer_flag is None:
                transfer_flag = "1" if transfer_target else "0"

            cont = build_continue_lf_args(
                case_id=args.case_id,
                channel=args.channel or "em_care",
                transfer=transfer_flag,
                target=transfer_target or None,
                salcus=salcus_value or None,
                cdp=args.cdp,
            )
            pid = spawn_continue_after_speichern(cont)
            if pid is None:
                print(
                    "ERROR: Could not arm continue-after-Speichern — click Speichern then retry Auto-LF manually.",
                    flush=True,
                )
                return gate_rc
            print(
                f"Armed — click Speichern for the previous LF; "
                f"Auto-LF for #{cont['case_id']} continues automatically.",
                flush=True,
            )
            # 3 = paused with continue watch armed (agent should --await-speichern-continue)
            return 3

        salcus_value = _normalise_salcus_value(args.salcus) if args.salcus else ""
        transfer_flag = args.transfer
        transfer_target = (args.target or "").strip()
        case_info: dict = {}

        if sprinklr:
            try:
                sprinklr.bring_to_front()
                sprinklr.wait_for_timeout(400)
                case_info = extract_case_info_from_sprinklr(sprinklr)
                if not salcus_value:
                    salcus_value = extract_salcus_from_sprinklr(sprinklr, case_info)
            except Exception:
                case_info = {}

        if transfer_flag is None and not transfer_target:
            transfer_flag, transfer_target = resolve_transfer(case_info)
        elif transfer_flag is None:
            transfer_flag = "1" if transfer_target else "0"

        fill_case_tracker_fields(
            tracker,
            args.case_id,
            salcus=salcus_value,
            channel=args.channel or "em_care",
            transfer=transfer_flag,
            transfer_target=transfer_target or None,
            submit=args.submit,
        )

        print("[CASE TRACKER] Form filled — stay on this tab; Sprinklr is not forced to front.")

        if args.submit:
            mark_speichern_seen(args.case_id, source="submit_flag")
            try:
                clear_page_speichern_marks(tracker)
            except Exception:
                pass
            clear_speichern_state()
            print("LF_SPEICHERN_CLEARED_AFTER_SUBMIT", flush=True)
        else:
            arm_speichern_for_case(tracker, args.case_id)
            set_speichern_pending(args.case_id)
            pid = spawn_speichern_watch(args.case_id)
            if pid is not None:
                st = read_speichern_state() or {}
                st["watch_pid"] = pid
                write_speichern_state(st)

        if args.close_tab:
            try:
                tracker.close()
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
