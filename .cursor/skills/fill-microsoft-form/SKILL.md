---
name: fill-microsoft-form
description: Fills out a Microsoft Form (e.g. Forms.office.com) with user-provided or known data. Use when the user wants to fill a Microsoft Form, submit form answers, or automate form completion. Requires Chrome with CDP (run sprinklr-open-login-status first to start the browser, or have answered emails in Sprinklr then run this).
---

# Fill Microsoft Form

**Independent script:** This skill runs on its own. It does not call Skill 1 or Skill 2; it connects to Chrome via CDP (port 9222). Run **sprinklr-open-login-status** first so Chrome is running with remote debugging; then run this script to fill the form in that browser.

---

## O2 Case Tracker Form (PRIMARY USE - run after every sent email)

After writing a reply in Sprinklr (whether via write-reply skill or manually), this skill
**automatically** opens the O2 case tracker form in a **new browser tab**, fills all fields,
submits, and reloads the blank form ready for the next case.

### Form URL
```
https://forms.office.com/pages/responsepage.aspx?id=U9hZg7dlBkOg9q1YALTAaNxfaEmV1w5Et9ekas02iq1URTA4VlY5ME1WNTlFNE1JUzRLVUlJS1RXNC4u&route=shorturl
```

### Field mapping (always use these rules)

| # | Question | Value | Source |
|---|---|---|---|
| 1 | Deine vollstandige NQ. | `NQ10061547` | Always fixed |
| 2 | WDE: Vollstandige Salcus-Nummer / SIKAS: Fall ID | `#<case_number>` | Full 8-digit ID from case, e.g. `#00646469` - never strip leading zeros |
| 3 | Kanal | `E-Mail Care` | Always fixed (radio button) |
| 4 | Wie viele Anhaenge hast Du im Email? | `0` / `1` / `2` / `3` / `mehr als 3` | Count from email; default 0 |

### How to invoke (case tracker script)

```powershell
python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#646469" --attachments 0
```

The script:
1. Opens the form in a **new tab** (Sprinklr tab stays open)
2. Fills all 4 fields
3. Leaves the form open for the user to review and submit manually

### Attachment count rule
- Read the number of visible attachment icons/files shown in the customer email in Sprinklr
- If none visible: use `0`
- If count is 4 or more: use `mehr als 3`
- Default to `0` if uncertain

---

## Generic Microsoft Form (any other form)

For arbitrary forms, use the general `run.py` script with a JSON answers file:

```powershell
python .cursor/skills/fill-microsoft-form/run.py --url "https://forms.office.com/..." --answers form_answers.json
```

**Args:** `--url` (required), `--answers` (path to JSON), optional `--no-submit`, `--cdp` (default `http://127.0.0.1:9222`)

**Answers JSON format:**
```json
{
  "Your name": "Max Mustermann",
  "Email address": "max@example.com"
}
```

---

## Order of skills

1. **sprinklr-open-login-status** — open Sprinklr, login, set status
2. **sprinklr-read-answer-email** — read email, query KB, draft reply
3. **sprinklr-write-reply** — write reply into Sprinklr editor; user sends
4. **fill-microsoft-form** (fill_case_tracker.py) — log the case in the O2 tracker form
