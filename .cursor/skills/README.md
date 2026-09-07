# Cursor skills (this project)

**Two chats:** Live commands (**login**, **RE**, **PR**, **LF**) run in the **email processing chat** (`EMAIL-PROCESSING-AGENT.md`). Rules/skills edits use the **instructions dashboard** (`AGENT-INSTRUCTIONS.md`).

## Shortforms

| Shortform | Meaning | Skill |
|-----------|---------|--------|
| **RE** | Read email (manual, per case) | sprinklr-read-answer-email |
| **PR** | Paste reply | sprinklr-write-reply |
| **LF** | Log form (Case Tracker) | fill-microsoft-form |
| **CALL listen** | Local STT voice brief | sprinklr-call-listen |

## Order (email processing chat)

1. **login** (once)
2. Open case → **RE** → 7-step output (+ Prowler audio cue)
3. **PR** → send → **LF**
4. Next case → **RE** again

## Scripts

- **RE:** `uv run python .cursor/skills/sprinklr-read-answer-email/run.py`
- **PR:** `uv run python .cursor/skills/sprinklr-write-reply/run.py <reply-file>`
- **LF:** `uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#FALL_ID"`
- **login:** `uv run python .cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py --login-only`
- **CALL listen:** `uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --arm` (stop: `--stop`; probe: `probe_call_audio.py --lock`)
