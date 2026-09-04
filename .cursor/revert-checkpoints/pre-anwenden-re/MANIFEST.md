# Checkpoint: pre-anwenden-re

**Created:** before Anwenden-gated auto-RE experiment  
**Restore command:** user types **`revert last`** in instructions chat

## Restore copies these files back

| File in this folder | Restore to |
|---------------------|------------|
| `run.py` | `.cursor/skills/sprinklr-read-answer-email/run.py` |
| `email_automation.py` | `.cursor/skills/sprinklr-email-automation/email_automation.py` |
| `run_sprinklr_email_automation.py` | `.cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py` |
| `fall_watch_state.py` | `.cursor/skills/sprinklr-email-automation/fall_watch_state.py` |
| `re-read-email.mdc` | `.cursor/rules/re-read-email.mdc` |
| `EMAIL-PROCESSING-AGENT.md` | `EMAIL-PROCESSING-AGENT.md` (repo root) |

## What this checkpoint is

Manual RE only: `run.py` → `--process-current-only --extract-only`  
No Anwenden click watch, no auto-click of `collapsed-case-item`.
