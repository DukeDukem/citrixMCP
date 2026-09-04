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

## Close-out commands (do not mix)

| Command | Case type | Arm |
|---------|-----------|-----|
| **PR LF** | Non-transfer (we answered) | **Anwenden** (`run.py --arm`) |
| **LF TR** | Transfer (no customer reply) | **Weiter** (`run.py --arm-weiter`) |

| Step | Command | What |
|------|---------|------|
| 1 | **login** | Once per session — sets **`FIRST_RE_ONCE_PENDING`** + Case Tracker tab |
| 2 | **RE** (first after login) | **`--once`**: extract the **currently open** case → 7-step RE (not Anwenden arm) |
| 3a | **PR LF** | Non-transfer: paste + log → **`--arm`** (Anwenden) |
| 3b | **LF TR** | Transfer: log Transfer Ja, no PR → **`--arm-weiter`** (Weiter) |
| 4 | You click Anwenden / Weiter | 3s → next case → extract → 7-step RE |

**Forced modes:**  
- Open case now: `run.py --once`  
- Arm Anwenden (after **PR LF**): `run.py --arm`  
- Arm Weiter (after **LF TR**): `run.py --arm-weiter`

**Mandatory:** **PR LF** → `--arm`. **LF TR** → `--arm-weiter`. Do not wait for typed **RE**. Do not swap the two arms.

---

## Commands

| Command | Script |
|---------|--------|
| **login** | `uv run python .cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py --login-only` |
| **RE** | `…/run.py` — first after login = **`--once`**; else Anwenden arm |
| **RE once** | `…/run.py --once` |
| **RE arm** | `…/run.py --arm` (after PR+LF) |
| **RE arm-weiter** | `…/run.py --arm-weiter` (after LF TR) |
| **PR** | sprinklr-write-reply + verify |
| **LF** | `uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#FALL_ID"` |
| **LF TR** | Transfer LF (`--transfer 1 --target …`) then `--arm-weiter` |
| **DONE** / **Done for today** | Stop Anwenden/Weiter RE / watches; pause until next login |

Rules: `.cursor/rules/re-read-email.mdc`, `pr-paste-reply.mdc`, `lf-log-form.mdc`, `lf-tr-transfer.mdc`, `login-command.mdc`, `done-for-today.mdc`.

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
