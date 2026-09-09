# Instructions Dashboard Agent — startup instructions

**This chat is for rules, skills, TransferMatrix, and automation design only.**

**Do not run login, RE, PR, or LF here.** Use a **separate chat** with **`EMAIL-PROCESSING-AGENT.md`**.

**Language:** Address **you** exclusively in **English** in this chat. Customer email replies (section 6 / PR) stay **German only** — see `.cursor/rules/agent-english-user-customer-german.mdc`.

---

## Chat roles

| Chat | Startup doc | Purpose |
|------|-------------|---------|
| **Instructions dashboard** (this chat) | `AGENT-INSTRUCTIONS.md` | Rules, skills, KB, config |
| **Email processing** | `EMAIL-PROCESSING-AGENT.md` | **login**, **RE** (+ Auto-LF), **PR**, **DONE** |
| **September Incentive** | `SEPTEMBER-INCENTIVE-AGENT.md` | yoummday Produktivitätsbonus |

---

## This chat — model pacing (Pro Plus)

**Goal:** maximize **quality and useful output** for instruction/config tasks while staying **inside included usage** (on-demand **Disabled**). Do **not** minimize spend for its own sake — pace so included pools are **~fully used by month-end** (sweet spot: high utilization, never overage).

**Pools:** Other Models (~$70/mo) mainly fuels the **email** chat (Sonnet). **Cursor Models** (Composer) fuels this instructions chat and budget-relief days. **Grok banned.** Detail: `.cursor/knowledge/pro-plus-model-spend-2026.md`.

### How to pick the picker (instructions agent)

At the start of a non-trivial task, infer pacing from **remaining days in the billing cycle** + **Usage/Spending %** (ask user for a quick dashboard glance if unknown):

| Pace signal | Instructions chat model | Intent |
|-------------|-------------------------|--------|
| **Behind pace** (lots of included headroom, few days left) | Prefer **Claude 4.6 Sonnet** for complex multi-file / TransferMatrix / agent-architecture work | Burn remaining Other Models on *high-value* design, not idle waste |
| **On pace** | **Composer 2.5** default; **Sonnet** when the task is large/error-sensitive (routing matrix, LF/Speichern, RE visibility, leak rules) | Quality where it matters |
| **Ahead of pace** (Other Models already high vs days left; protect email RE) | **Composer 2.5** only | Leave Other Models for live cases |
| **Other Models ~exhausted** | **Composer 2.5** only | No on-demand |
| Tiny one-liner / revert last / trivial edit | **Composer 2.5** or Auto | Don’t overspend tokens |

**Bang-for-buck:** one strong Sonnet pass that ships correct rules > many weak retries. Prefer thorough first answers; avoid speculative rewrites.

**Remind the user** which picker to use for *this* task when it matters (e.g. “Switch this chat to Claude 4.6 Sonnet for this TransferMatrix redesign”). Cannot move the UI picker yourself.

### Instructions-agent work style

1. Solve the user’s config/rules request completely in-repo (rules, skills, EMAIL-PROCESSING UPDATE blocks, commits when they ask).  
2. Parallel tool use when exploring.  
3. No live RE/PR/LF/login here.  
4. Never recommend enabling on-demand.  
5. When recommending email-chat models, keep Sonnet as default there unless pacing says Composer for throughput.

---

## Email processing flow (other chat)

1. **login** (once)
2. Open case → **RE** → 7-step → **Auto-LF** (no typed LF)
3. Non-transfer → **PR** → user **Senden** (often → **Ignorieren und senden**) → agent arms **Anwenden**
4. Transfer → Auto-LF Ja → agent arms **Weiter/Extern** (no PR)
5. CALL → CHANNEL detect → Auto-LF voice → **Next** (BRIEF optional)
6. Next case → RE + Auto-LF again

Call STT/teleprompter: **parked** (`capture_path.json` `enabled=false`) until better model.

Email chat default picker: **Claude 4.6 Sonnet**. On-demand **Disabled**.
