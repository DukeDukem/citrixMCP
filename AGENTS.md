# AGENTS.md — Citrix Sprinklr workspace

## Two chats (mandatory split)

| Chat | Startup doc | Runs login / RE / PR / LF? |
|------|-------------|----------------------------|
| **Instructions dashboard** | `AGENT-INSTRUCTIONS.md` | **No** |
| **Email processing** | `EMAIL-PROCESSING-AGENT.md` | **Yes** |

## Model lock

- Cursor picker: **Auto only**. Grok banned.

## Case commands (email processing chat)

- **login** — Sprinklr + Case Tracker tab
- **RE** — Anwenden-gated auto-RE (wait Anwenden click → 3s → open next case → extract) or `--once`; then 7-step output
- **PR** / **LF** — paste reply + Case Tracker; **after both succeed**, agent **auto-arms** Anwenden RE again
- **LF Salcus:** sidebar Kundennummer box only — `.cursor/rules/lf-salcus-kundennummer-exclusive.mdc`

## Instructions dashboard

Rules, skills, TransferMatrix — no live case scripts. **`revert last`** restores Anwenden-RE checkpoint if needed.
