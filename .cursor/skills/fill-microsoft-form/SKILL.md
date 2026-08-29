---
name: fill-microsoft-form
description: Opens and fills the Roberta O2 Case Tracker (and generic forms). Use when the user wants LF / log form / case tracker fill. Requires Chrome with CDP (login or sprinklr-open-login-status first).
---

# Fill Case Tracker (Roberta) / Microsoft Form

**Shorthand:** **LF** = fill the **Roberta Case Tracker** for the current Sprinklr case.

**Platform:** `https://roberta.yoummday.com/casetracker/` — **primary for LF**. Microsoft Forms is legacy only.

**Script:** Connects via CDP (port 9222). Run **login** first (opens Sprinklr + Case Tracker tab).

## Roberta Case Tracker (LF)

On **login** (`--login-only`), Sprinklr automation opens Case Tracker in a new tab automatically.

### Commands

```powershell
# Open/reuse tracker tab only
uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --open-only

# LF — fill current case (reads Sprinklr sidebar automatically)
uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#36698255" --attachments 0
```

Optional overrides: `--salcus`, `--transfer 0|1`, `--target`, `--submit`

### Field mapping

| Roberta | Sprinklr source | Rule |
|---------|-----------------|------|
| `sikas` (Case #) | Fall # | Digits only |
| `salcus` | **Kundennummer** `data-entityid="Kundennummer"` → `htmlText` | Empty if **Nicht festgelegt**. Not from email body. |
| Kanal | — | E-Mail Care |
| Transfer / target | Quelle, Ziel, Subject | See below |
| Ticketstatus Salcus | Derived | See below |

### Ticketstatus Salcus

| Condition | Value |
|-----------|--------|
| Transfer **Ja** | **3-Bot dokumentiert nicht in Salcus** (always) |
| Transfer **Nein** + Kundennummer | **1-Erfolgreich** |
| Transfer **Nein** + no Kundennummer | **3-Bot dokumentiert nicht in Salcus** |

### Transfer

| Signal | Transfer | Target |
|--------|----------|--------|
| Widerruf in Quelle/Subject | **Ja** | `CBC_XF_E_WIDERRUF` |
| Ziel = our team (`CBC_*_CARE_ALLGEMEIN`, incl. `CBC_XF_E_CARE_ALLGEMEIN`) | **Nein** | — |
| External Ziel queue / email | **Ja** | Ziel value |

**Never** log Transfer Ja to our own Care Allgemein team.

Default: does **not** click **Speichern**. Full rules: `.cursor/rules/lf-log-form.mdc`.

### Config (`config.json`)

```json
{
  "case_tracker_url": "https://roberta.yoummday.com/casetracker/",
  "case_tracker_nq": "NQ10061547",
  "case_tracker_password": "YOUR_PASSWORD"
}
```

## Generic Microsoft Form (legacy)

```powershell
uv run python .cursor/skills/fill-microsoft-form/run.py --url "https://forms.office.com/..." --answers form_answers.json
```

## Order of skills

1. **login** — Sprinklr + Case Tracker tab  
2. **RE** — read and answer emails  
3. **PR** — paste reply  
4. **LF** — `fill_case_tracker.py` after sending email  
