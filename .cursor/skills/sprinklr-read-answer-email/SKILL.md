---
name: sprinklr-read-answer-email
description: Reads the current email in Sprinklr Console and prints it to output; then Cursor summarizes the entire email conversation in the chat, queries the knowledge base, and writes the suggested reply. Does not write to the browser. Use sprinklr-write-reply when the user says "reply with ...". Requires sprinklr-open-login-status first.
---

# Sprinklr: Read Email (script prints email, Cursor writes reply in chat)

The **script** only reads the current email and **prints it to stdout, then terminates**. It does **not** query the knowledge base or generate the reply. **You (Cursor)** must then **summarize the entire email conversation** in the Cursor chat, query the KnowledgeBase, and **write the suggested reply** in the chat window.

## Agent instructions (required when you run this skill)

1. **Run the skill.** The script connects to the browser (CDP 9222), extracts the customer email and **full conversation thread** from the current case, and prints **"CUSTOMER EMAIL"** plus **"COMPLETE CONVERSATION THREAD"**. Then the script exits.
2. **Summarize the entire email conversation in the Cursor chat (in English).** First provide a clear **summary of the full conversation** in **English**: who wrote what, in what order (customer vs. brand/agent), main points and requests, and current status. Use the script output as the source.
3. **Verify the customer (in English).** Check whether the email/thread contains **at least 3 key identifiers** (name, Kundennummer, Geburtsdatum, bill/invoice number, last 4 IBAN, home address, or third party with Vollmacht). **Never ask for PKK.** Output in **English**: **Customer verified: Yes** or **Customer verified: No**, and list only the verified key data found.
4. **If NOT verified:** Use **only** the premade template for unverified customers (case-specific thank you + sympathy + the fixed security text asking for last 4 IBAN and Kundennummer + tip Mein o2). Do **not** query the KnowledgeBase. Skip to step 6.
5. **If verified:** Check **Exceptions – do NOT query Knowledge Base** (name change, bill clarification, closing/thank-you email, new offer/contract/extension). If the case falls under an exception, handle as described there (e.g. hotline template for offers/contracts) and skip KB query. Otherwise: **query the KnowledgeBase** (grep/search only; never read entire files) for relevant articles and solution; advise the agent on documentation/tickets; apply the **Authentifizierung matrix** (E-Mail column, 3 Eckdaten) where relevant. Draft a **fitting reply** (e.g. confirm ticket created, case forwarded, refund initiated) based on KB and handling actions.
6. **Write the suggested reply in the chat (German customer email).** Show the **suggested email reply** text in the chat, written **in German** and following the **mandatory email reply template** (salutation mirroring contact / "Guten Tag" or "Guten Tag [Vorname Nachname],", case-specific thank you + sympathy, survey line, fixed signature block). Use this German template for unverified, verified, or exception replies.
7. **When the user says "reply with …" or "write that reply in the box"**: run the **sprinklr-write-reply** skill with a file containing the reply text.

**No reload or navigation:** The script must **not** reload the page or navigate to any URL. It only reads from the **current tab** (email content page). Run **sprinklr-open-login-status** first. The script processes the current page once (extract-only), prints the email, then exits. It does **not** write to the editor.

---

## Customer verification (mandatory before case processing)

Each customer **must be verified** in our system before proceeding with case processing. Apply this **after** you have summarized the conversation and **before** querying the KnowledgeBase or drafting a substantive reply.

### Key identifiers (at least 3 required for verification)

A customer is **verified** only if the email (or thread) contains **at least 3** of the following, clearly visible/mentioned:

- **Name** (Vorname + Nachname, or abbreviated e.g. "M. Mustername")
- **Customer number** (Kundennummer)
- **Date of birth** (Geburtsdatum)
- **Bill/invoice number** (Rechnungsnummer) or last invoice/charge details
- **Last 4 digits of IBAN**
- **Home address** (Kontaktadresse – can be partial but recognizable)
- **Third party with power of attorney (Vollmacht)** – legal guardian, representative, etc., clearly mentioned and authorized to act for the customer (in that case the third party is the verified contact)

**Never ask for PKK** (Persönliche Kundenkennzahl).

### Output in chat

All agent-facing output in the Cursor chat (summaries, explanations, verification result) must be written **in English**, even if the customer email is in German.

- Provide a clear **Yes/No** answer in English: **Customer verified: Yes** or **Customer verified: No**.
- List **only the key verified data** you found (e.g. "Name, Kundennummer, last 4 IBAN"), still described in **English**.

### If customer is NOT VERIFIED

Do **not** process the case. Use **only** the following premade template. The reply must still follow the **mandatory email reply template** (salutation, then body, then security block, then survey line, then signature block).

- **Salutation:** Per template (Guten Tag [Vorname Nachname], or "Guten Tag," if no/full name not given).
- **Body:** Issue a **case-specific thank you** to the customer, mentioning the case in the thank you; apologise and show **specific sympathy** for the customer's case and circumstances; be friendly.
- Then include **exactly** this security block:

> Um zu verhindern, dass unbefugte Dritte Ihre Kundendaten ändern oder Informationen aus Ihrem Vertrag erhalten, bearbeiten wir E-Mail-Anfragen zu Vertragsinhalten nur dann, wenn im Vorfeld bestimmte Angaben vom Anfragesteller gemacht werden.
>
> Wir versichern Ihnen, dass es sich um eine Sicherheitsmaßnahme handelt, die ausschließlich dem Schutz Ihrer persönlichen Daten dient und bitten um Ihr Verständnis für diese Vorgehensweise.
>
> Lassen Sie uns mit Ihrer Anfrage bitte noch folgende Informationen zukommen:
>
> - die letzten 4 Stellen Ihrer IBAN  
> - und Ihre Kundennummer  
>
> Senden Sie bei Rückfragen den bisherigen E-Mail-Verlauf sowie mögliche Anhänge mit und fügen Sie Ihre Antwort ganz oben ein. Dann kümmern wir uns sofort um Ihr Anliegen.
>
> Noch ein Tipp: Vieles können Sie rund um die Uhr auch direkt online unter o2.de erledigen. Ganz bequem und unabhängig von Öffnungszeiten. Registrieren Sie sich einfach für „Mein o2“.

- Then add the **survey line** and **signature block** from the mandatory email reply template (see "Email reply template" section).

**Do not query the KnowledgeBase** for unverified customers; only output the summary, verification No, and this full template (salutation + body + security block + survey line + signature).

### If customer IS VERIFIED

Proceed with **case processing** (see below). Also apply the **Authentifizierung matrix** (E-Mail column, 3-Eckdaten rule) on a case-by-case basis to decide whether the request may be handled per E-Mail or must be referred to Web/App/Hotline/Formular.

---

## Authentifizierung – Backoffice E-Mail (gültig seit 04.07.2023, Stand 14.11.2025)

Applies **only** to requests received by **E-Mail, Brief or Fax** and answered in writing. For **E-Mail**, the initial email must contain **at least 3 of these Eckdaten**:

- Vorname + Nachname (auch gekürzt)
- Kontaktadresse (erkennbar)
- Geburtsdatum
- PIN/PUK
- IBAN (erkennbar)
- MSISDN oder Festnetznummer (vollständig)
- Kundennummer (vollständig)
- Letzter Rechnungs-/Abbuchungs-Betrag
- Letztes Abbuchungsdatum
- Aktueller Tarif
- Datum letzte Vertragsverlängerung
- Umfangreiche Schilderung dokumentierter Vorgänge
- E-Mail von verifizierter E-Mail-Adresse

**Anfragen durch Dritte:** If the request obviously comes from a third party (even with Vollmacht), do **not** process in Backoffice; use text block "Datenschutz Verweis auf anderen Kanal" and refer to the appropriate hotline. PKK+OTP cannot be done in Backoffice.

**Matrix:** For each process type (Kundendaten, Tarife, Hardware, Rechnung & Zahlung, Vertrag, etc.) the matrix defines whether handling per E-Mail is **zulässig** (✓), **nur mit Kopie Ausweis/Pass**, **Web/App/Hotline**, **Formular**, or **nicht zulässig** (✗). Apply the **E-Mail** column and 3-Eckdaten rule. If fewer than 3 Eckdaten: use TBS "Alternativ Info statt PKK" (Postpaid) or "prepaid_authentifizierung_alternativ_mit_adresse_oder_geburtsdatum" (Prepaid), or refer to the channel given in the matrix. **Never ask for PKK** in E-Mail.

(Full matrix tables: see KnowledgeBase or internal Authentifizierung document for process-by-process E-Mail/Brief-Fax columns.)

---

## Email reply template (mandatory for every reply)

**Language rule:** All **customer-facing email replies** you draft must be written **in German**, regardless of whether the customer's original email was in German or another language. Agent-facing reasoning and summaries stay in English; only the customer email body is German.

**Every** suggested email reply (verified, unverified, or exception) must use this structure. Fill in the variable parts; keep the rest as given.

### Salutation

- **Mirror** how the contact signs (e.g. first name only, full name). Ideally: **"Guten Tag [Vorname Nachname],"** — use first and last name **without** Herr/Frau.
- **If no name is known**, or **only the last name** is given without (abbreviated) first name: use **"Guten Tag,"** only (no name).

### Body (after salutation)

1. A **case-specific thank you** to the customer, **mentioning the case** in the thank you.
2. **Apologise** and show **specific sympathy** for the customer's case and circumstances; be friendly.

### Survey line (before signature)

Include exactly:

> Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

### Signature block (use exactly)

```
Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski 

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz
```

**Apply this template** to: (1) unverified-customer template (after the security text and Mein o2 tip), (2) verified case-specific replies, (3) exception replies (e.g. hotline referral). Salutation + body content may vary; survey line and signature block are fixed.

---

## Case processing (when customer IS verified)

1. **Query the KnowledgeBase** (grep/search only – do not read entire files) for **relevant articles and the most likely solution** to the customer's case.
2. **Advise the customer service agent** on necessary **documentation or tickets** that need to be filled out (e.g. which form, which ticket type).
3. **Create a fitting reply** for the customer that:
   - **Uses the mandatory email reply template** (salutation, case-specific thank you + sympathy, survey line, signature block),
   - Reflects **specific handling actions** (e.g. ticket created, case forwarded, refund initiated, document sent),
   - Follows **KnowledgeBase instructions and guidelines** for that type of case,
   - Is case-specific (confirm what was done or what will happen next).

---

## Exceptions – do NOT query the Knowledge Base

In the following situations, **do not query the KnowledgeBase** for solution articles. Handle as below. **This list may be updated by user instruction** – add or change exceptions as instructed.

1. **Customer wishes to update their name** – Handle according to Authentifizierung matrix (typically Web/App/Schriftweg with Kopie Ausweis/Pass); do not query KB for general solution.
2. **Customer wishes clarification on their bill** (specific cost positions, extraordinary costs, etc.) – Handle per matrix; do not query KB.
3. **Customer sends a final, positive acknowledgment** (thank you, closing email, satisfaction confirmation) – Reply with a short, friendly closing; no KB query needed.
4. **Customer wishes new offer, new contract, or contract extension** – Backoffice E-Mail team does **not** handle sales, offers, or contract extensions. Use **only** the following approach:
   - Issue a **case-specific thank you**, mentioning the case.
   - Be **apologetic**, and inform the customer that due to data safety regulation the email team does **not** handle promotions, offers or actions for new contracts and extensions.
   - Say that for that it would be best to contact the **care hotline**, where the contract specialist team can help: **089 78 79 79 400**.
   - Be kind and friendly.

---

## Single-shot behavior

1. Connect to the browser Skill 1 left open (CDP port 9222). **Do not reload the page or navigate to any URL.**
2. Use **only the current tab** as-is. **Must be on the email content page** (case/Fall #... open).
3. Extract case ID and email (subject, from, body) from the current page. **Print** the customer email to stdout, then **exit**.
4. **Cursor:** Read the printed email and full conversation thread, **summarize the entire email conversation** in the Cursor chat, query KnowledgeBase (via grep/search), then write the suggested reply in the chat.

If the user is on the console list (no case open), the script asks them to open a case and run again.

## How to invoke

```powershell
uv run python .cursor/skills/sprinklr-read-answer-email/run.py
```

The script runs with **`--process-current-only --extract-only`**: reads the email and full thread, prints them, then stops. You must then: (1) **summarize the entire email conversation** in the Cursor chat, (2) query the KnowledgeBase (grep/search), (3) write the suggested reply in the chat. To put that reply into the Sprinklr reply box, use **sprinklr-write-reply** with a file containing the reply.

## UI mapping (Sprinklr)

- **Case ID:** `h2` containing "Fall #" and the case number.
- **Conversation:** `[data-testid="inboundChatConversationItemFanMessage"]`, `[data-testid="inboundChatConversationItemBrandMessage"]`; body in `[data-testid="html-message-content"]`.
- **Reply box** (used by sprinklr-write-reply, not this skill): `section[aria-label="Nachricht verfassen"]`, `[data-testid="baseEditorContainer"]`, TinyMCE iframe `body#tinymce`.

## Script file

- **Path:** `.cursor/skills/sprinklr-read-answer-email/run.py`
- **Does:** Invokes the runner with **`--process-current-only --extract-only`**. Script prints the customer email and full conversation thread and exits; **Cursor** summarizes the entire conversation in the chat, queries KnowledgeBase (grep/search), and writes the suggested reply in the chat.

## Knowledge base

**You (Cursor)** draft the reply using **KnowledgeBase/** at repo root. The files there (e.g. **KnowledgeBase_Complete.md**, **TransferMatrix_KnowledgeBase.md**) are **extremely long (millions of lines)**. You must **never read an entire KnowledgeBase file**. Instead: **grep or search** for keywords/phrases from the customer email (e.g. Rückerstattung, refund, Kündigung, transfer, Rechnung, IBAN, Kundennummer, specific product names) and read only the **matching lines or surrounding context**. Use the search results to draft and cite the reply.
