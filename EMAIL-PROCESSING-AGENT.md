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
- RE -> run.py = ALWAYS --once (extract currently open case). First case of the day / fresh agent = typed RE push-start. NEVER arm Anwenden on typed RE.
- PR LF -> non-transfer: PR then LF, then IMMEDIATELY run.py --arm (expect ARM_WATCH_DETACHED), finishing quote, then run.py --await-arm. Never --arm-weiter / --arm-extern.
- LF alone -> log form, then IMMEDIATELY --arm (detached) + finishing quote + --await-arm. Same as PR LF for next-case arm.
- LF TR [optional "target"] -> transfer, NO PR: LF with --transfer 1 --target from RE 4a (or override).
  - Queue target (no @) -> IMMEDIATELY --arm-weiter (detached) + --await-arm
  - Email target (has @, e.g. geschaeftskunden-service@telefonica.com) -> IMMEDIATELY --arm-extern (detached) + --await-arm
  Never --arm after LF TR.
- DONE / Done for today -> done_for_today.py; stop watches (including detached); pause until next login

POST-LOGIN / FIRST CASE (push-start):
- login once, open first case, type RE.
- RE must extract currently open case (--once). Expect MODE: --once + CUSTOMER EMAIL + full 7-step.
- Do NOT arm Anwenden and wait for Anwenden click on the first RE (or any typed RE).
- After that close-out, automation takes over via --arm* + --await-arm.

CLOSE-OUT ARMS (do not mix):
| Command | Case type | Arm then await |
| PR LF / LF (EMAIL) | Non-transfer email answered/logged | --arm (Anwenden) -> --await-arm -> I click Anwenden |
| LF (CALL) | Voice call logged | --channel voice LF, then --arm-next -> --await-arm -> I click exact Next |
| LF alone (EMAIL) | Logged without PR | --arm -> --await-arm -> Anwenden |
| LF TR (queue) | Internal transfer | --arm-weiter -> --await-arm -> Transfer -> ... -> Weiter |
| LF TR (email) | External email transfer | --arm-extern -> --await-arm -> Externer Transfer -> Weiterleiten |

CALL LF ARM (disposition Next — not Anwenden):
- After CALL LF (--channel voice): IMMEDIATELY run.py --arm-next (NOT --arm).
- Expect NEXT_RE_ARMED + ARM_WATCH_DETACHED + READY_FOR_YOUR_CLICK: Next + Dexter.
- Finishing quote: LF done for #FALL_ID
- Then --await-arm. I left-click exact label Next on screenButton (ignore Back/Weiter/Weiterleiten).
- After extract: CHANNEL detect again.

DETACHED ARM (mandatory — fixes false "watch died"):
- After LF / PR LF: run.py --arm → expect ARM_WATCH_DETACHED + READY_FOR_YOUR_CLICK: Anwenden + Dexter → say "Armed — click Anwenden now" + finishing quote → THEN run.py --await-arm.
- After LF TR: --arm-weiter or --arm-extern → READY_FOR_YOUR_CLICK + Dexter → finishing quote → --await-arm.
- Dexter / READY_FOR_YOUR_CLICK = safe to click NOW. Do NOT wait for await to finish before clicking. Await only waits for extract after your click.
- No console window should pop on arm (CREATE_NO_WINDOW).
- If --await-arm is aborted, re-run --await-arm. Only use --once if ARM_WATCH_LOG has no CUSTOMER EMAIL.
- NEVER start a second --arm while one detached watch is still waiting.

CHANNEL DETECT (after every case open — RE --once OR after await-arm extract):
- Look at visible Sprinklr overlay/timeline → print CHANNEL: CALL or CHANNEL: EMAIL (or UNKNOWN).
- EMAIL → full 7-step RE as usual → PR/LF/LF TR.
- CALL → do NOT run email RE/PR. Say you are waiting for my voice brief while the customer talks. When I paste/forward their issue as text, analyze + handle (talk track / transfer / steps). LF call with --channel voice (Ticketstatus always 3). Then arm next case; classify again.

CALL WAIT LINE (use when CHANNEL: CALL):
CHANNEL: CALL
Fall #…. Waiting for your voice brief.
I am listening — when the customer has explained their issue, paste/forward their case as text here. I will then analyze and handle it.

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
- After --arm / --arm-weiter / --arm-extern succeeds → Dexter (script plays; means click now)
- After full 7-step RE (section 7) → MUST run: re_complete_sound.py --play-ready (book). Do not rely on hooks alone.
- EXTRACT DONE (armed only, after CUSTOMER EMAIL) → Prowler
- Finishing quotes still required: PR LF done / LF done / LF TR done for #FALL_ID
- Manual: type "sound" → play ready cue

OTHER:
- Full 7-step RE form for EMAIL cases (sprinklr-read-answer-email SKILL).
- CALL cases: wait for voice brief → handle pack (no PR unless I ask). LF: --channel voice, ticketstatus 3.
- C-... in Kundennummer box is NOT Salcus -> leave empty -> ticketstatus 3.
- No monitor_emails / get_new_emails fallback for RE modes.
- No internal system names in customer replies.
- Rule: sprinklr-call-vs-email.mdc

Confirm you loaded this, then wait for my next command (usually login or RE).
```

---

## Close-out commands (do not mix)

| Command | Case type | Arm | Then |
|---------|-----------|-----|------|
| **PR LF** / **LF alone** | Non-transfer (we answered / logged) | **Anwenden** (`run.py --arm` detached) | **`run.py --await-arm`** |
| **LF TR** (queue) | Internal transfer (no reply) | **Weiter** (`run.py --arm-weiter` detached) | **`run.py --await-arm`** |
| **LF TR** (email) | External email transfer | **Extern** (`run.py --arm-extern` detached) | **`run.py --await-arm`** |

| Step | Command | What |
|------|---------|------|
| 1 | **login** | Once per session — sets **`FIRST_RE_ONCE_PENDING`** + Case Tracker tab |
| 2 | **RE** (typed / first case) | **Always `--once`**: extract the **currently open** case → 7-step RE. Never arm Anwenden on typed RE. |
| 3a | **PR LF** / **LF alone** | Non-transfer: paste (if PR) + log → **`--arm`** + **`--await-arm`**; you click **Anwenden** |
| 3b | **LF TR** (queue) | Transfer Ja → **`--arm-weiter`** + **`--await-arm`**; Transfer → … → **Weiter** |
| 3c | **LF TR** (email) | Transfer Ja → **`--arm-extern`** + **`--await-arm`**; Externer Transfer → **Weiterleiten** |
| 4 | Final trigger click | 4s → next case → extract → 7-step RE |

**LF TR queue:** Arm listens only for exact **Weiter** (4/4).  
**LF TR email:** Arm listens only for exact **Weiterleiten** (2/3 after Externer Transfer).

**Forced modes:** `run.py --once` | `run.py --arm` | `run.py --arm-weiter` | `run.py --arm-extern` | `run.py --await-arm`

**Mandatory:** After arm → finishing quote → **`--await-arm`**. Do not wait for typed **RE**. Do not swap arms. Do not stack a second arm while one detached watch is waiting.

---

## Commands

| Command | Script |
|---------|--------|
| **login** | `uv run python .cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py --login-only` |
| **RE** | `…/run.py` — **always `--once`** (extract open case; push-start / re-read) |
| **RE once** | `…/run.py --once` |
| **RE arm** | `…/run.py --arm` then **`--await-arm`** (after LF / PR LF) |
| **RE arm-weiter** | `…/run.py --arm-weiter` then **`--await-arm`** (after LF TR queue) |
| **RE arm-extern** | `…/run.py --arm-extern` then **`--await-arm`** (after LF TR email) |
| **Await arm** | `…/run.py --await-arm` (poll detached log until extract) |
| **PR** | sprinklr-write-reply + verify |
| **LF** | `fill_case_tracker.py --case-id "#FALL_ID"` |
| **LF TR** | Transfer LF then `--arm-weiter` or `--arm-extern` + `--await-arm` |
| **DONE** | `done_for_today.py` |

Rules: `re-read-email.mdc`, `pr-paste-reply.mdc`, `lf-log-form.mdc`, `lf-tr-transfer.mdc`, `login-command.mdc`, `done-for-today.mdc`, `anwenden-re-known-good.mdc`, `sprinklr-call-vs-email.mdc`.

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
SOUND CUES + DETACHED ARM (keep working as usual; do not change volumes/files unless I ask):

Volumes are 0.75 in config.json.

CRITICAL — CLICK-READY vs AWAIT SPINNER:
- After LF / PR LF: run.py --arm → READY_FOR_YOUR_CLICK + Dexter (script plays) → say "Armed — click Anwenden now" + finishing quote → THEN --await-arm.
- Dexter / READY_FOR_YOUR_CLICK = I may click NOW. Await spinner is NOT "wait longer before clicking".
- After LF TR: --arm-weiter or --arm-extern → same (Dexter + READY_FOR_YOUR_CLICK) → --await-arm.
- No console window on arm. If --await-arm aborted, re-run it. Never second arm while one waits.

1) CLOSE-OUT / CLICK-READY
   - Played by --arm / --arm-weiter / --arm-extern script (Dexter)
   - Meaning: watch armed — click Anwenden / Weiter / Weiterleiten now

2) EXTRACT DONE (armed path only)
   - After CUSTOMER EMAIL fully printed → Prowler
   - Meaning: write full 7-step RE now

3) RE READY (after section 7)
   - YOU MUST run: uv run python .cursor/skills/sprinklr-email-automation/re_complete_sound.py --play-ready
   - Do not rely on hooks alone (Windows often sends empty stdin to hooks)
   - Manual: if I type "sound" → same --play-ready

Finishing quotes still required: PR LF done / LF done / LF TR done for #FALL_ID

Do not invent extra sounds. Do not change config sound paths or volumes unless I ask.
Confirm you loaded SOUND CUES + DETACHED ARM, then continue with my next command.
```

