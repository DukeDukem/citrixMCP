---
name: sprinklr-open-login-status
description: Opens the Sprinklr (Telefonica Germany) webpage, logs in with configured credentials, sets agent status to "Verfügbar" (active), and starts the email monitor so new emails are auto-detected and replied. Use for cold start (after restart) or to open Sprinklr and keep monitoring active. Stop with Ctrl+C.
---

# Sprinklr: Open, Login, Set Status, and Start Email Monitor

**One command:** Run this to open Sprinklr, log in, set status to **Verfügbar**, and **start the email monitoring loop**. The script stays active and watches for new emails until you press **Ctrl+C**. Ideal after closing Cursor or restarting the PC.

**Order:** Skill 1 of 3. Run this first; it now includes the monitor so you do not need to run the monitor script separately.

## How to invoke

From repo root (or anywhere, script finds repo):

```powershell
uv run python .cursor/skills/sprinklr-open-login-status/run.py
```

Or with system Python:

```powershell
python .cursor/skills/sprinklr-open-login-status/run.py
```

The script runs the automation with **--login-then-monitor**: starts Chrome with CDP if needed, opens Sprinklr, logs in, sets status to Verfügbar, then **starts the email monitor** and keeps running until Ctrl+C.

## Mandatory login verification gate

Before any follow-up automation (monitoring, RE, PR, LF, or case handling), the agent must verify that login actually succeeded.

- Required checks (at least one must be true, and none may indicate login page):
  - Sprinklr console URL is loaded (`/app/console` or console workspace visible), or
  - UI shows authenticated console elements (queue/case area, agent status controls), and
  - Login form is no longer present (`input[name="uid"]` / `input[name="pass"]` not active).
- If login is not verified:
  - Re-run login flow once.
  - If still not verified, stop and report login failure instead of continuing.

**To stop:** Press **Ctrl+C** in the terminal.

**Login only (no monitor):** If you only want to log in and exit without starting the monitor, run the runner directly with `--login-only`:
```powershell
uv run python .cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py --login-only
```

## Script file

- **Path:** `.cursor/skills/sprinklr-open-login-status/run.py`
- **Does:** Runs the automation with `--login-then-monitor` (login + set status, then start email monitoring).

## Prerequisites

- Chrome installed; `uv sync`; `uv run playwright install chromium`; `config.json` at repo root with `login_email`, `login_password`, `cdp_endpoint`.
