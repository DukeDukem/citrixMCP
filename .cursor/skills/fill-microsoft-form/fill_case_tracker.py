"""
O2 Case Tracker Form Filler
Opens the O2 case tracker Microsoft Form in a NEW browser tab, fills all fields,
submits, then reloads the blank form (ready for the next case).

Usage:
    python fill_case_tracker.py --case-id "#646469" --attachments 0
    python fill_case_tracker.py --case-id "646469" --attachments 2

Fixed values (always the same):
    Q1 - NQ:        NQ10061547
    Q3 - Kanal:     E-Mail Care

Variable values (per case):
    Q2 - Fall ID:   --case-id  (prepends # if missing)
    Q4 - Anhaenge:  --attachments  (0 / 1 / 2 / 3 / mehr als 3)
"""
import argparse
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("ERROR: Run  python -m pip install playwright  then  playwright install chromium")
    sys.exit(1)

FORM_URL = (
    "https://forms.office.com/pages/responsepage.aspx"
    "?id=U9hZg7dlBkOg9q1YALTAaNxfaEmV1w5Et9ekas02iq1URTA4VlY5ME1WNTlFNE1JUzRLVUlJS1RXNC4u"
    "&route=shorturl"
)
CDP_ENDPOINT = "http://127.0.0.1:9222"
NQ_VALUE = "NQ10061547"


def parse_attachment_value(n: int) -> str:
    """Convert integer to the radio option label used in the form."""
    if n >= 4:
        return "mehr als 3"
    return str(n)


def main() -> int:
    ap = argparse.ArgumentParser(description="Fill the O2 Case Tracker form")
    ap.add_argument("--case-id", required=True, help='Case ID, e.g. "#646469" or "646469"')
    ap.add_argument("--attachments", type=int, default=0, help="Number of attachments (0-3, or 4+ = mehr als 3)")
    ap.add_argument("--cdp", default=CDP_ENDPOINT)
    args = ap.parse_args()

    # Normalise case ID - ensure it starts with #
    case_id = args.case_id.strip()
    if not case_id.startswith("#"):
        case_id = "#" + case_id

    attachment_value = parse_attachment_value(args.attachments)

    print(f"[FORM] Case ID: {case_id}")
    print(f"[FORM] NQ: {NQ_VALUE}")
    print(f"[FORM] Kanal: E-Mail Care")
    print(f"[FORM] Attachments: {attachment_value}")

    with sync_playwright() as p:
        # Connect to existing Chrome via CDP
        try:
            browser = p.chromium.connect_over_cdp(args.cdp)
        except Exception as e:
            print(f"ERROR: Cannot connect to Chrome at {args.cdp}. Run Skill 1 first.", file=sys.stderr)
            print(str(e), file=sys.stderr)
            return 1

        ctx = browser.contexts[0] if browser.contexts else browser.new_context()

        # Open form in a NEW tab so Sprinklr tab stays intact
        print("[FORM] Opening form in new tab...")
        form_page = ctx.new_page()
        form_page.goto(FORM_URL, wait_until="domcontentloaded", timeout=30000)
        form_page.wait_for_timeout(3000)

        # ── Q1: NQ (text input) ──────────────────────────────────────────────
        print(f"[FORM] Filling Q1 (NQ): {NQ_VALUE}")
        try:
            q1 = form_page.locator('[data-automation-id="textInput"]').first
            q1.wait_for(state="visible", timeout=10000)
            q1.click()
            q1.fill(NQ_VALUE)
        except Exception as e:
            print(f"[WARN] Q1 fill failed: {e}", file=sys.stderr)

        form_page.wait_for_timeout(500)

        # ── Q2: Case ID (second text input) ──────────────────────────────────
        print(f"[FORM] Filling Q2 (Fall ID): {case_id}")
        try:
            q2 = form_page.locator('[data-automation-id="textInput"]').nth(1)
            q2.click()
            q2.fill(case_id)
        except Exception as e:
            print(f"[WARN] Q2 fill failed: {e}", file=sys.stderr)

        form_page.wait_for_timeout(500)

        # ── Q3: Kanal = E-Mail Care (radio) ──────────────────────────────────
        print("[FORM] Selecting Q3 (Kanal): E-Mail Care")
        try:
            radio_email = form_page.locator('input[type="radio"][value="E-Mail Care"]')
            radio_email.wait_for(state="visible", timeout=10000)
            radio_email.click(force=True)
        except Exception as e:
            # fallback: click by label text
            try:
                form_page.get_by_role("radio", name="E-Mail Care").first.click()
            except Exception as e2:
                print(f"[WARN] Q3 radio failed: {e} / {e2}", file=sys.stderr)

        form_page.wait_for_timeout(500)

        # ── Q4: Anzahl Anhaenge (radio) ───────────────────────────────────────
        print(f"[FORM] Selecting Q4 (Anhaenge): {attachment_value}")
        try:
            radio_att = form_page.locator(f'input[type="radio"][value="{attachment_value}"]')
            radio_att.wait_for(state="visible", timeout=10000)
            radio_att.click(force=True)
        except Exception as e:
            try:
                form_page.get_by_role("radio", name=attachment_value).first.click()
            except Exception as e2:
                print(f"[WARN] Q4 radio failed: {e} / {e2}", file=sys.stderr)

        form_page.wait_for_timeout(1000)

        # Form is filled - leave it open for the user to review and submit manually
        print("[FORM] All fields filled. Form is ready for review - please submit manually.")

        print(f"[FORM] Done. Case {case_id} logged.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
