# Knowledge Base (Markdown)

## Authority

1. **[TransferMatrix.md](TransferMatrix.md)** — routing (Ziel-Kontakt / Action)  
2. **[REMAP/exports/](REMAP/exports/)** — article knowledge base (full overwrite 2026-09-17)

Legacy Word dumps (`knowledgebase1–7.md`) were **deleted**. Do not restore them for case work.

## Maps / navigation

- **[INDEX.md](INDEX.md)** — export file map  
- **[SEARCH_HINT.md](SEARCH_HINT.md)** — topic → export quick map  
- **[REMAP/_INDEX.md](REMAP/_INDEX.md)** — L1 walk order + checklists  
- **[REMAP/REMAP-GUIDELINE.md](REMAP/REMAP-GUIDELINE.md)** — REMAP / SKIM / SKIP verdicts  
- Skip list: [REMAP/skip-log.md](REMAP/skip-log.md)

## Layout

```
KnowledgeBase/
  TransferMatrix.md
  INDEX.md / SEARCH_HINT.md / README.md
  REMAP/
    process/   systems/     <- checklists
    exports/
      process/…             <- Care articles
      systems/…             <- Telefónica Prozesse + Systeme
```

## Adding / refreshing articles

1. Open Sabio from a checklist row in `REMAP/process/` or `REMAP/systems/`.  
2. Save as `.md` (preferred) into the matching `REMAP/exports/...` folder.  
3. Mark checklist Status → `captured`.  
4. Keep TransferMatrix in sync when Ziel-Kontakt changes.
