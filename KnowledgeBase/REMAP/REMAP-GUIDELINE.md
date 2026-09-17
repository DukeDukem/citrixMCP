# KB Remap Guideline + Prediction Algorithm

**Purpose:** Permanent reference for all future KB remaps. Covers every L1/L2/leaf with a
REMAP / SKIM / SKIP verdict and a scoring-based model for predicting which branches will
need re-checking next.

**Routing authority:** Always [`../TransferMatrix.md`](../TransferMatrix.md) first.
These verdicts govern *capture and maintenance* only — not case routing.

**Last updated:** 2026-09-17

---

## Verdict legend

| Tag | Meaning | Capture action |
|---|---|---|
| **REMAP** | Capture in full at every remap cycle | All leaves, full text, Themen-ID |
| **SKIM** | Capture overview / Auf einen Blick only; skip deep sub-leaves | One-pager or summary leaf |
| **SKIP** | Do not capture; exclude from KB | Log reason in `skip-log.md` |

---

## Part 1 — Branch-by-branch verdicts

Sections ordered by Care case volume (highest-impact first).

---

### 4. Rechnung & Zahlung — REMAP FULL

*Highest daily case volume. Almost every leaf is agent-handled.*

| L2 | Child branch | Verdict | Notes |
|---|---|---|---|
| Rechnung | Einstellungen > Online / Papier | **REMAP** | Agent handles directly |
| Rechnung | Einstellungen > EVN (Komfort/Kompakt) | **REMAP** | Agent handles directly |
| Rechnung | Einstellungen > SMS/E-Mail Benachrichtigung | **REMAP** | Agent handles directly |
| Rechnung | Rechnungskopie versenden | **REMAP** | |
| Rechnung | Musterrechnungen | **REMAP** | |
| Rechnung | Archiv | **SKIP** | Dead leaves |
| Reklamation | Bearbeitung > Auf einen Blick | **REMAP** | |
| Reklamation | Bearbeitung > Backoffice | **REMAP** | |
| Reklamation | Bearbeitung > Strittige Beträge | **REMAP** | |
| Reklamation | Bearbeitung > Rechnungen nach Vertragsende | **REMAP** | |
| Reklamation | Bearbeitung > Umbuchungen | **REMAP** | |
| Reklamation | Bearbeitung > Zahlungssuche | **REMAP** | |
| Reklamation | Nach Posten > Auf einen Blick | **REMAP** | |
| Reklamation | Nach Posten > Roaming-Posten | **SKIM** | One-pager only |
| Reklamation | Nach Posten > WLAN Ausland | **SKIM** | |
| Reklamation | Nach Posten > 3. Personen | **SKIM** | |
| Reklamation | Nach Posten > Internet & Festnetz | **SKIM** | |
| Reklamation | Rechnung fehlt | **REMAP** | |
| Zahlung | SEPA-Lastschrift | **REMAP** | |
| Zahlung | Überweisung | **REMAP** | |
| Zahlung | Zahlungsziele / Billing-Kalender | **SKIM** | Dates change; capture overview only |
| Zahlung | Archiv | **SKIP** | |
| Drittanbieter | Zahlen per Handyrechnung | **REMAP** | |
| Drittanbieter | Beschwerdebearbeitung | **REMAP** | |
| Mahnwesen | Mahnsperren / CACS / Inkasso | **REMAP** | Transfer-only one-pager acceptable |
| Mahnwesen | Archiv | **SKIP** | |
| Guthabenbuchung | Auf einen Blick / Gründe / Kategorien / Auszahlung / Ticket | **REMAP** | |

---

### 5. Vertrag — REMAP FULL + HUNT

*Core daily case type. Some leaves sit under Telefónica > Prozesse in Sabio — hunt them.*

| L2 | Child branch | Verdict | Notes |
|---|---|---|---|
| Kündigung | Fristgerecht Mobile (Themen-ID 590) | **REMAP** | Core daily |
| Kündigung | Fristgerecht FMS (Themen-ID 1849) | **REMAP** | Core daily |
| Kündigung | Festnetz / Home | **REMAP** | |
| Kündigung | AOK / Rücknahme / Bestätigung | **REMAP** | |
| Kündigung | SalCus Kündigungswizard / OCF | **REMAP** | |
| Kündigung | Archiv | **SKIP** | |
| Widerruf | Storno Neuvertrag | **REMAP** | Always transfer to CBC_XF_E_WIDERRUF |
| Widerruf | Storno VVL | **REMAP** | |
| Stammdaten | Name / Adresse / Bank-SEPA | **REMAP** | Auth-Matrix gated — check matrix too |
| Stammdaten | Geburtsdatum / E-Mail | **REMAP** | |
| Vertragsabschluss | Aktivierung Festnetz (→ 2a-Aktivierung) | **REMAP** | |
| Vertragsabschluss | Beratung / AGB / Preislisten (→ 2b-Beratung) | **SKIM** | Mostly reference material |
| Vertragsabschluss | Bonität / Check24 / Verivox / AOP | **SKIP** | Sales-channel only |
| Vertragsabschluss | Mixed Basket | **SKIP** | Sales-channel only |
| MNP | Mobile MNP | **REMAP** | |
| MNP | Festnetz MNP / I@H | **REMAP** | |
| Vertragsstilllegung | — | **REMAP** | Transfer-only one-pager |
| Rufnummer | Portierung / Rufnummernmitnahme | **REMAP** | |
| Rufnummer | Sperren | **SKIM** | |
| Betrug / Sicherheit | Betrugsvorwürfe / Sicherheitsabfrage | **REMAP** | |
| Spezielle Kundengruppen | — | **SKIM** | |
| Sterbefall | — | **REMAP** | Transfer-only one-pager |
| Umzug | — | **REMAP** | |
| Beeinträchtigungen | — | **SKIM** | Live-only; refresh each remap |

---

### 8. Telefónica — REMAP AUTH + SYSTEMS

*Auth and core systems underpin every case. Split across 4 files after last remap.*

**Prozesse (4a — Authentifizierung)**

| Child branch | Verdict | Notes |
|---|---|---|
| Authentifizierung > Auf einen Blick | **REMAP** | Referenced in every case |
| Authentifizierung > Prozesse und Stufen (alle Kanäle) | **REMAP** | |
| Authentifizierung > Prozesse und Stufen Backoffice | **REMAP** | |
| Authentifizierung > Mit One Time Password (OTP) | **REMAP** | |
| Persönliche Kundenkennzahl / Kennwort | **REMAP** | |
| SMS-Identverfahren | **SKIM** | |
| Allgemeinlautende Vollmachten | **SKIM** | |

**Prozesse (4b — Kontaktbearbeitung)**

| Child branch | Verdict | Notes |
|---|---|---|
| Kontaktleitfaden Backoffice | **REMAP** | |
| Beschwerden > Definition + Erkennen | **REMAP** | |
| Kontakteintrag / Erforderliche Pflichtfelder | **REMAP** | |
| Zuständigkeit / Vor- und Folgebearbeitung | **REMAP** | |
| Sensible Kundendaten | **REMAP** | |
| Englische Anfragen / Schriftweg | **SKIM** | Transfer one-pager only |
| Betrugsversuche | **REMAP** | |
| Suiziddrohung-Anweisung | **REMAP** | |
| Gesprächsleitfaden (Outbound / Telesales) | **SKIP** | Not E-Mail |
| KVP | **SKIP** | Internal process only |
| Gesprächsführung soft-skills | **SKIP** | |
| Korrespondenz / Tone of Voice | **SKIM** | Reference |

**Übergreifend (1a — Rechtliches)**

| Child branch | Verdict | Notes |
|---|---|---|
| TKG / AGB-Widerspruch | **REMAP** | Changes with each TKG amendment |
| EECC / Informationspflichten | **REMAP** | |
| DSGVO / Datenschutz | **REMAP** | |
| Widerrufsrecht | **REMAP** | |
| GffV | **REMAP** | |
| DNS-Sperren / Lieferketten / PTSG | **SKIM** | Low agent frequency |
| Sanktionen | **SKIM** | |
| Medienberichte / Sponsoring / THG-Quote | **SKIP** | PR / comms only |
| Whitelabel / blauworld / Ortel | **SKIP** | Sub-brand |

**Übergreifend (1b — Kontakt)**

| Child branch | Verdict | Notes |
|---|---|---|
| o2 Kontaktdaten / Service-Hotline | **REMAP** | Phone numbers change |
| Fremdsprachen-Service | **SKIM** | |
| Bankverbindungen | **SKIM** | |
| Auslastung / Jugendschutzhotline | **SKIM** | |

**Arbeitsmittel und Systeme**

| File / System group | Verdict | Notes |
|---|---|---|
| Beeinträchtigungen A–C (Aura, CACS, Citrix, CorFlow) | **REMAP** | Live/current state only |
| Systeme D–M (DPM, Marquez, Mein o2, Merlin) | **REMAP** | Marquez critical for agents |
| Systeme N–R (NBA, o2pedia, PRISM) | **SKIM** | NBA + o2pedia leaves only |
| Systeme S–Z (SalCus, SIKAS/Sprinklr, TIM) | **REMAP** | SalCus + TIM critical |
| ePOS | **SKIP** | Shop terminal — not E-Mail |
| Ortel-inbound leaves | **SKIP** | Sub-brand legacy |
| Archive für migrierte Systeme | **SKIP** | |

---

### 7. Self Service — REMAP FULL

*Mein o2 paths shift with every app update — score as urgent.*

| L2 | Child branch | Verdict | Notes |
|---|---|---|---|
| Registrierung / Login | Login-Prozess | **REMAP** | Daily case type |
| Registrierung / Login | Passwort vergessen | **REMAP** | |
| Registrierung / Login | 2FA / OTP outages | **REMAP** | Shifts when app updates |
| Mein o2 | Kündigung vormerken | **REMAP** | |
| Mein o2 | Rechnung einsehen | **REMAP** | |
| Mein o2 | Bankdaten ändern | **REMAP** | |
| Mein o2 | Tarif & SIM verwalten | **REMAP** | |
| Mein o2 | App Sitemap / Web-Sitemap | **SKIM** | App layout shifts with updates |
| Weitere o2 Services | Aura / Chatbot Lisa | **SKIM** | Capture current paths only |
| Sicherheitsabfrage | — | **REMAP** | Auth-Matrix linked |
| Social Media | — | **SKIP** | Not E-Mail Care |
| Archiv | — | **SKIP** | |

---

### 1. Tarife — SKIM (thin MUST)

*Content changes each tariff cycle (~quarterly). Capture text tables; strip screenshots.*

| L2 | Child branch | Verdict | Notes |
|---|---|---|---|
| Aktuelle Tarife | Auf einen Blick overview | **REMAP** | Refresh each tariff cycle |
| Aktuelle Tarife | Mobilfunk — current lineup | **REMAP** | Active tariffs only; skip discontinued |
| Aktuelle Tarife | Festnetz — text tables | **REMAP** | Strip embedded images on capture |
| Aktuelle Tarife | MediaMarkt / Saturn offers | **SKIP** | Retail-channel specific |
| Aktuelle Tarife | simyo-at-Blau | **SKIP** | Sub-brand |
| Aktuelle Tarife | Archiv | **SKIP** | |
| Tarifwechsel | Mobilfunk | **REMAP** | |
| Tarifwechsel | Festnetz | **SKIM** | |
| Tarifwechsel | Archiv | **SKIP** | |
| Sonderrufnummern | — | **SKIM** | Stable; rarely changes |
| Servicegebühren | Mobile / Hardware-Versand | **SKIM** | |
| Beeinträchtigungen | Rabattentzug / Preisanpassung | **REMAP** | Capture only when live |

---

### 9. Technik — REMAP FESTNETZ / SKIM REST

*Festnetz Entstörung is high-volume. RF/spectrum detail and deep Mobilfunk have low RE value.*

| L2 | Child branch | Verdict | Notes |
|---|---|---|---|
| Festnetz | DSL Entstörung | **REMAP** | High daily volume |
| Festnetz | Glasfaser | **REMAP** | Growing install base |
| Festnetz | Kabel | **REMAP** | |
| Festnetz | Technikertermin Entstörung | **REMAP** | |
| Festnetz | Kostenfreier Installationsservice | **REMAP** | |
| Festnetz | Kostenpflichtige Expertenhilfe | **SKIM** | |
| Mobilfunk | Empfang / LTE-5G | **SKIM** | |
| Mobilfunk | Mailbox / SMS Fehlerbehebung | **SKIM** | |
| Mobilfunk | VoLTE / VoWiFi | **SKIP** | Too technical for E-Mail |
| Netztechnik | Netzausbau overview | **SKIM** | No RF spectrum detail |
| Netztechnik | 3,6-GHz / 70 MHz spectrum detail | **SKIP** | Too technical |
| Cyber-Kriminalität | Phishing | **SKIM** | |
| Kundenbeschwerden | EECC Entschädigung | **REMAP** | |
| Archiv | — | **SKIP** | |

---

### 6. Ausland — REMAP FULL (stable)

*EU Roaming rules stable since 2022. Re-check Nicht-EU zones for country additions.*

| L2 | Child branch | Verdict | Notes |
|---|---|---|---|
| Im Ausland (Roaming) | EU-Roaming overview | **REMAP** | Stable; check for new country additions |
| Im Ausland | Nicht-EU Roaming | **REMAP** | Zone changes possible |
| Im Ausland | Roaming-Optionen | **REMAP** | |
| Im Ausland | Notfallkarten | **SKIM** | |
| Im Ausland | Archiv | **SKIP** | |
| Ins Ausland (International) | Tarife / Zonen | **REMAP** | |
| Netzstörung | — | **SKIM** | Capture live state only |
| Beeinträchtigungen | — | **SKIM** | Live only |

---

### 3. Hardware — REMAP SIM / SKIM REST

*SIM-Karte is daily; device-specific leaves have low RE value.*

| L2 | Child branch | Verdict | Notes |
|---|---|---|---|
| SIM-Karte | eSIM / Nano / Micro / Standard | **REMAP** | Daily case type |
| SIM-Karte | 2G-only formats | **SKIP** | Legacy — no current devices |
| Reparatur & Austausch | Garantie / Gewährleistung | **REMAP** | |
| Reparatur & Austausch | Austauschprogramme | **SKIM** | |
| o2 Handy Versicherung | Leistungen / Schaden melden | **REMAP** | |
| o2 Handy Versicherung | Archiv | **SKIP** | |
| Entsorgung alter Handys | — | **SKIP** | Low case volume |
| Beeinträchtigungen | — | **SKIM** | Live state only |
| Archiv | — | **SKIP** | |

---

### 2. Optionen, Packs & Apps — SKIM LIVE ONLY

*Most sub-branches are Archiv or discontinued. Check bookability before capturing.*

| L2 | Child branch | Verdict | Notes |
|---|---|---|---|
| Aktive Packs (non-Archiv) | Roaming-Optionen / Datenpacks | **SKIM** | Only if still bookable |
| Internet / Zusatzdaten | — | **SKIM** | |
| Telefonie & SMS | — | **SKIP** | Covered by Tarife |
| Sicherheit & Schutz | — | **SKIP** | |
| Ausland-Optionen | — | **SKIM** | Cross-ref Ausland L1 instead |
| o2 Apps & Entertainment | Live streaming (Disney+, etc.) | **SKIM** | Verify bookability each cycle |
| o2 Apps & Entertainment | Napster / Qello / o2 Music Paket | **SKIP** | Discontinued |
| o2 Apps & Entertainment | PlayStation / Nintendo vouchers | **SKIP** | Discontinued |
| Fernsehen | Core booking / cancellation | **SKIM** | |
| Fernsehen | Full HD Pay-TV upsell / Aufnahmespeicher | **SKIP** | Niche; low volume |
| Versicherungen | — | **SKIP** | Covered under Hardware |
| Drittanbieter | — | **SKIP** | Cross-ref Rechnung & Zahlung |
| SIM-Karte (duplicate) | — | **SKIP** | Cross-ref Hardware |
| Archiv (entire) | — | **SKIP** | |

---

### 10. Vermarktung — SELECTIVE (VVL overview only)

*Care agents do not sell. Only VVL retention overview has RE value. Monthly content changes too fast to maintain.*

| L2 | Child branch | Verdict | Notes |
|---|---|---|---|
| Kunden halten (VVL) | Aktuelle VVL-Angebote overview | **SKIM** | Refresh monthly if possible |
| Kunden halten (VVL) | Hardware-Angebote (current cycle) | **SKIP** | Changes weekly — too transient |
| Kunden halten (VVL) | Wordings VVL mit Hardware | **SKIP** | Too transient |
| Kunden halten | Monthly Vermarktungsbriefing | **SKIP** | Month-specific; obsoletes itself |
| Aktionen (campaigns) | — | **SKIP** | Care does not sell |
| Beeinträchtigungen | — | **SKIM** | Live state only |

---

## Part 2 — Change Prediction Algorithm

### Volatility Score formula

Every branch receives a **Volatility Score (0–10)** from five weighted factors.

```
Score = (F1 × 0.30) + (F2 × 0.25) + (F3 × 0.20) + (F4 × 0.15) + (F5 × 0.10)
```

| Code | Factor | What it measures |
|---|---|---|
| F1 | Case volume | How often this branch drives an RE case (last 90 days) |
| F2 | Content age | Days since Sabio "Geändert am" on any leaf in this branch |
| F3 | Tariff/promo cycle | Is content tied to seasonal pricing or monthly campaigns? |
| F4 | Regulatory sensitivity | Scope of TKG / EU directives / DSGVO exposure |
| F5 | System dependency | Does the leaf describe UI/steps in a tool with ongoing changes? |

**Action thresholds:**

| Score | Action |
|---|---|
| >= 7.0 | **REMAP** at next opportunity |
| 5.0 – 6.9 | **SKIM-check** — compare against current Sabio; update changed leaves |
| 3.0 – 4.9 | Review at next full cycle |
| < 3.0 | Stable — no action until trigger event |

---

### Factor scoring guide

**F1 — Case volume** (source: agent RE transcripts / TransferMatrix routing frequency):

| Volume | Points |
|---|---|
| 8+ cases per week on this topic | 10 |
| 3–7 cases per week | 6 |
| 1–2 cases per week | 3 |
| Rarely or never | 0 |

**F2 — Content age** (check Sabio "Geändert am" / "Zuletzt aktualisiert"):

| Age | Points |
|---|---|
| Modified < 30 days ago | 10 — urgent |
| 30–90 days | 7 |
| 90–180 days | 4 |
| > 180 days | 1 |

**F3 — Tariff/promo cycle:**

| Type | Points |
|---|---|
| Monthly briefing content (Vermarktung, active promos) | 10 |
| Seasonal tariff cycle (o2 Mobile, Festnetz pricing, ~quarterly) | 7 |
| Annual regulatory update (TKG, EVN) | 4 |
| Structural / rarely changes (Ausland zones, Sonderrufnummern) | 1 |

**F4 — Regulatory sensitivity:**

| Exposure | Points |
|---|---|
| Directly governed by TKG / EECC / DSGVO with active amendments | 10 |
| Referenced in regulatory context but currently stable | 4 |
| No regulatory tie | 0 |

**F5 — System dependency:**

| Dependency | Points |
|---|---|
| Leaf describes UI/steps in a system with known ongoing changes (Mein o2, SIKAS, SalCus) | 10 |
| References a system that is stable / legacy | 3 |
| No system dependency | 0 |

---

### Pre-scored branches (baseline 2026-09-17)

Re-score at each cycle by updating F1–F5 columns.

| Branch | F1 | F2 | F3 | F4 | F5 | Score | Action |
|---|---|---|---|---|---|---|---|
| Self Service > Mein o2 | 10 | 7 | 4 | 0 | 10 | **7.50** | REMAP — urgent |
| Authentifizierung | 10 | 7 | 1 | 4 | 6 | **6.65** | REMAP next cycle |
| Tarife > Aktuelle Tarife | 6 | 10 | 7 | 1 | 3 | **6.25** | SKIM next cycle |
| Rechnung > Reklamation | 10 | 4 | 1 | 4 | 3 | **6.00** | SKIM-check |
| Vermarktung > Kunden halten | 3 | 10 | 10 | 0 | 0 | **5.90** | SKIP — too transient |
| Systeme (SalCus / SIKAS) | 6 | 7 | 1 | 0 | 10 | **5.65** | SKIM-check |
| TKG / AGB-Widerspruch | 3 | 7 | 4 | 10 | 0 | **5.15** | Watch F4 trigger |
| Festnetz Technik | 6 | 4 | 1 | 0 | 6 | **3.90** | Next full cycle |
| Hardware SIM-Karte | 6 | 4 | 1 | 0 | 3 | **3.60** | Next full cycle |
| Ausland Roaming | 3 | 4 | 4 | 4 | 0 | **3.05** | Stable |

---

### Trigger events — force immediate re-check regardless of score

The following events override the scheduled cadence and require immediate branch review:

| Trigger | Branches to check |
|---|---|
| o2 publishes a new tariff / price adjustment | Tarife > Aktuelle Tarife, Tarifwechsel, Vermarktung VVL |
| Bundesnetzagentur / EU issues TKG or EECC amendment | 1a-Rechtliches: TKG, EECC, GffV, Informationspflichten |
| Mein o2 app releases a UI update | Self Service: Login, Mein o2 paths, 2FA |
| SIKAS (Sprinklr) or SalCus UI change | Systeme S-Z, Kontaktbearbeitung |
| A queue is added or removed in TransferMatrix | Corresponding L2 routing leaves for that case type |
| Any branch's case volume jumps > 3× week-over-week | That branch immediately |
| New sub-brand activated or deactivated | Übergreifend 1b-Kontakt, affected Tarife leaves |

---

### Recommended review cadence

| Cadence | Branches |
|---|---|
| **Monthly** | Vermarktung VVL overview, Beeinträchtigungen (all L1 folders) |
| **Quarterly** | Tarife Aktuelle, Self Service Mein o2, Authentifizierung, Systeme SalCus/SIKAS |
| **Semi-annually** | Rechnung & Zahlung full, Vertrag Kündigung/Widerruf, Ausland, Hardware SIM |
| **On trigger only** | TKG/Rechtliches, Festnetz Technik, Organisationsstruktur, Kontaktdaten |
| **Never (stable)** | Sonderrufnummern, Sterbefall structure, Betrugsvorwürfe process |

---

## Part 3 — Remap execution checklist

Use this checklist at the start of every remap session.

```
[ ] 1. Open Sabio — navigate to O2 Care Postpaid root
[ ] 2. For each branch in Part 1 (walk order from _INDEX.md):
        a. Check "Geändert am" date on all leaves → update F2 score
        b. Compare verdict: REMAP = capture all; SKIM = Auf einen Blick only; SKIP = log and move on
        c. For REMAP/SKIM: save as .docx under KB folder matching L1 number
        d. Add KB-LEAF-SEPARATOR between each leaf in the .docx
        e. Strip screenshots (or note "[Bild entfernt]"); keep text tables
[ ] 3. Run kb_media_cleanup.py on all new/updated .docx files
[ ] 4. Update Volatility Scores in Part 2 baseline table
[ ] 5. Add any newly skipped branches to skip-log.md with date + reason
[ ] 6. Update _INDEX.md walk order if new L2s appeared
```

**Walk order (by Care payoff — from `_INDEX.md`):**

1. Rechnung & Zahlung
2. Vertrag
3. Hardware
4. Self Service
5. Telefónica Prozesse (Auth + Kontaktbearbeitung)
6. Telefónica Systeme (Arbeitsmittel)
7. Technik
8. Ausland
9. Tarife
10. Vermarktung
11. Optionen, Packs & Apps
