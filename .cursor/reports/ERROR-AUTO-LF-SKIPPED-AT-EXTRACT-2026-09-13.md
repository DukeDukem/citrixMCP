# ERROR REPORT — Auto-LF skipped at extract (Turn A never ran)

**For:** Instructions / rules agent (`AGENT-INSTRUCTIONS.md`)  
**From:** Email Processing Agent chat (`EMAIL-PROCESSING-AGENT.md` GO session)  
**Date:** 2026-09-13 (local)  
**Operator impact:** Case Tracker not filled until manual correction; delayed Speichern; wrong channel LF on one case; operator had to type LF / complain multiple times.

---

## User report

Operator reported repeatedly that **Auto-LF did not file** — initially upon extract, not “after 7-step”. Session showed a consistent pattern: extract succeeded, 7-step appeared in chat, but `fill_case_tracker.py` + closeout arm were **not** chained in Turn A.

---

## Verdict

**Auto-LF at extract (Turn A) was systematically skipped by the agent.** This is an **agent workflow violation**, not a script failure. `fill_case_tracker.py` runs correctly when invoked (verified on manual runs).

---

## Expected workflow (authoritative)

Per `.cursor/rules/lf-log-form.mdc`, `.cursor/rules/re-no-background-tasks-ui.mdc`, `.cursor/rules/re-read-email.mdc`, and `EMAIL-PROCESSING-AGENT.md` (Turn A table):

| Turn | Agent action | Tools |
|------|--------------|-------|
| **A** | Extract → **immediate** best-guess Auto-LF → **immediate** `--closeout-*` | `run.py`, `fill_case_tracker.py`, `run.py --closeout-*` — **no operator-facing chat** |
| **B** | Full 7-step RE (sections 1–7) | **ZERO tools** |
| **C** | None — arm already running from Turn A | — |

Turn B must end with:  
`Auto-LF filed at extract — best-guess: Transfer [Nein/Ja to X]. Reiterate if needed.`

**Hard rule:** Auto-LF runs **at extract time**, **before** the 7-step chat message — not as text promising “Auto-LF filing now”.

---

## What the agent did instead (this session)

| Fall # | Extract source | Turn A (LF + arm) | What happened |
|--------|----------------|-------------------|---------------|
| **#57677586** | Typed **RE** / `run.py --once` | **Skipped** | 7-step only; operator requested **LF TR** → `CS_XF_E_DSL_TECHNIK` manually |
| **#57728816** | Anwenden / `--await-arm` notify | **Skipped** | 7-step only; operator: “you didnt paste LF” → manual LF Transfer Nein + `--closeout-anwenden` |
| **#57732470** | Anwenden notify (misclassified **CALL**) | **Wrong path** | Voice LF + `--closeout-next`; operator: “this is an email LF” → kill Next arm, re-LF em_care |
| **#57732503** | Anwenden notify | **Skipped** | 7-step + “Auto-LF filing now” text; LF only on later notification follow-up |
| **#57734062** | Anwenden notify | **Skipped** | 7-step + “Auto-LF filing now” text; operator complained; manual LF at 11:54 (Salcus 64223303, status 1) |

---

## Root causes

### 1. `RE_TEXT_ONLY_GATE` misread (primary)

Extract stdout ends with:

```
RE_TEXT_ONLY_GATE — agent: STOP tools; next message = 7-step sections 1–7 only
```

Agent interpreted this as **“no tools until after 7-step is visible”** — including **no Turn A LF**.

**Correct reading:** Gate applies to the **Turn B chat message** (7-step must not be hidden in tool output). Turn A LF + arm must still run **in the same agent turn as extract** (or immediately when processing `DETACHED_ARM_EXTRACT_READY`), **before** Turn B text.

### 2. Conflicting doc lines in GO bootstrap

`EMAIL-PROCESSING-AGENT.md` GO block contains both:

- Turn A: extract + LF + arm (correct)
- “ORDER LOCK: 7-step visible first; then agent Auto-LF” + reference to missing `re-before-auto-lf.mdc` (incorrect / stale relative to lf-log-form)

Agent followed the **wrong** line and deferred LF to after 7-step — then often **never ran it at all**.

### 3. Notification / background-shell handler = Turn B only

When `--await-arm` or `--closeout-*` printed `DETACHED_ARM_EXTRACT_READY` + `RE_TEXT_ONLY_GATE`, the agent’s “follow-up to task finished” response was **only** the 7-step paste. **No** `fill_case_tracker.py` in that workflow branch.

### 4. Placeholder text substituted for execution

Agent repeatedly ended Turn B with *“Auto-LF filing now”* instead of executing Turn A. Operator correctly treated this as failure.

### 5. Secondary: channel misdetect (#57732470)

Script reported `CHANNEL: CALL` / `CALL_LF_GATE` (minimal email body in DOM). Agent ran Voice LF. Operator override to EMAIL required manual kill of Next arm + re-LF. Separate issue from LF skip but compounded operator pain.

---

## Evidence (manual LF succeeded when finally run)

**#57734062** — `fill_case_tracker.py --case-id "#57734062" --transfer 0`:

```
[CASE TRACKER] Salcus from Sprinklr Kundennummer field: 64223303
[CASE TRACKER] Case # (sikas): 57734062
[CASE TRACKER] Ticketstatus Salcus: 1-Erfolgreich
[CASE TRACKER] Kanal: em_care
[CASE TRACKER] Transfer: Nein
LF_SPEICHERN_PENDING case=#57734062
```

Script works; agent did not invoke it at extract.

---

## Recommended fixes (instructions agent)

### Rules / docs

1. **Resolve GO vs lf-log-form conflict** — single source: **LF at extract Turn A**, always. Remove or fix “7-step visible first; then Auto-LF” and dead link to `re-before-auto-lf.mdc`.
2. **Clarify `RE_TEXT_ONLY_GATE` in `run.py` stdout** — e.g.  
   `Turn A: run fill_case_tracker + closeout NOW (this turn). Turn B next message: 7-step text only, zero tools.`
3. **Ban placeholder** — agent must not write “Auto-LF filing now” unless `fill_case_tracker.py` already succeeded in the **same case’s Turn A** (or prior turn for that Fall #).
4. **Notification handler rule** — on `DETACHED_ARM_EXTRACT_READY` / `[AUTO_PIPELINE]`: mandatory tool batch = LF + closeout **before** 7-step chat (or LF as first tools in same turn if 7-step follows immediately after).

### Agent behavior (email processing chat)

5. **Extract turn checklist (hard):**  
   After any extract stdout with Fall # → `fill_case_tracker.py` → `--closeout-*` → **then** 7-step in following message.
6. **Never treat typed RE recovery as exempt** — first case **RE** still needs Turn A LF at extract.
7. **Reiterate LF** only when 7-step §3 differs from best-guess — not as substitute for initial Turn A.

### Optional script hardening

8. Emit explicit marker after extract: `AUTO_LF_REQUIRED case=#FALL_ID` so hooks or agent rules can grep for missing LF before 7-step.
9. Consider writing `extract_lf_pending.json` with Fall # until LF script confirms fill (agent-side gate).

---

## Operator recovery commands used this session

- Manual **LF TR** with target override  
- Manual **fill_case_tracker.py** after complaint  
- Kill detached Next arm + re-LF em_care for misclassified CALL  
- **PR** blocked once on stale `latest_re_reply.json` case mismatch (#57728816 vs #57647158) — fixed by updating lock file

---

## Severity

**High** — Case Tracker gaps, wrong Kanal on one case, extra operator input, trust loss. Data-leak rules were not violated; LF Salcus rules were followed when LF finally ran.

---

## Files to update

| File | Action |
|------|--------|
| `EMAIL-PROCESSING-AGENT.md` | Align GO block with Turn A-at-extract; remove conflicting ORDER LOCK line |
| `.cursor/rules/re-read-email.mdc` | Add explicit anti-pattern: “7-step without prior LF for same Fall # = failure” |
| `.cursor/rules/re-no-background-tasks-ui.mdc` | Add notification-path Turn A requirement |
| `.cursor/skills/sprinklr-read-answer-email/run.py` | Reword `RE_TEXT_ONLY_GATE` banner (Turn A vs Turn B) |
| Create `.cursor/rules/re-before-auto-lf.mdc` **or** remove all references | Eliminate dead rule reference |

---

**Report status:** Fixed 2026-09-13 — Turn A Aut-LF enforced in `run.py` gate + `auto_lf_at_extract.py` spawn on EMAIL extract; hook/GO/rules aligned.
