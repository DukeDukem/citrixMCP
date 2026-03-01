---
name: sprinklr-monitor-emails
description: Continuously monitors Sprinklr Console for new customer emails, auto-opens each case, lets Cursor AI generate a reply, writes the reply into the email editor, waits until the email is sent, then watches for the next new email. Use when you want fully automatic handling of incoming emails instead of triggering read-answer-email manually.
---

# Sprinklr: Always-on email monitor (auto-read + auto-write)

**When to use:** You are logged into Sprinklr and want an **always-on helper** that:

- **Detects new customer emails** appearing in the Sprinklr Console.
- **Automatically opens each new case**, extracts the full conversation thread, calls Cursor AI to create the reply using the standard template (salutation, thank you + sympathy, survey line, signature).
- **Writes the reply** into the TinyMCE reply editor (`Nachricht verfassen`) for that case.
- **Waits until you send the email** (or the case leaves the list), then **returns to the Console** and keeps watching for the **next new email**.

Run this once at the start of a shift and leave it running in the background while you work.

## What this skill does

1. Starts (or reuses) Chrome with remote debugging on port **9222**.
2. Connects to Sprinklr using the existing automation (same runner as other skills).
3. Ensures the **Console** page is open (no unnecessary reloads).
4. Enters an **infinite monitoring loop**:
   - Scans the Console for **new/unprocessed emails** by watching:
     - The collapsed preview list buttons: `div[data-entityid="CollapsedPreviewsList"] button[data-testid="collapsed-case-item"]`.
     - The console stream case cards: `div[data-testid="case-item-root"] div.cardItem` (showing Fallnummer, avatar, subject, preview, SLA "0s", etc.).
   - For each new email (new case ID), **clicks the corresponding collapsed-case-item** to open the case, then extracts the email + conversation thread.
   - Calls **Cursor AI** to analyze the case, KnowledgeBase, and generate a **customer reply** using the mandatory email reply template (Guten Tag…, case-specific thank you + sympathy, survey line, fixed signature block).
   - Writes the reply into the TinyMCE editor (`Nachricht verfassen`), preformatted and converted to HTML.
   - **Waits for you to send the email** (monitors for returning to Console / disappearance of the case).
5. Returns to the Console and keeps checking for new emails every few seconds until you stop it (Ctrl+C).

This skill uses the same formatting + template rules defined in `sprinklr-read-answer-email` and `sprinklr-write-reply`.

## How to invoke

From the repo root (or any directory, the script finds the repo root automatically):

```powershell
uv run python .cursor/skills/sprinklr-monitor-emails/run.py
```

Or with system Python if dependencies are installed:

```powershell
python .cursor/skills/sprinklr-monitor-emails/run.py
```

The script runs the **email automation runner without `--process-current-only`**, so it:

- Logs in / attaches to Chrome (CDP 9222),
- Ensures the Sprinklr Console is open,
- Then calls `automation.monitor_emails()` to **continuously** watch for new emails and auto-generate replies.

## Interaction with other skills

- **Skill 1 (`sprinklr-open-login-status`)**: Recommended to run first to open Sprinklr, log in, and set status to **Verfügbar**. This monitor skill will then attach to that same browser session.
- **Skill 2 (`sprinklr-read-answer-email`)**: Manual, single-shot read + chat-only reply. Use **instead of** this monitor skill when you want full manual control (you trigger each case yourself).
- **Skill 3 (`sprinklr-write-reply`)**: Manual writer for a reply text file into the editor. The monitor skill does **not** need it, because it writes replies directly.

Do **not** run this monitor skill and the manual Skill 2 in parallel on the same queue; pick **either** fully automatic monitoring (this skill) or manual per-case triggering.

## Stopping the monitor

- To stop monitoring, press **Ctrl+C** in the terminal where you started the skill.
- The script catches the interrupt, prints a stop message, and **cleans up** the Playwright browser context while leaving Chrome (debugging session) available for other skills if needed.

## Script file

- **Path:** `.cursor/skills/sprinklr-monitor-emails/run.py`
- **Does:** Resolves repo root, sets `SPRINKLR_CDP_ENDPOINT`, runs `.cursor/skills/sprinklr-email-automation/run_sprinklr_email_automation.py` **without** `--process-current-only` so that the underlying script logs in (if needed), opens the Console, and calls `monitor_emails()` in an endless loop.

