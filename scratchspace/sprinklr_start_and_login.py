"""
Start Chrome with remote debugging, open Sprinklr login page, and fill email + password.
Allows automation scripts to run against the Sprinklr (Telefonica Germany) console.

Usage: uv run python scratchspace/sprinklr_start_and_login.py
       or: python scratchspace/sprinklr_start_and_login.py (with playwright installed)

Credentials are below; for shared use, prefer env vars SPRINKLR_EMAIL and SPRINKLR_PASSWORD.
"""

import os
import subprocess
import sys
import time

# Login URL (full returnTo for console)
LOGIN_URL = (
    "https://telefonica-germany-app.sprinklr.com/ui/login"
    "?returnTo=%2Fui%2Fservice%2Flogin%3Fservice%3Dspr"
    "%26returnTo%3Dhttps%253A%252F%252Ftelefonica-germany.sprinklr.com%252Fapp%252Fconsole"
    "&service=spr"
)
EMAIL = os.environ.get("SPRINKLR_EMAIL", "harun.husic.external@telefonica.com")
PASSWORD = os.environ.get("SPRINKLR_PASSWORD", "tHUnDerBoLt!92#fLaMe")

CDP_PORT = 9222
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"

# Chrome paths (Windows)
CHROME_PATHS = [
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_chrome() -> str | None:
    for path in CHROME_PATHS:
        if path and os.path.isfile(path):
            return path
    return None


def is_cdp_listening() -> bool:
    try:
        import urllib.request
        req = urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=2)
        return req.status == 200
    except Exception:
        return False


def launch_chrome_with_remote_debug() -> bool:
    chrome = find_chrome()
    if not chrome:
        print("Chrome not found. Install Chrome or set Chrome path.", file=sys.stderr)
        return False
    print(f"Launching Chrome with remote debugging on port {CDP_PORT}...")
    subprocess.Popen(
        [chrome, f"--remote-debugging-port={CDP_PORT}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(25):
        time.sleep(1)
        if is_cdp_listening():
            print("Chrome is listening for CDP.")
            return True
    print("Chrome did not become ready in time. If Chrome was already running, close ALL Chrome windows and run again.", file=sys.stderr)
    return False


def main() -> int:
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    if dry_run:
        chrome = find_chrome()
        print(f"Dry run: Chrome path = {chrome or 'NOT FOUND'}")
        print(f"CDP listening (port {CDP_PORT}): {is_cdp_listening()}")
        try:
            from playwright.sync_api import sync_playwright
            print("Playwright: OK")
        except ImportError as e:
            print(f"Playwright: NOT INSTALLED ({e})")
        print("Login URL (first 80 chars):", LOGIN_URL[:80])
        return 0

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Run: pip install playwright && playwright install chromium", file=sys.stderr)
        return 1

    if not is_cdp_listening():
        if not launch_chrome_with_remote_debug():
            return 1
        time.sleep(2)

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(f"Cannot connect to Chrome at {CDP_URL}: {e}", file=sys.stderr)
            print("Close all Chrome windows and run this script again, or run launch_chrome_remote_debug.bat first.", file=sys.stderr)
            return 1

        contexts = browser.contexts
        if not contexts:
            context = browser.new_context()
            page = context.new_page()
        else:
            context = contexts[0]
            pages = context.pages
            page = pages[0] if pages else context.new_page()

        print(f"Navigating to Sprinklr login: {LOGIN_URL[:60]}...")
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(1.5)

        # Email: input[name="uid"] or Enter Email
        email_selectors = ['input[name="uid"]', 'input[aria-label="Enter Email"]', 'input[type="email"]']
        email_ok = False
        for sel in email_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.click()
                    time.sleep(0.3)
                    el.fill("")
                    el.type(EMAIL, delay=50)
                    email_ok = True
                    print("Email filled.")
                    break
            except Exception:
                continue
        if not email_ok:
            print("Could not find email field.", file=sys.stderr)
            return 1

        time.sleep(0.5)

        # Password: input[name="pass"] or Enter Password
        pass_selectors = ['input[name="pass"]', 'input[aria-label="Enter Password"]', 'input[type="password"]']
        pass_ok = False
        for sel in pass_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click()
                    time.sleep(0.3)
                    el.fill("")
                    el.type(PASSWORD, delay=50)
                    pass_ok = True
                    print("Password filled.")
                    break
            except Exception:
                continue
        if not pass_ok:
            print("Could not find password field.", file=sys.stderr)
            return 1

        time.sleep(0.8)

        # Submit
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Anmelden")',
            'button:has-text("Sign in")',
        ]
        for sel in submit_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=1500):
                    btn.click()
                    print("Login form submitted.")
                    break
            except Exception:
                continue

        # Wait for URL to leave login
        for _ in range(20):
            time.sleep(1)
            url = page.url
            if "login" not in url.lower() and "sprinklr.com" in url:
                print("Login completed.")
                break
        else:
            print("Still on login page; check manually.")

        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
