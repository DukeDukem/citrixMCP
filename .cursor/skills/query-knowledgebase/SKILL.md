# Skill: query-knowledgebase

## When to use
Case handling lookups: Kündigung, Rechnung, SIM/eSIM, Tarif, Hardware, Roaming, tickets (SalCus/Marquez), TransferMatrix, Authentifizierung, process articles.

## Location
```
KnowledgeBase/
  TransferMatrix.md     <- routing authority (always first)
  INDEX.md              <- export file map
  SEARCH_HINT.md        <- topic → export quick map
  REMAP/
    _INDEX.md / checklists / skip-log.md
    exports/            <- THE knowledge base (full overwrite 2026-09-17)
      process/…         <- Care process articles
      systems/…         <- Telefónica Prozesse + Systeme
```

**There is no legacy `knowledgebase1–7.md`.** Do not look for those files.

## Query procedure

### Step 0 — Transfer Matrix FIRST
```
Grep(pattern="<topic>", path="KnowledgeBase/TransferMatrix.md", -i=True)
```
Ziel-Kontakt / Action wins. Collections = `CBC_XF_E_COLLECTIONS`. See `transfer-matrix-priority.mdc`.

### Step 1 — Find the export file
1. Use `KnowledgeBase/SEARCH_HINT.md` (topic → file) or `INDEX.md` / `REMAP/_INDEX.md`.
2. Skip branches listed in `REMAP/skip-log.md`.
3. Read the matching file under `KnowledgeBase/REMAP/exports/...`.

### Step 2 — Grep / read
```
Grep(pattern="<keyword>", path="KnowledgeBase/REMAP/exports", -i=True)
Read(path="KnowledgeBase/REMAP/exports/<area>/<file>.md", offset=…, limit=100)
```

### Output
English explanations; German UI labels; Ticket ID + program + tray + steps; TransferMatrix for transfers.
