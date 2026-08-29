---
name: fill-microsoft-form
description: Opens and fills the Roberta O2 Case Tracker (and generic forms). Use when the user wants LF / log form / case tracker fill. Requires Chrome with CDP (login or sprinklr-open-login-status first).
---

# Fill Case Tracker (Roberta) / Microsoft Form

**Shorthand:** The user may type **LF** instead of "log form" or "fill the form". Treat **LF** as "fill the Roberta Case Tracker for the current Sprinklr case".

**Independent script:** Connects to Chrome via CDP (port 9222). Run **login** or **sprinklr-open-login-status** first so Chrome is running with Sprinklr open.

## Roberta Case Tracker (primary — LF)

URL: `https://roberta.yoummday.com/casetracker/`

On **login**, the Sprinklr automation opens Case Tracker in a new tab automatically (`--login-only`).

### Open only (after login)

```powershell
uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --open-only
```

### Fill one case (LF)

```powershell
uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#36698255" --attachments 0
```

- **Case #** → field `sikas` (Sprinklr Fall ID, `#` optional)
- **Salcus** → field `salcus` — source is Sprinklr sidebar **Kundennummer** (`data-entityid="Kundennummer"`, value in `htmlText`); left empty when **Nicht festgelegt** or absent. (Sprinklr labels this Kundennummer; Roberta calls it Salcus.)
- **Kanal** → E-Mail Care (`#channel_em_care`)
- **Transfer** → Nein (default)
- **Status** → **Ticketstatus Salcus**: Transfer cases → always `3-Bot dokumentiert nicht in Salcus`; non-transfer → `1-Erfolgreich` when Salcus filled, else `3-Bot dokumentiert nicht in Salcus`
- **Anhänge** → optional note when `--attachments` > 0
- **Default:** does **not** click Speichern — user submits after sending the email
- Add `--submit` to click Speichern automatically

### Config (`config.json`)

```json
{
  "case_tracker_url": "https://roberta.yoummday.com/casetracker/",
  "case_tracker_nq": "NQ10061547",
  "case_tracker_password": "YOUR_PASSWORD"
}
```

## Generic Microsoft Form (legacy)

For other Forms.office.com pages, use `run.py`:

```powershell
uv run python .cursor/skills/fill-microsoft-form/run.py --url "https://forms.office.com/..." --answers form_answers.json
```

## Order of skills

1. **login** / **sprinklr-open-login-status** — Sprinklr + Case Tracker tab  
2. **sprinklr-read-answer-email** — read and answer emails  
3. **fill_case_tracker.py** — LF after sending email  
