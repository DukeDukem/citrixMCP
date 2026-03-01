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
Use case-insensitive search. Try multiple keyword variants if the first returns nothing.

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

### Step 5 - Cross-reference Transfer Matrix
If the case may require transfer to another division, search specifically for:
```
Grep(pattern="Transfermatrix|Transfer Matrix|Weiterleitung", path="KnowledgeBase/", -i=True)
```
Then read that section to get the exact transfer destination.

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

1. Keywords: Kündigung, Vertrag, Kuendigung
2. Grep: `Grep(pattern="Kündigung|Kuendigung", path="KnowledgeBase/", -i=True)`
3. Read matching section in e.g. knowledgebase3.md
4. Produce step-by-step agent instructions:
   - "Open SalCus -> Navigate to 'VERTRAGSDETAILS' -> Select ticket [ID] 'Kündigung'"
   - "Fill in: Kündigungsdatum = [date], Grund = [reason from email]"
   - "Confirm via 'Speichern'"
5. Draft German reply confirming receipt and expected processing time
