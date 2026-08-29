"""
Roberta / Yoummday O2 Case Tracker filler.

Opens https://roberta.yoummday.com/casetracker/ in a NEW browser tab (Sprinklr stays open),
optionally logs in, fills Case # + channel + defaults, leaves save to the user unless --submit.

Usage:
    uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#36698255"
    uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "36698255" --attachments 2 --submit
    uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --open-only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("ERROR: Run  uv sync  and  uv run playwright install chromium")
    sys.exit(1)

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


def _normalise_salcus_value(raw: str | None) -> str:
    """Return Salcus ID for tracker fill, or empty when unset / placeholder."""
    value = (raw or "").replace("\u200f", "").replace("\u200e", "").strip()
    value = " ".join(value.split())
    if value.lower() in _SALCUS_UNSET:
        return ""
    # Salcus IDs are numeric; reject obvious labels/URLs
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return ""
    if "http" in value.lower() or "@" in value:
        return ""
    return digits[:20]


_EXTRACT_SALCUS_JS = """
() => {
  const unset = new Set(['', '—', '-', 'nicht festgelegt', 'not set', 'n/a', 'na']);
  const norm = (s) => (s || '').replace(/[\\u200f\\u200e]/g, '').replace(/\\u00a0/g, ' ').replace(/\\s+/g, ' ').trim();
  const isUnset = (v) => unset.has(norm(v).toLowerCase());
  const isLabel = (v) => /^(Kundennummer|Salcus|Customer ID)$/i.test(norm(v));

  const readKundennummerField = (field) => {
    if (!field) return '';
    const prefer = field.querySelector('[data-testid="htmlText"]');
    if (prefer) {
      const v = norm(prefer.textContent);
      if (v && !isUnset(v) && !isLabel(v)) return v;
    }
    for (const sel of [
      '[data-testid="linkifiedText"] [data-testid="htmlText"]',
      '[data-testid="linkifiedText"] span',
      'span.spr-text-03',
      'span[class*="spr-text-03"]',
      '.font-500 span',
    ]) {
      for (const el of field.querySelectorAll(sel)) {
        const v = norm(el.textContent);
        if (v && !isUnset(v) && !isLabel(v)) return v;
      }
    }
    return '';
  };

  // Primary: Sprinklr sidebar "Kundennummer" = Salcus ID for Roberta tracker
  const knFields = document.querySelectorAll('[data-entityid="Kundennummer"]');
  for (const field of knFields) {
    const v = readKundennummerField(field);
    if (v) return v;
  }

  // Fallback: aria-label on presentation field
  for (const field of document.querySelectorAll('[aria-label="Kundennummer"]')) {
    const v = readKundennummerField(field);
    if (v) return v;
  }

  const readValueFromBox = (box) => {
    if (!box) return '';
    const htmlText = box.querySelector('[data-testid="htmlText"]');
    if (htmlText) {
      const v = norm(htmlText.textContent);
      if (v && !isUnset(v) && !isLabel(v)) return v;
    }
    const span = box.querySelector('span.spr-text-03, span[class*="spr-text-03"]');
    const v = norm(span ? span.textContent : box.textContent);
    return v && !isLabel(v) ? v : '';
  };

  // Legacy fallback: explicit "Salcus" label row
  const boxes = Array.from(document.querySelectorAll('[data-testid="box"]'));
  for (let i = 0; i < boxes.length; i++) {
    const label = norm(boxes[i].textContent);
    if (label === 'Salcus' || /^Salcus\\b/i.test(label)) {
      let value = readValueFromBox(boxes[i + 1]);
      if ((!value || isUnset(value)) && boxes[i].parentElement) {
        value = readValueFromBox(boxes[i].parentElement);
      }
      if (value && !isUnset(value) && !/^Salcus/i.test(value)) return value;
    }
  }

  // Label/value pair walk for "Kundennummer" text label (no data-entityid)
  for (let i = 0; i < boxes.length; i++) {
    const label = norm(boxes[i].textContent);
    if (label === 'Kundennummer') {
      const value = readValueFromBox(boxes[i + 1]) || readValueFromBox(boxes[i].parentElement);
      if (value && !isUnset(value) && !isLabel(value)) return value;
    }
  }

  return '';
}
"""


def extract_salcus_from_sprinklr(page) -> str:
    """Read Salcus ID from Sprinklr Kundennummer sidebar field; empty if unset."""
    if page is None:
        return ""
    try:
        raw = page.evaluate(_EXTRACT_SALCUS_JS)
    except Exception:
        return ""
    salcus = _normalise_salcus_value(raw if isinstance(raw, str) else "")
    if salcus:
        print(f"[CASE TRACKER] Salcus from Sprinklr Kundennummer: {salcus}")
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
    subject = (case_info.get("Subject") or "").lower()

    # Widerruf cases → real transfer to Widerruf queue (not our Care Allgemein team)
    if "widerruf" in quelle or "widerruf" in subject:
        return "1", "CBC_XF_E_WIDERRUF"

    # Our team (CBC_*_CARE_ALLGEMEIN incl. CBC_XF_E_CARE_ALLGEMEIN) — never Transfer Ja to ourselves
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
    attachments: int = 0,
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

    if tstate is None:
        if transfer_flag == "1":
            tstate = "3"
        else:
            tstate = "1" if salcus_value else "3"
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
    }
    channel_sel = channel_map.get(channel, "#channel_em_care")
    page.locator(channel_sel).click(force=True)

    transfer_sel = "#transfer1" if transfer_flag == "1" else "#transfer0"
    page.locator(transfer_sel).click(force=True)
    if transfer_flag == "1" and transfer_target:
        page.locator('input[name="target"]').fill(transfer_target.strip())
        print(f"[CASE TRACKER] Transfer: Ja -> {transfer_target.strip()}")
    elif transfer_flag == "1":
        print("[CASE TRACKER] Transfer: Ja (no target)")
    else:
        print("[CASE TRACKER] Transfer: Nein")

    tstate_map = {"1": "#tstate1", "2": "#tstate2", "3": "#tstate3"}
    page.locator(tstate_map.get(str(tstate), "#tstate1")).click(force=True)

    if attachments > 0:
        att_note = f"Anhänge: {attachments}" if attachments < 4 else "Anhänge: mehr als 3"
        try:
            page.locator('input[name="note"]').fill(att_note)
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
    ap.add_argument("--transfer", choices=["0", "1"], help="Transfer Nein/Ja override")
    ap.add_argument("--target", help="Transfer target queue/email override")
    ap.add_argument("--attachments", type=int, default=0)
    ap.add_argument("--cdp", default=CDP_ENDPOINT)
    ap.add_argument("--open-only", action="store_true", help="Only open/reuse Case Tracker tab (login if needed)")
    ap.add_argument("--submit", action="store_true", help="Click Speichern after fill")
    ap.add_argument("--close-tab", action="store_true", help="Close tracker tab after fill (default: leave open)")
    args = ap.parse_args()

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

        tracker = open_or_reuse_case_tracker_tab(ctx, config, bring_sprinklr_back=sprinklr)
        print(f"[CASE TRACKER] Tab ready: {tracker.url}")

        if args.open_only:
            if sprinklr:
                sprinklr.bring_to_front()
            return 0

        salcus_value = _normalise_salcus_value(args.salcus) if args.salcus else ""
        transfer_flag = args.transfer
        transfer_target = (args.target or "").strip()
        case_info: dict = {}

        if sprinklr:
            try:
                sprinklr.bring_to_front()
                sprinklr.wait_for_timeout(400)
                if not salcus_value:
                    salcus_value = extract_salcus_from_sprinklr(sprinklr)
                case_info = extract_case_info_from_sprinklr(sprinklr)
            except Exception:
                case_info = {}

        if transfer_flag is None and not transfer_target:
            transfer_flag, transfer_target = resolve_transfer(case_info)
        elif transfer_flag is None:
            transfer_flag = "1" if transfer_target else "0"

        fill_case_tracker_fields(
            tracker,
            args.case_id,
            args.attachments,
            salcus=salcus_value,
            transfer=transfer_flag,
            transfer_target=transfer_target or None,
            submit=args.submit,
        )

        if sprinklr:
            sprinklr.bring_to_front()

        if args.close_tab:
            try:
                tracker.close()
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
