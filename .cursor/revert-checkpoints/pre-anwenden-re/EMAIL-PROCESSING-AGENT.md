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

## Manual per-case workflow

| Step | Command | What |
|------|---------|------|
| 1 | **login** | Once per session — Sprinklr + Case Tracker tab |
| 2 | Open case in Sprinklr | You switch cases manually |
| 3 | **RE** | Extract email → 7-step analysis in chat |
| 3b | *(agent)* | After **section 7** → Prowler audio cue |
| 4 | **PR** | Paste reply |
| 5 | Send | You send in Sprinklr |
| 6 | **LF** | Case Tracker (or **PR LF** if paste not done yet) |
| 7 | Repeat | Next case → **RE** again |

No background watch. **Type RE for each case.**

---

## Commands

| Command | Script |
|---------|--------|
| **login** | `uv run python .cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py --login-only` |
| **RE** | `uv run python .cursor/skills/sprinklr-read-answer-email/run.py` |
| **PR** | sprinklr-write-reply + verify |
| **LF** | `uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#FALL_ID"` |

Rules: `.cursor/rules/re-read-email.mdc`, `pr-paste-reply.mdc`, `lf-log-form.mdc`, `login-command.mdc`.

---

## RE complete sound

Plays **after section 7** (Summary of response) — not when the extract script exits.

**Automatic (default):** `.cursor/hooks.json` runs `re_complete_sound_hook` after each agent reply. Requires **project hooks enabled** in Cursor (Settings → Hooks). Reload Cursor once after hook install. Check **Output → Hooks** if silent.

Flow: **RE** extract prints **`RE_PENDING_SOUND`** → agent finishes section 7 → hook plays Prowler → **`RE_COMPLETE_SOUND`** in Hooks output.

**Manual fallback:** type **`sound`** in chat, or run:

```powershell
uv run python .cursor/skills/sprinklr-email-automation/re_complete_sound.py --play
```

---

## Model

**Auto only.** Grok banned.
