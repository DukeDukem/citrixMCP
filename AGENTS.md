# AGENTS.md — Citrix Sprinklr workspace

## Chats (mandatory split)

| Chat | Startup doc | Runs login / RE / PR / LF? |
|------|-------------|----------------------------|
| **Instructions dashboard** | `AGENT-INSTRUCTIONS.md` | **No** |
| **Email processing** | `EMAIL-PROCESSING-AGENT.md` | **Yes** |
| **September Incentive** | `SEPTEMBER-INCENTIVE-AGENT.md` | **No** — yoummday Produktivitätsbonus / shift points / Treue-Bonus only |

## Language

- **To you (operator):** **English only** — RE sections 1–5/7, warnings, CALL packs, instructions chat.
- **To customer:** **German only** — RE section 6 + PR paste. Rule: `.cursor/rules/agent-english-user-customer-german.mdc`.

## Model policy (Pro Plus)

- **Email processing:** **Auto** (user choice since **2026-09-09**, speed). Recommended fallback: **Claude 4.6 Sonnet** for hard RE. Picker log: `.cursor/knowledge/pro-plus-model-spend-2026.md`.
- **Instructions dashboard:** **pace-based** — Composer default; Sonnet when behind pace / complex design so included pools land ~full by month-end. See `AGENT-INSTRUCTIONS.md`.
- **Grok banned.** **On-demand Disabled.** Never recommend overages.
- Spend / pacing: `.cursor/knowledge/pro-plus-model-spend-2026.md`.

## Case commands (email processing chat)

- **login** — Sprinklr + Case Tracker; agent **auto `--once`** on first visible case (no typed **RE**)
- **New EMAIL case** — sidetray click → **immediate** extract (`SIDETRAY_EMAIL_PROCESSING_IMMEDIATE`) → agent **auto** 7-step + **Auto-LF** with no pause after `--await-arm`. Operator types **PR** only (not **RE**). Recovery: typed **RE** / **RE SHOW** / **RE FILE** (`re-no-background-tasks-ui.mdc`).
- **PR** (EMAIL non-transfer) — paste reply (LF already done at RE) → **`--arm`** → Anwenden → **`--await-arm`**
- **Auto-LF transfer** — during RE when §3 says transfer → Transfer Ja fill → **`--arm-weiter`** / **`--arm-extern`** (no typed LF TR needed)
- **CALL** — on CHANNEL detect → Auto-LF voice → **`--arm-next`** (BRIEF optional; not required for LF)
- Typed **LF** / **LF TR** / **PR LF** — recovery/override only
- **CALL vs EMAIL:** After every case open, classify via overlay. Post-arm sidetray: **EMAIL click**, **CALL auto-open** (no sidetray click). **Teleprompter/STT parked** — do **not** `--arm`/`--prime` call_listen. Rule: `sprinklr-call-vs-email.mdc`
- **Transfer path:** Always **TransferMatrix.md** first. Rule: `transfer-matrix-priority.mdc`
- **Auto-LF:** Rule: `lf-log-form.mdc`

## Instructions dashboard

Rules, skills, TransferMatrix — no live case scripts. **`revert last`** restores Anwenden-RE checkpoint if needed.

## September Incentive

Bonus / shift-planning chat only. Startup: **`SEPTEMBER-INCENTIVE-AGENT.md`**. Knowledge: **`.cursor/knowledge/september-incentive-2026.md`**. No Sprinklr automation.
