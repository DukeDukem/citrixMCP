# Instructions Dashboard Agent

**PURPOSE:** Rules, skills, TransferMatrix, config. **Not** live case processing.

**Case chat:** **`EMAIL-PROCESSING-AGENT.md`** (paste GO block there for fresh agent).  
**Bonus chat:** **`SEPTEMBER-INCENTIVE-AGENT.md`** (Produktivitätsbonus / points / 500 €).

---

## Email processing (other chat) — current state 2026-09-11

| Step | Command / trigger | Behavior |
|------|-------------------|----------|
| Start | **login** | Sprinklr + Case Tracker; agent **auto `--once`** on first visible case (no typed **RE**) |
| New EMAIL case | **`--await-arm` extract** (or post-login auto) | Agent **auto** 7-step + **Auto-LF** — operator does **not** type **RE** |
| Paste | **PR** | Write reply; then **`--arm`** Anwenden (LF already at RE) |
| Send (user) | **Senden** → often **Ignorieren und senden** | Grammar gate normal; empty box after send = success, not paste fail |
| Transfer | Auto-LF at RE | Queue → **`--arm-weiter`**; email `@` → **`--arm-extern`** |
| CALL | CHANNEL detect → Auto-LF voice | **`--arm-next`** → click **Next** (BRIEF optional) |
| End day | **DONE** | Stop watches; pause until next login |

**Typed LF / LF TR / PR LF:** recovery only.  
**Call listen/teleprompter:** parked until reactivated.

**Notify:** READY_FOR_YOUR_CLICK on arm; `--await-arm` / `[AUTO_PIPELINE]` after extract; `re_auto_lf_hook` after section 7. No audio.  
**Baseline:** `.cursor/rules/anwenden-re-known-good.mdc`, `lf-log-form.mdc`

---

## Blocked in this chat

**login**, **RE**, **PR**, **LF**, **LF TR**, **DONE** — warn user; point to case chat.  
Allowed: **`revert last`** (checkpoint restore).

---

**This chat = instructions only.**
