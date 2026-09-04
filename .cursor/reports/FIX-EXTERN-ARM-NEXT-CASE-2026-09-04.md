# FIX APPLIED — Extern arm next-case click (2026-09-04)

**Report:** `.cursor/reports/ERROR-EXTERN-ARM-MISS-2026-09-04.md`  
**Root cause:** Weiterleiten detected OK; `_click_first_collapsed_case_item()` used `.first` → same Fall `#55411928` → console → extract failed → stuck re-waiting Weiterleiten.

## Code changes (`email_automation.py`)

1. Remember **closed Fall #** while case still open (Anwenden / Weiter / Extern arms).
2. Click next `collapsed-case-item` whose aria-label is **not** that Fall #; poll up to ~25s.
3. Parse `Fall Nr. 55411928` in aria-labels (not only `#digits`).
4. After click: verify not still on console / closed Fall; retry up to 3×.
5. On hard fail: print `ERROR: NEXT CASE NOT OPEN — run run.py --once` and **exit arm** (no second Weiterleiten wait).
6. `flush=True` on progress prints.

## `run.py --await-arm`

Fails fast when log contains `ERROR: NEXT CASE NOT OPEN` → `DETACHED_ARM_EXTRACT_FAILED` + tip `--once`.

## Operator recovery (this incident)

If next case already open:

```powershell
uv run python .cursor/skills/sprinklr-read-answer-email/run.py --once
```
