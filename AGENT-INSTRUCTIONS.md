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

1. **login** (once) — login-only; Case Tracker tab; **no** Verfügbar day-start arm (reverted 2026-09-11)
2. Open case → **RE** → **three-turn EMAIL RE** → **Auto-LF** (no typed LF)
3. Non-transfer → **PR** → user **Senden** (often → **Ignorieren und senden**) → agent arms **Anwenden**
4. Transfer → Auto-LF Ja → agent arms **Weiter/Extern** (no PR)
5. CALL → CHANNEL detect → Auto-LF voice → **Next** (BRIEF optional)
6. Next case → RE + Auto-LF again

**EMAIL three-turn RE:** (1) `run.py` extract → `RE_TEXT_ONLY_GATE` → stop (2) **text-only** 7-step — zero tools (3) play-ready → Auto-LF → PR or transfer arm. Recovery: **`RE SHOW`**, **`RE FILE`**, or open `.cursor/state/latest_re_visible.md`. Rule: `re-no-background-tasks-ui.mdc`.

Call STT/teleprompter: **parked** (`capture_path.json` `enabled=false`) until better model.

Email chat picker (user): **Auto** since 2026-09-09 (speed). Fallback: **Composer 2.5** or **Sonnet** if background-task menus persist. On-demand **Disabled**.

---

## Rules baseline (2026-09-11)

Git reset to **`0a98818`** — background-tray fix + language split + Speichern continue + Pro Plus policy. **Not active:** post-login Verfügbar day-start / `--arm-verfuegbar` (commits after `0a98818` were reverted).

### Always-applied rule files (high priority)

| Rule | Purpose |
|------|---------|
| `re-no-background-tasks-ui.mdc` | Three-turn RE; no Task/explore; RE SHOW / RE FILE |
| `re-read-email.mdc` | RE entry, visible 7-step, Auto-LF order, arms |
| `agent-english-user-customer-german.mdc` | English to operator; German section 6 / PR |
| `ai-model-stay-auto.mdc` | Pro Plus pacing; Grok banned; no Task for 7-step |
| `lf-log-form.mdc` | Auto-LF, Speichern gate + continue-await |
| `pr-paste-reply.mdc` | PR paste, leak checks, Anwenden arm after PR |
| `transfer-matrix-priority.mdc` | Matrix before KB for routing |
| `sprinklr-call-vs-email.mdc` | CHANNEL detect; CALL Auto-LF + Next |
| `instructions-only-no-re-pr-lf.mdc` | This chat: no live RE/PR/LF |

Full list: `.cursor/rules/*.mdc`

---

## UPDATE RULES — paste to **email processing** chat

Use when the case agent needs a delta without full GO re-bootstrap (copy block from `EMAIL-PROCESSING-AGENT.md` § UPDATE, or this shortened sync):

```
UPDATE — rules sync 2026-09-11 (baseline 0a98818):

RE — THREE TURNS (EMAIL): (1) run.py only → RE_TEXT_ONLY_GATE → stop (2) text-only full 7-step sections 1–7 — ZERO tools (3) play-ready → Auto-LF → PR or transfer arm. No Task/explore; no Read terminals/*.txt.

RE recovery: RE SHOW / visible RE / RE FILE (show_latest_re.py). Backup: .cursor/state/latest_re_visible.md

LANGUAGE: English to me (sections 1–5, 7); German customer reply (section 6 + PR).

MODEL: Auto (user choice); Grok forbidden; on-demand DISABLED. If background trays persist → Composer 2.5 or Sonnet.

AUTO-LF: mandatory at RE (EMAIL) and CHANNEL:CALL. Speichern gate + --await-speichern-continue on pause.

NOT ACTIVE: Verfügbar day-start arm / --arm-verfuegbar (reverted). login = login-only + Case Tracker.

Confirm and continue with next case command.
```
