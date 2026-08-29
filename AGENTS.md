# AGENTS.md — Citrix Sprinklr workspace

## Model lock (non-negotiable)

- Cursor model picker: **Auto only**.
- **Never** switch to Grok or any named model.
- If this session is Grok / named model: **STOP**. Tell the user to set picker to **Auto** and resend. Do not run RE/PR/LF.
- Full rule: `.cursor/rules/ai-model-stay-auto.mdc`

## Case commands

- RE / PR / LF / login: follow `.cursor/rules/` and skills under `.cursor/skills/`.
- **Instructions-only chats:** Do **not** run RE, PR, LF, or login — warn user to use a separate chat (`.cursor/rules/instructions-only-no-re-pr-lf.mdc`).
