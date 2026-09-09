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

## Utilization goal (not “spend as little as possible”)

**Target:** finish the billing cycle at **~maximum included usage** (Other Models ≈100% and healthy Composer use) while **on-demand stays Disabled**.

- Maximize **quality and shipped output** (correct rules, fewer retries).  
- Pace across remaining days — neither burn the Other Models pool in week 1 nor leave large unused headroom on the last day.  
- If behind pace late in the month: prefer Sonnet for high-value **instructions** work and keep email on Sonnet.  
- If ahead of pace: instructions → Composer; email sticky cases → Sonnet, throughput → Composer.  
- **Never** enable on-demand to “finish the month strong.”

### Rough Other Models pacing

`daily Other Models budget ≈ (remaining $ in Other Models pool) / (remaining days in cycle)`

Email RE is first claim on that budget. Instructions Sonnet usage is the valve when email volume is low and headroom would otherwise go unused.

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

## User picker log (actual UI choice — for usage breakdowns)

Document what **you** set in the Cursor model picker, not what agents recommend. When reconciling dashboard spend, compare against this log.

| Date | Chat | Picker set | Reason / notes |
|------|------|------------|----------------|
| **2026-09-09** | **Email processing** (`EMAIL-PROCESSING-AGENT.md`) | **Auto** | Higher processing and case-solving speed. Usage will **not** match Sonnet-primary estimates below — Auto routes across included models (often Composer / Cursor Models; may use Other Models on harder turns). **Grok still forbidden** if Auto selects it → switch picker manually. |
| *(prior)* | Email processing | Claude 4.6 Sonnet (thinking) | Default recommendation for German RE quality |

**When email chat is on Auto:** treat per-case **Other Models** $ as **variable**; track **Cursor Models vs Other Models** split in [Dashboard → Usage](https://cursor.com/dashboard/spending) separately from Sonnet-only baselines.

## Recommended picker

| Work | Model | Pool |
|------|--------|------|
| Live EMAIL/CALL RE·PR·LF | **Claude 4.6 Sonnet** (thinking) — or **Auto** if user prioritizes speed (see log above) | Other Models / mixed when Auto |
| Hard escalation only | Claude 4.6 Opus / Opus 5 | Other Models |
| Instructions (default / protect email budget) | **Composer 2.5** | Cursor Models |
| Instructions (behind pace / complex design / unused Other Models late-cycle) | **Claude 4.6 Sonnet** | Other Models |
| Forbidden | **Grok** (all); **on-demand enable** | — |

## Total cash

**$60 plan fee only** + consumption of **included** pools paced to ~month-end full use. **$0 on-demand** while Disabled.
