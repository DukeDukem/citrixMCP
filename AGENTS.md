# AGENTS.md — Citrix Sprinklr workspace

## Chats (mandatory split)

| Chat | Startup doc | Runs login / RE / PR / LF? |
|------|-------------|----------------------------|
| **Instructions dashboard** | `AGENT-INSTRUCTIONS.md` | **No** |
| **Email processing** | `EMAIL-PROCESSING-AGENT.md` | **Yes** |
| **September Incentive** | `SEPTEMBER-INCENTIVE-AGENT.md` | **No** — yoummday Produktivitätsbonus / shift points / Treue-Bonus only |

## Model policy (Pro Plus)

- **Email processing chat:** Cursor picker → **Claude 4.6 Sonnet** (thinking). Escalation: Opus. Throughput/budget: Composer 2.5.
- **Instructions / Incentive chats:** Composer 2.5 or Auto (save Other Models pool).
- **Grok banned** for all case work.
- **On-demand / overage usage: DISABLED** — never recommend enabling it; near Other Models cap → Composer 2.5 or pause until cycle reset.
- Spend notes: `.cursor/knowledge/pro-plus-model-spend-2026.md`. Rule: `.cursor/rules/ai-model-stay-auto.mdc` (filename historical; content is Pro Plus policy).

## Case commands (email processing chat)

- **login** — Sprinklr + Case Tracker; sets first-RE marker
- **RE** (typed) — **always `--once`** extract open case → 7-step (EMAIL) + **Auto-LF**. Never Anwenden arm on typed RE.
- **PR** (EMAIL non-transfer) — paste reply (LF already done at RE) → **`--arm`** → Anwenden → **`--await-arm`**
- **Auto-LF transfer** — during RE when §3 says transfer → Transfer Ja fill → **`--arm-weiter`** / **`--arm-extern`** (no typed LF TR needed)
- **CALL** — on CHANNEL detect → Auto-LF voice → **`--arm-next`** (BRIEF optional; not required for LF)
- Typed **LF** / **LF TR** / **PR LF** — recovery/override only
- **CALL vs EMAIL:** After every case open, classify via overlay. **Teleprompter/STT parked** — do **not** `--arm`/`--prime` call_listen. Rule: `sprinklr-call-vs-email.mdc`
- **Transfer path:** Always **TransferMatrix.md** first. Rule: `transfer-matrix-priority.mdc`
- **Auto-LF:** Rule: `lf-log-form.mdc`

## Instructions dashboard

Rules, skills, TransferMatrix — no live case scripts. **`revert last`** restores Anwenden-RE checkpoint if needed.

## September Incentive

Bonus / shift-planning chat only. Startup: **`SEPTEMBER-INCENTIVE-AGENT.md`**. Knowledge: **`.cursor/knowledge/september-incentive-2026.md`**. No Sprinklr automation.
