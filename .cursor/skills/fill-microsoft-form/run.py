"""
Skill 3: Fill a Microsoft Form with provided answers. Uses the same Chrome instance
as Skill 1/2 (must be running with remote debugging on port 9222).

  uv run python .cursor/skills/fill-microsoft-form/run.py --url "https://forms.office.com/..." --answers answers.json
  uv run python .cursor/skills/fill-microsoft-form/run.py --url "https://..." --answers answers.json --no-submit

Answers JSON: object mapping question label (or placeholder) to answer string, e.g.:
  { "Your name": "John", "Email": "john@example.com", "Comment": "Hello" }
"""
import argparse
import json
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright required: uv run playwright install chromium", file=sys.stderr)
    sys.exit(1)

CDP_DEFAULT = "http://127.0.0.1:9222"

def main() -> int:
    ap = argparse.ArgumentParser(description="Fill a Microsoft Form via existing Chrome (CDP)")
    ap.add_argument("--url", required=True, help="Microsoft Form URL")
    ap.add_argument("--answers", required=True, help="Path to JSON file: { \"Question label\": \"answer\", ... }")
    ap.add_argument("--no-submit", action="store_true", help="Fill but do not click submit")
    ap.add_argument("--cdp", default=CDP_DEFAULT, help=f"CDP endpoint (default: {CDP_DEFAULT})")
    args = ap.parse_args()

    answers_path = Path(args.answers)
    if not answers_path.is_absolute():
        # Relative to repo root
        repo_root = Path(__file__).resolve().parent.parent.parent
        answers_path = repo_root / answers_path
    if not answers_path.exists():
        print(f"Answers file not found: {answers_path}", file=sys.stderr)
        return 1
    with open(answers_path, "r", encoding="utf-8") as f:
        answers = json.load(f)
    if not isinstance(answers, dict):
        print("Answers JSON must be an object: { \"label\": \"value\", ... }", file=sys.stderr)
        return 1

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(args.cdp)
        except Exception as e:
            print(f"Cannot connect to Chrome at {args.cdp}. Run Skill 1 first (open Sprinklr / login).", file=sys.stderr)
            print(str(e), file=sys.stderr)
            return 1
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(args.url, wait_until="networkidle")
        page.wait_for_timeout(2000)

        filled = 0
        for label_or_placeholder, value in answers.items():
            if not value:
                continue
            try:
                # Try by role and label first (covers most MS Form fields)
                loc = page.get_by_label(label_or_placeholder.strip())
                if loc.count() > 0:
                    loc.first.fill(str(value))
                    filled += 1
                    continue
            except Exception:
                pass
            try:
                # Fallback: placeholder or visible text near input
                loc = page.locator(f'input[placeholder*="{label_or_placeholder[:30]}"], textarea[placeholder*="{label_or_placeholder[:30]}"]').first
                if loc.is_visible():
                    loc.fill(str(value))
                    filled += 1
                    continue
            except Exception:
                pass
            try:
                # Radio: click option that matches value
                opt = page.get_by_role("radio", name=value)
                if opt.count() > 0:
                    opt.first.click()
                    filled += 1
                    continue
            except Exception:
                pass
            print(f"[WARN] Could not find field for: {label_or_placeholder!r}", file=sys.stderr)

        if not args.no_submit:
            try:
                submit = page.get_by_role("button", name="Submit").or_(page.locator('button:has-text("Submit")').first)
                if submit.count() > 0:
                    submit.first.click()
                    print("Submitted.")
                else:
                    print("[WARN] No submit button found; form not submitted.", file=sys.stderr)
            except Exception as e:
                print(f"[WARN] Submit failed: {e}", file=sys.stderr)

        print(f"Filled {filled} field(s).")
        # Do not close browser - we connected to user's Chrome via CDP
    return 0

if __name__ == "__main__":
    sys.exit(main())
