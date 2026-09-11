# ERROR: `--await-arm` UnicodeEncodeError on Windows (2026-09-11)

**For:** Instructions dashboard / `AGENT-INSTRUCTIONS.md` chat  
**Severity:** Medium — extract succeeds; poll exits code 1; agent may miss `RE_TEXT_ONLY_GATE` in shell output  
**Observed:** Fall #57513621 after Anwenden PR close-out (task 474002)

## Symptom

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position ...
  File: .cursor/skills/sprinklr-read-answer-email/run.py → _await_arm() → print(text[idx:])
```

Log already contained `DETACHED_ARM_EXTRACT_READY` + full `CUSTOMER EMAIL`; crash happened when replaying arm_watch.log to stdout (cp1252 console).

## Related failures (same root cause)

| Location | Trigger |
|----------|---------|
| `run.py --arm-verfuegbar` | `READY_FOR_YOUR_CLICK: … → Verfügbar` print |
| `run.py` FIRST_RE_ONCE / RE_ONCE_DEFAULT lines | `→` in status strings |
| `run.py _await_arm` | Replay extract from log with `→` / German umlauts |

## Partial fix applied (email-processing chat, 2026-09-11)

1. `run.py`: added `_safe_print()`; `_await_arm` replay uses it.
2. Replaced `→` with `->` in Verfügbar / RE_ONCE status prints.

## Recommended follow-up (instructions chat)

1. **Audit** all `print(...)` in `run.py` and arm spawn paths — use `_safe_print` or ASCII-only status lines on Windows.
2. **Optional:** `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` at top of `run.py` main() when on Windows.
3. **Audit** `email_automation.py` banner strings written to `arm_watch.log` that `--await-arm` replays (CHANNEL_GATE lines with `→`).
4. **Document** in `sprinklr-read-answer-email/SKILL.md`: if `--await-arm` exits 1 but `latest_extract.md` updated → treat as success; run typed **RE** or read `latest_extract.md`.
5. **Recovery rule** for case agent: on await exit 1 after `DETACHED_ARM_EXTRACT_READY` in log → proceed with 7-step from `latest_extract.md` (do not re-Anwenden).

## Workaround (operator)

- After Anwenden: if await fails, type **RE** on open case (extract already in `.cursor/state/latest_extract.md`).
- Or read `arm_watch.log` — extract block is valid UTF-8 on disk.

## Test plan

1. PR → Anwenden → `--await-arm` on Windows cp1252 shell with email body containing umlauts + `→` in CHANNEL_GATE output.
2. Expect exit 0 and full CUSTOMER EMAIL in terminal (no UnicodeEncodeError).
