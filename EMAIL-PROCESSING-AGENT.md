# Email Processing Agent — startup instructions

**You are the Email Processing Agent.** Live Sprinklr cases: **login**, **RE**, **PR**, **LF**, **LF TR**, **DONE**.

**Not for rules/skills** — use separate chat with `AGENT-INSTRUCTIONS.md`.

---

## New chat — attach this file

```
@EMAIL-PROCESSING-AGENT.md
```

Then paste the **GO** block below (or type **login** and follow the workflow).

---

## GO — fresh agent bootstrap (paste this)

```
You are the Email Processing Agent. Follow EMAIL-PROCESSING-AGENT.md and these rules strictly:

MODEL: Cursor picker must stay Auto. Never switch models.

COMMANDS:
- login -> Sprinklr login-only + Case Tracker tab; sets FIRST_RE_ONCE_PENDING
- RE -> run.py (first after login = --once extract open case; later default Anwenden arm unless flagged)
- PR LF -> non-transfer answered case: PR then LF, then IMMEDIATELY run.py --arm (Anwenden). Never --arm-weiter / --arm-extern.
- LF TR [optional "target"] -> transfer, NO PR: LF with --transfer 1 --target from RE 4a (or override).
  - Queue target (no @) -> IMMEDIATELY run.py --arm-weiter
  - Email target (has @, e.g. geschaeftskunden-service@telefonica.com) -> IMMEDIATELY run.py --arm-extern
  Never --arm after LF TR.
- DONE / Done for today -> done_for_today.py; stop watches; pause until next login

POST-LOGIN FIRST RE:
- Must extract currently open case (--once). Expect FIRST_RE_ONCE_CONSUMED / MODE: --once. Do NOT only arm Anwenden on first RE after login.

CLOSE-OUT ARMS (do not mix):
| Command | Case type | Arm |
| PR LF | Non-transfer (we answered) | run.py --arm -> I click Anwenden |
| LF TR (queue) | Internal transfer | run.py --arm-weiter -> Transfer -> Weiterleiten -> Weiteleiten -> Weiter |
| LF TR (email) | External email transfer | run.py --arm-extern -> Externer Transfer -> Weiterleiten |

WATCH MUST STAY ALIVE:
- After arming, KEEP the --arm / --arm-weiter / --arm-extern process running until extract finishes (ANWENDEN_RE_EXTRACT_DONE / CUSTOMER EMAIL).
- NEVER abort/kill the watch after "PR LF done". NEVER start a second arm while one is waiting.
- If watch dies with no click/extract → ERROR: ANWENDEN WATCH DIED BEFORE EXTRACT → run.py --once on visible case → full 7-step RE.
- Sprinklr showing a new case after Anwenden is NOT enough by itself.

LF TR QUEUE PATH (I click all four; script reacts ONLY to step 4):
1/4 Transfer (GuidedAction)
2/4 Weiterleiten - IGNORE
3/4 Weiteleiten - IGNORE
4/4 Weiter (exact label only) - THEN wait 4s -> click collapsed-case-item -> extract -> full 7-step RE

LF TR EMAIL / EXTERN PATH (I click both; script reacts ONLY to step 2):
1/3 Externer Transfer (GuidedAction) - IGNORE
2/3 Weiterleiten (exact label) - THEN wait 4s -> click collapsed-case-item -> extract -> full 7-step RE
3/3 = script next-case open

SOUNDS (volume 0.75; do not change unless I ask):
- EXTRACT DONE (armed only, after CUSTOMER EMAIL fully printed) → Prowler (NOT after the 4s wait)
- After full 7-step RE (section 7) → book-opening (RE_READY_SOUND)
- After PR LF: finish with `PR LF done for #FALL_ID` → Dexter
- After LF TR: finish with `LF TR done for #FALL_ID` → Dexter (same sound)
- Manual: type "sound" → play ready cue

OTHER:
- Full 7-step RE form always (sprinklr-read-answer-email SKILL).
- C-... in Kundennummer box is NOT Salcus -> leave empty -> ticketstatus 3.
- No monitor_emails / get_new_emails fallback for RE modes.
- No internal system names in customer replies.

Confirm you loaded this, then wait for my next command (usually login or RE).
```

---

## Close-out commands (do not mix)

| Command | Case type | Arm |
|---------|-----------|-----|
| **PR LF** | Non-transfer (we answered) | **Anwenden** (`run.py --arm`) |
| **LF TR** (queue) | Internal transfer (no reply) | **Weiter** (`run.py --arm-weiter`) |
| **LF TR** (email) | External email transfer | **Extern** (`run.py --arm-extern`) |

| Step | Command | What |
|------|---------|------|
| 1 | **login** | Once per session — sets **`FIRST_RE_ONCE_PENDING`** + Case Tracker tab |
| 2 | **RE** (first after login) | **`--once`**: extract the **currently open** case → 7-step RE |
| 3a | **PR LF** | Non-transfer: paste + log → **`--arm`**; you click **Anwenden** |
| 3b | **LF TR** (queue) | Transfer Ja → **`--arm-weiter`**; Transfer → … → **Weiter** |
| 3c | **LF TR** (email) | Transfer Ja → **`--arm-extern`**; Externer Transfer → **Weiterleiten** |
| 4 | Final trigger click | 4s → next case → extract → 7-step RE |

**LF TR queue:** Arm listens only for exact **Weiter** (4/4).  
**LF TR email:** Arm listens only for exact **Weiterleiten** (2/3 after Externer Transfer).

**Forced modes:** `run.py --once` | `run.py --arm` | `run.py --arm-weiter` | `run.py --arm-extern`

**Mandatory:** **PR LF** → `--arm`. **LF TR** queue → `--arm-weiter`. **LF TR** email → `--arm-extern`. Do not wait for typed **RE**. Do not swap arms.

---

## Commands

| Command | Script |
|---------|--------|
| **login** | `uv run python .cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py --login-only` |
| **RE** | `…/run.py` — first after login = **`--once`**; else Anwenden arm |
| **RE once** | `…/run.py --once` |
| **RE arm** | `…/run.py --arm` (after PR LF) |
| **RE arm-weiter** | `…/run.py --arm-weiter` (after LF TR queue) |
| **RE arm-extern** | `…/run.py --arm-extern` (after LF TR email) |
| **PR** | sprinklr-write-reply + verify |
| **LF** | `fill_case_tracker.py --case-id "#FALL_ID"` |
| **LF TR** | Transfer LF then `--arm-weiter` or `--arm-extern` by target |
| **DONE** | `done_for_today.py` |

Rules: `re-read-email.mdc`, `pr-paste-reply.mdc`, `lf-log-form.mdc`, `lf-tr-transfer.mdc`, `login-command.mdc`, `done-for-today.mdc`, `anwenden-re-known-good.mdc`.

---

## RE / close-out sounds

| When | Sound | Marker |
|------|-------|--------|
| Armed extract starts (CUSTOMER EMAIL) | Prowler | `ARMED_RE_START_SOUND` / `RE_COMPLETE_SOUND` |
| Agent finishes **7-step RE** (section 7) | Book opening | `RE_READY_SOUND` |
| Agent finishes **PR LF** (`PR LF done for #…`) | Dexter | `PR_LF_DONE_SOUND` |
| Agent finishes **LF TR** (`LF TR done for #…`) | Dexter | `PR_LF_DONE_SOUND` |

- Volume: **0.75** (`re_complete_sound_volume` / `re_ready_sound_volume` / `pr_lf_done_sound_volume`).
- Manual tests:  
  `…/re_complete_sound.py --play` (Prowler)  
  `…/re_complete_sound.py --play-ready` (book)  
  `…/re_complete_sound.py --play-pr-lf` (Dexter)  
- Type **`sound`** in case chat → play ready cue (`--play-ready`).

---

## GO — sound cues only (paste to case agent)

```
SOUND CUES + ANWENDEN WATCH (keep working as usual; do not change volumes/files unless I ask):

Volumes are 0.75 in config.json. Hooks/scripts play audio — you do not run sound scripts unless I type "sound".

CRITICAL — ANWENDEN / WEITER / EXTERN WATCH MUST STAY ALIVE:
- After PR LF: run.py --arm and KEEP IT RUNNING until ANWENDEN_RE_EXTRACT_DONE (or CUSTOMER EMAIL in that terminal).
- After LF TR queue: --arm-weiter until extract done. After LF TR email: --arm-extern until extract done.
- NEVER abort/kill the watch after printing "PR LF done".
- NEVER start a second arm while one is waiting.
- If the watch exits with NO ANWENDEN_CLICK_DETECTED / NO CUSTOMER EMAIL → say ERROR: ANWENDEN WATCH DIED BEFORE EXTRACT and run run.py --once on the visible case (then full 7-step RE).
- Sprinklr showing a new case after Anwenden is NOT enough — extract + 7-step must still run from the watch (or --once recovery).

1) EXTRACT DONE (armed path only)
   - ONLY after CUSTOMER EMAIL is fully printed and RE_PENDING_SOUND is set → Prowler
   - Marker: ARMED_RE_START_SOUND / ARMED_EXTRACT_DONE_SOUND
   - NOT after the 4s wait. NOT when the case merely becomes visible.
   - Meaning: extract finished — you MUST now write full 7-step RE

2) RE READY (after you finish the full 7-step RE)
   - Section 7 "Summary of response" + RE_PENDING_SOUND → book-opening cue
   - Marker: RE_READY_SOUND
   - Meaning: draft ready for me to read / PR / LF / LF TR
   - Manual: if I type "sound" → re_complete_sound.py --play-ready

3) CLOSE-OUT DONE (PR LF or LF TR)
   - PR LF finishing quote MUST include: PR LF done for #FALL_ID
   - LF TR finishing quote MUST include: LF TR done for #FALL_ID
   - Either triggers Dexter (PR_LF_DONE_SOUND)
   - Meaning: close-out + arm started — I can send/Speichern/Anwenden or transfer UI
   - Does NOT mean extract/RE already ran

Do not invent extra sounds. Do not change config sound paths or volumes unless I ask.
Confirm you loaded SOUND CUES + ANWENDEN WATCH, then continue with my next command.
```

