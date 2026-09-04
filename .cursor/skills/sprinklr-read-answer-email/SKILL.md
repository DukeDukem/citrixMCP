---
name: sprinklr-read-answer-email
description: Reads the current email in Sprinklr Console and prints it to output; then Cursor summarizes the entire email conversation in the chat, queries the knowledge base, and writes the suggested reply. Does not write to the browser. Use sprinklr-write-reply when the user says "reply with ...". Requires sprinklr-open-login-status first.
---

# Sprinklr: Read Email (script prints email, Cursor writes reply in chat)

**Chat scope:** **Email processing agent chat only** (`EMAIL-PROCESSING-AGENT.md`). Instructions dashboard does not run RE or produce live 7-step output.

**Shorthand:** The user may type **RE** instead of "read email". Treat **RE** the same as "read email" and run this skill (invoke the script and then follow all agent instructions below).

---

## CRITICAL: Always stick to the processing form

**You must ALWAYS, AT ALL TIMES, stick to the given processing form in the chat with the user.** Do not skip sections. Do not reorder sections. Do not merge sections or substitute a different structure. Follow the mandatory output structure (sections 1–7), verification rules, and case-processing flow defined in this skill exactly. Any reply to the user when handling a read-email case must use this form—no exceptions.

## CRITICAL: AI model stays on Auto (Grok banned)

**ABSOLUTE:** Cursor model picker must stay **Auto**. Never switch to **Grok** or any named model.

**If this session is Grok / named model:** Do **not** run the read-email script. Do **not** draft section 1–7. Output:

`ERROR: MODEL NOT AUTO (GROK/NAMED MODEL DETECTED). Set the Cursor model picker to Auto, then resend your command.`

See `.cursor/rules/ai-model-stay-auto.mdc`.

---

The **script** only reads the current email and **prints it to stdout, then terminates**. It does **not** query the knowledge base or generate the reply. **You (Cursor)** must then follow the **mandatory output structure** below and **write the suggested reply** in the chat window.

---

## Mandatory output structure (follow exactly, in order)

You **must** output the following sections in this order. Do not occlude or merge sections. (Steps 5 and 6 are combined: one "Instructions on handling case" section.)

| # | Section | Content |
|---|---------|--------|
| **1** | **Customer case summary** | **Target: 35–50 words, hard max 60.** Ultra-easy to scan: Fall # + name, **one concrete problem** (no vague “issue”), **what they want now**. Optional: **one** short clause on prior o2/brand only if it changes understanding; optional one-line date/deadline if it matters. **No** thread chronology, filler, emotions, or process narration. One paragraph, no bullets. Follow `.cursor/rules/case-summary-format.mdc`. |
| **2** | **Verification** | **Customer verified: Yes**, **Customer verified: No**, or **Awaiting manual verification by user**. If Yes, list verified key data. If Awaiting manual verification, list the 2 identifiers found (and state that neither is the Von: email). Never ask for PKK. |
| **3** | **Transfer eligibility** | **If verified:** Query **KnowledgeBase/TransferMatrix.md** (unless an explicit exception overrides this). Identify Thema and Fall; state Ziel-Kontakt. **Transfer eligible: Yes** (case goes to another team/queue/email) or **Transfer eligible: No** (we handle directly or Kein Transfer). |
| **4a** | **Transfer goal (if transferable)** | If Transfer eligible = Yes: state **Transfer goal** (queue/team name or email) and action (e.g. "Transfer in Sprinklr" or "Forward to email"). **Once a case is clearly transfer-eligible with a definitive transfer goal, you may treat the routing decision as final and keep the remaining sections extremely short (no further KB queries or detailed handling beyond confirming the transfer).** |
| **4b** | **If not transferable** | If Transfer eligible = No: **query the KnowledgeBase** (grep/search; never read entire files) for relevant handling. Skip 4a. |
| **5** | **Instructions on handling case** | KB-based + agent steps in one section: which path, ticket type/Themen-ID, inbox, Buchungsgrund, or "direct customer to X"; what to do in Sprinklr/systems (create ticket, transfer, write reply, no promise of Y). Cite KB where relevant. Numbered or bulleted. **If the case is transfer-eligible with a definitive transfer goal, this section can be reduced to a single, clear instruction (e.g. "Transfer case in Sprinklr to \<Queue\> and do not process further").** |
| **6** | **Your response to customer** | **Full** suggested email reply in **German**, copyable block: salutation, body (template), survey line, signature block. Do not truncate. **If the case is transfer-eligible with a definitive transfer goal, the body can be minimal and only inform the customer that their concern has been forwarded to the responsible team, without additional substantive processing.** |
| **7** | **Summary of response** | One short paragraph in English: what the reply says and what the agent/customer should do next. **For transfer-eligible cases with a definitive transfer goal, this can be a one-sentence note that the case was routed to \<Queue\> and no further Backoffice handling is performed.** |

If customer is **not verified**: do steps 1, 2, then skip transfer matrix; use unverified template only (security block + Mein o2 tip); output section 5 briefly (no KB query for substantive case), then 6 (full template) and 7. If **awaiting manual verification** (2-of-3 exception): do steps 1–7 as if verified, but set verification status to "Awaiting manual verification by user" and add the follow-up instruction (see below).

---

## Agent instructions (required when you run this skill)

**Always stick to the processing form:** When you run this skill or respond to the user about a read-email case, you must use the mandatory output structure (sections 1–7) and the verification/case-processing flow defined here. Do not deviate, skip, or reorder. **Do not show or require any "accept", "approve", or similar confirmation pop-ups during the RE output flow; all steps must be executed automatically unless the user explicitly interrupts or overrides them.**

1. **Run the skill.** User types **RE**. After **login**, first RE is **`--once`** (open-case extract). After **PR LF**, use **`run.py --arm`** (Anwenden). After **LF TR**, use **`run.py --arm-weiter`** (exact **Weiter** only, step 4/4). Default `run.py` consumes **`FIRST_RE_ONCE_PENDING`** when set. You output sections 1–7. Hook plays sound when section 7 is in your reply (or user types **`sound`**).
2. **After script output**, output sections 1–7 in order (see Mandatory output structure). Use the script output as the source for section 1. **Include date/time context in section 1.**
3. **Verification (section 2):** At least 3 key identifiers (name, Kundennummer, Geburtsdatum, bill/invoice number, last 4 IBAN, home address, or third party with Vollmacht). **Never ask for PKK.** Apply the **2-of-3 exception** (see below) when exactly 2 identifiers are present and neither is the Von: (From:) email address.
4. **If NOT verified:** Use **only** the premade template for unverified customers (case-specific thank you + sympathy + the fixed security text asking for last 4 IBAN and Kundennummer + tip Mein o2). Do **not** query the KnowledgeBase for substantive handling. Output section 5 briefly, then 6 (full template) and 7.
5. **If verified** or **Awaiting manual verification:** Query **TransferMatrix.md** (section 3). If **Transfer eligible: Yes** → section 4a (transfer goal and action). If **Transfer eligible: No** → section 4b (query KB for handling). Then **Exceptions** and **Standard premade** as usual. Fill 5 (instructions), draft **case-specific** reply (6), summary (7). For **Awaiting manual verification**, state in section 2 and in section 7 that the user must manually verify; if they confirm verified, use the drafted reply; if they say unverified, reply with the **standard verification inquiry email** (unverified template with security block + Mein o2).
6. **Section 6** must always show the **full** suggested email reply in German (complete, copyable block). **Section 7** must summarize in English what the reply does and next steps.
7. **When the user says "reply with …" or "write that reply in the box"**: run the **sprinklr-write-reply** skill with a file containing the reply text.

**Iterations and case specificity:** Premade responses (unverified template, router/Schadensersatz, etc.) may be **adapted** to the case. During RE output, **draft the full customer response autonomously** unless the user explicitly overrides.

7. **When section 7 (Summary of response) is complete**, audio plays via project hook (`.cursor/hooks/re_complete_sound_hook.py`) if **`RE_PENDING_SOUND`** was set. Manual: **`sound`** or `re_complete_sound.py --play`.
8. **After both PR and LF succeed** (**PR LF**, non-transfer): **immediately** run **`run.py --arm`** (Anwenden). Do not wait for typed **RE**.
9. **LF TR** (transfer, no PR): Transfer Ja LF, then **immediately** run **`run.py --arm-weiter`**. User clicks Transfer → Weiterleiten → Weiteleiten → exact **Weiter** (4/4 only). Never swap arms with PR LF.

**No reload or navigation:** Script reads the **current tab** only. Run **login** first. Script does **not** write to the editor.

---

## Customer verification (mandatory before case processing)

Each customer **must be verified** in our system before proceeding with case processing. Apply this **after** you have summarized the conversation and **before** querying the KnowledgeBase or drafting a substantive reply.

### Key identifiers (at least 3 required for verification)

A customer is **verified** only if the email (or thread) contains **at least 3** of the following, clearly visible/mentioned:

- **Name** – **full name** required: Vorname + Nachname (or abbreviated e.g. "M. Mustername"). First name only or last name only does **not** count as a valid identifier.
- **Customer number** (Kundennummer)
- **Date of birth** (Geburtsdatum)
- **Bill/invoice number** (Rechnungsnummer) or last invoice/charge details
- **Last 4 digits of IBAN**
- **Home address** (Kontaktadresse – can be partial but recognizable)
- **Phone number** (**MSISDN / Rufnummer / Telefonnummer**, mobile or landline)
- **Third party with power of attorney (Vollmacht)** – legal guardian, representative, etc., clearly mentioned and authorized to act for the customer (in that case the third party is the verified contact)

**Never ask for PKK** (Persönliche Kundenkennzahl).

### Alternative: Sender email matches account in Marquez

The customer can **also** be considered **verified** if the **sender email address matches the customer account in the Marquez program** (even when fewer than 3 key identifiers appear in the email text). The agent currently has **no access** to Marquez; permissions may be granted in the near future so the agent can perform this check. Until then, if the **user or an internal process confirms** that the sender email matches the account in Marquez, treat the customer as **verified** and proceed with case processing (query KnowledgeBase if applicable, draft substantive reply). When documenting verification in chat, you may state: **Customer verified: Yes** (e.g. "Name, Kundennummer; sender email confirmed as matching account in Marquez").

### Exception: 2 of 3 identifiers (awaiting manual verification by user)

If the customer has **exactly 2** of the key identifiers listed above (name, Kundennummer, Geburtsdatum, bill/invoice number, last 4 IBAN, home address, mobile/landline phone number, Vollmacht), **and neither of those 2 is the email address shown in the "Von:" (From:) field** of the email you read:

- Set verification status to: **Awaiting manual verification by user**. This signals that **you** (the user) must manually verify the customer (e.g. in Marquez or your systems).
- **Proceed with case and email processing as if the customer were verified**: query TransferMatrix, query KnowledgeBase, determine transfer eligibility, draft the **case-specific reply** (section 6), and fill sections 3–5 and 7 as usual.
- In section 2, output: **Awaiting manual verification by user.** List the 2 identifiers found and state that neither is the Von: email.
- In section 7 (summary), add: **You must manually verify this customer.** If you confirm they are verified, use the case-specific reply above (or say "reply with this"). If you find them unverified, instruct the agent to **reply with the standard verification inquiry email** (the same unverified-customer template: case-specific thank you + sympathy, then the security block asking for last 4 IBAN and Kundennummer, then Mein o2 tip, survey line, signature).

So: with **Awaiting manual verification**, the agent always produces a **case-specific draft reply**. You then either approve it (reply with this) or reject verification and ask for the **standard verification inquiry** (unverified template).

### Output in chat

All agent-facing output in the Cursor chat (summaries, explanations, verification result) must be written **in English**, even if the customer email is in German.

- Provide a clear status in English: **Customer verified: Yes**, **Customer verified: No**, or **Awaiting manual verification by user**.
- If Yes: list the key verified data you found (e.g. "Name, Kundennummer, last 4 IBAN"), in **English**.
- If Awaiting manual verification: list the **2** identifiers found and state that neither is the Von: (From:) email address.

### If customer is NOT VERIFIED

Do **not** process the case. Use **only** the following premade template. The reply must still follow the **mandatory email reply template** (salutation, then body, then security block, then survey line, then signature block).

- **Salutation:** Per template (Guten Tag [Vorname Nachname], or "Guten Tag," if no/full name not given).
- **Body:** Issue a **case-specific thank you** to the customer, mentioning the case in the thank you; show **specific sympathy** for the customer's case and circumstances; be friendly. Add an apology only if contextually necessary (clear inconvenience/error/delay caused by us).
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

### If customer is AWAITING MANUAL VERIFICATION (2-of-3 exception)

Proceed with **case processing exactly as if the customer were verified**: query TransferMatrix, query KnowledgeBase, fill sections 3–5, and draft the **full case-specific reply** (section 6) and summary (section 7). In addition:

- In section 2, output **Awaiting manual verification by user** and list the 2 identifiers (and that neither is the Von: email).
- In section 7, add: **Manual verification required.** If you confirm the customer is verified, use the case-specific reply above (e.g. "reply with this"). If you find the customer unverified, instruct the agent to **reply with the standard verification inquiry email** (unverified template: case-specific thank you + sympathy, then the fixed security block asking for last 4 IBAN and Kundennummer, Mein o2 tip, survey line, signature).

---

## Authentifizierung – Backoffice E-Mail (gültig seit 04.07.2023, matrix-basierter Stand aus bereitgestellten Screenshots)

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

### Matrix-first enforcement (from provided screenshots)

Treat the provided Authentifizierung matrix screenshots as authoritative process guidance. Apply them in this order:

1. Check if process is **keine Authentifizierung nötig** for the relevant channel.
2. Otherwise apply **3-Eckdaten rule** for E-Mail.
3. Then apply exact channel/result from matrix row:
   - `✓` = handling allowed in that channel
   - `nur mit Kopie Ausweis/Pass` = only allowed with ID/pass copy
   - `Web/App/Hotline` or `Hotline` or `Web` or `Formular` = do not process in Backoffice E-Mail; route customer accordingly
   - `✗` = not allowed; route to allowed channel

### Process-specific matrix snapshot (from screenshots)

- **1. Kundendaten (persönlich):**
  - Änderung Name -> Web/App (mit Kopie Ausweis/Pass)
  - Änderung Geburtsdatum -> Schriftweg (mit Kopie Ausweis/Pass)
  - Änderung Kontakt-/Rechnungsadresse -> E-Mail: Web/App/Hotline
  - Änderung Kontakt-E-Mail-Adresse -> Web/App/Hotline
  - Bankverbindung auf Dritte ändern -> Formular
  - Kundeneinwilligung einrichten/ändern -> E-Mail: Web/App/Hotline
  - Kundeneinwilligung löschen -> E-Mail: ✓
  - Telefonbucheintrag anlegen/ändern/auf Dritte ändern/Inverssuche freischalten -> Formular
  - Telefonbucheintrag löschen / Inverssuche widersprechen -> E-Mail: ✓

- **2. Kundendaten (vertragsbezogen):**
  - Accounttrennung/-zusammenlegung -> Hotline
  - Vertragsübernahme Postpaid -> Web
  - FSK-Einstellungen ändern -> Hotline
  - PKK-Änderung -> Formular (mit Kopie Ausweis/Pass)
  - PKK-Versand per Ticket -> keine Authentifizierung nötig
  - PIN/PUK-Auskunft -> E-Mail: Web/App/Hotline
  - Herausgabe Festnetz-Zugangsdaten oder MAC-Adresse -> E-Mail: Hotline
  - Änderung MAC-Adresse / Auskunft Vertragslaufzeit / Versand Vertragsdokumente an Kontaktadresse -> E-Mail: ✓

- **3. Tarife & Optionen:** Allgemeine Fragen -> keine Authentifizierung nötig; gezeigte Änderungsprozesse -> E-Mail: ✓

- **4. Hardware:**
  - Allgemeine Fragen / Störung erfassen / Technikertermin -> keine Authentifizierung nötig
  - Entsperrung/Teilsperrung, Multicard/Datacard deaktivieren, Multicard-Einstellungen ändern -> Web/App/Hotline
  - Reparatur beauftragen, Retouren-Erfassung, vollständige SIM-Sperre, Teilsperrung SIM -> E-Mail: ✓

- **5. Rechnung & Zahlung:**
  - Fragen zur Rechnung **mit** Nennung von Verkehrsdaten in Antwort -> E-Mail: Web/App/Hotline (Brief/Fax: ✗)
  - EVN einrichten/ändern -> Web/App
  - Rechnungsduplikat abweichende Adresse -> Hotline
  - übrige gezeigte Zeilen (z. B. Rechnungsart ändern, Umbuchung, offene Posten, Mahnstatus) -> E-Mail: ✓

- **6. Vertrag:**
  - Reaktivierung -> E-Mail: Hotline (Brief/Fax nur mit Kopie Ausweis/Pass)
  - Rufnummernportierung Import zu uns -> Web/App (NettoKOM/Ay Yildiz teils Formular)
  - Rufnummernportierung Export -> Hotline
  - Rufnummerntausch -> Web/App/Hotline
  - Kündigung sowie Storno/Widerruf Neuvetrag oder VVL -> keine Authentifizierung nötig

- **7. Vermarktung:**
  - Hardware-Bestellung abweichende Lieferadresse -> Web/App/Hotline
  - VVL mit Hardware an abweichende Lieferadresse -> Hotline
  - Verkaufsprozess Neukunden -> keine Authentifizierung nötig
  - Bestandskunden-Verkaufsprozess mit Versand an abweichende Lieferadresse -> Hotline

- **8. Prepaid:**
  - Prepaid-Aufladung per Voucher-Code -> keine Authentifizierung nötig
  - Prepaid Registrierung Express-Aufladung -> E-Mail: Web
  - Vertragsübernahme Prepaid / Rücksetzung Prepaid-Registrierungsdaten -> E-Mail: ✓ (gemäß Matrixhinweis)
  - Auskunft Prepaid-Aufladungen -> E-Mail: Web/App/Hotline

---

## Email reply template (mandatory for every reply)

**Language rule:** All **customer-facing email replies** you draft must be written **in German**, regardless of whether the customer's original email was in German or another language. Agent-facing reasoning and summaries stay in English; only the customer email body is German.

**Every** suggested email reply (verified, unverified, or exception) must use this structure. Fill in the variable parts; keep the rest as given.

### Salutation

- **Absolute mirroring rule:** Always **mirror exactly how the customer signs their email**, without adding titles such as Herr/Frau or any other form of address that does not appear in the customer’s signature.
- **Signature variants (examples):**
  - If the customer signs with **full name** (e.g. `Viktoria Anaya`), use **"Guten Tag Viktoria Anaya,"**.
  - If the customer signs with **initial + last name** (e.g. `M. Beispielname`), use **"Guten Tag M. Beispielname,"**.
  - If the customer signs with **first name only** (e.g. `Viktoria`), use **"Guten Tag Viktoria,"**.
  - If the customer signs with **last name only** (e.g. `Beispielname`), use **"Guten Tag Beispielname,"**.
  - If the customer signs with any **custom/self-chosen title or description** (e.g. "The supreme queen of England, ruler of the universe"), you must address them using exactly that wording in the salutation (e.g. **"Guten Tag The supreme queen of England, ruler of the universe,"**).
- **Exception for prank/derogatory signatures:** If the signature clearly contains **slurs, insults, hate speech, or obviously abusive/prank wording** directed at the agent, the brand, or third parties, **do not mirror that wording**. In those cases, fall back to a neutral salutation: **"Guten Tag,"** (no name), even if a “name” is technically present.
- **No signature present:** If there is **no recognizable signature or name** at the end of the email, use **"Guten Tag,"** only (no name).
- **Name change (Namensänderung):** Whenever the case involves a **customer request to change their name on the account**, you must **by default address the customer with the new, desired name** in the salutation and body, but still formatted according to the mirroring rule above (e.g. if they sign as `Malik Bieliauskas` use "Guten Tag Malik Bieliauskas,"; if they sign as `Malik`, use "Guten Tag Malik,"). Only deviate from this if the user explicitly instructs you in chat to do otherwise for that specific case.

### Body (after salutation)

1. **A case-specific thank you** to the customer, **mentioning the case meaningfully** in the thank you.
   - **CRITICAL:** The thank you must be **specific to the customer's individual concern**, not generic.
   - **NEVER use:** 
     - Generic lines like *"vielen Dank für Ihre E-Mail zu Fall #36747021"* or *"thank you for contacting us about your case"*
     - **NEVER include "Fall #" in the thank you** — do not mention the case number to the customer
   - **DO use:** A personalized thank you that reflects the **specific issue** (e.g. *"vielen Dank, dass Sie uns auf die fehlende Gutschrift aufmerksam gemacht haben"* / "thank you for bringing the missing refund to our attention" or *"vielen Dank für Ihre Geduld bezüglich der Verzögerung bei der Bearbeitung Ihrer Kündigung"* / "thank you for your patience as we process your cancellation").
2. Show **specific sympathy** for the customer's case and circumstances; be friendly. Add an apology only if contextually necessary (clear inconvenience/error/delay caused by us).

**Repeating numbers to the customer (data protection):** When you need to repeat the customer number (Kundennummer), phone number, or similar identifiers back to the customer in the email reply, **never write the full number**. Use only a short partial reference, e.g. *"mit 523 am Ende"* / *"with 523 at the end"* for customer number 6030029523, or *"mit … am Ende"* / *"ending in …"* for a phone number. Same rule for the customer's personal phone number or any other long numeric identifier. This reduces risk of misuse if the email is read by third parties.

### No uninvited promises (default — strict)

**Unless the chat user explicitly instructs you** to include specific wording for that reply:

- **Do not** promise or imply **internal checks, reviews, investigations, ticket handling, logistics checks, or “we will look into it”** in the customer email (e.g. avoid *wir prüfen*, *wir werden prüfen*, *Logistikprüfung* as a promise of outcome, *wir kümmern uns darum* as a commitment to future processing).
- **Do not** promise **another message, callback, email, Rückmeldung, update, or timeline** (e.g. avoid *Sie hören von uns*, *Sie erhalten eine Rückmeldung*, *in Kürze*, *bald*, *innerhalb von X Tagen*, *Bearbeitungsfrist*, *wir melden uns*).
- **Do not** promise **processing steps** the agent has not been told to state as fact (*Ticket wurde angelegt* only if the chat user confirmed that; otherwise describe receipt of the concern neutrally without guaranteeing backend action).

**Allowed without special instruction:** thank you, sympathy, **factual routing** already done (*Ihr Anliegen wurde an … weitergeleitet* if true), **requests for documents** (IBAN, Kundennummer), **links/hotline numbers only where KB, TransferMatrix, or a documented exception below explicitly requires hotline referral in the customer email**, and the **fixed survey + signature block**.

**Solutions, self-service, alternatives (default customer body):** Prefer **case-specific actionable paths** — **Mein o2**, **o2.de**, app self-service, official forms, links, and **concrete alternatives** — so the customer can progress without vague internal processing language. **Do not** paste care hotline numbers by default. Follow `.cursor/rules/reply-customer-solutions-qa.mdc`.

**When KB is thin or chat-user rewrite instructions lack substance:** Use **web search** (official o2/Telefónica pages, help content, reputable forums) to find **viable, issue-specific** self-service or alternative steps; include **1–3** in section 6 where they genuinely help. Goal: **QA-safe, substantive replies** that reduce bounce-backs and speed workflow.

**No quoted internal actions in the customer email (unless chat user instructs):** Do **not** state what **we** are doing or will do internally (tickets opened, checks running, cases forwarded as a commitment, “we will process…”) unless the chat user **explicitly** tells you to include those exact statements for this reply. Agent-facing instructions (sections 4–5) may still describe backend steps; the **customer-facing section 6** stays solution- and self-service-oriented by default.

**No internal systems in the customer email (hard rule):** Never mention **Authentifizierungsmatrix**, **Sabio**, **TIM**, **Wissensbasis**, TransferMatrix, Sprinklr, Marquez, Themen-ID, or internal queue names in section 6. Follow `.cursor/rules/reply-no-internal-systems.mdc`. Agent sections may use those names; the customer reply must not.

**Premade templates in this skill:** If a template sentence **conflicts** with this rule, **adapt or omit** that sentence unless the chat user explicitly tells you to keep it.

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

**Apply this template** to: (1) unverified-customer template (after the security text and Mein o2 tip), (2) verified case-specific replies, (3) exception replies **only when KB, matrix, or a documented exception below requires hotline or channel wording in the customer email**. Salutation + body content may vary; survey line and signature block are fixed.

---

## Case processing (when customer IS verified)

1. **Query the KnowledgeBase** (grep/search only – do not read entire files) for **relevant articles and the most likely solution** to the customer's case.
2. **If KB output is generic or insufficient** for a substantive customer reply, **search the web** for case-specific official or community-supported paths (Mein o2 flows, o2.de pages, documented workarounds). Use results only when relevant to **this** customer's issue.
3. **Advise the customer service agent** on necessary **documentation or tickets** that need to be filled out (e.g. which form, which ticket type).
4. **Create a fitting reply** for the customer that:
   - **Uses the mandatory email reply template** (salutation, case-specific thank you + sympathy, survey line, signature block),
   - Prioritizes **viable self-service, app/web paths, case-specific alternatives, and clear next steps** (see **Solutions, self-service, alternatives** above); **omits hotline** unless KB/matrix/exception/chat user requires it; avoids quoting internal brand actions unless the chat user instructed those exact lines; **never names internal systems** (Authentifizierungsmatrix, Sabio, TIM, Wissensbasis, etc.).
   - Reflects **only what the chat user has confirmed or what is strictly factual** (e.g. transfer completed, document attached) — **not** speculative processing or future contact (see **No uninvited promises** above),
   - Follows **KnowledgeBase instructions and guidelines** for that type of case **except** where KB text would add promises; in those cases **omit or neutralize** unless the chat user instructs otherwise,
   - Is case-specific without **default promises** of checks, processing, or follow-up messages.

---

## Exceptions – do NOT (or only partially) query the Knowledge Base

In the following situations, **do not query the KnowledgeBase** for general solution articles, or **override normal TransferMatrix behavior**. Handle as below. **This list may be updated by user instruction** – add or change exceptions as instructed.

1. **Customer wishes to update their name (Namensänderung)** – Handle according to Authentifizierung matrix (typically Web/App/Schriftweg with Kopie Ausweis/Pass); do not query KB for general solution.  
   - **If the customer has already provided valid ID documents and the Authentifizierung matrix allows the change:**  
     - Treat the name change as **approved and to be carried out**.  
     - In section 6 (customer reply), **confirm the desired legal name change explicitly** (e.g. "wir haben Ihren Namen von [Altname] auf [Neuer Name] aktualisiert" or equivalent) and **address the customer consistently with the new name** in the salutation and body (see "Name change (Namensänderung)" rule in the Email reply template).  
     - Default behavior after RE is: **confirmation of the requested name change with the new name**, unless the user later corrects or overrides the draft.  
   - **When such cases appear, always output the following block in the chat** (before the suggested reply), so the agent can see and copy the values to be updated:
   - **Current name:** [Bisheriger Vorname] [Bisheriger Nachname]
   - **Desired name:** [Neuer Vorname] [Neuer Nachname]
   - **Update:** state which position is to be updated (First name / Last name / Both) and show the **exact value to paste** in a copyable format (e.g. in a code block or on a line labeled "Copy for [field]:") next to that position.
   - **Name in Bankverbindung ändern:** yes / no / not mentioned — depending on the case: use **yes** if the customer wants the account-holder name on the bank details updated too; **no** if they do not; **not mentioned** if the request or form does not state it.
   **Example:**
   - Current name: Julia Morais Gancz  
   - Desired name: Luiza Morais Gancz  
   - **Update: First name** → Copy for field: `Luiza`  
   - Name in Bankverbindung ändern: yes.  
   (If last name or both were changing, add e.g. **Update: Last name** → Copy for field: `…` or **Update: Both** → First: `…` | Last: `…`.)
   This makes it clear what to update and gives a one-click copyable value next to the position (first name, last name, or both).
2. **Customer contract withdrawal (Widerruf)** – Customer explicitly exercises the right of withdrawal from a newly activated contract.  
   - If the withdrawal request is **within 3 months of contract activation** (based on dates in the thread):  
     - **Ignore verification status for routing purposes** (you may still describe verification in section 2, but you must **not block or alter routing based on it**).  
     - **Bypass normal TransferMatrix routing logic**: regardless of what the Transfer Matrix would normally say for the topic, you must set:  
       - **Transfer eligible: Yes**  
       - **Transfer goal:** queue **`CBC_XF_E_WIDERRUF`**  
     - In section 5, clearly instruct the agent to transfer the case in Sprinklr to **`CBC_XF_E_WIDERRUF`** as the handling team for withdrawal cases within 3 months of activation.  
     - Do **not** attempt alternative routing based on other matrix entries for this case type.  
   - If the withdrawal is **older than 3 months after activation** or the timing is unclear, fall back to the standard TransferMatrix + KB behavior.
3. **Customer wishes clarification on their bill** (specific cost positions, extraordinary costs, etc.) – Handle per matrix; do not query KB.
4. **Customer sends a final, positive acknowledgment** (thank you, closing email, satisfaction confirmation) – Reply with a short, friendly closing; no KB query needed.
5. **Customer wishes new offer, new contract, or contract extension** – Backoffice E-Mail team does **not** handle sales, offers, or contract extensions. Use **only** the following approach:
   - Issue a **case-specific thank you**, mentioning the case.
   - Be **apologetic**, and inform the customer that due to data safety regulation the email team does **not** handle promotions, offers or actions for new contracts and extensions.
   - Say that for that it would be best to contact the **care hotline**, where the contract specialist team can help: **089 78 79 79 400**.
   - Be kind and friendly.
6. **Customer writes their email in English** – Regardless of verification status (verified or unverified), do **not** process the case yourself and do **not** query the KnowledgeBase. Treat this as a language-routing exception and **transfer the case directly to queue `CBC_XF_E_ENGLISCH`** so that the English-speaking specialist team can take over. If a customer-facing reply is needed, draft only a short German info that the concern has been forwarded to the English-language specialist team for further processing.

---

## Standard premade response: Router return / Schadensersatz (Erstattung Routerkosten)

**When to use:** The customer case is about **router return**, **Schadensersatzkosten** (damage compensation charges) for late or delayed router return, or **refund of router costs / Erstattung der Routerkosten** that was promised or not applied. Use this as the **standard premade response** during email processing for such cases. Do not draft a different reply; use the template below and adapt only salutation (customer name) and, if needed, the conditional paragraph. **If the chat user explicitly instructs** you to add ticket/logistics details or promises of Rückmeldung, you may extend the middle paragraph accordingly; otherwise keep the neutral *„Wir haben Ihr Anliegen zur Kenntnis genommen.“* line and do not add promises of processing or further messages.

**Include vs exclude the return paragraph:** You must **recognise from the customer email/thread** whether the customer has already returned the router or not.

- **Signals that the customer has already returned the router** (→ **exclude** the return paragraph): e.g. "habe den Router zurückgeschickt", "Router bereits zurückgesendet", "habe ich zurückgegeben", "ist zurück", "retour geschickt", "zurückgesandt", "Rücksendung erfolgt", "verschickt", "zurückgegeben", "sent back", "returned", "already sent", "bereits zurück", "schon zurückgeschickt", or clear description that they sent it back / completed the return. If the thread or a previous brand message confirms the return was received, treat as already returned.
- **Signals that the customer has not returned the router or it is unclear** (→ **include** the return paragraph): no mention of return; customer only complains about charges or missing refund; customer asks what to do; customer says they still have the router or have not sent it; or wording is ambiguous. In case of doubt, **include** the paragraph (so the customer gets the return link if needed).

**Action:** If **already returned** → **omit** the whole paragraph that starts with "Um die monatlichen Kosten zu stoppen und die bereits entstandenen Beträge zu erstatten, bitten wir Sie, den Router bitte zurückzusenden, sofern Sie dies noch nicht getan haben." and ends with "... https://router-retoure.o2online.de/start". Keep the rest of the reply unchanged. If **not returned or unclear** → **include** that paragraph.

**Template (German).** Replace `[Vorname Nachname]` with the customer's name.

```
Guten Tag [Vorname Nachname],

vielen Dank für Ihre E-Mail. Es tut uns leid, dass es zu dieser Unannehmlichkeit gekommen ist.

Derartige Kosten entstehen, wenn ein zurückzugebender Router nicht rechtzeitig zurückgesendet wird oder die Rücksendung sich bei der Bearbeitung verzögert; in diesen Fällen können monatlich Schadensersatzkosten anfallen. Wir entschuldigen uns für die entstandene Unannehmlichkeit.

Wie es bei solchen Fällen in der automatischen Abwicklung vorkommen kann, ist bei der Erstattung des Schadensersatzes ein Fehler aufgetreten. Wir haben Ihr Anliegen zur Kenntnis genommen.

Vielen Dank für Ihr Verständnis und Ihre Geduld. Wir wünschen Ihnen alles Gute und stehen bei Rückfragen gerne zur Verfügung.

Um die monatlichen Kosten zu stoppen und die bereits entstandenen Beträge zu erstatten, bitten wir Sie, den Router bitte zurückzusenden, sofern Sie dies noch nicht getan haben. Für die bereits angefallenen Kosten haben wir bereits ein Erstattungsticket für Sie veranlasst. Die Rücksendung können Sie über ein Retoureticket einleiten, auf dem die Empfängeradresse bereits vermerkt ist. Den Link zum Retoureticket finden Sie hier: https://router-retoure.o2online.de/start

Nochmals vielen Dank.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski 

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz
```

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

Default **`run.py`**: if **`FIRST_RE_ONCE_PENDING`** (set by login) → consume flag and run **`--once`** (extract open case). Otherwise → Anwenden arm. Explicit: **`run.py --once`**, **`run.py --arm`** (after PR LF), **`run.py --arm-weiter`** (after LF TR; exact Weiter only). You output sections 1–7 in chat; hook plays Prowler after section 7. To put the reply into Sprinklr, use **sprinklr-write-reply**.

## UI mapping (Sprinklr)

- **Case ID:** `h2` containing "Fall #" and the case number.
- **Conversation:** `[data-testid="inboundChatConversationItemFanMessage"]`, `[data-testid="inboundChatConversationItemBrandMessage"]`; body in `[data-testid="html-message-content"]`.
- **Reply box** (used by sprinklr-write-reply, not this skill): `section[aria-label="Nachricht verfassen"]`, `[data-testid="baseEditorContainer"]`, TinyMCE iframe `body#tinymce`.

## Script file

- **Path:** `.cursor/skills/sprinklr-read-answer-email/run.py`
- **Does:** Post-login first RE → **`--once`**. **`--arm`** → Anwenden watch (PR LF). **`--arm-weiter`** → Weiter watch (LF TR; exact **Weiter** step 4/4 only). **Cursor** then writes sections 1–7 in chat.

## Knowledge base

**You (Cursor)** draft the reply using **KnowledgeBase/** at repo root. The files there (e.g. **KnowledgeBase_Complete.md**, **TransferMatrix_KnowledgeBase.md**) are **extremely long (millions of lines)**. You must **never read an entire KnowledgeBase file**. Instead: **grep or search** for keywords/phrases from the customer email (e.g. Rückerstattung, refund, Kündigung, transfer, Rechnung, IBAN, Kundennummer, specific product names) and read only the **matching lines or surrounding context**. Use the search results to draft and cite the reply.
