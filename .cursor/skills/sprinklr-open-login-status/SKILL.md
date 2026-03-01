---
name: sprinklr-open-login-status
description: Opens the Sprinklr (Telefonica Germany) webpage, logs in with configured credentials, and sets agent status to "Verfügbar" (active). Use when the user wants to open Sprinklr, log in, set status as available/active, or prepare the console for handling emails. Must run first before read-answer-email or fill-microsoft-form.
---

# Sprinklr: Open, Login, Set Status Active

**Independent script:** This skill runs on its own. It does not call any other skill. Run it first so the browser is logged in; Skills 2 and 3 then use that same browser when you run them separately.

**Order:** Skill 1 of 3. Run this first. Without it, read-answer-email and fill-microsoft-form have no logged-in session to attach to.

## How to invoke

**Run the script in this skill.** From repo root (or anywhere, script finds repo):

```powershell
uv run python .cursor/skills/sprinklr-open-login-status/run.py
```

Or with system Python if dependencies are installed:

```powershell
python .cursor/skills/sprinklr-open-login-status/run.py
```

The script runs `scratchspace/run_sprinklr_email_automation.py --login-only` (starts Chrome with CDP if needed, logs in, sets status to Verfügbar, then exits).

## Script file

- **Path:** `.cursor/skills/sprinklr-open-login-status/run.py`
- **Does:** Resolves repo root, sets `SPRINKLR_CDP_ENDPOINT`, runs the runner with `--login-only`.

## Prerequisites

- Chrome installed; `uv sync`; `uv run playwright install chromium`; `config.json` at repo root with `login_email`, `login_password`, `cdp_endpoint`.
