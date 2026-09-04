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
| 1 | **login** | Once per session — Sprinklr + Case Tracker tab |
| 2 | **RE** (first case / manual) | Arms Anwenden watch → you click Anwenden → next case extract → 7-step RE |
| 3 | **PR** | Paste reply |
| 4 | Send | You send in Sprinklr |
| 5 | **LF** (or **PR LF**) | Case Tracker |
| 6 | *(agent, automatic)* | After **both PR + LF** succeed → **auto-arm** Anwenden RE again (no need to type RE) |
| 7 | You click **Anwenden** | Script waits 3s → opens next case → extract → 7-step RE |

**Manual extract** (case already open):  
`uv run python .cursor/skills/sprinklr-read-answer-email/run.py --once`

**Mandatory:** After PR and LF are both done for a case, the agent **must** start  
`uv run python .cursor/skills/sprinklr-read-answer-email/run.py`  
without waiting for the user to type **RE**.

---

## Commands

| Command | Script |
|---------|--------|
| **login** | `uv run python .cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py --login-only` |
| **RE** | `uv run python .cursor/skills/sprinklr-read-answer-email/run.py` (Anwenden-gated) |
| **RE once** | `…/run.py --once` (current open case only) |
| **PR** | sprinklr-write-reply + verify |
| **LF** | `uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#FALL_ID"` |

Rules: `.cursor/rules/re-read-email.mdc`, `pr-paste-reply.mdc`, `lf-log-form.mdc`, `login-command.mdc`.

**Rollback:** in instructions chat type **`revert last`** → restores pre-Anwenden-RE checkpoint.

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
