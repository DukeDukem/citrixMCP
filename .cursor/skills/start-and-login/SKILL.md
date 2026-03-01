---
name: start-and-login
description: Starts Chrome with remote debugging for automation, navigates to Sprinklr (Telefonica Germany) login, and fills email and password so automation scripts can run. Use when the user wants to open Sprinklr, log into the Sprinklr console, or prepare the browser for email/console automation.
---

# Start and Login (Sprinklr)

Starts Chrome with remote debugging enabled, opens the Sprinklr login page, and performs login so automation (e.g. email processing) can run.

## When to use

- User asks to "start Chrome with remote debugging", "log into Sprinklr", "open Sprinklr and login", or "prepare browser for automation".
- User wants to run scripts that control the Sprinklr console and needs a logged-in browser with CDP.

## Quick start

1. **Launch Chrome with remote debugging** (if not already running):
   ```bash
   scratchspace/launch_chrome_remote_debug.bat
   ```
   Or from PowerShell:
   ```powershell
   & "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
   ```
   Close any existing Chrome windows first so the new instance can bind to port 9222.

2. **Run the start-and-login script** (starts Chrome if needed, navigates to login URL, fills credentials, submits):
   ```bash
   uv run python scratchspace/sprinklr_start_and_login.py
   ```
   Requires: `playwright` and Chromium for CDP (`pip install playwright` then `playwright install chromium`), or use project venv with playwright installed.

## What the script does

- Ensures Chrome is running with `--remote-debugging-port=9222` (launches it if not).
- Connects to Chrome via CDP (Playwright).
- Navigates to the Sprinklr login URL (Telefonica Germany app).
- Fills **Email**: `harun.husic.external@telefonica.com` (field `input[name="uid"]` or `input[aria-label="Enter Email"]`).
- Fills **Password** in `input[name="pass"]` / `input[aria-label="Enter Password"]`.
- Submits the form and waits for navigation.

## Script location

- **Start + login (all-in-one):** `scratchspace/sprinklr_start_and_login.py`
- **Chrome launcher only:** `scratchspace/launch_chrome_remote_debug.bat`

Credentials are set inside `sprinklr_start_and_login.py`. For shared or secure use, switch to environment variables (e.g. `SPRINKLR_EMAIL`, `SPRINKLR_PASSWORD`).

## Login URL

```
https://telefonica-germany-app.sprinklr.com/ui/login?returnTo=%2Fui%2Fservice%2Flogin%3Fservice%3Dspr%26returnTo%3Dhttps%253A%252F%252Ftelefonica-germany.sprinklr.com%252Fapp%252Fconsole&service=spr
```

## Test (dry run)

To verify the script and environment without opening the browser or logging in:
```bash
uv run python scratchspace/sprinklr_start_and_login.py --dry-run
```
Prints Chrome path, whether CDP is listening, Playwright availability, and the login URL.

## Troubleshooting

- **"Cannot connect to Chrome"**: Close all Chrome windows, then run `launch_chrome_remote_debug.bat` or the script (which can launch Chrome for you).
- **Port 9222 in use**: Another app is using it; close that app or use a different port in the script and launcher.
- **Login field not found**: Page layout may have changed; update selectors in `sprinklr_start_and_login.py` (e.g. `input[name="uid"]`, `input[name="pass"]`).
