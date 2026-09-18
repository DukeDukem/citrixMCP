# Transfer Matrix (Sabio Transfermatrix)

> Extracted from Sabio Transfer Matrix screenshots. Covers both E-Mail and Hotline channels.
> Last updated: 2026-09-18 (full remap from 512 screenshots).
> Our domain (E-Mail): **EMAIL_O2_CARE** — email cases with this Ziel-Kontakt are handled directly (**Transfer eligible: No**).
> Our domain (Call): **o2 Mobile Care** — voice cases with this Ziel-Kontakt are handled directly (**Transfer eligible: No**).
> Sprinklr (SIKAS) is the active platform. WDE is retired — all WDE-specific instructions are disregarded.

## How to use this document

**Priority:** This Transfer Matrix is the **authoritative handling path** for every case. If Knowledge Base articles disagree on transfer vs handle-directly, **this matrix wins**.

**Own-team override (this workspace):** Ziel-Kontakt **`EMAIL_O2_CARE`** (email) or **`o2 Mobile Care`** (calls) always means **we handle — Transfer eligible: No**. Do not Sprinklr-transfer to ourselves even if an Action cell says “Cold transfer” (that wording is for other Sabio readers).

1. **Identify the Thema** (topic) from the customer contact.
2. **Identify the Fall** (case type) and **Kanal** (E-Mail or Hotline).
3. **Look up the Ziel-Kontakt** and read the **Action** column.
4. **If Ziel-Kontakt = EMAIL_O2_CARE** (email) **or o2 Mobile Care** (call) **or Action = HANDLE DIRECTLY**: Handle directly — **Transfer eligible: No**.
5. **If Ziel-Kontakt = EMAIL_O2_*** queue **other than EMAIL_O2_CARE**: Forward the email via Sprinklr to that queue.
6. **If Ziel-Kontakt = other internal hotline team** (e.g. o2 Tech Fixnet, o2 Fixnet Care — **not** o2 Mobile Care): Transfer call — cold transfer unless Action says warm/traffic-light. Respect 120s wait threshold unless stated otherwise.
7. **If Ziel-Kontakt = email address**: Forward via Sprinklr **Externer Transfer** to that address.
8. **If Ziel-Kontakt = Kein Transfer**: Do not transfer. Follow the Action steps (Themen-ID tickets, text blocks, hotline referral for customer, etc.).
9. **If Action = ticket instruction**: Create the specified ticket (Themen-ID number, copy email content to Problembeschreibung as instructed).

See also: `.cursor/rules/transfer-matrix-priority.mdc`

---

## Quick Reference: All Transfer Goals

### Email queues (Sprinklr internal routing)

| Queue | Description |
|---|---|
| EMAIL_O2_CARE | General o2 care — **our email team** — handle directly (Transfer eligible: No) |
| EMAIL_O2_MOBILE_TECHNIK | Mobile technical support team |
| EMAIL_O2_ENGLISCH | English-language care |
| EMAIL_COLLECTIONS | Collections (dunning) |
| EMAIL_O2_KUENDIGUNGEN_SME_SOHO | SOHO/SME cancellations |
| EMAIL_O2_KUENDIGUNGEN_NETZ | Network-related cancellations |
| EMAIL_O2_KUENDIGUNG_RECHNUNG | Billing-complaint cancellations |
| EMAIL_O2_KUENDIGUNGEN_AUSLAND | Move-abroad cancellations |
| EMAIL_O2_WIDERRUF | Revocation/withdrawal |
| EMAIL_O2_EKL_ONLINESHOP | Online shop revocation |
| EMAIL_O2_HAENDLERBESCHWERDEN | Dealer complaints |
| EMAIL_O2_SOHO | SOHO customer service |
| EMAIL_O2_VERTRAGSSTILLEGUNG | Contract suspension |
| EMAIL_O2_KUNDENDATEN | Customer data / bank details |
| EMAIL_O2_EVN_OFFICE | EVN (itemised billing) office |
| EMAIL_BLAU_CARE | Blau postpaid care |
| EMAIL_BLAU_PREPAID_CARE | Blau prepaid care |
| EMAIL_O2_EXKLUSIV_SERVICE | Exklusiv / Premium TOP / VIP service |
| EMAIL_O2_PRESSESTELLE | Press/media enquiries |
| EMAIL_O2_PREPAID_CARE | o2 Prepaid care |

### Hotline teams (internal transfer targets)

| Team | Hours | Transfer type |
|---|---|---|
| o2 Mobile Care | Mo–Fr 7–20 Uhr, Sa 10–18 Uhr | **Our call team** — handle directly (Transfer eligible: No). Sabio may show “Cold transfer” for other readers. |
| o2 Fixnet Care | Mo–Fr 7–20 Uhr, Sa 10–18 Uhr | Cold (kalt), 120s threshold |
| o2 Tech Mobile (Postpaid, Homespot, FMS) | Mo–Fr 7–20 Uhr, Sa 10–18 Uhr | Cold (kalt), 120s threshold |
| o2 Tech Fixnet (DSL, FTTH, Kabel) | Mo–Fr 7–22 Uhr, Sa 10–18 Uhr | Cold (kalt), 120s threshold |
| o2 Activation Care Fixnet (DSL, FTTH, Kabel) | Mo–Fr 7–20 Uhr, Sa 10–18 Uhr | Cold (kalt) |
| o2 Activation Fixnet (DSL/FTTH/Kabel) | Mo–Fr 8–20 Uhr, Sa 10–18 Uhr | Cold (kalt), 120s threshold |
| Mahnwesen Postpaid | Mo–Fr 8–18 Uhr | Cold (kalt), 120s threshold; CACS-aktive only |
| Handyversicherung | Mo–Sa 09–18 Uhr | Cold (kalt) |
| oneSoho (Care) | Mo–Fr 8–20 Uhr, Sa 10–18 Uhr | Warm (traffic-light system) |
| Permission Mitarbeiter | Mo–Fr 9–20 Uhr | Cold (kalt) |
| Türkisch o2 Care | Mo–Fr 06–20, Sa 10–18 Uhr | Cold (kalt) |
| VVL Mobile – Privatkunden | Mo–Fr 9–20 Uhr, Sa 10–18 Uhr | Cold (kalt) |
| Guru – kaufmännisch | Mo–Fr 7–20 Uhr, Sa 10–18 Uhr | Cold (kalt) |
| Telesales Mobile/Data | Mo–Fr 8–20 Uhr, Sa 10–18 Uhr | Cold (kalt) |
| Business_Mobile_Hotline | Mo–Fr 7–20 Uhr, Sa 10–18 Uhr | Transfer in Sprinklr |
| Business_Mobile_Daimler_Team | Mo–Fr 7–18 Uhr | Transfer in Sprinklr |
| Exklusiv Team (TOP/VIP) | Mo–Fr 7–20 Uhr, Sa 10–18 Uhr | Cold (kalt) |

### Email-based external transfers (Externer Transfer in Sprinklr)

| Email | When to use |
|---|---|
| alditalk@cc.o2online.de | ALDI TALK E-Mail |
| ayyildiz@cc.o2online.de | AY YILDIZ E-Mail (Postpaid + Prepaid) |
| nettokom@cc.o2online.de | NettoKOM E-Mail |
| whatsappsim@cc.o2online.de | WhatsApp SIM E-Mail |
| service@kunde.aetkasmart.de | aetkaSMART / Mobilka / Whitelabel E-Mail |
| DS_Beauskunftung@telefonica.com | DSGVO data disclosure requests |
| eretail-widerruf@telefonica.com | eRetail revocation |
| HUR@telefonica.com | High-spend payment cases |
| o2-portierung@telefonica.com | Festnetz number porting import |
| o2-rufnummernmitnahme@telefonica.com | MNP import — incoming porting documents |
| Verbraucherauskunft@telefonica.com | Bundesnetzagentur (BNA) inquiries |
| geschaeftskunden-service@telefonica.com | Business customers — DSL E-Mail |

---

## Full Transfer Matrix by Thema

---

### 1. andere Kundentypen (z. B. SOHO, Business, Händler, Presse, o.Ä.)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Ämter/Sicherheitsbehörden (Polizei, Gericht, Staatsanwaltschaft) — Anfragen | Alle Kanäle | Kein Transfer | Verweis auf Schriftweg. Textbaustein/Formblatt nutzen (E-Mail: "anfragen von behoerden"; Brief/Fax: "anfragen_von_behoerden"). TIM: "Rechtliches - Anfragen von Sicherheitsbehörden". Hotline: Führungskraft kontaktieren; Angaben weiterleiten: Name/Kontaktperson der Behörde, Rückrufnummer, E-Mail. |
| 2 | Businesskunde | Hotline – DSL / Hotline – Mobile | Kein Transfer | Zuordnung SOHO/Business per Kundentyp/Subtyp prüfen (Tabelle in TIM). Business Mobile/Fixnet: max. 2 Min. Wartezeit; Transfer an 56189 (Warm-Transfer); Nichterreichbarkeit: Kunden bitten, 0800 22 111 22 direkt anzurufen. Testkarten: Hazard Note "Testkarte/n" nicht löschen. |
| 3 | Businesskunde | Hotline – Mobile | Business_Mobile_Hotline | Transfer in Sprinklr; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr. |
| 4 | Businesskunde | E-Mail – DSL | geschaeftskunden-service@telefonica.com | Forward via Externer Transfer in Sprinklr to geschaeftskunden-service@telefonica.com. |
| 5 | Businesskunde | E-Mail – Mobile | BUSINESS-TEAM | Transfer in Sprinklr. |
| 6 | Daimler-MA | Hotline | Business_Mobile_Daimler_Team | Transfer in Sprinklr; Mo–Fr 7–18 Uhr. Außerhalb der Geschäftszeiten: kostenlose Rufnummer 0800 99 111 22 nennen. |
| 7 | Exklusiv-Kunden (nur Servicetyp "Premium TOP" und "VIP") | Hotline | Exklusiv Team (TOP/VIP) | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 8 | Exklusiv-Kunden (nur Servicetyp "Premium TOP" und "VIP") | E-Mail | EMAIL_O2_EXKLUSIV_SERVICE | Transfer in Sprinklr. |
| 9 | Geschäftsführung – Beschwerde | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 10 | Geschäftsführung – Beschwerde | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 11 | Geschäftsführung – Beschwerde | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 4073 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |
| 12 | Händleranfragen (Händlerstornos, provisionsrelevante Änderungen) | Hotline | Kein Transfer | Händler an Händlerbetreuung verweisen: 089/41851717 oder 0176/88888888. |
| 13 | Händlerbeschwerde — Kundenbeschwerden über Vertriebspartner (Händlernr. 12..., 13..., 14..., 19...) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 14 | Händlerbeschwerde — Kundenbeschwerden über Vertriebspartner (Händlernr. 12..., 13..., 14..., 19...) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Ticket Themen-ID 4304 erstellen. |
| 15 | Händlerbeschwerde — Kundenbeschwerden über Vertriebspartner (Händlernr. 12..., 13..., 14..., 19...) | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 4304 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |
| 16 | Journalisten / Presse — Anfragen | Hotline | Kein Transfer | Verweis auf Schriftweg. |
| 17 | Journalisten / Presse — Anfragen | E-Mail | EMAIL_O2_PRESSESTELLE | Transfer in Sprinklr. |
| 18 | Mitarbeiter — Anfrage zum Vertrag | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 19 | Mitarbeiter — Anfrage zum Vertrag | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. TIM "Diensttarif — Kundenbetreuung mit Dienstkarten". Legitimation mit PKK. Ticket Themen-ID 2823 bei Herausforderungen. |
| 20 | Mitarbeiter — Anfrage zum Vertrag | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. TIM "Diensttarif — Kundenbetreuung mit Dienstkarten". Keine Änderung eigener Daten. Offboarding: Inhaberwechsel oder RNM möglich. Ticket Themen-ID 2823 bei Herausforderungen. |
| 21 | Rechtsanwalt — im Auftrag eines Kunden | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 872 (Portalanfrage: Themen-ID ändern; sonst: neu anlegen mit vollst. E-Mail-Inhalt). Textbaustein "An Fachabteilung weitergeleitet". |
| 22 | Rechtsanwalt — in eigener Sache | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 4073 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |
| 23 | Selbstständige (SOHO) — kaufmännisch/technisch — alle sonstigen Anfragen | Hotline | Kein Transfer | ⚠️ Routing flagged as potentially incorrect — verify with team |
| 24 | Selbstständige (SOHO) — kaufmännisch/technisch — alle sonstigen Anfragen | E-Mail | EMAIL_O2_SOHO | Transfer in Sprinklr. |
| 25 | Selbstständige (SOHO) — Kündigung | Hotline | Kein Transfer | ⚠️ Routing flagged as potentially incorrect — verify with team |
| 26 | Selbstständige (SOHO) — Kündigung | E-Mail – Mobile | EMAIL_O2_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr. |
| 27 | Selbstständige (SOHO) — Stammdaten-Änderung per Brief/Fax/E-Mail | E-Mail | EMAIL_O2_SOHO | Transfer in Sprinklr. |
| 28 | SOHO | Hotline | Kein Transfer | ⚠️ Routing flagged as potentially incorrect — verify with team |
| 29 | SOHO | E-Mail | EMAIL_O2_SOHO | Transfer in Sprinklr. |
| 30 | Verbraucherschutz — Anfragen | Hotline | Kein Transfer | Verweis auf Schriftweg. |
| 31 | Verbraucherschutz — Anfragen | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 4061 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |
| 32 | Verbraucherschutz — Anfragen von der Bundesnetzagentur | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 4079 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |

---

### 2. andere Marken (z.B. Aldi, Blau, Prepaid)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | ALDI TALK | Hotline | Kein Transfer | Kunden an ALDI TALK Kundenbetreuung verweisen: +49 177 177 1157 / +49 800 552 2255; Mo–Fr 7–23, Sa/So/Feiertage 10–18 Uhr; alditalk@eplus.de; www.alditalk.de. |
| 2 | ALDI TALK | E-Mail | alditalk@cc.o2online.de | Forward via Externer Transfer in Sprinklr to alditalk@cc.o2online.de. (WDE instructions disregarded — Sprinklr Externer Transfer applies.) |
| 3 | AOL Anfragen | Alle Kanäle | Kein Transfer | Kunden an AOL Hotline 089-78 79 79 431 verweisen. |
| 4 | AY YILDIZ | Hotline | Kein Transfer | Kunden an AY YILDIZ Kundenbetreuung verweisen: +49 177 177 1135 / 0800 55 222 55; Mo–Fr 8–22, Sa 10–20, So/Feiertage 10–18 Uhr; service@ayyildiz.de. Ausnahme Zahlung: Transfer an Mahnwesen (56156). |
| 5 | AY YILDIZ | E-Mail – Postpaid | ayyildiz@cc.o2online.de | Forward via Externer Transfer in Sprinklr to ayyildiz@cc.o2online.de. (WDE instructions disregarded — Sprinklr Externer Transfer applies.) |
| 6 | AY YILDIZ | E-Mail – Prepaid | ayyildiz@cc.o2online.de | Forward via Externer Transfer in Sprinklr to ayyildiz@cc.o2online.de. (WDE instructions disregarded — Sprinklr Externer Transfer applies.) |
| 7 | BLAU | Hotline | Kein Transfer | Kunden an Blau Kundenbetreuung verweisen: +49 177 1 77 11 59 (Prepaid), +49 177 1 77 11 60 (Postpaid), +49 89 78 79 79 420 (My-Handy); Mo–Fr 8–20, Sa 10–16 Uhr. Bestellhotline: 0800 40 40 410. |
| 8 | BLAU | E-Mail – Postpaid | EMAIL_BLAU_CARE | Transfer in Sprinklr. |
| 9 | BLAU | E-Mail – Prepaid | EMAIL_BLAU_PREPAID_CARE | Transfer in Sprinklr. |
| 10 | FONIC | Hotline / E-Mail | Kein Transfer | Kunden an FONIC verweisen: 0176 8888 0000 (Mo–Fr 8–18, Sa 10–18 Uhr); service@fonic.de; FONIC Kundenbetreuung, Postfach 1038, 90001 Nürnberg. |
| 11 | Mobilka | Hotline | Kein Transfer | Kunden an Mobilka Kundenbetreuung verweisen. |
| 12 | Mobilka | E-Mail | service@kunde.aetkasmart.de | Forward via Externer Transfer in Sprinklr to service@kunde.aetkasmart.de. |
| 13 | NettoKOM | Hotline | Kein Transfer | Kunden an NettoKOM verweisen: +49 177 17 11415 (Mo–Fr 8–20, Sa 10–18 Uhr); service@nettokom.de; www.nettokom.de. |
| 14 | NettoKOM | E-Mail | nettokom@cc.o2online.de | Forward via Externer Transfer in Sprinklr to nettokom@cc.o2online.de. |
| 15 | novamobil | Hotline / E-Mail | Kein Transfer | Marke zu FONIC migriert. Kunden an FONIC verweisen: 0176 8888 0000 (Mo–Fr 8–18, Sa 10–18 Uhr); service@fonic.de. |
| 16 | o2 Prepaid/Loop | Hotline | Kein Transfer | Kunden an o2 Prepaidhotline verweisen. |
| 17 | o2 Prepaid/Loop | E-Mail | EMAIL_O2_PREPAID_CARE | Transfer in Sprinklr. |
| 18 | simyo | Hotline | Kein Transfer | Kunden an simyo Kundenservice (mobilezone) verweisen. |
| 19 | simyo | E-Mail | Kein Transfer | Kunden auf kundenservice@simyo.de und widerruf@simyo.de verweisen. Kein Transfer. |
| 20 | Tchibo mobil | Hotline / E-Mail | Kein Transfer | Kunden an Tchibo mobil verweisen: 040-605 90 00 95 (Mo–Sa 8–22 Uhr, außer Feiertage); www.tchibo-mobilfunk.de. |
| 21 | WhatsApp SIM | Hotline | Kein Transfer | Kunden an WhatsApp SIM Kundenbetreuung verweisen. |
| 22 | WhatsApp SIM | E-Mail | whatsappsim@cc.o2online.de | Forward via Externer Transfer in Sprinklr to whatsappsim@cc.o2online.de. |
| 23 | Whitelabel (aetkaSMART) | Hotline | Kein Transfer | Kunden an jeweilige Kundenbetreuung verweisen. |
| 24 | Whitelabel (aetkaSMART) | E-Mail | service@kunde.aetkasmart.de | Forward via Externer Transfer in Sprinklr to service@kunde.aetkasmart.de. |

---

### 3. Englisch/Türkisch (o2 Postpaid Privatkunden)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Inhouse Dunning — Englisch | Hotline | Kein Transfer | Kein Transfer. E-Mail an FPF: rueckruf-englisch-inhouse-dunning@telefonica.com. Rückrufnummer + Anliegen angeben. |
| 2 | Inhouse Dunning — Englisch | E-Mail | EMAIL_COLLECTIONS | Transfer in Sprinklr. |
| 3 | Vertragsthemen o2 Postpaid Care — Englisch | Hotline | Kein Transfer | Kein Transfer. Verweis auf Hotline. |
| 4 | Vertragsthemen o2 Postpaid Care — Englisch | E-Mail | EMAIL_O2_ENGLISCH | Transfer in Sprinklr. |
| 5 | Vertragsthemen o2 Postpaid Care — Türkisch | Hotline | Türkisch o2 Care | Cold transfer to Türkisch o2 Care; Mo–Fr 6–20, Sa 10–18 Uhr. |

---

### 4. Hardware — Benutzen & Defekt

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Defekt — Beschwerde über Bearbeitung | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | Defekt — Beschwerde über Bearbeitung | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 3 | Defekt — Beschwerde über Bearbeitung | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 4 | Defekt — DSL Router | Hotline | o2 Tech Fixnet (DSL, FTTH, Kabel) | Cold transfer; Mo–Fr 7–22 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 5 | Defekt — DSL Router | E-Mail | Kein Transfer | Kein Transfer. Verweis auf Hotline 0176-888 55 222. |
| 6 | Defekt — mobile Hardware | Hotline | Guru – kaufmännisch | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 7 | Defekt — mobile Hardware | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 8 | DSL-Zugangsdaten, MAC-Adresse und Telefon-PIN | Hotline | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 9 | DSL-Zugangsdaten, MAC-Adresse und Telefon-PIN | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 10 | Installation, Nutzung, Hilfe — DSL/Glasfaser/Kabel Router | Hotline – DSL/Glasfaser/Kabel | o2 Tech Fixnet (DSL, FTTH, Kabel) | Cold transfer; Mo–Fr 7–22 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 11 | Installation, Nutzung, Hilfe — DSL/Glasfaser/Kabel Router | E-Mail | Kein Transfer | Kein Transfer. Verweis auf Hotline 0176-888 55 222. |
| 12 | Installation, Nutzung, Hilfe — mobile Hardware/Homespot | Hotline | o2 Tech Mobile (Postpaid, Homespot, FMS) | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Bedienungsfragen: Deeplink per SMS aus TIM; Zugangsdaten mobiles Internet: OTA Konfigbox zusenden. |
| 13 | Installation, Nutzung, Hilfe — mobile Hardware/Homespot | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 14 | WLAN-Hotspots | Hotline | o2 Tech Mobile (Postpaid, Homespot, FMS) | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 15 | WLAN-Hotspots | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |

---

### 5. Hardware — Logistik, Beratung & Vertrag

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Beratung zu Hardware und Routern | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | Beratung zu Hardware und Routern | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 3 | Beratung zu Hardware und Routern | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 4 | Fundsachen/Fundbüro (kein Prepaid) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 5 | Fundsachen/Fundbüro (kein Prepaid) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 6 | Fundsachen/Fundbüro (kein Prepaid) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 7 | Handyversicherung | Hotline | Handyversicherung | Cold transfer; Mo–Sa 9–18 Uhr; ab 120 s Wartezeit informieren. |
| 8 | Handyversicherung | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 9 | Logistik — Lieferung und Retouren | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 10 | Logistik — Lieferung und Retouren | Hotline – Mobile/Homespot | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 11 | Logistik — Lieferung und Retouren | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 12 | o2 My Handy — Fragen zum Ratenplan | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 13 | o2 My Handy — Fragen zum Ratenplan | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 14 | o2 My Handy — Vorzeitige Vertragsauflösung beantragen & Beschwerden | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Transfer vermeiden wenn möglich: Online-Selfcare oder Shorty-SMS. |
| 15 | o2 My Handy — Vorzeitige Vertragsauflösung beantragen & Beschwerden | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. Transfer vermeiden wenn möglich: Selfcare oder Shorty-SMS. |
| 16 | o2 My Handy — Vorzeitige Vertragsauflösung stornieren | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 17 | o2 My Handy — Vorzeitige Vertragsauflösung stornieren | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |

---

### 6. Hardware — SIM Karte & Sperren

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | eSIM — Installation, Einrichten, Synchronisieren, Beeinträchtigungen | Hotline | o2 Tech Mobile (Postpaid, Homespot, FMS) | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | eSIM — Installation, Einrichten, Synchronisieren, Beeinträchtigungen | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 3 | eSIM/SIM/Multicard/Datacard — Bestellung, Tausch, Versand, Aktivierung, Deaktivierung | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 4 | eSIM/SIM/Multicard/Datacard — Bestellung, Tausch, Versand, Aktivierung, Deaktivierung | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 5 | PIN/PUK — Auskunft | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 6 | PIN/PUK — Auskunft | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 7 | Sperren & Entsperren (SIM, DSL, Drittanbieter etc.) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 8 | Sperren & Entsperren (SIM, DSL, Drittanbieter etc.) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 9 | Sperren & Entsperren (SIM, DSL, Drittanbieter etc.) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |

---

### 7. Rechnung

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Ändern/Einrichten Rechnungseinstellungen (Rechnungsart, Zustellungsart, EVN-Typ) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | Ändern/Einrichten Rechnungseinstellungen (Rechnungsart, Zustellungsart, EVN-Typ) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 3 | Ändern/Einrichten Rechnungseinstellungen (Rechnungsart, Zustellungsart, EVN-Typ) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 4 | Anfrage / Reklamation Rechnungsinhalt (EVN Einsicht nötig) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 5 | Anfrage / Reklamation Rechnungsinhalt (EVN Einsicht nötig) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 6 | Anfrage / Reklamation Rechnungsinhalt (EVN Einsicht nötig) | E-Mail | EMAIL_O2_EVN_OFFICE | Transfer in Sprinklr. |
| 7 | Anfrage / Reklamation Rechnungsinhalt (keine EVN Einsicht nötig) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 8 | Anfrage / Reklamation Rechnungsinhalt (keine EVN Einsicht nötig) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 9 | Anfrage / Reklamation Rechnungsinhalt (keine EVN Einsicht nötig) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 10 | Drittanbieter — Reklamation / Anzweiflung | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 11 | Drittanbieter — Reklamation / Anzweiflung | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 12 | Drittanbieter — Reklamation / Anzweiflung | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 13 | Rechnungsduplikat | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 14 | Rechnungsduplikat | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 15 | Rechnungsduplikat | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 16 | Rechnungsduplikat Hardware | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 17 | Rechnungsduplikat Hardware | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 18 | Rechnungsduplikat Hardware | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |

---

### 8. Roaming

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Kaufmännisch — Optionen und Kosten | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | Kaufmännisch — Optionen und Kosten | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 3 | Technisch — Nutzung im Ausland nicht möglich | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 4 | Technisch — Nutzung im Ausland nicht möglich | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |

---

### 9. Rufnummernmitnahme Festnetz I@H (DSL, Kabel, FTTH)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Export — Beauftragung auflaufendem Vertrag, gekündigt | Hotline | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | Export — Beauftragung auflaufendem Vertrag, gekündigt | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 3 | Export — Beauftragung auflaufendem Vertrag, ungekündigt | Hotline | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 4 | Export — Beauftragung auflaufendem Vertrag, ungekündigt | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 5 | Import — Rufnummernmitnahme zu DSL/Kabel/Glasfaser — Auftrag, Terminverschiebung | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |

---

### 10. Rufnummernmitnahme Festnetznummer (Homezone und Homespot)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Export — Portierungsstatus unklar | Alle Kanäle | Kein Transfer | Kein Transfer. Übersicht Portierungsstatus in Sabio prüfen. |
| 2 | Import — Beauftragung per Formular | E-Mail | o2-portierung@telefonica.com | Forward via Externer Transfer in Sprinklr to o2-portierung@telefonica.com. |
| 3 | Import — Portierungsstatus unklar | Alle Kanäle | Kein Transfer | Kein Transfer. Übersicht Portierungsstatus in Sabio prüfen. |

---

### 11. Rufnummernmitnahme MNP (Mobilfunknummer)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Betrugsverdacht | Hotline / E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 653 an NP-Desk erstellen. |
| 2 | Export — Portierungserklärung zur Freigabe aus dem Vertrag | Hotline | Kein Transfer | Kein Transfer. Opt-In durch #1st Level/Care setzen. |
| 3 | Export — Portierungserklärung zur Freigabe aus dem Vertrag | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 4 | Import — automatische Änderung Portierungstermin | Alle Kanäle | Kein Transfer | Kein Transfer. Kunde bekommt Info per E-Mail oder SMS. Kein Ticket nötig. |
| 5 | Import — Beauftragung (außer interne Portierung) | Alle Kanäle | Kein Transfer | Kein Transfer. Verweis auf Selfservice-Portal oder App. Kein Ticket an NP-Desk. |
| 6 | Import — Eingang wichtiger Dokumente (Portierungsaufträge, Formulare, Kündigungsbestätigung, MNP-Beschwerden) | E-Mail | o2-rufnummernmitnahme@telefonica.com | Forward via Externer Transfer in Sprinklr to o2-rufnummernmitnahme@telefonica.com. |
| 7 | Import — Portierungsstatus unklar | Alle Kanäle | Kein Transfer | Kein Transfer. Portierungsstatus prüfen. Ablehnungsgründe erläutern (Rufnummer unbekannt, Kundendaten falsch, Opt-In fehlt, Portierung zu früh/spät, Storno, etc.). |
| 8 | Import — Sonstiges / spezieller Fehlerfall | Hotline / E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 653 an NP-Desk erstellen. |
| 9 | Import — Storno für Portierung zum Vertragsende | Alle Kanäle | Kein Transfer | Kein Transfer. Ticket Themen-ID 653 an NP-Desk erstellen. |
| 10 | Interne Portierung (innerhalb Telefónica Marken) | Alle Kanäle | Kein Transfer | Kein Transfer. Shorty SMS mit Link zu Formular interne Portierung versenden: https://www.o2online.de/service/downloads/formulare/internes-portierungsformular/ |

---

### 12. Self Service

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Newsletter | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | Newsletter | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 3 | Newsletter | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 4 | o2 Apps (z.B. Mein o2, o2 Protect) | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 5 | o2 E-Mail (@o2mail.de — Festnetz) | Hotline – Festnetz | o2 Tech Fixnet (DSL, FTTH, Kabel) | Cold transfer; Mo–Fr 7–22 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 6 | o2 E-Mail (@o2online.de — Mobile) | Hotline – Mobile | o2 Tech Mobile (Postpaid, Homespot, FMS) | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 7 | o2 E-Mail | E-Mail – Festnetz | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 8 | o2 E-Mail | E-Mail – Mobile | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 9 | o2.de Portal | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 10 | o2.de Portal | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 11 | o2.de Portal | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |

---

### 13. Störung

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | DSL | Hotline – DSL/Glasfaser | o2 Tech Fixnet (DSL, FTTH, Kabel) | Cold transfer; Mo–Fr 7–22 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | DSL | E-Mail | Kein Transfer | Kein Transfer. Kunden bitten, unter 0800 525 13 78 anzurufen. |
| 3 | Forderung Entschädigung/Minderung EECC TKG | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Transfer vermeiden: Kunden zur Beantragung auf Landingpage verweisen (Link per Shorty). |
| 4 | Forderung Entschädigung/Minderung EECC TKG | E-Mail | Kein Transfer | Kein Transfer. Textbaustein "Forderung Verweis auf Online" verwenden. |
| 5 | Homespot | Hotline | o2 Tech Mobile (Postpaid, Homespot, FMS) | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 6 | Homespot | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 7 | Kabel | Hotline – Kabel | o2 Tech Fixnet (DSL, FTTH, Kabel) | Cold transfer; Mo–Fr 7–22 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 8 | Kabel | E-Mail | Kein Transfer | Kein Transfer. Kunden bitten, unter 0800 525 13 78 anzurufen. |
| 9 | Mailbox, Visual Voice Mail, o2 Voicemail (Infos, Menü, Kontaktwege) | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 10 | Mailbox, Visual Voice Mail, o2 Voicemail (Infos, Menü, Kontaktwege) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 11 | MMS | Hotline | o2 Tech Mobile (Postpaid, Homespot, FMS) | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 12 | MMS | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 13 | Mobilfunk Daten (Ursache vermutlich Hardware/Konfiguration) | Hotline | o2 Tech Mobile (Postpaid, Homespot, FMS) | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 14 | Mobilfunk Daten (Ursache vermutlich Hardware/Konfiguration) | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 15 | Mobilfunk Daten (Ursache vermutlich Netz) | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 16 | Mobilfunk Daten (Ursache vermutlich Netz) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 17 | Mobilfunk Daten (Ursache vermutlich Netz) — Anfragen von der Bundesnetzagentur | E-Mail | Verbraucherauskunft@telefonica.com | Forward via Externer Transfer in Sprinklr to Verbraucherauskunft@telefonica.com. |
| 18 | Mobilfunk Sprache | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 19 | Mobilfunk Sprache | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 20 | Mobilfunk Sprache — Anfragen von der Bundesnetzagentur | E-Mail | Verbraucherauskunft@telefonica.com | Forward via Externer Transfer in Sprinklr to Verbraucherauskunft@telefonica.com. |
| 21 | o2 Mehrwertdienste (keine Drittanbieterdienste) | Hotline | o2 Tech Mobile (Postpaid, Homespot, FMS) | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 22 | o2 Mehrwertdienste (keine Drittanbieterdienste) | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 23 | o2 TV (technisches Problem) | Hotline | o2 Tech Mobile (Postpaid, Homespot, FMS) | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr. Transfer nur wenn: (1) technisches Problem mit o2 TV; (2) o2 TV Pack aktiv; (3) passende App (GVP weiß / waipu blau) genutzt; (4) keine Großstörung; (5) Login in Mein o2 funktioniert (wenn nein: Ticket 793, kein Transfer). |

---

### 14. Vertrag — Kündigung

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Androhung, Fristen, Ablauf — fristgerecht & außerordentlich | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Kunden von Kündigung abhalten; auf OCF/Shorty-SMS verweisen. Kein Transfer durch CCS & OCF bei erkennbarer Kündigungsabsicht. |
| 2 | Androhung, Fristen, Ablauf — fristgerecht & außerordentlich | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Kunden von Kündigung abhalten; auf OCF/Shorty-SMS verweisen. Kein Transfer durch CCS & OCF bei erkennbarer Kündigungsabsicht. |
| 3 | Androhung, Fristen, Ablauf — fristgerecht & außerordentlich | E-Mail – Festnetz / E-Mail – Mobile | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 4 | Beschwerde über fehlende Kündigungsbestätigung / verzögerte Deaktivierung | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 5 | Beschwerde über fehlende Kündigungsbestätigung / verzögerte Deaktivierung | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 6 | Beschwerde über fehlende Kündigungsbestätigung / verzögerte Deaktivierung | E-Mail – Festnetz | Kein Transfer | Kein Transfer. Ticket Themen-ID 5134 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |
| 7 | Beschwerde über fehlende Kündigungsbestätigung / verzögerte Deaktivierung | E-Mail – Mobile/FMS | EMAIL_O2_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr. |
| 8 | eingehende Kündigung — außerordentlich (AOK) — DSL — Insolvenz | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 897 (Portalanfrage: Themen-ID ändern; sonst: neu anlegen mit vollst. E-Mail-Inhalt). Textbaustein "An Fachabteilung weitergeleitet". |
| 9 | eingehende Kündigung — außerordentlich (AOK) — DSL — sonstige Fälle | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 2537 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |
| 10 | eingehende Kündigung — außerordentlich (AOK) — Mobile/FMS — Haft/Krankheit/Nutzertod | E-Mail | EMAIL_O2_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr. |
| 11 | eingehende Kündigung — außerordentlich (AOK) — Mobile/FMS — Insolvenz | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 897 (Portalanfrage: Themen-ID ändern; sonst: neu anlegen mit vollst. E-Mail-Inhalt). Textbaustein "An Fachabteilung weitergeleitet". |
| 12 | eingehende Kündigung — außerordentlich (AOK) — Mobile/FMS — Handydefekt | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 13 | eingehende Kündigung — außerordentlich (AOK) — Mobile/FMS — Handyverlust | E-Mail | EMAIL_O2_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr. |
| 14 | eingehende Kündigung — außerordentlich (AOK) — Mobile/FMS — Netzverfügbarkeit | E-Mail | EMAIL_O2_KUENDIGUNGEN_NETZ | Transfer in Sprinklr. |
| 15 | eingehende Kündigung — außerordentlich (AOK) — Mobile/FMS — Rechnungs-/Servicebeschwerde | E-Mail | EMAIL_O2_KUENDIGUNG_RECHNUNG | Transfer in Sprinklr. |
| 16 | eingehende Kündigung — außerordentlich (AOK) — Mobile/FMS — Todesfall Vertragsinhaber | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 895 (Portalanfrage: Themen-ID ändern; sonst: neu anlegen mit vollst. E-Mail-Inhalt). Textbaustein "An Fachabteilung weitergeleitet". |
| 17 | eingehende Kündigung — außerordentlich (AOK) — Mobile/FMS — Umzug ins Ausland | E-Mail | EMAIL_O2_KUENDIGUNGEN_AUSLAND | Transfer in Sprinklr. |
| 18 | eingehende Kündigung — fristgerecht — DSL | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 5134 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |
| 19 | eingehende Kündigung — fristgerecht — Mobile Handydefekt | E-Mail | EMAIL_O2_MOBILE_TECHNIK | Transfer in Sprinklr. |
| 20 | eingehende Kündigung — fristgerecht — Mobile Rechnungs-/Servicebeschwerde | E-Mail | EMAIL_O2_KUENDIGUNG_RECHNUNG | Transfer in Sprinklr. |
| 21 | eingehende Kündigung — fristgerecht — Mobile/FMS Netzverfügbarkeit | E-Mail | EMAIL_O2_KUENDIGUNGEN_NETZ | Transfer in Sprinklr. |
| 22 | eingehende Kündigung — fristgerecht — Mobile/FMS ohne Grund | E-Mail | EMAIL_O2_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr. |
| 23 | eingehende Kündigung als Anhang in E-Mail (PDF/Word) — DSL | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 5134 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |
| 24 | eingehende Kündigung als Anhang in E-Mail (PDF/Word) — Mobile/FMS | E-Mail | EMAIL_O2_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr. |
| 25 | Kündigungsrücknahme mit VVL-Interesse | Hotline – DSL | Kein Transfer | Kein Transfer. VVL durchführen; Kündigungsrücknahme erfolgt automatisch durch VVL. |
| 26 | Kündigungsrücknahme mit VVL-Interesse | Hotline – Mobile | Kein Transfer | Kein Transfer. VVL durchführen; Kündigungsrücknahme erfolgt automatisch. Für spätere Entscheidung: 0800 3310 130 nennen. |
| 27 | Kündigungsrücknahme mit VVL-Interesse | E-Mail | EMAIL_O2_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr. |
| 28 | Kündigungsrücknahmen ohne VVL-Interesse | Hotline – DSL | Kein Transfer | Kein Transfer. Kunden bitten, von gekündigter Rufnummer 0800 8780 800 anzurufen (Mo–Fr 8–20, Sa 10–18 Uhr). Winback-Flag Voraussetzung. |
| 29 | Kündigungsrücknahmen ohne VVL-Interesse | Hotline – Mobile | Kein Transfer | Kein Transfer. Kunden bitten, von gekündigter Rufnummer 0800 3310 130 anzurufen. Winback-Flag Voraussetzung. |
| 30 | Kündigungsrücknahmen ohne VVL-Interesse | E-Mail – DSL | Kein Transfer | Kein Transfer. Ticket Themen-ID 17 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |
| 31 | Kündigungsrücknahmen ohne VVL-Interesse | E-Mail – Mobile/FMS | EMAIL_O2_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr. |
| 32 | Kündigungstermin falsch hinterlegt | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 33 | Kündigungstermin falsch hinterlegt | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 34 | Kündigungstermin falsch hinterlegt | E-Mail – Festnetz | Kein Transfer | Kein Transfer. Ticket Themen-ID 17 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |
| 35 | Kündigungstermin falsch hinterlegt | E-Mail – Mobile/FMS | EMAIL_O2_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr. |
| 36 | Reaktivierungswunsch durch Kunden | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 37 | Reaktivierungswunsch durch Kunden | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 38 | Reaktivierungswunsch durch Kunden | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 39 | Reklamation Kündigungsrücknahme | Hotline | Kein Transfer | Kein Transfer. Kunden bitten, von gekündigter Rufnummer 0800 3310 130 anzurufen. Winback-Flag Voraussetzung. |
| 40 | Reklamation Kündigungsrücknahme | E-Mail – DSL | Kein Transfer | Kein Transfer. Ticket Themen-ID 17 (Portalanfrage: Themen-ID ändern + Fall-ID; sonst: neu anlegen mit vollst. E-Mail-Inhalt + Fall-ID). Textbaustein "An Fachabteilung weitergeleitet". |
| 41 | Reklamation Kündigungsrücknahme | E-Mail – Mobile/FMS | EMAIL_O2_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr. |

---

### 15. Vertrag — Stammdaten

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Accountzusammenführen/-trennung | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | Accountzusammenführen/-trennung | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 3 | Accountzusammenführen/-trennung | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 4 | Bankverbindung / SEPA / Einzugsermächtigung ändern/erteilen/widerrufen | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 5 | Bankverbindung / SEPA / Einzugsermächtigung ändern/erteilen/widerrufen | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 6 | Bankverbindung / SEPA / Einzugsermächtigung ändern/erteilen/widerrufen | E-Mail | EMAIL_O2_KUNDENDATEN | Transfer in Sprinklr. |
| 7 | Beauskunftung gemäß DSGVO (Datenschutz) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 8 | Beauskunftung gemäß DSGVO (Datenschutz) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 9 | Beauskunftung gemäß DSGVO (Datenschutz) | E-Mail | DS_Beauskunftung@telefonica.com | Forward via Externer Transfer in Sprinklr to DS_Beauskunftung@telefonica.com. |
| 10 | Betreuung (Unterlagen zur gesetzlichen Betreuung von Kunden) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 11 | Betreuung (Unterlagen zur gesetzlichen Betreuung von Kunden) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 12 | Betreuung (Unterlagen zur gesetzlichen Betreuung von Kunden) | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 826 (Portalanfrage: Themen-ID ändern; sonst: neu anlegen mit vollst. E-Mail-Inhalt). Textbaustein "An Fachabteilung weitergeleitet". |
| 13 | Datenschutzanfragen allgemein | Hotline / E-Mail | Kein Transfer | Kein Transfer. Allgemeine Anfragen direkt bearbeiten (TIM-Einträge und Textbausteine). Infoseite: https://www.telefonica.de/unternehmen/datenschutzanfrage.html |
| 14 | Festnetz — Umzug | Hotline | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 15 | Festnetz — Umzug | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 16 | Kundendaten ändern (Name, Adresse, Geburtsdatum) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 17 | Kundendaten ändern (Name, Adresse, Geburtsdatum) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 18 | Kundendaten ändern (Name, Adresse, Geburtsdatum) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 19 | Kundeneinwilligung / Permission Änderung/Beschwerde | Hotline | Permission Mitarbeiter | Cold transfer to Permission Mitarbeiter; Mo–Fr 9–20 Uhr. Nur wenn NBA-Aktivität zur Permissionabfrage vorliegt. Transfercode 56659. Außerhalb Servicezeiten: Rückrufwunsch mit Ticket 4479 aufnehmen. |
| 20 | Kundeneinwilligung / Permission Änderung/Beschwerde | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 21 | Kundenkennzahl ändern | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 22 | Kundenkennzahl ändern | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 23 | Kundenkennzahl ändern | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 24 | Kundentyp ändern (Privat auf SOHO) | Hotline | oneSoho (Care) | Warm transfer zu oneSoho (Care); Mo–Fr 8–20, Sa 10–18 Uhr; Transfercode 56129. Traffic-Light: Grün (<60 s) → warm; Gelb (61–120 s) → kalt mit Wartehinweis; Rot (>121 s) → nur auf Kundenwunsch transferieren oder Rückruf empfehlen. |
| 25 | Kundentyp ändern (Privat auf SOHO) | E-Mail | EMAIL_O2_SOHO | Transfer in Sprinklr. |
| 26 | Kundentyp ändern (SOHO auf Privat) | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 27 | Kundentyp ändern (SOHO auf Privat) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 28 | Vertragslaufzeit Anfrage | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Wenn möglich: Laufzeit aus SalCus-Reiter "Vertragsdaten" mitteilen. |
| 29 | Vertragslaufzeit Anfrage | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Wenn möglich: Laufzeit aus SalCus mitteilen. |
| 30 | Vertragslaufzeit Anfrage | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. Wenn möglich: Laufzeit aus SalCus "Vertragsdaten" mitteilen. |
| 31 | Vertragsstillegung | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 32 | Vertragsstillegung | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 33 | Vertragsstillegung | E-Mail | EMAIL_O2_VERTRAGSSTILLEGUNG | Transfer in Sprinklr. |
| 34 | Vertragsübernahme / Inhaberwechsel | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 35 | Vertragsübernahme / Inhaberwechsel | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 36 | Vertragsübernahme / Inhaberwechsel | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |

---

### 16. Vertrag — Tarife & Optionen

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Information zu Produkten, Optionen und Tarifen | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | Information zu Produkten, Optionen und Tarifen | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 3 | Information zu Produkten, Optionen und Tarifen | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 4 | Mailbox (Infos, Menü, Kontaktwege etc.) | Hotline | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 5 | Mailbox (Infos, Menü, Kontaktwege etc.) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 6 | Packs und Optionen aktivieren & deaktivieren | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 7 | Packs und Optionen aktivieren & deaktivieren | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 8 | Packs und Optionen aktivieren & deaktivieren | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 9 | Reklamation zu Tarif-, Pack- oder Optionswechsel (wenn nicht im Shop) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 10 | Reklamation zu Tarif-, Pack- oder Optionswechsel (wenn nicht im Shop) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 11 | Reklamation zu Tarif-, Pack- oder Optionswechsel (wenn nicht im Shop) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 12 | Rufnummerntausch | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 13 | Rufnummerntausch | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 14 | Rufnummerntausch | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 15 | Super Select Tarife (Mediamarkt/Saturn) | Alle Kanäle | Kein Transfer | Kein Transfer. Kunden an MSD Service verweisen: 0176 8885 3330 (Mo–Sa 8–20 Uhr). Post: Telefonica Germany, Kundenbetreuung MSD, Postfach 45 20, 90024 Nürnberg. TBS: "Kontakt Kundenbetreuung MSD". |
| 16 | Tarifwechsel (keine Vertragsverlängerung) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 17 | Tarifwechsel (keine Vertragsverlängerung) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 18 | Tarifwechsel (keine Vertragsverlängerung) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 19 | Telefon-Dienste (Anruf-Info-SMS, CLIP, CLIR etc.) | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 20 | Telefon-Dienste (Anruf-Info-SMS, CLIP, CLIR etc.) | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 21 | Telefon-Dienste (Anruf-Info-SMS, CLIP, CLIR etc.) | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 22 | Widerruf — Tarifwechsel, Pack- und Optionsbuchung | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 23 | Widerruf — Tarifwechsel, Pack- und Optionsbuchung | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 24 | Widerruf — Tarifwechsel, Pack- und Optionsbuchung | E-Mail | EMAIL_O2_WIDERRUF | Transfer in Sprinklr. |

---

### 17. Vertrag — Vertragsabschluss

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Ablehnung Neuvertrag (z.B. Bonität) — Anfrage/Reklamation | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | Ablehnung Neuvertrag (z.B. Bonität) — Anfrage/Reklamation | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 3 | Ablehnung Neuvertrag (z.B. Bonität) — Anfrage/Reklamation | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 4 | DSL-Auftrag im Aktivierungs-Status — Rückfragen | Hotline | o2 Activation Care Fixnet (DSL, FTTH, Kabel) | Transfer in Sprinklr; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr. |
| 5 | DSL-Auftrag im Aktivierungs-Status — Rückfragen | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 6 | Neuvertrag — Interessentenanfrage | Hotline | Telesales Mobile/Data | Cold transfer; Mo–Fr 8–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 7 | Neuvertrag — Interessentenanfrage | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 8 | Neuvertrag — Reklamation — Abschluss Hotline/Online | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 9 | Neuvertrag — Reklamation — Abschluss Hotline/Online | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 10 | Neuvertrag — Reklamation — Abschluss Hotline/Online | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 11 | Portierung — Export — aus laufendem Vertrag — Vertrag gekündigt | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 12 | Portierung — Export — aus laufendem Vertrag — Vertrag gekündigt | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Winback: Kunden auf 0800 3310 130 verweisen. |
| 13 | Portierung — Export — aus laufendem Vertrag — Vertrag gekündigt | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 14 | Portierung — Export — aus laufendem Vertrag — Vertrag ungekündigt | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 15 | Portierung — Export — aus laufendem Vertrag — Vertrag ungekündigt | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Transfer vermeiden: Portierungserklärung in SalCus "SIM-Details" aktivieren. Kein Transfer bei erkennbarer Kündigungsabsicht. |
| 16 | Portierung — Export — aus laufendem Vertrag — Vertrag ungekündigt | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 17 | Portierung — Import — Beauftragung, Bearbeitungsstand oder Fehler | Hotline – DSL/Glasfaser | o2 Activation Care Fixnet (DSL, FTTH, Kabel) | Transfer in Sprinklr; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr. |
| 18 | Portierung — Import — Beauftragung, Bearbeitungsstand oder Fehler | Hotline – Kabel | o2 Activation Fixnet (DSL/FTTH/Kabel) | Cold transfer; Mo–Fr 8–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 19 | Portierung — Import — Beauftragung, Bearbeitungsstand oder Fehler | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 20 | Portierung — Import — Beauftragung, Bearbeitungsstand oder Fehler | E-Mail – Festnetz | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 21 | Portierung — Import — Beauftragung, Bearbeitungsstand oder Fehler | E-Mail – Mobile | Kein Transfer | Kein Transfer. Ticket Themen-ID 653 an NP-Desk erstellen. |
| 22 | Terminverschiebung / Anfragen Technikertermin für Neuvertrag | Hotline | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 23 | Terminverschiebung / Anfragen Technikertermin für Neuvertrag | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 24 | Vertragsanzweiflung / Betrugsverdacht | Hotline – DSL/Glasfaser / Hotline – Kabel / Hotline – Mobile | Kein Transfer | Kein Transfer. Nur schriftliche Bearbeitung. Checkliste "Vorgehen bei Identitätsmissbrauch" per SMS-Link zusenden. SIM kostenfrei sperren. Ticket Themen-ID 609 (Fraud) erstellen. SalCus-Vorgehen: erfüllt → Inbox "AnzweiflVertr_Fraud"; nicht erfüllt → Fachbereich. Hinweise intern — nicht an Kunden kommunizieren. |
| 25 | Vertragsanzweiflung / Betrugsverdacht | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 609 (Portalanfrage: Themen-ID ändern; sonst: neu anlegen mit vollst. E-Mail-Inhalt). Textbaustein "An Fachabteilung weitergeleitet". |
| 26 | Vertragskopie | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 27 | Vertragskopie | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 28 | Vertragskopie | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |

---

### 18. Vertrag — Vertragsverlängerung

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Laufzeit — Anfrage mit VVL-Wunsch | Hotline – DSL | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | Laufzeit — Anfrage mit VVL-Wunsch | Hotline – Mobile | VVL Mobile – Privatkunden | Cold transfer; Mo–Fr 9–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Nur für Worktypes ohne VVL-Berechtigung AAW. |
| 3 | Laufzeit — Anfrage mit VVL-Wunsch | E-Mail | Kein Transfer | Kein Transfer. Wenn keine Klärung per Solution by Call möglich: Verweis auf Hotline 0176-888 55 222. |
| 4 | Laufzeit — Anfrage ohne VVL-Wunsch | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Wenn möglich: Laufzeit aus SalCus "Vertragsdaten" mitteilen. |
| 5 | Laufzeit — Anfrage ohne VVL-Wunsch | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Wenn möglich: Laufzeit aus SalCus mitteilen. |
| 6 | Laufzeit — Anfrage ohne VVL-Wunsch | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. Wenn möglich: Laufzeit aus SalCus "Vertragsdaten" mitteilen. |
| 7 | Reklamation / Rückfrage nach Vertragsverlängerung | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 8 | Reklamation / Rückfrage nach Vertragsverlängerung | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 9 | Reklamation / Rückfrage nach Vertragsverlängerung | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 10 | Vertragsverlängerung (VVL) Anfrage / Angebot | Hotline – DSL | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 11 | Vertragsverlängerung (VVL) Anfrage / Angebot | Hotline – Mobile | VVL Mobile – Privatkunden | Cold transfer; Mo–Fr 9–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 12 | Vertragsverlängerung (VVL) Anfrage / Angebot | E-Mail | Kein Transfer | Kein Transfer. Wenn keine Klärung per Solution by Call möglich: Verweis auf Hotline 0176-888 55 222. |

---

### 19. Vertrag — Widerruf

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Neuvertrag — DSL | E-Mail – DSL | Kein Transfer | Kein Transfer. Ticket Themen-ID 1671 erstellen; E-Mail-Inhalt vollständig in "Problembeschreibung" kopieren. |
| 2 | Neuvertrag — eRetail | E-Mail | eretail-widerruf@telefonica.com | Forward via Externer Transfer in Sprinklr to eretail-widerruf@telefonica.com. |
| 3 | Neuvertrag — Hotline/Online — nur Storno — Abschluss < 14 Tage | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 4 | Neuvertrag — Hotline/Online — nur Storno — Abschluss < 14 Tage | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 5 | Neuvertrag — Hotline/Online — nur Storno — Abschluss < 14 Tage | E-Mail – Festnetz | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 6 | Neuvertrag — Hotline/Online — nur Storno — Abschluss < 14 Tage | E-Mail – Homespot | EMAIL_O2_WIDERRUF | Transfer in Sprinklr. Hinweis: Kein Transfer aus o2 Care! Stattdessen direkt Ticket 1671 erstellen und Fragebaum befüllen. |
| 7 | Neuvertrag — Hotline/Online — nur Storno — Abschluss < 14 Tage | E-Mail – Mobile | EMAIL_O2_EKL_ONLINESHOP | Transfer in Sprinklr. |
| 8 | Neuvertrag — Hotline/Online — nur Storno — Abschluss > 14 Tage | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 9 | Neuvertrag — Hotline/Online — nur Storno — Abschluss > 14 Tage | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 10 | Neuvertrag — Hotline/Online — nur Storno — Abschluss > 14 Tage | E-Mail | EMAIL_O2_WIDERRUF | Transfer in Sprinklr. |
| 11 | Neuvertrag — Reklamation — Abschluss Hotline/Online | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 12 | Neuvertrag — Reklamation — Abschluss Hotline/Online | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 13 | Neuvertrag — Reklamation — Abschluss Hotline/Online | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 14 | Neuvertrag — Reklamation — Abschluss Shop | Hotline | Kein Transfer | Kein Transfer. Verweis auf Händler oder Händlerbeschwerde. |
| 15 | Neuvertrag — Reklamation — Abschluss Shop | E-Mail | EMAIL_O2_HAENDLERBESCHWERDEN | Transfer in Sprinklr. |
| 16 | Neuvertrag — Shop — Storno | Hotline | Kein Transfer | Kein Transfer. Verweis auf Händler. |
| 17 | Neuvertrag — Shop — Storno | E-Mail | EMAIL_O2_WIDERRUF | Transfer in Sprinklr. |
| 18 | Neuvertrag — Shop — Storno — DSL | E-Mail – DSL | Kein Transfer | Kein Transfer. Ticket Themen-ID 1671 erstellen; E-Mail-Inhalt vollständig in "Problembeschreibung" kopieren. |
| 19 | Vertragsverlängerung — Hotline/Online | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 20 | Vertragsverlängerung — Hotline/Online | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. Transfer vermeiden wenn möglich: Ticket 604 erstellen und Fragebaum befüllen. |
| 21 | Vertragsverlängerung — Hotline/Online | E-Mail | EMAIL_O2_WIDERRUF | Transfer in Sprinklr. |
| 22 | Widerruf — Tarifwechsel, Pack- und Optionsbuchung | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 23 | Widerruf — Tarifwechsel, Pack- und Optionsbuchung | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 24 | Widerruf — Tarifwechsel, Pack- und Optionsbuchung | E-Mail | EMAIL_O2_WIDERRUF | Transfer in Sprinklr. |

---

### 20. Zahlung

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Auszahlung | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 2 | Auszahlung | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 3 | Auszahlung | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 4 | Highspend — nur aktuelle Ticketeinträge und "wichtigen Hinweis" im Kundendatensatz beachten | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 5 | Highspend — nur aktuelle Ticketeinträge und "wichtigen Hinweis" im Kundendatensatz beachten | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 6 | Highspend — nur aktuelle Ticketeinträge und "wichtigen Hinweis" im Kundendatensatz beachten | E-Mail | HUR@telefonica.com | Forward via Externer Transfer in Sprinklr to HUR@telefonica.com. |
| 7 | Inkasso — Rückfragen nach Abgabe | Hotline | Kein Transfer | Kein Transfer. Ansprechpartner ist das Inkassobüro. |
| 8 | Inkasso — Rückfragen nach Abgabe | E-Mail | Kein Transfer | Kein Transfer. Ticket Themen-ID 887 (Portalanfrage: Themen-ID ändern; sonst: neu anlegen mit vollst. E-Mail-Inhalt). Textbaustein "An Fachabteilung weitergeleitet". |
| 9 | Mahnung — Rückfragen | Hotline | Mahnwesen Postpaid | Cold transfer; Mo–Fr 8–18 Uhr; ab 120 s Wartezeit informieren. |
| 10 | Mahnung — Rückfragen | E-Mail | EMAIL_COLLECTIONS | Transfer in Sprinklr. |
| 11 | Ratenzahlung | Hotline | Mahnwesen Postpaid | Cold transfer; Mo–Fr 8–18 Uhr; ab 120 s Wartezeit informieren. Nur CACS-aktive Kunden. Keine Inkassoabgaben. |
| 12 | Ratenzahlung | E-Mail | EMAIL_COLLECTIONS | Transfer in Sprinklr. Nur CACS-aktive Kunden. Keine Inkassoabgaben. |
| 13 | Rechnungslauf ändern | Hotline – DSL/Glasfaser/Kabel | o2 Fixnet Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 14 | Rechnungslauf ändern | Hotline – Mobile | o2 Mobile Care | Cold transfer; Mo–Fr 7–20 Uhr, Sa 10–18 Uhr; ab 120 s Wartezeit informieren. |
| 15 | Rechnungslauf ändern | E-Mail | EMAIL_O2_CARE | HANDLE DIRECTLY. |
| 16 | Rücklastschrift — Ankündigung | Hotline | Mahnwesen Postpaid | Cold transfer; Mo–Fr 8–18 Uhr; ab 120 s Wartezeit informieren. |
| 17 | Rücklastschrift — Ankündigung | E-Mail | EMAIL_COLLECTIONS | Transfer in Sprinklr. |
| 18 | Rücklastschrift — Rückfragen | Hotline | Mahnwesen Postpaid | Cold transfer; Mo–Fr 8–18 Uhr; ab 120 s Wartezeit informieren. |
| 19 | Rücklastschrift — Rückfragen | E-Mail | EMAIL_COLLECTIONS | Transfer in Sprinklr. |
| 20 | Sperrung — Rückfragen | Hotline | Mahnwesen Postpaid | Cold transfer; Mo–Fr 8–18 Uhr; ab 120 s Wartezeit informieren. |
| 21 | Sperrung — Rückfragen | E-Mail | EMAIL_COLLECTIONS | Transfer in Sprinklr. |
| 22 | Umbuchung (Einzahlung unter falscher Kundennummer) | Hotline | Mahnwesen Postpaid | Cold transfer; Mo–Fr 8–18 Uhr; ab 120 s Wartezeit informieren. |
| 23 | Umbuchung (Einzahlung unter falscher Kundennummer) | E-Mail | EMAIL_COLLECTIONS | Transfer in Sprinklr. |
| 24 | Verbleib einer Einzahlung / Überweisung | Hotline | Mahnwesen Postpaid | Cold transfer; Mo–Fr 8–18 Uhr; ab 120 s Wartezeit informieren. Vor Transfer: prüfen ob Überweisung > 2 Tage her und ob an richtige Bankverbindung überwiesen. |
| 25 | Verbleib einer Einzahlung / Überweisung | E-Mail | EMAIL_COLLECTIONS | Transfer in Sprinklr. |
| 26 | Zahlung — Zahlungsaufschub — CACS-Status "rot" | Hotline | Mahnwesen Postpaid | Cold transfer; Mo–Fr 8–18 Uhr; ab 120 s Wartezeit informieren. |
| 27 | Zahlung — Zahlungsaufschub — CACS-Status "rot" | E-Mail | EMAIL_COLLECTIONS | Transfer in Sprinklr. |

---

## Removed / Legacy Transfer Goals

The following Sprinklr queue names from previous versions of this matrix are **no longer used** after the 2026-09-18 remap:

| Former Goal | Replacement |
|---|---|
| CBC_CARE_ALLGEMEIN | EMAIL_O2_CARE (email) / handle directly |
| CBC_KUENDIGUNGEN_SME_SOHO | EMAIL_O2_KUENDIGUNGEN_SME_SOHO |
| CBC_XF_E_COLLECTIONS | EMAIL_COLLECTIONS |
| CBC_XF_E_VERTRAGSSTILLLEGUNG | EMAIL_O2_VERTRAGSSTILLEGUNG |
| CBC_XF_E_WIDERRUF | EMAIL_O2_WIDERRUF |
| CBC_XF_E_KUNDENDATEN | EMAIL_O2_KUNDENDATEN |
| CS_XF_E_HARDWARE | EMAIL_O2_MOBILE_TECHNIK (email) / o2 Tech Mobile (hotline) |
| BUSINESS-TEAM | See matrix — routing now channel-specific |
| KUENDIGUNG_RECHNUNG | EMAIL_O2_KUENDIGUNG_RECHNUNG |
| AS_E_XF_DSL_SALCUS_KUENDIGUNG_ANFRAGEN_2ND_LEVEL | Inactive — Kein Transfer, handle per KB |
| EKL_Onlineshop | EMAIL_O2_EKL_ONLINESHOP |
| ALDITALK_XF_SERVICE | alditalk@cc.o2online.de (Externer Transfer) |
| AYYILDIZ_XF_POSTPAID | ayyildiz@cc.o2online.de (Externer Transfer) |
| AYYILDIZ_XF_PREPAID | ayyildiz@cc.o2online.de (Externer Transfer) |
| NETTOKOM_XF_SERVICE | nettokom@cc.o2online.de (Externer Transfer) |
| WHATSAPPSIM_XF_SERVICE | whatsappsim@cc.o2online.de (Externer Transfer) |
| WHITELABEL_XF_SERVICE | service@kunde.aetkasmart.de (Externer Transfer) |
| CS_E_XF_AKTION1 | EMAIL_O2_KUENDIGUNGEN_NETZ |
| CS_E_XF_AKTION2 | EMAIL_O2_KUENDIGUNGEN_AUSLAND |
| DM_XF_E_HAENDLERBESCHWERDEN | EMAIL_O2_HAENDLERBESCHWERDEN |
| WB_ANFRAGEN_PRESSESTELLE | See matrix Thema 1 — Kein Transfer |
| CS_XF_E_LOOP_ALLGEMEIN | See matrix Thema 2 — o2 Prepaid/Loop |
| CBC_ENGLISCH | EMAIL_O2_ENGLISCH |
| CS_Premium | See matrix — Exklusiv-Kunden routing |
| CS_E_XF_SELBSTSTAENDIGE | EMAIL_O2_SOHO (email) / oneSoho Care (hotline) |
| BLAU_XF_IMPRESSUM | See matrix Thema 2 — BLAU |
| BLAU_E_XF_PREPAID | EMAIL_BLAU_PREPAID_CARE |

---

> **BACKDOOR FOR UPDATES**: When a transfer goal changes, find the row and update Ziel-Kontakt + Action.
> When a goal is retired, add it to the Removed section above.
> Last full remap: **2026-09-18** from 512 Sabio screenshots.
> Use the `update-transfer-goals` skill for targeted updates.
