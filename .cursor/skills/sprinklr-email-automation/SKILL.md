# sprinklr-email-automation (shared automation)

This folder holds the **Sprinklr email automation scripts** used by Skill 1 and Skill 2. Do not run this folder directly; use the skill scripts:

- **Skill 1:** `.cursor/skills/sprinklr-open-login-status/run.py` → runs this runner with `--login-only`
- **Skill 2:** `.cursor/skills/sprinklr-read-answer-email/run.py` → runs this runner with `--process-current-only`

## Contents

- `run_sprinklr_email_automation.py` – Starts Chrome (if needed), then runs `email_automation.py` with repo root as cwd.
- `email_automation.py` – CDP connect, Sprinklr login/status, email detection, Cursor AI, TinyMCE write, etc.

All skill scripts live under `.cursor/skills/` (this directory); they do not depend on `scratchspace/`.
