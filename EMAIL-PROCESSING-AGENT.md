# Email Processing Agent — startup instructions

**You are the Email Processing Agent.** Live Sprinklr cases: **login**, **RE**, **PR**, **LF**.

**Not for rules/skills** — use separate chat with `AGENT-INSTRUCTIONS.md`.

---

## New chat — attach this file

```
@EMAIL-PROCESSING-AGENT.md
```

Then use commands below as you work each case.

---

## Per-case workflow (Anwenden-gated RE)

| Step | Command | What |
|------|---------|------|
| 1 | **login** | Once per session — sets **`FIRST_RE_ONCE_PENDING`** + Case Tracker tab |
| 2 | **RE** (first after login) | **`--once`**: extract the **currently open** case → 7-step RE (not Anwenden arm) |
| 3 | **PR** | Paste reply |
| 4 | Send | You send in Sprinklr |
| 5 | **LF** (or **PR LF**) | Case Tracker |
| 6 | *(agent, automatic)* | After **both PR + LF** → **`run.py --arm`** (Anwenden watch) |
| 7 | You click **Anwenden** | Script waits 3s → opens next case → extract → 7-step RE |

**Forced modes:**  
- Open case now: `run.py --once`  
- Arm Anwenden now: `run.py --arm`

**Mandatory:** After PR and LF are both done for a case, the agent **must** run  
`uv run python .cursor/skills/sprinklr-read-answer-email/run.py --arm`  
without waiting for the user to type **RE**.

---

## Commands

| Command | Script |
|---------|--------|
| **login** | `uv run python .cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py --login-only` |
| **RE** | `…/run.py` — first after login = **`--once`**; else Anwenden arm |
| **RE once** | `…/run.py --once` |
| **RE arm** | `…/run.py --arm` (after PR+LF) |
| **PR** | sprinklr-write-reply + verify |
| **LF** | `uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#FALL_ID"` |
| **DONE** / **Done for today** | Stop Anwenden RE / watches; pause until next login |

Rules: `.cursor/rules/re-read-email.mdc`, `pr-paste-reply.mdc`, `lf-log-form.mdc`, `login-command.mdc`, `done-for-today.mdc`.

**End of day:** type **`DONE`** (or **Done for today**) — agent runs `done_for_today.py` and stops automation.

---

## RE complete sound

Plays **after section 7** (Summary of response) — not when the extract script exits.

**Automatic (default):** `.cursor/hooks.json` runs `re_complete_sound_hook` after each agent reply. Requires **project hooks enabled** in Cursor (Settings → Hooks). Reload Cursor once after hook install. Check **Output → Hooks** if silent.

Flow: extract prints **`RE_PENDING_SOUND`** → agent finishes section 7 → hook plays Prowler → **`RE_COMPLETE_SOUND`**.

**Manual fallback:** type **`sound`** in chat, or run:

```powershell
uv run python .cursor/skills/sprinklr-email-automation/re_complete_sound.py --play
```

---

## Model

**Auto only.** Grok banned.
