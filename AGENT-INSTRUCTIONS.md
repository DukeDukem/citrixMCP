# Instructions Dashboard Agent — startup instructions

**This chat is for rules, skills, TransferMatrix, and automation design only.**

**Do not run login, RE, PR, or LF here.** Use a **separate chat** with **`EMAIL-PROCESSING-AGENT.md`**.

---

## Chat model

| Chat | Startup doc | Purpose |
|------|-------------|---------|
| **Instructions dashboard** | `AGENT-INSTRUCTIONS.md` | Rules, skills, KB, config |
| **Email processing** | `EMAIL-PROCESSING-AGENT.md` | **login**, **RE** (+ Auto-LF), **PR**, **DONE** |
| **September Incentive** | `SEPTEMBER-INCENTIVE-AGENT.md` | yoummday Produktivitätsbonus — `.cursor/knowledge/september-incentive-2026.md` |

---

## Email processing flow (other chat)

1. **login** (once)
2. Open case → **RE** → 7-step → **Auto-LF** (no typed LF)
3. Non-transfer → **PR** → user **Senden** (often → **Ignorieren und senden**) → agent arms **Anwenden**
4. Transfer → Auto-LF Ja → agent arms **Weiter/Extern** (no PR)
5. CALL → BRIEF → pack → Auto-LF voice → **Next**
6. Next case → RE + Auto-LF again

Call STT/teleprompter: **parked** (`capture_path.json` `enabled=false`) until better model.

---

## Model lock

**Auto only.** Grok banned.
