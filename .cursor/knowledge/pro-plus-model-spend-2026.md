# Pro Plus model spend — Sprinklr care agent (2026-09)

## Plan

| Item | Value |
|------|--------|
| Plan | Cursor **Pro Plus** ~**$60**/mo |
| Other Models pool | ~**$70**/mo included (API rates) |
| Cursor Models pool | Generous (Composer 2.5, Grok family) — **do not use Grok for cases** |
| **On-demand / overage** | **DISABLED** — no pay-as-you-go beyond included pools |

Sources: [Cursor models & pricing](https://cursor.com/docs/models-and-pricing), [Overages](https://cursor.com/help/account-and-billing/overages.md), [Spend limits](https://cursor.com/help/account-and-billing/spend-limits.md).

## On-demand must stay OFF

User requirement: **do not enable on-demand usage.**

Verify / set:

1. Open [cursor.com/dashboard/spending](https://cursor.com/dashboard/spending)  
2. **On-Demand Usage** → Monthly Limit → **Disabled** → Save  
3. Or: Cursor **Settings → Plan & Usage → On-Demand Usage → Monthly Limit → Disabled**

When included usage hits 100% with on-demand Disabled, Cursor throttles / blocks further Other Models requests — **no extra charges**. Switch the email chat to **Composer 2.5** (Cursor Models pool) or pause until the billing cycle resets.

Agents must **never** recommend enabling on-demand, raising overage limits, or “just pay for more.”

## Recommended picker

| Work | Model | Pool |
|------|--------|------|
| Live EMAIL/CALL RE·PR·LF | **Claude 4.6 Sonnet** (thinking) | Other Models |
| Hard escalation only | Claude 4.6 Opus / Opus 5 | Other Models |
| Rules / bonus / throughput / near-cap | **Composer 2.5** | Cursor Models |
| Forbidden | **Grok** (all); **on-demand enable** | — |

## Claude 4.6 Sonnet rates (per 1M tokens)

| | USD |
|--|-----|
| Input | $3 |
| Cache read | ~$0.30 |
| Output | $15 |

## Per-case ballpark (warm cache)

| | USD / case |
|--|------------|
| EMAIL full cycle | $0.35–0.80 |
| CALL cycle | $0.10–0.30 |

## Monthly ballpark (Sonnet-primary, 20 days)

| Volume / day | Other Models $/mo |
|--------------|-------------------|
| 15 EMAIL + 10 CALL | ~$8–16 |
| 30 EMAIL + 20 CALL | ~$15–30 |
| 50 EMAIL + 30 CALL | ~$25–50 |
| 80 EMAIL + 40 CALL | ~$40–75 → **move to Composer before hitting 100%** |

If Other Models nears **~$45–50** mid-month → shift throughput to Composer 2.5; keep Sonnet for sticky/QA cases.

## Total cash

**$60 plan fee only** + consumption of **included** pools. **$0 on-demand** while Disabled.
