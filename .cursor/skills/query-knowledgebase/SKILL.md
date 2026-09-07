# Skill: query-knowledgebase

## When to use this skill
Use this skill whenever you need to look up:
- How to handle a specific customer case type (Kuendigung, Rechnung, SIM, eSIM, Tarif, Geraet, Sperrung, Entstoerung, Rückerstattung, Storno, Roaming, etc.)
- Which ticket ID and program to use (SalCus, Marquez, Viagint)
- Where to route a case (Transfermatrix / Sabio)
- Verification / authentication rules for customers
- Specific form fields, trays, or locations within backend systems
- Response templates and escalation paths

## Knowledge Base Location
```
KnowledgeBase/
  INDEX.md              <- table of contents (start here)
  SEARCH_HINT.md        <- detailed query strategy
  TransferMatrix.md     <- TRANSFER MATRIX (check FIRST for every case!)
  knowledgebase1.md     <- KB article 1 (full text + image refs)
  knowledgebase3.md     <- KB article 3
  knowledgebase4.md     <- KB article 4
  knowledgebase5.md     <- KB article 5
  knowledgebase6.md     <- KB article 6
  knowledgebase7.md     <- KB article 7
  images/               <- extracted screenshots and diagrams
    knowledgebase1/img_001.png ... img_NNN.png
    knowledgebase3/...
    ...
```

## Query Procedure

### Step 0 — Transfer Matrix FIRST (authoritative handling path)

**Before** grepping knowledgebase1–7.md, determine routing via the Transfer Matrix:

```
Grep(pattern="<case_topic>", path="KnowledgeBase/TransferMatrix.md", -i=True)
```

Read **Ziel-Kontakt** + **Action** (handling hint).

| Matrix result | Meaning |
|---------------|---------|
| **CBC_CARE_ALLGEMEIN** / **HANDLE DIRECTLY** | We handle. Action column = primary handling advice. Then query KB for compatible detail only. |
| **Other queue / coding** | Transfer in Sprinklr to that Ziel-Kontakt. Do **not** let KB send you elsewhere. |
| **Email (`@…`)** | External forward / LF TR extern. |
| **"Kein Transfer"** | No Sprinklr transfer; follow **Action** instructions. |
| **Ticket instruction** | Create the specified ticket per Action. |

**Conflict rule:** If a KB article says to transfer/handle differently than the matrix → **Transfer Matrix wins**. See `.cursor/rules/transfer-matrix-priority.mdc`.

**Collections (Sprinklr queue):**
- Ziel-Kontakt for collections/dunning/payment cases is **`CBC_XF_E_COLLECTIONS`**.
- Action: **Transfer in Sprinklr** (not email forward).
- In agent instructions and RE sections, state the destination as **`CBC_XF_E_COLLECTIONS`**. Do not use retired names `collection_webform@cc.o2online.de` or `CBC_XF_Collections`.
- Customer reply: do **not** paste this internal email address unless KB/chat user explicitly requires it; use customer-safe wording (e.g. responsible team) per `.cursor/rules/reply-no-internal-systems.mdc`.

Only proceed to query the general KB articles (knowledgebase1-7.md) if the Transfer Matrix says we handle (or Kein Transfer with process-in-place), **and** only for steps that support the matrix Action.

### Step 1 - Identify topic keywords
Extract 2-4 German keywords from the customer case. Examples:
- "Kündigung" → search for Kuendigung, Kündigung, Storno, Vertragsende
- "Rechnung" → Rechnung, Rechnungskorrektur, Rückerstattung
- "SIM gesperrt" → Sperrung, SIM-Karte, Entsperrung
- "eSIM" → eSIM, eSIM-Profil, ESIM-PROFILE
- "Gerät" → Gerät, Geräteversicherung, Hardwaretausch
- "Roaming" → Roaming, Ausland, Datenvolumen Ausland
- "Tarif" → Tarifwechsel, Tarifoptionen, Basispaket

### Step 2 - Grep the knowledge base
Search all KB markdown files for the keyword:
```
Grep(pattern="<keyword>", path="KnowledgeBase/", -i=True)
```
Use case-insensitive search. Try multiple keyword variants if the first returns nothing. Prefer hits that support the matrix Action already chosen.

### Step 3 - Read the relevant section
Once you have matching files and line numbers, read those sections:
```
Read(path="KnowledgeBase/<filename>.md", offset=<start_line>, limit=100)
```
Read enough context around the match (at least 50 lines before and after).

### Step 4 - Check images if referenced
If the text references a diagram or screenshot (marked `![...]`), read the image:
```
Read(path="KnowledgeBase/images/<docname>/img_NNN.png")
```
This may show a form, system screen, or flow diagram.

## Output Rules (always follow these for agent responses)

- Communicate in ENGLISH for all explanations, reasoning, and procedural steps
- Use original GERMAN labels for all system fields, buttons, tabs, program names
  (e.g., "GERAETE & SIM-KARTEN", "ESIM-PROFILE", "RECHNUNGSHISTORIE", "Kundendaten")
- Always include:
  - Specific Ticket ID number
  - Program name (SalCus, Marquez, Viagint, etc.)
  - Exact tray/location/tab in the program
  - Step-by-step numbered actions
  - Transfer destination if applicable (cite Transfer Matrix section)
- If no backend action needed: state "No backend action required - reply only"
- If case cannot be handled via email: cite the Transfer Matrix destination

## Example Query Flow

Customer email: "Ich moechte meinen Vertrag kuendigen."

1. TransferMatrix first: Fall Kündigung → Ziel-Kontakt + Action (HANDLE DIRECTLY vs transfer queue)
2. Keywords: Kündigung, Vertrag, Kuendigung
3. Grep KB only if matrix says we handle / Kein Transfer with process: `Grep(pattern="Kündigung|Kuendigung", path="KnowledgeBase/", -i=True)`
4. Produce step-by-step agent instructions starting from matrix Action, then KB detail:
   - "Open SalCus -> Navigate to 'VERTRAGSDETAILS' -> Select ticket [ID] 'Kündigung'"
   - "Fill in: Kündigungsdatum = [date], Grund = [reason from email]"
   - "Confirm via 'Speichern'"
5. Draft German reply (thank you + sympathy + only factual/routing content; **do not** promise processing timelines or follow-up messages unless the chat user instructs you to)
