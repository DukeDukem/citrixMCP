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
- **PR LF** / **LF alone** — non-transfer → **`--arm`** (detached) → Dexter / READY_FOR_YOUR_CLICK → finishing quote → **`--await-arm`**
- **LF TR** — transfer, no PR → queue **`--arm-weiter`** or email **`--arm-extern`**, then **`--await-arm`**
- Arms are **detached** (`CREATE_NO_WINDOW`); click-ready = Dexter, not await spinner; re-run `--await-arm` if poll aborted
- Next-case open skips closed Fall #; fail → `ERROR: NEXT CASE NOT OPEN` → **`--once`**
- After section 7 → `re_complete_sound.py --play-ready` (book)
- Never swap: PR LF / LF ≠ Weiter/Extern; LF TR ≠ Anwenden; queue ≠ email arm
- **DONE** — stop watches (including detached); pause until next login
- **LF Salcus:** Kundennummer sidebar only; **`C-…`** is not Salcus → empty → ticketstatus **3**

## Instructions dashboard

Rules, skills, TransferMatrix — no live case scripts. **`revert last`** restores Anwenden-RE checkpoint if needed.
