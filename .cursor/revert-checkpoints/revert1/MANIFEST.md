# Revert checkpoint: revert1

**Created:** 2026-09-01  
**Git HEAD at checkpoint:** `bfdb74dda37d40d6ee096737ee9932b798efe4d6`

## Purpose

Safety checkpoint before RE read-email experiment:
- Prefer **focused** Sprinklr case tab when multiple `/app/console/c/<id>` tabs exist
- Read Fall # from sidebar **`data-entityid="Fallnummer"`** first, then h2 header fallback

## Restore

Say **`revert1`** in chat, or run:

```powershell
Copy-Item ".cursor/revert-checkpoints/revert1/email_automation.py" ".cursor/skills/sprinklr-email-automation/email_automation.py" -Force
Copy-Item ".cursor/revert-checkpoints/revert1/run.py" ".cursor/skills/sprinklr-read-answer-email/run.py" -Force
```

## Files in this checkpoint

| File | Role |
|------|------|
| `email_automation.py` | Pre-experiment automation |
| `run.py` | RE runner (unchanged in experiment; copied for completeness) |
