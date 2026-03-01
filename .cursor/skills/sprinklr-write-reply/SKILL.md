---
name: sprinklr-write-reply
description: Writes the suggested email reply into the Sprinklr reply box. Clears any existing content in the editor (section "Nachricht verfassen", TinyMCE body), then writes the reply text from a file. Use when the user says "reply with ..." or "write the reply in the box" after Skill 2 has shown the suggested email in chat.
---

# Sprinklr: Write Reply to Editor

**When to use:** After running **sprinklr-read-answer-email** (Skill 2), the suggested reply is shown in the chat only. When the user says **"reply with …"** or **"write that reply in the box"**, run this skill to clear the reply box and write the suggested email into the browser editor.

## What this skill does

1. Connects to the browser (CDP port 9222). **Does not reload the page or navigate to any URL** — uses the current tab as-is. Skill 1 must have been run and the email case must be open.
2. Finds the reply area on the **current page**: `section[aria-label="Nachricht verfassen"]` and the TinyMCE editor inside `[data-testid="baseEditorContainer"]`.
3. **Preformats** the reply text from the file: normalizes line endings, trims each line, and enforces consistent paragraph spacing (one blank line between paragraphs, no leading/trailing blank lines) so the email displays correctly in the editor.
4. **Clears** all existing content in the editor (including placeholder like `[Antwort]` and signature blocks).
5. **Writes** the preformatted reply into the editor (plain text is converted to HTML paragraphs for TinyMCE).
6. **Waits for send and auto-reads the next email (extract-only).** After the reply is written, the automation waits until you send the email (return to Console / case leaves the list). Then it continuously checks the Console for the **next new email**, opens that new case once, and prints the **customer email + full conversation thread** in the same extract-only format as Skill 2 (`sprinklr-read-answer-email`). Cursor then summarizes that new case in English and drafts the German reply for you.

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
2. Write that reply text to a temporary file (e.g. in the repo or temp directory).
3. Run this skill with the path to that file:  
   `uv run python .cursor/skills/sprinklr-write-reply/run.py <path-to-file>`
4. After the script runs, the reply box in Sprinklr will contain the text; the user can edit and send.

## Reply content (standard template)

The reply file should follow the **standard email reply template** (defined in **sprinklr-read-answer-email**): salutation (Guten Tag [Vorname Nachname], or "Guten Tag," if no/full name), case-specific thank you + sympathy, survey line about Zufriedenheitsbefragung, then the fixed signature block (Freundliche Grüße, Ihr o2 Kundenbetreuer, Lukasz Kowalski, Telefónica block, Umweltschutz, Pflichtangaben, Fußnote). When drafting the reply in Skill 2, Cursor uses that template; the file passed here should already contain the full text in that structure.

## Requirements

- Skill 1 (sprinklr-open-login-status) must have been run (browser open and logged in).
- An email case (Fall #…) must **already be open** in the current tab; the script does **not** navigate or reload — it only writes into the reply field on the current page.
- The reply file must exist and contain the email body (plain text; will be converted to HTML paragraphs), ideally in the standard template structure above.

## Script file

- **Path:** `.cursor/skills/sprinklr-write-reply/run.py`
- **Does:** Invokes the sprinklr-email-automation runner with `--write-reply-only --reply-file=<path>`.
