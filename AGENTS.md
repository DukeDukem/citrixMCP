# AGENTS.md — Citrix Sprinklr workspace

## Two chats (mandatory split)

| Chat | Startup doc | Runs login / RE / PR / LF? |
|------|-------------|----------------------------|
| **Instructions dashboard** | `AGENT-INSTRUCTIONS.md` | **No** |
| **Email processing** | `EMAIL-PROCESSING-AGENT.md` | **Yes** |

## Model lock

- Cursor picker: **Auto only**. Grok banned.

## Case commands (email processing chat)

- **login** — Sprinklr + Case Tracker; sets first-RE marker
- **RE** (typed) — **always `--once`** extract open case (first case of day / fresh agent push-start, or manual re-read). Never Anwenden arm on typed RE.
- **PR LF** / **LF** (EMAIL) — **`--arm`** → Anwenden → **`--await-arm`**
- **LF** (**CALL**) — `--channel voice` then **`--arm-next`** → exact **Next** → **`--await-arm`** (never Anwenden after a call)
- **LF TR** — queue **`--arm-weiter`** or email **`--arm-extern`**, then **`--await-arm`**
- **CALL vs EMAIL:** After every case open, classify via overlay. **CALL** → `call_listen.py --arm` (local STT) → **BRIEF** / paste → handle; LF voice + stop listen + **`--arm-next`**. **EMAIL** → 7-step RE/PR/LF + **`--arm`**. Rule: `sprinklr-call-vs-email.mdc`
- **Transfer path:** Always **TransferMatrix.md** first (Ziel-Kontakt + Action). KB must not override routing; if not transferable, handle from matrix Action hint then KB. Rule: `transfer-matrix-priority.mdc`

## Instructions dashboard

Rules, skills, TransferMatrix — no live case scripts. **`revert last`** restores Anwenden-RE checkpoint if needed.
