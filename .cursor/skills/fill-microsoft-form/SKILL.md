---
name: fill-microsoft-form
description: Opens and fills the Roberta O2 Case Tracker (and generic forms). Auto-LF runs during RE/CALL processing; typed LF is recovery. Requires Chrome with CDP (login first).
---

# Fill Case Tracker (Roberta) / Microsoft Form

**Shorthand:** **LF** = fill the **Roberta Case Tracker** for the current Sprinklr case.

**Default:** Agent runs **Auto-LF** after EMAIL 7-step RE (or CALL pack) — user does **not** type `LF`. Typed `LF` / `LF TR` / `PR LF` = override/recovery. See `.cursor/rules/lf-log-form.mdc`.

**Platform:** `https://roberta.yoummday.com/casetracker/` — **primary for LF**. Microsoft Forms is legacy only.

**Script:** Connects via CDP (port 9222). Run **login** first (opens Sprinklr + Case Tracker tab).

## Roberta Case Tracker (LF)

On **login** (`--login-only`), Sprinklr automation opens Case Tracker in a new tab automatically.

### Commands

```powershell
# Open/reuse tracker tab only
uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --open-only

# Auto-LF / LF — fill current case (reads Sprinklr sidebar automatically)
uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#36698255"
```

Optional overrides: `--salcus`, `--transfer 0|1`, `--target`, `--channel voice`, `--submit`

### After EMAIL Auto-LF

| Outcome | Next |
|---------|------|
| Non-transfer | Wait for user **PR** → then `run.py --arm` + `--await-arm` |
| Transfer | Immediately `--arm-weiter` or `--arm-extern` + `--await-arm` |

### After CALL Auto-LF

`--channel voice` → immediately `run.py --arm-next` + `--await-arm` (or weiter/extern if transfer).

Full rules: `.cursor/rules/lf-log-form.mdc`, `.cursor/rules/lf-tr-transfer.mdc`.

### Field mapping

| Roberta | Sprinklr source | Rule |
|---------|-----------------|------|
| `sikas` (Case #) | Fall # | Digits only |
| `salcus` | **Exclusive:** `div[data-entityid="Kundennummer"][aria-label="Kundennummer"]`. Re-read every Fall. Prefer `htmlText` when a number is shown; `spr-text-03` only if **Nicht festgelegt**. | Empty if unset/missing. **Never** from email/Webform body or other DOM. |
| Kanal | — | **EMAIL:** E-Mail Care. **CALL:** Voice (Tel.) (`--channel voice`) |
| Transfer / target | Quelle, Ziel, Subject | See below |
| Ticketstatus Salcus | Derived | See below — **CALL always 3** |
| Notiz | — | **Always empty** — never log attachment counts or other notes |

### Salcus (mandatory — exclusive source)

Fill Roberta `salcus` **only** from:

`div[data-entityid="Kundennummer"][aria-label="Kundennummer"]`

The number **changes every Fall #**. Prefer `[data-testid="htmlText"]` when a number is shown (do not rely on `spr-text-03` alone). Else `span.spr-text-03` for **Nicht festgelegt**. Missing/unset → empty. **Never** from email body, Webform, Betreff, or any other DOM. Full spec: `.cursor/rules/lf-log-form.mdc`.

### Ticketstatus Salcus

| Condition | Value |
|-----------|--------|
| **CALL / Voice (Tel.)** | **3-Bot dokumentiert nicht in Salcus** (**always**) |
| Transfer **Ja** | **3-Bot dokumentiert nicht in Salcus** (always) |
| Transfer **Nein** + valid numeric Kundennummer/Salcus | **1-Erfolgreich** |
| Transfer **Nein** + no Kundennummer / **`C-…` Vertragsnummer** | **3-Bot dokumentiert nicht in Salcus** |

**`C-` IDs are not Salcus:** e.g. Fall #55920431 — Kundennummer box shows `C-0026448826` → Salcus empty → ticketstatus **3**.

**Call LF example:**

```powershell
uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#57114650" --channel voice
```

### Transfer

| Signal | Transfer | Target |
|--------|----------|--------|
| Widerruf in **Quelle** (e.g. Care Widerruf, not Webform) | **Ja** | `EMAIL_O2_WIDERRUF` |
| Care Webform + our **Ziel** | **Nein** | — (ignore `\|Widerruf` in Betreff categories) |
| Ziel = our team (`EMAIL_O2_CARE`, `o2 Mobile Care`, legacy `*CARE_ALLGEMEIN*`) | **Nein** | — |
| External Ziel queue / email | **Ja** | Ziel value |

**Never** log Transfer Ja to our own team (`EMAIL_O2_CARE` / `o2 Mobile Care`).

Default: does **not** click **Speichern**. After fill, arms a detached Speichern click watch. Next Auto-LF on a **different** Fall # is **paused** until Speichern and **auto-continues**: `LF_CONTINUE_AFTER_SPEICHERN_ARMED` → agent `--await-speichern-continue` → `CONTINUE_LF_DONE`. Full rules: `.cursor/rules/lf-log-form.mdc`.

```powershell
uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --await-speichern-continue
uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --check-speichern
uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --clear-speichern-pending
```

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
