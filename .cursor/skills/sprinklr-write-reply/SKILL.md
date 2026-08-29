---
name: sprinklr-write-reply
description: Writes the suggested email reply into the Sprinklr reply box. Clears any existing content in the editor (section "Nachricht verfassen", TinyMCE body), then writes the reply text from a file. Use when the user says "reply with ..." or "write the reply in the box" after Skill 2 has shown the suggested email in chat.
---

# Sprinklr: Write Reply to Editor

**Shorthand:** The user may type **PR** instead of "paste reply" or "reply with …". Treat **PR** the same as "paste reply" / "write that reply in the box" and run this skill (with the reply text in a file; invoke the script with that file path).

**When to use:** After running **sprinklr-read-answer-email** (Skill 2), the suggested reply is shown in the chat only. When the user says **"reply with …"** or **"write that reply in the box"**, run this skill to clear the reply box and write the suggested email into the browser editor.

## What this skill does

1. Connects to the browser (CDP port 9222). **Does not reload the page or navigate to any URL** — uses the current tab as-is. Skill 1 must have been run and the email case must be open.
2. Finds the reply area on the **current page**: `section[aria-label="Nachricht verfassen"]` and the TinyMCE editor inside `[data-testid="baseEditorContainer"]`.
3. **Preformats** the reply text from the file: normalizes line endings, trims each line, and enforces consistent paragraph spacing (one blank line between paragraphs, no leading/trailing blank lines) so the email displays correctly in the editor.
4. **Clears** all existing content in the editor (including placeholder like `[Antwort]` and signature blocks).
5. **Writes** the preformatted reply into the editor (plain text is converted to HTML paragraphs for TinyMCE).
6. **Fills the O2 Roberta case tracker** in a **new tab**: opens `https://roberta.yoummday.com/casetracker/`, fills Case # (Fall ID), Kanal (E-Mail Care), and optional Anhänge note. **Speichern** is **not** clicked — you save manually after sending the email. To skip this step, run with `--no-fill-case-tracker`.

By default the script **exits after writing the reply and filling the form**; it does **not** wait for you to send or monitor for the next email. To enable that behaviour (wait for send, then open and print the next new email once), run with `--wait-next-extract-only`.

## How to invoke

You must pass the path to a **file containing the reply text** (the email body to write):

```powershell
uv run python .cursor/skills/sprinklr-write-reply/run.py path/to/reply.txt
```

or

```powershell
uv run python .cursor/skills/sprinklr-write-reply/run.py --reply-file=path/to/reply.txt
```

**Agent instructions:**

1. When the user says "reply with …" or "write the reply in the box", take the suggested email reply (from the previous Skill 2 output in chat, or from the user’s instructions).
2. Before writing the file, run a strict content gate:
   - Exactly one salutation (`Guten Tag`)
   - Exactly one survey line (`Zur Verbesserung unseres Kundenservices ...`)
   - Exactly one signature block (`Freundliche Grüße`, `Ihr o2 Kundenbetreuer`)
   - No duplicated/near-duplicated paragraph blocks
   - No uninvited promises of internal checks, processing, or further messages unless explicitly instructed by the user
   - If any check fails: STOP and rewrite to one clean response before running paste.
   - Confirm source case integrity: the reply text must come from the currently visible case only; if the latest RE case ID differs from current visible Fall #, STOP and require fresh RE for the visible case.
3. Write that reply text to a temporary file (e.g. in the repo or temp directory).
4. Run this skill with the path to that file:  
   `uv run python .cursor/skills/sprinklr-write-reply/run.py <path-to-file>`
5. Immediately run `python .cursor/skills/sprinklr-write-reply/verify_no_data_leak.py`.
6. If verification is not CLEAN:
   - Clear the editor content completely.
   - STOP immediately. Do not repaste automatically.
   - Report failure and require fresh RE-based rebuild before next PR.
7. After CLEAN verification, terminate the write flow immediately (no repaste loop). The reply box in Sprinklr will contain the text and the Roberta case tracker will be filled (in a tab, not saved). The user can edit the reply, send the email, then click Speichern in Case Tracker. To skip filling the form, add `--no-fill-case-tracker` when invoking the automation.

## Reply content (standard template)

The reply file should follow the **standard email reply template** (defined in **sprinklr-read-answer-email**): salutation (Guten Tag [Vorname Nachname], or "Guten Tag," if no/full name), case-specific thank you + sympathy, survey line about Zufriedenheitsbefragung, then the fixed signature block (Freundliche Grüße, Ihr o2 Kundenbetreuer, Lukasz Kowalski, Telefónica block, Umweltschutz, Pflichtangaben, Fußnote). When drafting the reply in Skill 2, Cursor uses that template; the file passed here should already contain the full text in that structure.

## Requirements

- Skill 1 (sprinklr-open-login-status) must have been run (browser open and logged in).
- An email case (Fall #…) must **already be open** in the current tab; the script does **not** navigate or reload — it only writes into the reply field on the current page.
- The reply file must exist and contain the email body (plain text; will be converted to HTML paragraphs), ideally in the standard template structure above.

## Script file

- **Path:** `.cursor/skills/sprinklr-write-reply/run.py`
- **Does:** Invokes the sprinklr-email-automation runner with `--write-reply-only --reply-file=<path>`.
