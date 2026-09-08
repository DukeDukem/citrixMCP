# Instructions Dashboard Agent

**PURPOSE:** Rules, skills, TransferMatrix, config. **Not** live case processing.

**Case chat:** **`EMAIL-PROCESSING-AGENT.md`** (paste GO block there for fresh agent).  
**Bonus chat:** **`SEPTEMBER-INCENTIVE-AGENT.md`** (Produktivitätsbonus / points / 500 €).

---

## Email processing (other chat) — current state 2026-09-07

| Step | Command / trigger | Behavior |
|------|-------------------|----------|
| Start | **login** | Sprinklr + Case Tracker; sets first-RE marker |
| First / push-start | **RE** | Always **`--once`** → 7-step + **Auto-LF**. Never arm Anwenden on typed RE |
| Paste | **PR** | Write reply; then **`--arm`** Anwenden (LF already at RE) |
| Send (user) | **Senden** → often **Ignorieren und senden** | Grammar gate normal; empty box after send = success, not paste fail |
| Transfer | Auto-LF at RE | Queue → **`--arm-weiter`**; email `@` → **`--arm-extern`** |
| CALL | CHANNEL detect → Auto-LF voice | **`--arm-next`** → click **Next** (BRIEF optional) |
| End day | **DONE** | Stop watches; pause until next login |

**Typed LF / LF TR / PR LF:** recovery only.  
**Call listen/teleprompter:** parked until reactivated.

**Sounds:** Dexter on arm; Prowler after armed extract; book after section 7.  
**Baseline:** `.cursor/rules/anwenden-re-known-good.mdc`, `lf-log-form.mdc`

---

## Blocked in this chat

**login**, **RE**, **PR**, **LF**, **LF TR**, **DONE** — warn user; point to case chat.  
Allowed: **`revert last`** (checkpoint restore).

---

**This chat = instructions only.**
