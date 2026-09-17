# 5. Vertrag — MUST + HUNT

**Export:** `exports/process/vertrag/`  
If Kündigung/Widerruf/Stammdaten missing under Vertrag, hunt `Telefónica > Prozesse > Kontaktbearbeitung > Backoffice`.

| Priority | Breadcrumb / topic | Tag | Status | Found under | Export path |
|---|---|---|---|---|---|
| MUST HUNT | Kündigung fristgerecht Mobile/FMS (+ Themen-ID 590/1849) | HANDLE | pending | | |
| MUST HUNT | Kündigung Festnetz/Home, AOK, Bestätigung, Rücknahme, Termin | HANDLE | pending | | |
| MUST HUNT | OCF / SalCus Kündigungswizard | HANDLE | pending | | |
| MUST HUNT | Widerruf / Storno Neuvertrag & VVL | HANDLE / TRANSFER_ONLY | pending | | |
| MUST HUNT | Stammdaten Name / Adresse / Geburtsdatum / Bank-SEPA | HANDLE / TRANSFER_ONLY | pending | | |
| MUST HUNT | Vertragsstilllegung | HANDLE / TRANSFER_ONLY | pending | | |
| MUST HUNT | MNP Mobile + Festnetz I@H | HANDLE / TRANSFER_ONLY | pending | | |
| MUST | `Vertrag > Vertragsabschluss > Aktivierung Festnetz` | HANDLE | pending | | |
| MUST | `… > Bestell-/Kaufprozess > Beratung` | HANDLE | pending | | |
| MUST | `… > Reklamationen` | HANDLE | pending | | |
| SELECTIVE | Bonität / Vertragsdokumente / Welcome Kommunikation | HANDLE | pending | | |

**Skip:** Archiv, Rotational Churn, deep Mixed Basket  
**Keywords:** Kündigung, Widerruf, Stammdaten, MNP, OCF, AOK, Vertragsstilllegung
