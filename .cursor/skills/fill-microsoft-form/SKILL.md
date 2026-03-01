---
name: fill-microsoft-form
description: Fills out a Microsoft Form (e.g. Forms.office.com) with user-provided or known data. Use when the user wants to fill a Microsoft Form, submit form answers, or automate form completion. Requires Chrome with CDP (run sprinklr-open-login-status first to start the browser, or have answered emails in Sprinklr then run this).
---

# Fill Microsoft Form

**Independent script:** This skill runs on its own. It does not call Skill 1 or Skill 2; it connects to Chrome via CDP (port 9222). Run **sprinklr-open-login-status** first so Chrome is running with remote debugging; then run this script with `--url` and `--answers` to fill the form in that browser.

## How to invoke

**Run the script in this skill** with the form URL and a JSON file of answers.

From repo root:

```powershell
uv run python .cursor/skills/fill-microsoft-form/run.py --url "https://forms.office.com/..." --answers form_answers.json
```

To fill but not submit:

```powershell
uv run python .cursor/skills/fill-microsoft-form/run.py --url "https://forms.office.com/..." --answers form_answers.json --no-submit
```

If the answers file is in the skill folder:

```powershell
uv run python .cursor/skills/fill-microsoft-form/run.py --url "https://forms.office.com/..." --answers .cursor/skills/fill-microsoft-form/form_answers.json
```

## Script file

- **Path:** `.cursor/skills/fill-microsoft-form/run.py`
- **Args:** `--url` (required), `--answers` (path to JSON), optional `--no-submit`, `--cdp` (default `http://127.0.0.1:9222`)
- **Answers JSON:** Object mapping question label (or placeholder) to answer string, e.g. `{ "Your name": "John", "Email": "john@example.com" }`

## Example answers file

Create a JSON file (e.g. `form_answers.json`) in the skill folder or repo:

```json
{
  "Your name": "Max Mustermann",
  "Email address": "max@example.com",
  "Comment": "My answer here"
}
```

The script finds fields by label (or placeholder) and fills them; then clicks Submit unless `--no-submit` is set.

## Order of skills

1. **sprinklr-open-login-status** (run.py) — open Sprinklr, login, set status  
2. **sprinklr-read-answer-email** (run.py) — read and answer emails  
3. **fill-microsoft-form** (run.py) — fill the form in the same browser  
