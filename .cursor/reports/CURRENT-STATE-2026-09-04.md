# CURRENT STATE — Email RE / arm workflow (2026-09-04)

Canonical baseline for instructions + fresh case agents.

## Model

Cursor picker: **Pro Plus** — email chat **Claude 4.6 Sonnet**; instructions **Composer 2.5** (pace-based). Grok banned. On-demand **Disabled**.

## Two chats

| Chat | Doc |
|------|-----|
| Instructions | `AGENT-INSTRUCTIONS.md` — rules only; no RE/PR/LF |
| Cases | `EMAIL-PROCESSING-AGENT.md` — paste **GO** block |

## Commands

| User | Script behavior |
|------|-----------------|
| **login** | Login + Case Tracker; `FIRST_RE_ONCE_PENDING` marker |
| **RE** | Always `--once` extract open case |
| **PR LF** / **LF** | Tracker → `--arm` → Dexter + READY_FOR_YOUR_CLICK → `--await-arm` → Anwenden |
| **LF TR** queue | `--arm-weiter` → … → exact **Weiter** |
| **LF TR** email | `--arm-extern` → … → exact **Weiterleiten** |
| **DONE** | Kill detached watches; clear arm state |

## Sounds

| Cue | When | How |
|-----|------|-----|
| Dexter | Arm succeeds (click-ready) | `run.py --arm*` plays |
| Prowler | Armed extract CUSTOMER EMAIL done | automation |
| Book | After section 7 | Agent runs `re_complete_sound.py --play-ready` |

## Next-case open

Remember closed Fall # → skip that sidebar item → poll ~25s → retry → else `ERROR: NEXT CASE NOT OPEN — run.py --once` and stop arm.

## Key files

- `run.py` — `--once` default, detach, `--await-arm`
- `email_automation.py` — Anwenden/Weiter/Extern watches + next-case skip
- Rules: `re-read-email.mdc`, `anwenden-re-known-good.mdc`, `lf-log-form.mdc`, `lf-tr-transfer.mdc`
- Reports: `ERROR-EXTERN-ARM-MISS-2026-09-04.md`, `FIX-EXTERN-ARM-NEXT-CASE-2026-09-04.md`
