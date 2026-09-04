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
uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#36698255"
```

Optional overrides: `--salcus`, `--transfer 0|1`, `--target`, `--submit`

### LF TR (transfer, no PR)

When the user types **LF TR** / **lf tr** (optional `"alternate target"`):

1. Fill with `--transfer 1 --target "<RE 4a goal or user override>"`
2. Do **not** run PR
3. After fill succeeds, arm Weiter RE:
   `uv run python .cursor/skills/sprinklr-read-answer-email/run.py --arm-weiter`

Full rule: `.cursor/rules/lf-tr-transfer.mdc`.

### Field mapping

| Roberta | Sprinklr source | Rule |
|---------|-----------------|------|
| `sikas` (Case #) | Fall # | Digits only |
| `salcus` | **Exclusive:** `div[data-entityid="Kundennummer"][aria-label="Kundennummer"]`. Re-read every Fall. Prefer `htmlText` when a number is shown; `spr-text-03` only if **Nicht festgelegt**. | Empty if unset/missing. **Never** from email/Webform body or other DOM. |
| Kanal | — | E-Mail Care |
| Transfer / target | Quelle, Ziel, Subject | See below |
| Ticketstatus Salcus | Derived | See below |
| Notiz | — | **Always empty** — never log attachment counts or other notes |

### Salcus (mandatory — exclusive source)

Fill Roberta `salcus` **only** from:

`div[data-entityid="Kundennummer"][aria-label="Kundennummer"]`

The number **changes every Fall #**. Prefer `[data-testid="htmlText"]` when a number is shown (do not rely on `spr-text-03` alone). Else `span.spr-text-03` for **Nicht festgelegt**. Missing/unset → empty. **Never** from email body, Webform, Betreff, or any other DOM. Full spec: `.cursor/rules/lf-log-form.mdc`.

### Ticketstatus Salcus

| Condition | Value |
|-----------|--------|
| Transfer **Ja** | **3-Bot dokumentiert nicht in Salcus** (always) |
| Transfer **Nein** + valid numeric Kundennummer/Salcus | **1-Erfolgreich** |
| Transfer **Nein** + no Kundennummer / **`C-…` Vertragsnummer** | **3-Bot dokumentiert nicht in Salcus** |

**`C-` IDs are not Salcus:** e.g. Fall #55920431 — Kundennummer box shows `C-0026448826` → Salcus empty → ticketstatus **3**.

### Transfer

| Signal | Transfer | Target |
|--------|----------|--------|
| Widerruf in **Quelle** (e.g. Care Widerruf, not Webform) | **Ja** | `CBC_XF_E_WIDERRUF` |
| Care Webform + our **Ziel** | **Nein** | — (ignore `\|Widerruf` in Betreff categories) |
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
