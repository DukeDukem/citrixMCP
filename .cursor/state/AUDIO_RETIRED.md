# Audio cues RETIRED (2026-09-18)

All Prowler / book / Dexter playback is disabled.

## Processing path (only)

1. Arm (`--closeout-*` / `--arm*`) → `monitoring_armed`
2. Extract → `extract_ready.json` pending
3. Stop hook `extract_auto_continue_hook` → `[AUTO_PIPELINE]` (email chat owner)
4. Agent types 7-step
5. `re_auto_lf_hook` (text) → `auto_lf_after_re.py`

## Removed from active hooks

- `re_complete_sound_hook` (removed from `hooks.json`)

## Code no-ops

- `re_complete_sound.py` — all `play_*` return False
- Extract path — no Prowler / `RE_PENDING_SOUND`
- Arm path — no Dexter
