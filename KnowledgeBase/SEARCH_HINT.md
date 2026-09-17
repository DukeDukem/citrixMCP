# KnowledgeBase Search Instructions

Full overwrite 2026-09-17. Article corpus = `REMAP/exports/` only.
Legacy `knowledgebase1–7.md` removed — do not search them.

---

## Query strategy

### Step 0 — TransferMatrix FIRST (hard rule)
```
grep KnowledgeBase/TransferMatrix.md
```
Matrix decides routing. KB supports execution, never overrides Ziel-Kontakt.

### Step 1 — REMAP exports only
1. Find the right export file from the table below
2. Grep or read that file under `KnowledgeBase/REMAP/exports/`
3. Never use `REMAP/skip-log.md` branches for routine cases

---

## Topic → export file quick map

| Customer topic | Primary export file(s) | Keywords |
|---|---|---|
| **Rechnung / Reklamation** | `rechnung-zahlung/reklamation.md` · `rechnung-zahlung/rechnung.md` | Rechnung, Gutschrift, Doppelabbuchung, Reklamation, EVN |
| **SEPA / Zahlung** | `rechnung-zahlung/zahlung.md` | SEPA, Bankeinzug, Lastschrift, Zahlungsart |
| **Mahnung / Inkasso** | `rechnung-zahlung/mahnwesen.md` | Mahnung, Inkasso, Ratenzahlung, Sperrung |
| **Drittanbieter** | `rechnung-zahlung/drittanbieter-zahlung.md` · `optionen/drittanbieter-optionen.md` | Drittanbieter, WAP, Premium-SMS, Sperre |
| **Kündigung** | `vertrag/kuendigung.md` | Kündigung, Sonderrecht, Frist, Portierungskündigung |
| **Widerruf / Storno** | `vertrag/widerruf.md` | Widerruf, Storno, 14 Tage, Fernabsatz |
| **Stammdaten / Adresse** | `vertrag/aenderung-vertrag.md` | Stammdaten, Adresse, Name, E-Mail, IBAN, Bankverbindung |
| **MNP / Rufnummer** | `vertrag/rufnummer.md` | MNP, Portierung, Mitnahme, Rufnummer, Wunschrufnummer |
| **Aktivierung / Technikertermin** | `vertrag/2a-vertragsabschluss-aktivierung.md` | Aktivierung, Technikertermin, DSL-Zugangsdaten, Expressaktivierung |
| **DSL Verfügbarkeit / Beratung** | `vertrag/2b-vertragsabschluss-beratung.md` | Verfügbarkeit, DSL, Glasfaser, Kabel, Wechselservice |
| **Umzug** | `vertrag/umzug.md` | Umzug, Anschlussübernahme, Neubestellung |
| **Betrug / SIM-Swap** | `vertrag/betrugsverdacht.md` · `technik/cyber-kriminalitaet.md` | Betrug, SIM-Swap, Phishing, Identitätsmissbrauch |
| **Tarifwechsel** | `tarife/tarifwechsel.md` | Tarifwechsel, VVL, ARES, Tarifupgrade |
| **Aktuelle Tarife** | `tarife/mobilfunk-tarife.md` · `tarife/festnetz-tarife.md` | o2 Mobile, Unlimited, Home, DSL, Kabel |
| **Servicegebühren** | `tarife/servicegebuehren.md` | Servicegebühr, Shipping, Verwaltungsgebühr |
| **Sonderrufnummern** | `tarife/sonderrufnummern.md` | Sonderrufnummer, Freecall, Premium, Notruf |
| **eSIM / SIM-Karte** | `hardware/sim-karte-hardware.md` | eSIM, SIM-Tausch, Multicard, Triple-SIM, SIM-Lock |
| **Reparatur / Austausch** | `hardware/reparatur-austausch.md` | Reparatur, Garantie, Austausch, Defekt |
| **Roaming / Ausland** | `ausland/roaming.md` · `ausland/ins-ausland.md` | Roaming, RLAH, Ausland, VoWiFi, Fair Use |
| **Mein o2 / Login** | `self-service/registrierung-login-passwort.md` · `self-service/mein-o2-sitemap.md` | Mein o2, Login, Passwort, 2FA, Registrierung |
| **Datenpakete / Internet** | `optionen/internet-optionen.md` | Datenpaket, Throttling, 5G-Option, SpeedOn |
| **Fernsehen** | `optionen/fernsehen-tv.md` | o2 TV, Sender, Buchung, Streaming |
| **VVL / Kundenbindung** | `vermarktung/kunden-halten-vvl.md` | VVL, ARES, Vertragsverlängerung, Berechtigung |
| **Entstörung Mobile** | `technik/mobilfunk-technik.md` | Entstörung, LTE, 5G, Empfang, Datenfehler |
| **Entstörung Festnetz** | `technik/festnetz-technik.md` | DSL, Glasfaser, Router, Entstörung, Speed |
| **EECC Minderung** | `technik/kundenbeschwerden.md` · `systems/telefonica-prozesse/1a-uebergreifend-rechtliches.md` | Minderung, Entschädigung, Netzstörung, EECC |
| **Authentifizierung** | `systems/telefonica-prozesse/4a-prozesse-authentifizierung.md` | Authentifizierung, OTP, PKK, SMS-Ident, Vollmacht |
| **Kontaktbearbeitung / Beschwerden** | `systems/telefonica-prozesse/4b-prozesse-kontaktbearbeitung.md` | Kontakteintrag, Backoffice, Beschwerde, Schriftweg, TBS |
| **SalCus** | `systems/telefonica-systeme/systeme-s-z.md` | SalCus, GoodWill, Hazard, Inbox, Ticketing |
| **SIKAS / Sprinklr** | `systems/telefonica-systeme/systeme-s-z.md` | SIKAS, Sprinklr, Transfer, Mailbearbeitung |
| **Marquez / HaLoS** | `systems/telefonica-systeme/systeme-d-m.md` | Marquez, HaLoS, Fiori, DPM, Dokument |
| **Excalibur / DSL-Tool** | `systems/telefonica-systeme/systeme-d-m.md` | Excalibur, TTM, DSL, Troubleshoot |
| **Rechtliches / TKG / EECC** | `systems/telefonica-prozesse/1a-uebergreifend-rechtliches.md` | TKG, EECC, DSGVO, AGB, Widerspruch, GffV |
| **Bankverbindungen / Kontaktdaten** | `systems/telefonica-prozesse/1b-uebergreifend-kontakt.md` | Bankverbindung, IBAN, Kontaktdaten, Hotline |

---

## Deleted files (no longer in KB)

The following were removed in the 2026-09-17 triage — do not search for them:

| Removed file | Reason |
|---|---|
| `1. Tarifberatung.docx` | Stub (empty) |
| `6. Handyankauf.docx` | Pure upsell / Foxway VVL |
| `3. Deeplinks versenden (App).docx` | Internal Shorty UI guide |
| `6. App Bonus.docx` | Time-bound promotion |
| `5. Trainings.docx` | SuccessFactors catalog |
| `5. Home Office Support.docx` | IT onboarding |
| `2. Aktionen.docx` | Weekly hardware promos |
| `3. Sales in Service (SIS).docx` | Monthly sales briefing |
| `5. Vertriebskanäle.docx` | Sales channel management |

---

## Output format reminder

- **Sections 1–5, 7** → English (to agent)
- **Section 6** → German (to customer)
- Ticket/Themen-ID + program + steps from exports; TransferMatrix for routing
- Never mention internal system names in section 6
