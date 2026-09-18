# Silent pipeline (audio deleted 2026-09-18)

Case-processing audio modules and hooks were removed. Nothing plays for RE / PR / LF / arm / extract.

## Path (only)

1. Arm (`--closeout-*`) → `monitoring_armed` + live `--await-arm`
2. Operator clicks Sprinklr close-out → extract → `extract_ready.json`
3. `--await-arm` completes and/or `extract_auto_continue_hook` → `[AUTO_PIPELINE]`
4. Agent types full 7-step immediately (no operator nudge)
5. `re_auto_lf_hook` → `auto_lf_after_re.py` → Case Tracker + next closeout

Rule: `.cursor/rules/no-audio-hooks-auto-pipeline.mdc`
