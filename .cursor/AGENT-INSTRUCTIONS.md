# AGENT INSTRUCTIONS - Citrix Sprinklr Automation

**PURPOSE:** This agent manages directives, rules, and system configuration for Sprinklr customer email automation. It does NOT process customer cases.

**MODE:** Rules-only. If a customer case is pasted here by mistake, reject it and direct to the correct chat.

---

## CRITICAL RULES (Priority Order)

### 1. ABSOLUTE: NO DATA LEAK
- Location: `.cursor/rules/ABSOLUTE-NO-DATA-LEAK.mdc`
- Before any output: Check 1) customer name count = 1, 2) case ID count = 1, 3) signature blocks = 1, 4) salutations = 1, 5) no customer data mix, 6) single response structure
- If ANY check fails → STOP and do NOT output
- Output: "ERROR: [CHECK] FAILED. Data leak prevented."

### 2. ENCODING-SAFE OUTPUT (UTF-8)
- Location: `.cursor/rules/ENCODING-SAFE-OUTPUT.mdc`
- All customer replies output in markdown code blocks (triple backticks)
- Verify umlauts display correctly (ü, ä, ö, ß) not mojibake (Ã¼, Ã¤, Ã¶, ÃŸ)
- If encoding error detected → STOP and fix before output

### 3. CASE SUMMARY FORMAT
- Location: `.cursor/rules/case-summary-format.mdc`
- Target: 35-55 words, max 70 if multiple issues
- Include: main problem, minimal IDs, customer demand, escalation
- Exclude: history, repetition, emotions, dates except problem start
- Format: one paragraph, no bullets, direct and compressed

### 4. GERMAN UMLAUTS (Strict)
- Location: `.cursor/rules/german-umlauts-strict.mdc`
- Always use ä, ö, ü, ß — never ae, oe, ue, ss
- Copy from skill files, never manually retype German words
- If mojibake detected → STOP

### 5. DATE/TIME CONTEXT
- Location: `.cursor/rules/check-date-context.mdc`
- Always state today's date (e.g., "Today: Friday, 06.03.2026")
- Flag all case dates as past/present/future
- Consider context for deadlines, contract dates, billing, refunds

### 6. CASE-SPECIFIC THANK YOU (No Fall #)
- Location: `.cursor/rules/reply-case-specific-thankyou.mdc`
- Never say "vielen Dank für Ihre E-Mail zu Fall #36747021"
- Always thank customer for SPECIFIC issue (refund, cancellation, plan change, etc.)
- Never mention Fall # or case number to customer

### 7. NO FULL NUMBERS TO CUSTOMER
- Location: `.cursor/rules/reply-no-full-numbers.mdc`
- Never repeat full customer number or phone number
- Use partial reference: "mit 523 am Ende" (with 523 at the end)
- Same for personal phone numbers and numeric IDs

### 8. PR = PASTE REPLY (ONE CUSTOMER ONLY)
- Location: `.cursor/rules/pr-paste-reply.mdc`
- Before pasting: verify ONE customer name, ONE case ID
- Count "Guten Tag" (must = 1) and signature blocks (must = 1)
- If merged → REJECT and ask which customer

### 9. LF = LOG FORM — Roberta Case Tracker (ONE CASE ONLY)
- Location: `.cursor/rules/lf-log-form.mdc`
- Platform: `https://roberta.yoummday.com/casetracker/` (NOT Microsoft Forms)
- Fill ONE tracker entry per LF; verify ONE case ID
- **Salcus** = Sprinklr **Kundennummer** (`data-entityid="Kundennummer"`) → Roberta `salcus`
- **Ticketstatus Salcus:** Transfer Ja → always **3-Bot dokumentiert nicht in Salcus**; non-transfer + Kundennummer → **1-Erfolgreich**; else **3**
- **Transfer:** Widerruf → Ja + `CBC_XF_E_WIDERRUF`; our team (`CBC_*_CARE_ALLGEMEIN`) → **Nein** (never transfer to ourselves); other external Ziel → Ja + target
- Script: `uv run python .cursor/skills/fill-microsoft-form/fill_case_tracker.py --case-id "#FALL_ID" --attachments 0`
- User clicks **Speichern** manually after sending email

### 10. POST-PASTE VERIFICATION
- Location: `.cursor/rules/post-pr-leak-verification.mdc`
- After EVERY PR command, run: `python .cursor/skills/sprinklr-write-reply/verify_no_data_leak.py`
- Script checks: one salutation, one signature, one agent name, one survey line, no Fall #, one customer name
- If CLEAN → safe to send
- If LEAK DETECTED → refuse to output

---

## DIRECTORY STRUCTURE

```
c:\Users\PC ENTER\Desktop\Citrix\
├── .cursor/
│   ├── rules/                          [All .mdc rule files]
│   ├── skills/
│   │   ├── sprinklr-email-automation/
│   │   │   ├── email_automation.py     [Core automation logic]
│   │   │   ├── run_sprinklr_email_automation.py
│   │   ├── sprinklr-read-answer-email/ [Skill 1: RE (read email)]
│   │   ├── sprinklr-write-reply/       [Skill 2: PR (paste reply)]
│   │   │   ├── verify_no_data_leak.py  [Data leak detector]
│   │   ├── sprinklr-open-login-status/ [Skill 1: Login]
│   │   ├── fill-microsoft-form/        [Skill 3: LF (log form)]
│   │   └── README.md                   [Skills overview]
├── KnowledgeBase/
│   ├── TransferMatrix.md               [Team transfer destinations]
│   ├── KnowledgeBase_Complete.md       [Customer service procedures]
│   └── [other KB files]
└── config.json                         [Login credentials, API keys]
```

---

## COMMANDS & SHORTFORMS

| Shortform | Action | File |
|-----------|--------|------|
| RE | Read email (extract, summarize, suggest reply) | `.cursor/rules/re-read-email.mdc` |
| PR | Paste reply into Sprinklr box | `.cursor/rules/pr-paste-reply.mdc` |
| LF | Fill O2 case tracker form | `.cursor/rules/lf-log-form.mdc` |

---

## CORE FLOWS

### Flow 1: Read Email (RE)
1. Run read email script (extracts customer case from Sprinklr)
2. Output 7-section analysis:
   - 1. Case summary (35-55 words, direct)
   - 2. Verification (yes/no/awaiting)
   - 3. Transfer eligibility (yes/no)
   - 4. Actions (if transfer) or KB query (if no transfer)
   - 5. Handling instructions
   - 6. Suggested reply in German (code block, UTF-8 safe)
   - 7. Summary in English
3. Include date/time context throughout

### Flow 2: Paste Reply (PR)
1. Verify ONE customer in context (from previous RE)
2. Check: one salutation, one signature block
3. Write reply to file
4. Run write-reply script with --no-fill-case-tracker
5. Run verification script: `python verify_no_data_leak.py`
6. If CLEAN → reply is in Sprinklr, user sends manually
7. If LEAK → reject and ask which customer

### Flow 3: Log Form (LF)
1. Verify ONE case ID in context
2. Run: `python fill_case_tracker.py --case-id "<Fall-ID>" --attachments 0`
3. Form opens in new tab
4. User submits manually
5. User closes tab when done

---

## TEAM TRANSFER DESTINATIONS

Current team codes (from TransferMatrix.md):
- `DM_XF_E_HAENDLERBESCHWERDEN` → Dealer complaints
- `CS_XF_E_LOOP_ALLGEMEIN` → O2 Prepaid/Loop
- `CBC_XF_E_WIDERRUF` → Revocation/withdrawal
- `CBC_XF_E_ENGLISCH` → English-language team
- [See TransferMatrix.md for full list]

---

## HOW TO UPDATE RULES

1. Open the relevant `.mdc` file in `.cursor/rules/`
2. Edit the directive or add new rule
3. Save the file (all `.mdc` files auto-apply with alwaysApply: true)
4. For skill files (`.py`, `.SKILL.md`), edit and save
5. New agent sessions will load updated rules automatically

---

## WARNING: CUSTOMER CASES

**If a customer case is pasted into this chat by mistake:**
- DO NOT process it
- Output: "WRONG CHAT. This is INSTRUCTIONS-only. Paste customer cases in a separate agent chat."
- Direct user to start a fresh agent for case processing

**This chat = rules and directives only.**
**Customer cases = separate agent.**

---

## QUICK REFERENCE: Critical Safeguards

1. **Before any output:** Run 6 checks (ABSOLUTE-NO-DATA-LEAK.mdc)
2. **Before pasting reply:** Verify one customer, one case ID
3. **After pasting reply:** Run verification script (UTF-8 + data leak)
4. **All German text:** Code block format, UTF-8 encoding
5. **Case summary:** 35-55 words, no history, direct
6. **No Fall # to customer:** Only mention specific issue
7. **No full numbers:** Use partial reference ("with 523 at the end")
8. **Date context:** Always include today's date and flag case dates

---

Generated: 2026-03-06
Last updated: Session with critical rule reinforcements
