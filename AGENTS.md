# AGENTS.md — Citrix Sprinklr workspace

## Two chats (mandatory split)

| Chat | Startup doc | Runs login / RE / PR / LF? |
|------|-------------|----------------------------|
| **Instructions dashboard** | `AGENT-INSTRUCTIONS.md` | **No** |
| **Email processing** | `EMAIL-PROCESSING-AGENT.md` | **Yes** |

## Model lock

- Cursor picker: **Auto only**. Grok banned.

## Case commands (email processing chat)

- **login** — Sprinklr + Case Tracker tab; sets first-RE **`--once`** gate
- **RE** — first after login = **`--once`**; later / after PR+LF = **`--arm`** Anwenden; then 7-step output
- **PR LF** — **non-transfer** answered case → after both succeed, **`run.py --arm`** (**Anwenden**)
- **LF TR** — **transfer** (no PR) → Transfer Ja LF then **`run.py --arm-weiter`** (**Weiter**); `.cursor/rules/lf-tr-transfer.mdc`
- Never swap: PR LF ≠ Weiter; LF TR ≠ Anwenden
- **DONE** / **Done for today** — stop Anwenden/Weiter RE / watches; pause until next login (`.cursor/rules/done-for-today.mdc`)
- **LF Salcus:** sidebar Kundennummer box only — `.cursor/rules/lf-salcus-kundennummer-exclusive.mdc`

## Instructions dashboard

Rules, skills, TransferMatrix — no live case scripts. **`revert last`** restores Anwenden-RE checkpoint if needed.
