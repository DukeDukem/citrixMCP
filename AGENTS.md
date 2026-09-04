# AGENTS.md — Citrix Sprinklr workspace

## Two chats (mandatory split)

| Chat | Startup doc | Runs login / RE / PR / LF? |
|------|-------------|----------------------------|
| **Instructions dashboard** | `AGENT-INSTRUCTIONS.md` | **No** |
| **Email processing** | `EMAIL-PROCESSING-AGENT.md` | **Yes** |

## Model lock

- Cursor picker: **Auto only**. Grok banned.

## Case commands (email processing chat)

- **login** — Sprinklr + Case Tracker; sets first-RE **`--once`** gate
- **RE** — first after login = **`--once`**; after **PR LF** = **`--arm`** (Anwenden); after **LF TR** = **`--arm-weiter`** (queue) or **`--arm-extern`** (email)
- **PR LF** / **LF alone** — non-transfer → **`run.py --arm`** (Anwenden only)
- **LF TR** — transfer, no PR → Transfer Ja LF → queue → **`--arm-weiter`**; email → **`--arm-extern`**
- Never swap: PR LF / LF ≠ Weiter/Extern; LF TR ≠ Anwenden; queue ≠ email arm
- **DONE** — stop watches; pause until next login
- **LF Salcus:** Kundennummer sidebar only; **`C-…`** is not Salcus → empty → ticketstatus **3**

## Instructions dashboard

Rules, skills, TransferMatrix — no live case scripts. **`revert last`** restores Anwenden-RE checkpoint if needed.
