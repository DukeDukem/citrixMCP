# ERROR REPORT — Extern arm / Weiterleiten → next-case extract failed

**For:** Instructions / rules agent (`AGENT-INSTRUCTIONS.md`)  
**From:** Email Processing Agent  
**Date:** 2026-09-04 (evening, local)  
**Fall # (transfer):** `#55411928` (Sandra Wachala — DSGVO Art. 15 → `DS_Beauskunftung@telefonica.com`)  
**Command path:** `LF TR` (email target) → `run.py --arm-extern` → user Externer Transfer → Weiterleiten → `--await-arm`

---

## User report

User completed **Externer Transfer** and **Weiterleiten** quickly (possibly faster than expected). They asked to check monitoring intervals, suspected clicks were missed, and requested this report for the instructions agent.

---

## Verdict (evidence from `arm_watch.log`)

**Weiterleiten was NOT missed.** The detached Extern watch detected the click.

```
EXTERN_WEITERLEITEN_CLICK_DETECTED
tracker: @guidedWorkflow/runner/screenButton
button text: Weiterleiten
Waiting 4s before clicking next case...
```

**Failure is after the click:** auto-open of next case + extract.

```
CASE_ITEM_AUTO_CLICKED
aria-label: Fall Nr. 55411928 von Unbekannter Kunde
[PAGE STATE] Current page state: console
[INFO] RE extract-only does not open cases from console list.
[WARN] Extract after Extern failed — waiting for another Extern Weiterleiten click.
```

So the watch:

1. Caught **Weiterleiten** correctly.
2. Waited **4 seconds**.
3. Clicked the **first** `button[data-testid="collapsed-case-item"]`.
4. That item was **the same Fall `#55411928`** just transferred (label: Unbekannter Kunde) — **not** a new next case.
5. Page stayed / landed as **console** → extract-only **refused** to open from list.
6. Loop went back to **waiting for another Weiterleiten** — user already finished that UI → **stuck** until manual `--once` / DONE.

`--await-arm` therefore never saw `CUSTOMER EMAIL` / `AWAIT_ARM_EXTRACT_DONE` for a new case (user backgrounded await; later session may have been DONE-stopped).

---

## Monitoring intervals (current code)

Source: `.cursor/skills/sprinklr-email-automation/email_automation.py` + `.cursor/skills/sprinklr-read-answer-email/run.py`

| Stage | Interval / delay | Code |
|-------|------------------|------|
| Extern click poll | **0.5 s** | `_wait_for_extern_weiterleiten_click(poll_seconds=0.5)` |
| Re-inject listener if `__externReArmed` lost | same **0.5 s** tick | evaluate + re-arm in poll loop |
| Heartbeat “Still waiting for Extern Weiterleiten…” | every **5 s** | `last_heartbeat >= 5` |
| Post-Weiterleiten wait before case click | **4 s** | `_ANWENDEN_RE_WAIT_SECONDS = 4` / `monitor_extern_then_open_case_for_re(wait_seconds=4)` |
| After case-item click | `domcontentloaded` ≤10 s + **1.5 s** sleep | then `process_current_page_once(extract_only=True)` |
| `--await-arm` log poll | **1.0 s** | `run.py` `_await_arm(poll_s=1.0)` |
| Legacy send-wait visibility poll (other path) | **2 s** | `wait_for_email_sent` — **not** used by Extern arm |

Listener: capture-phase `mousedown` + `click` on exact label `/^Weiterleiten$/i` + `screenButton` tracker. Step 1 **Externer Transfer** is intentionally ignored.

**Fast-click note:** If the user clicks Weiterleiten **before** the detached watch finishes CDP connect + JS inject (~1–2 s after `ARM_WATCH_DETACHED`), that click can be lost. **This incident’s Weiterleiten was detected**, so “too fast for the listener” is **not** the root cause here. Possible secondary risk for future incidents.

---

## Root causes to fix (instructions agent)

1. **Wrong collapsed-case-item selection**  
   `_click_first_collapsed_case_item()` uses `.first` only. After Extern/Weiterleiten, the transferred case (`#55411928`) can still be the first sidebar item → script “opens” the closed case / stays on console.

2. **No Fall-ID / “next case” filter**  
   Should skip the Fall # that was just closed/transferred; prefer a **new** case item, or wait until a **different** `aria-label` / case ID appears.

3. **4 s may be too short for console + new case to settle**  
   Combined with (1), short wait clicks a stale item before the queue refreshes.

4. **Extract-only hard-stop on console**  
   Message: `RE extract-only does not open cases from console list` → after bad click, no recovery open; only “wait for another Weiterleiten” which the user cannot repeat.

5. **Recovery UX**  
   After failed extract, watch should not only re-arm Weiterleiten; should allow / document **`--once`** when the next case is already open, or retry case-item click with a longer settle / different selector.

6. **Log ordering**  
   `CASE_ITEM_AUTO_CLICKED` print lacks `flush=True`; logger lines can appear before the print in `arm_watch.log`, confusing chronology.

---

## Suggested fixes (for instructions / code chat)

- After Extern Weiterleiten: remember **closed Fall #**; click first `collapsed-case-item` whose aria-label **does not** contain that Fall #.
- Optionally increase post-click settle (e.g. 4 → 6–8 s) or poll until a **new** case item appears (timeout → warn + `--once` hint).
- If still on console after click: retry click / wait / fail with clear `ERROR: NEXT CASE NOT OPEN — run --once`.
- On extract failure: print recovery line and optionally stop waiting for a second Weiterleiten.
- Flush all arm progress prints; align `--await-arm` heartbeats with `CLICK_DETECTED` / `EXTRACT failed` lines.

---

## Timeline (this session)

| Local time | Event |
|------------|--------|
| ~19:49:43 | Detached `--watch-extern-re` started (`ARM_WATCH_DETACHED` pid≈53424) |
| 19:49:45 | `EXTERN_RE_ARMED` — waiting for Weiterleiten |
| 19:49:45–19:50:00 | Heartbeats every 5 s — still waiting |
| ~19:50:05 | `EXTERN_WEITERLEITEN_CLICK_DETECTED` (Weiterleiten) |
| +4 s | Auto-click collapsed-case-item → **Fall #55411928** (same case) |
| 19:50:11 | Console state; extract failed; re-wait Weiterleiten |
| after | User: clicks already done; await backgrounded; later asked for this report |

---

## Operator recovery (email chat)

If next case is already open in Sprinklr:

```powershell
Set-Location "c:\Users\PC ENTER\Desktop\Citrix"
uv run python .cursor/skills/sprinklr-read-answer-email/run.py --once
```

Do **not** start a second `--arm-extern` while the stuck watch still waits, unless `done_for_today` / kill cleared it.

---

## Related files

- `.cursor/skills/sprinklr-email-automation/email_automation.py` — `_wait_for_extern_weiterleiten_click`, `monitor_extern_then_open_case_for_re`, `_click_first_collapsed_case_item`
- `.cursor/skills/sprinklr-read-answer-email/run.py` — detached arm + `--await-arm`
- `.cursor/state/arm_watch.log` — evidence for this incident
- Rules: `lf-tr-transfer.mdc`, `re-read-email.mdc`, `anwenden-re-known-good.mdc`

---

**END OF REPORT**
