# Instructions Dashboard Agent

**PURPOSE:** Rules, skills, TransferMatrix, config. **Not** live case processing.

**Case chat:** **`EMAIL-PROCESSING-AGENT.md`** (paste GO block there for fresh agent).

---

## Email processing (other chat) — current state 2026-09-04

| Step | Command | Behavior |
|------|---------|----------|
| Start | **login** | Sprinklr + Case Tracker; sets first-RE marker |
| First / push-start | **RE** | Always **`--once`** (extract open case). Never arm Anwenden on typed RE |
| Paste | **PR** | Write reply to Sprinklr |
| Log (answered) | **LF** / **PR LF** | Tracker → **`--arm`** (detached) → Dexter / READY_FOR_YOUR_CLICK → **`--await-arm`** → click **Anwenden** |
| Transfer | **LF TR** | Queue → **`--arm-weiter`**; email `@` → **`--arm-extern`**; then await → **Weiter** / **Weiterleiten** |
| End day | **DONE** | Stop watches (incl. detached); pause until next login |

**Sounds:** Dexter on arm (click-ready); Prowler after armed extract; book via `re_complete_sound.py --play-ready` after section 7.

**Next-case click:** skips closed Fall # in sidebar; on fail → `ERROR: NEXT CASE NOT OPEN — run.py --once`.

**Baseline rule:** `.cursor/rules/anwenden-re-known-good.mdc`  
**Reports:** `.cursor/reports/`

---

## Blocked in this chat

**login**, **RE**, **PR**, **LF**, **LF TR**, **DONE** — warn user; point to case chat.  
Allowed: **`revert last`** (checkpoint restore).

---

**This chat = instructions only.**
