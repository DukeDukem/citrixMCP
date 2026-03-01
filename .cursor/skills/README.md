# Cursor skills (this project)

These skills are **separate, independent scripts**. Each skill has its own **run.py**; the agent runs that script when you ask. No skill calls another—they only share the same browser (CDP) when you run them in sequence.

## How to invoke

Say what you want in chat; the agent picks the skill and runs **only that script**:

| You say (examples) | Skill | Script the agent runs |
|--------------------|--------|------------------------|
| "Open Sprinklr and log in", "Set my status to active" | **sprinklr-open-login-status** | `uv run python .cursor/skills/sprinklr-open-login-status/run.py` |
| "Read the email and suggest a reply" | **sprinklr-read-answer-email** | `uv run python .cursor/skills/sprinklr-read-answer-email/run.py` (reads current page; summarizes full conversation + suggested reply in chat; no reload/navigate) |
| "Reply with …" / "Write that reply in the box" | **sprinklr-write-reply** | `uv run python .cursor/skills/sprinklr-write-reply/run.py <path-to-reply.txt>` (writes into reply field on current page; no reload/navigate) |
| "Fill this Microsoft form with …" | **fill-microsoft-form** | `uv run python .cursor/skills/fill-microsoft-form/run.py --url "…" --answers …` |

**Order:** (1) Skill 1: login + status. (2) Skill 2: read email → summary + suggested reply in chat. (3) User says "reply with …" → Skill **sprinklr-write-reply** with a file containing the reply. (4) Optionally fill-microsoft-form.

---

## Prompts to run (test)

Copy one of these into Cursor chat. The agent will run the corresponding skill script.

**Test Skill 1 only (login + status):**
```
Run the sprinklr-open-login-status skill: open Sprinklr, log in, and set my status to Verfügbar. Use the script at .cursor/skills/sprinklr-open-login-status/run.py and run it once.
```

**Test Skill 2 only (read email, summarize conversation + suggested reply in chat):**  
*(Do Skill 1 first, open an email case, then run this.)*
```
Run the sprinklr-read-answer-email skill: read the current email, then in the Cursor chat (1) summarize the entire email conversation (who wrote what, main points, order), (2) search (grep) the KnowledgeBase for relevant terms — do not read entire KnowledgeBase files — and (3) write the suggested reply here. Run .cursor/skills/sprinklr-read-answer-email/run.py.
```

**Test "reply with …" (write reply into Sprinklr box):**  
*(After Skill 2 has shown the suggested reply in chat.)*
```
Reply with the suggested email you just showed me. (Agent: save that reply to a file, then run .cursor/skills/sprinklr-write-reply/run.py <path-to-file>)
```

**Test Skill 3 only (fill form):**  
*(Do Skill 1 first so Chrome is running, then run this with your form URL and answers file.)*
```
Run the fill-microsoft-form skill. Form URL: https://forms.office.com/...  Answers file: path/to/answers.json  (Use .cursor/skills/fill-microsoft-form/run.py with --url and --answers.)
```

---

## Prompts to run all three skills in series

Use one of these prompts so the agent runs all skills in the right order:

**Option A (one prompt for the full flow):**
```
Run the three Sprinklr skills in order: first open Sprinklr and set status (sprinklr-open-login-status), then read and answer emails (sprinklr-read-answer-email), then fill the Microsoft form (fill-microsoft-form). For the form I'll give you the URL and answers when you get to step 3.
```

**Option B (step-by-step):**
1. *"Run the sprinklr-open-login-status skill: open Sprinklr, log in, and set my status to Verfügbar."*
2. After that finishes: *"Run the sprinklr-read-answer-email skill: read and answer the current emails and write the replies in the reply box."*
3. After that (or when you want to fill the form): *"Run the fill-microsoft-form skill. Form URL: [paste URL]. Answers: [paste or attach JSON, or list question → answer]."*

**Option C (short):**
```
Execute all three skills in sequence: (1) sprinklr-open-login-status, (2) sprinklr-read-answer-email, (3) fill-microsoft-form. For step 3 I need to fill [form URL] with [answers].
```

**Option D (Skill 2: read + show reply in chat; then optionally write to box):**  
Skill 2 only outputs to chat. To also put the reply in the Sprinklr box, run **sprinklr-write-reply** with a file containing the reply.
```
Run the sprinklr-read-answer-email skill to read the current email. In the Cursor chat: (1) summarize the entire email conversation (who wrote what, in order, main points), (2) search (grep) the KnowledgeBase for keywords — do not read entire files — then (3) show the suggested reply. After you paste the reply here, I'll say "reply with that" and you run sprinklr-write-reply with the reply text in a file.
```

## Script files (each runs independently)

- **Skill 1:** `.cursor/skills/sprinklr-open-login-status/run.py` — login + set status (invokes runner with `--login-only`)
- **Skill 2:** `.cursor/skills/sprinklr-read-answer-email/run.py` — read current email, output summary + suggested reply in chat only (invokes runner with `--process-current-only --chat-only`). Does **not** write to the browser.
- **sprinklr-write-reply:** `.cursor/skills/sprinklr-write-reply/run.py <reply-file>` — clear the reply box and write the reply from the file (invokes runner with `--write-reply-only --reply-file=<path>`). Use when the user says "reply with …".
- **fill-microsoft-form:** `.cursor/skills/fill-microsoft-form/run.py` — `--url` + `--answers`; optional `--no-submit`

Sprinklr automation lives under `.cursor/skills/sprinklr-email-automation/`; Skill 1, Skill 2, and sprinklr-write-reply call that runner.

## KnowledgeBase (search only — do not read entire files)

The **KnowledgeBase/** folder (e.g. `KnowledgeBase_Complete.md`, `TransferMatrix_KnowledgeBase.md`) contains very large files (millions of lines). When a skill says to use the KnowledgeBase, **grep or search** for keywords from the email or task (e.g. Rückerstattung, refund, transfer, Rechnung) and read only the **matching sections**. Never read or load an entire KnowledgeBase file.

## Requirements (once per machine)

- Chrome installed; `uv sync`; `uv run playwright install chromium`
- `config.json` at repo root: `login_email`, `login_password`, `cdp_endpoint`

## Skills in this folder

- **sprinklr-open-login-status** – Open Sprinklr, login, set status. Script: `run.py`
- **sprinklr-read-answer-email** – Read email, output summary + suggested reply in chat only. Script: `run.py`
- **sprinklr-write-reply** – Clear reply box and write reply from file (use when user says "reply with …"). Script: `run.py <reply-file>`
- **sprinklr-email-automation** – Shared runner + email_automation (do not run directly).
- **fill-microsoft-form** – Fill Microsoft Form. Script: `run.py` (needs `--url`, `--answers`)
- **start-and-login** – (Legacy) Prefer **sprinklr-open-login-status**.
