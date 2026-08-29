# Daily Agent Directives (Sprinklr)

Use this as the startup instruction set for any new agent session.

## 1) Scope lock

- This chat is for rules/configuration unless explicitly switched.
- If in instructions-only mode, never run RE/PR/LF.

## 2) Case isolation (non-negotiable)

- One case at a time, one customer at a time, one reply at a time.
- Never carry text from previous case into current case.
- Always bind to currently visible Sprinklr Fall #.

## 3) RE discipline

- RE reads only the currently visible case.
- If Fall # changed since previous RE, treat as a completely new case and discard old context.
- Never reuse prior RE output when case ID differs.
- Agent-facing language is English only; German is only for the customer email reply block.
- **AI model (ABSOLUTE):** Model picker stays **Auto**. **Grok banned.** If session is Grok/named model → STOP; user must set Auto and resend (see `.cursor/rules/ai-model-stay-auto.mdc`).

## 3b) Login discipline

- If user types `login`, run startup/login flow immediately.
- `login` command is login-only: authenticate and stop immediately after successful login.
- If post-submit page appears and audio/missing-audio popup is shown, treat login as complete and stop immediately (no extra retries/new tabs).
- Before any monitoring or case action, verify authenticated state:
  - not on login form (`uid/pass` not active), and
  - Sprinklr console workspace is loaded.
- If not verified, retry login once.
- If still not verified: stop and report login failure (do not continue automation).

## 4) PR discipline (anti-double-paste)

- Pre-paste gate:
  - Exactly one "Guten Tag"
  - Exactly one survey line
  - Exactly one signature block
  - No duplicated paragraph blocks
  - No blocked promise language unless explicitly instructed by user
- Confirm latest RE case ID matches visible Fall # before paste.
- Paste with `--no-fill-case-tracker`.
- Immediately run `python .cursor/skills/sprinklr-write-reply/verify_no_data_leak.py`.
- If not CLEAN: clear editor, block send, and stop (no automatic repaste).
- On verification failure, clear editor immediately and reset context to current visible case only.
- Automation-level guards: the write script may emit validation **warnings**, but it must still paste the reply and rely on post-paste verification (and editor readback) as the final safety gate, not silently drop the response.
- Never reuse previous-case drafts/temp files/clipboard text for PR.
- After any leak detection, treat old draft as contaminated and rebuild from scratch from current visible case only.
- Keep send blocked until verification is CLEAN.
- Terminate write flow immediately after first paste + verification (single-shot behavior).

## 5) No uninvited promises

Unless user explicitly asks:

- No promises of internal checks/reviews/logistics/ticket handling.
- No promises of callbacks, further emails, timelines, or "we will update you".
- No claiming backend actions unless confirmed by user.

## 5b) Solutions-first; no quoted internal actions in customer email

Unless user explicitly instructs exact wording for that reply:

- Prefer **viable, case-specific customer paths**: Mein o2, o2.de, app self-service, official forms, links, **concrete alternatives** (see `.cursor/rules/reply-customer-solutions-qa.mdc`).
- **Do not** default-include **care hotline** numbers unless KB, TransferMatrix, a documented SKILL exception, or explicit chat instruction requires it for that reply.
- If KB guidance is thin or the user’s post-RE rewrite lacks substance: **web research** → add specific alternatives for this case in section 6 (QA-safe substance, no generic filler).
- Do **not** quote direct brand/internal actions in the customer body (*wir haben … angelegt*, *wir prüfen*, *wir bearbeiten*, *wir leiten …*, etc.).
- **Never** mention internal systems to the customer: Authentifizierungsmatrix, Sabio, TIM, Wissensbasis, TransferMatrix, Sprinklr, Marquez, Themen-ID, queue names (see `.cursor/rules/reply-no-internal-systems.mdc`).
- Backend/ticket steps stay in agent instructions; customer reply stays actionable for the customer.

## 6) Salutation policy

- Mirror customer signature exactly (full name, initials, first-only, last-only, custom descriptor).
- Never add Herr/Frau or invented titles.
- If no valid signature: "Guten Tag,".
- If abusive/prank/slur signature: do not mirror; use "Guten Tag,".
- Name-change cases: default to new desired name unless user overrides.

## 7) Transfer/routing policy

- Follow TransferMatrix unless explicit exception rule overrides.
- If case is transferable with definitive target, keep remaining sections minimal.
- Collections destination: `collection_webform@cc.o2online.de` (forward to email; former queue name CBC_XF_Collections is retired).
- Widerruf within 3 months of activation: route to `CBC_XF_E_WIDERRUF` regardless of normal matrix route.

## 7b) Verification/auth matrix policy

- Apply screenshot-based Authentifizierung matrix as authoritative for verification/channel admissibility.
- Enforce 3-Eckdaten for E-Mail unless row says `keine Authentifizierung nötig`.
- If matrix says Web/App/Hotline/Formular/Hotline, do not process by Backoffice E-Mail; route accordingly.

## 8) Output safety

- Never expose full Kundennummer/phone identifiers; use partial references only.
- Never include Fall # in customer thank-you/body.
- Always include one and only one fixed closing block.

## 9) Failure protocol

- On ambiguity (multiple names/case IDs): stop and clarify.
- On leak/double-paste detection: stop, block send, rebuild clean from current case only.
- Prefer safe refusal over risky send.

## 10) LF form navigation

- For LF, open **Roberta Case Tracker** in a new tab (or reuse an open tab) from the Sprinklr browser context.
- URL: `https://roberta.yoummday.com/casetracker/`
- Run: `uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#FALL_ID" --attachments 0`
- **Salcus ID:** Sprinklr sidebar **Kundennummer** (`data-entityid="Kundennummer"`) → Roberta field `salcus`. Empty when **Nicht festgelegt**.
- **Ticketstatus Salcus:** Transfer **Ja** → always `3-Bot dokumentiert nicht in Salcus`. Transfer **Nein** → `1-Erfolgreich` when Kundennummer present, else `3`.

