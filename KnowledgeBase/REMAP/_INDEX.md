# O₂ Care Postpaid — KB Remap Index

**Purpose:** Case-volume-filtered breadcrumb checklist for remapping the live Sabio tree into this repo.  
**L1 order:** matches Sabio `O₂ Care Postpaid` menu.  
**Routing authority:** always [`../TransferMatrix.md`](../TransferMatrix.md) first; these articles support execution only.

## Legend

| Tag | Meaning |
|---|---|
| **MUST** | Remap fully (Auf einen Blick + working leaves) |
| **SELECTIVE** | Remap only listed leaves / one-pagers |
| **HUNT** | May sit under another L1 in the new tree; still required |
| **SKIP** | Do not export (see [`skip-log.md`](skip-log.md)) |

**Capture fields per leaf:** full breadcrumb · title · Themen-ID · system · `HANDLE` / `TRANSFER_ONLY` / `HOTLINE_REFER` · status (`pending` / `captured`) · export path

## How to provide article content (operator)

1. Walk Sabio using the checklists (walk order below).  
2. For each MUST/SELECTIVE leaf: save **Word `.docx`**, **PDF**, or **paste into a `.md` file** under `exports/…`.  
3. Prefer **markdown** for agent search; Word is fine — convert later with the docx pipeline.  
4. Mark the checklist row `captured` and set Export path.

## Folder layout

```
KnowledgeBase/REMAP/
  _INDEX.md
  skip-log.md
  process/          <- L1 checklists
  systems/          <- Telefónica Prozesse + Systeme
  exports/          <- captured articles land here
```

## Walk order (Care payoff)

1. [Rechnung & Zahlung](process/04-rechnung-zahlung.md)
2. [Vertrag](process/05-vertrag.md)
3. [Hardware](process/03-hardware.md)
4. [Self Service](process/07-self-service.md)
5. [Telefónica Prozesse](systems/08-telefonica-prozesse.md)
6. [Telefónica Systeme](systems/08-telefonica-systeme.md)
7. [Technik](process/09-technik.md)
8. [Ausland](process/06-ausland.md)
9. [Tarife](process/01-tarife.md)
10. [Vermarktung](process/10-vermarktung.md)
11. [Optionen, Packs & Apps](process/02-optionen-packs-apps.md)

## L1 → tier map

| # | L1 | Tier | Checklist |
|---|---|---|---|
| 1 | Tarife | Thin MUST | [01-tarife.md](process/01-tarife.md) |
| 2 | Optionen, Packs & Apps | Mostly SKIP | [02-optionen-packs-apps.md](process/02-optionen-packs-apps.md) |
| 3 | Hardware | MUST | [03-hardware.md](process/03-hardware.md) |
| 4 | Rechnung & Zahlung | Highest MUST | [04-rechnung-zahlung.md](process/04-rechnung-zahlung.md) |
| 5 | Vertrag | MUST + HUNT | [05-vertrag.md](process/05-vertrag.md) |
| 6 | Ausland | MUST | [06-ausland.md](process/06-ausland.md) |
| 7 | Self Service | MUST | [07-self-service.md](process/07-self-service.md) |
| 8 | Telefónica | MUST Auth + systems | [Prozesse](systems/08-telefonica-prozesse.md) · [Systeme](systems/08-telefonica-systeme.md) |
| 9 | Technik | MUST Festnetz | [09-technik.md](process/09-technik.md) |
| 10 | Vermarktung | SELECTIVE VVL | [10-vermarktung.md](process/10-vermarktung.md) |
