# Revert checkpoint: revert2

**Created:** 2026-09-01  
**Git HEAD at checkpoint:** `bfdb74dda37d40d6ee096737ee9932b798efe4d6`

## Purpose

Safety checkpoint for **click-gated Fall # watch (auto-RE)**:
- Default RE = wait for left-click on `button[data-testid="collapsed-case-item"]`, then poll h1 Fall # until change
- On change → extract → `FALL_DETECTION_STOPPED` → wait for next click
- Legacy single-shot: `run.py --once`

## Restore Fall # watch (after broken edits)

Say **`revert2`** in chat, or run:

```powershell
Copy-Item ".cursor/revert-checkpoints/revert2/email_automation.py" ".cursor/skills/sprinklr-email-automation/email_automation.py" -Force
Copy-Item ".cursor/revert-checkpoints/revert2/run_sprinklr_email_automation.py" ".cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py" -Force
Copy-Item ".cursor/revert-checkpoints/revert2/run.py" ".cursor/skills/sprinklr-read-answer-email/run.py" -Force
Copy-Item ".cursor/revert-checkpoints/revert2/re-read-email.mdc" ".cursor/rules/re-read-email.mdc" -Force
```

## Roll back to pre–Fall watch (manual RE only)

Say **`revert1`** — restores pre–Fall watch read-email behaviour (see `.cursor/revert-checkpoints/revert1/MANIFEST.md`).

## Files in this checkpoint

| File | Role |
|------|------|
| `email_automation.py` | Fall # watch + extract |
| `run_sprinklr_email_automation.py` | Runner (forwards `--watch-fall-re`) |
| `run.py` | Default `--watch-fall-re`; `--once` = legacy |
| `re-read-email.mdc` | RE rule (Fall watch default) |
