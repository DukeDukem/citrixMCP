# Transfer Matrix (Sabio Transfermatrix)

> Extracted from transfer tree screenshots. Kanal is always **E-Mail** (unless noted otherwise).
> Our domain: **CBC_CARE_ALLGEMEIN** -- cases with this Ziel-Kontakt stay with us and are processed directly.
> Sprinklr (SIKAS) is the active platform. WDE notes are disregarded.

## How to use this document

1. **Identify the Thema** (topic) from the customer email.
2. **Identify the Fall** (case type) that matches.
3. **Look up the Ziel-Kontakt** (transfer goal).
4. **If Ziel-Kontakt = CBC_CARE_ALLGEMEIN**: Handle the case directly -- summarize, query KnowledgeBase, advise agent, draft reply.
5. **If Ziel-Kontakt = another team/queue**: Transfer the case to that team in Sprinklr. Inform customer the case has been forwarded.
6. **If Ziel-Kontakt = an email address**: Forward the case/documents to that email address.
7. **If Ziel-Kontakt = "Kein Transfer"**: Follow the specific handling instructions in the notes column (refer to hotline, use text block, handle per knowledge base, etc.).
8. **If Ziel-Kontakt = a ticket instruction**: Create the specified ticket (e.g., "Ticket Themen-ID 653 an NP-Desk").

---

## Quick Reference: All Transfer Goals

### Cases WE handle (CBC_CARE_ALLGEMEIN)

These cases stay with us. Process directly: summarize, verify customer, query KB, draft reply, instruct agent.

### Cases transferred to other teams

| Transfer Goal | Description |
|---|---|
| AS_DSL_SALCUS_KUENDIGUNG_ANFRAGEN_2ND_LEVEL | DSL cancellation 2nd level team |
| ALDITALK_XF_SERVICE | ALDI TALK service |
| AYYILDIZ_XF_POSTPAID | AY YILDIZ postpaid |
| AYYILDIZ_XF_PREPAID | AY YILDIZ prepaid |
| BLAU_XF_IMPRESSUM | Blau postpaid |
| BLAU_E_XF_PREPAID | Blau prepaid |
| BUSINESS-TEAM | Business customers (mobile) |
| CBC_ENGLISCH | English-language care |
| CBC_Kundendaten | Customer data / bank details team |
| CBC_KUENDIGUNGEN_SME_SOHO | Cancellation team (SME/SOHO + specific mobile cases) |
| CBC_Vertragsstillegung | Contract suspension team |
| CBC_Widerruf | Revocation/withdrawal team |
| CBC_XF_Collections | Collections / dunning / payment team |
| CS_E_XF_SELBSTSTAENDIGE | Self-employed (SOHO) service |
| CS_Hardware | Hardware support team |
| CS_Premium | Premium/VIP customer service |
| CS_XF_AKTION1 | Retention - network availability cancellations |
| CS_XF_AKTION2 | Retention - move abroad cancellations |
| CS_XF_LOOP_Allgemein | o2 Prepaid/Loop service |
| DM_HAENDLERBESCHWERDEN | Dealer complaints team |
| EKL_Onlineshop | Online shop revocation team |
| KUENDIGUNG_RECHNUNG | Cancellation due to billing/service complaints |
| NETTOKOM_XF_SERVICE | NettoKOM service |
| WB_ANFRAGEN_PRESSESTELLE | Press office |
| WHATSAPPSIM_XF_SERVICE | WhatsApp SIM service |
| WHITELABEL_XF_SERVICE | Whitelabel service (Mobilka, aetkaSMART) |

### Email-based transfers

| Email | When to use |
|---|---|
| geschaeftskunden-service@telefonica.com | Business customers (DSL) |
| DS_Beauskunftung@telefonica.com | GDPR data disclosure requests |
| eretail-widerruf@telefonica.com | eRetail revocation |
| Fremdcarrier-D019@telefonica.com | Festnetz import porting (DSL/Kabel/FTTH) |
| HUR@telefonica.com | High-spend payment cases |
| o2-portierung@telefonica.com | Festnetz number porting import (Homezone/Homespot) |
| o2-rufnummernmitnahme@telefonica.com | MNP import - incoming porting documents |
| Verbraucherauskunft@telefonica.com | Bundesnetzagentur (BNA) inquiries |

---

## Full Transfer Matrix by Thema

---

### 1. andere Kundentypen (z. B. SOHO, Business, Haendler, Presse, o.Ae.)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 1 | Aemter/Sicherheitsbehoerden (Polizei, Gericht, Staatsanwaltschaft) - Anfragen | Alle Kanaele | Kein Transfer | Do not process directly. Use text block "anfragen_von_behoerden" (Sprinklr). Refer to internal security department. |
| 2 | Businesskunde | E-Mail - DSL | geschaeftskunden-service@telefonica.com | Forward to email |
| 3 | Businesskunde | E-Mail - Mobile | BUSINESS-TEAM | Transfer in Sprinklr |
| 4 | Exklusiv-Kunden (nur Servicetyp "Premium TOP" und "VIP") | E-Mail | CS_Premium | Transfer in Sprinklr |
| 5 | Geschaeftsfuehrung - Beschwerde | E-Mail | Kein Transfer | Handle per KB guidelines for executive complaints |
| 6 | Haendleranfragen (Haendlerstornos, provisionsrelevante Aenderungen, etc.) | E-Mail | Kein Transfer | Handle per KB |
| 7 | Haendlerbeschwerde - Kundenbeschwerden ueber Vertriebspartner (Haendlernr. 12/13/14/19) | E-Mail | DM_HAENDLERBESCHWERDEN | Transfer in Sprinklr |
| 8 | Journalisten / Presse - Anfragen | E-Mail | WB_ANFRAGEN_PRESSESTELLE | Transfer in Sprinklr |
| 9 | Mitarbeiter - Anfrage zum Vertrag | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** (employee service card policies apply - see KB for Dienstkarten rules) |
| 10 | Rechtsanwalt - im Auftrag eines Kunden | E-Mail | Kein Transfer | Handle per KB and Authentifizierung rules; do NOT process via Backoffice if third-party request |
| 11 | Rechtsanwalt - in eigener Sache | E-Mail | Kein Transfer | Handle per KB |
| 12 | Selbststaendige (SOHO) - kaufmaennisch/technisch - alle sonstigen Anfragen | E-Mail | CS_E_XF_SELBSTSTAENDIGE | Transfer in Sprinklr |
| 13 | Selbststaendige (SOHO) - Kuendigung | E-Mail - Mobile | CBC_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr |
| 14 | Selbststaendige (SOHO) - Stammdaten-Aenderung per Brief/Fax/E-Mail | E-Mail | CS_E_XF_SELBSTSTAENDIGE | Transfer in Sprinklr |
| 15 | SOHO | E-Mail | CS_E_XF_SELBSTSTAENDIGE | Transfer in Sprinklr |
| 16 | Verbraucherschutz - Anfragen | E-Mail | Kein Transfer | Handle per KB |
| 17 | Verbraucherschutz - Anfragen von der Bundesnetzagentur | E-Mail | Verbraucherauskunft@telefonica.com | Forward to email |

---

### 2. andere Marken (z. B. Aldi, Blau, Prepaid)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 18 | ALDI TALK | E-Mail | ALDITALK_XF_SERVICE | Transfer in Sprinklr |
| 19 | AOL Anfragen | Alle Kanaele | Kein Transfer | Inform customer AOL is discontinued; handle per KB |
| 20 | AY YILDIZ | E-Mail - Postpaid | AYYILDIZ_XF_POSTPAID | Transfer in Sprinklr |
| 21 | AY YILDIZ | E-Mail - Prepaid | AYYILDIZ_XF_PREPAID | Transfer in Sprinklr |
| 22 | BLAU | E-Mail - Postpaid | BLAU_XF_IMPRESSUM | Transfer in Sprinklr |
| 23 | BLAU | E-Mail - Prepaid | BLAU_E_XF_PREPAID | Transfer in Sprinklr |
| 24 | FONIC | E-Mail | Kein Transfer | Refer customer to FONIC directly (Hotline: 0176 8888 0000, service@fonic.de) |
| 25 | Mobilka | E-Mail | WHITELABEL_XF_SERVICE | Transfer in Sprinklr |
| 26 | NettoKOM | E-Mail | NETTOKOM_XF_SERVICE | Transfer in Sprinklr |
| 27 | novamobil | E-Mail | Kein Transfer | Handle per KB |
| 28 | o2 Prepaid/Loop | E-Mail | CS_XF_LOOP_Allgemein | Transfer in Sprinklr |
| 29 | simyo | E-Mail | Kein Transfer | Handle per KB |
| 30 | Tchibo mobil | E-Mail | Kein Transfer | Refer customer to Tchibo MOBIL (040-605 90 00 95) |
| 31 | WhatsApp SIM | E-Mail | WHATSAPPSIM_XF_SERVICE | Transfer in Sprinklr |
| 32 | Whitelabel (aetkaSMART) | E-Mail | WHITELABEL_XF_SERVICE | Transfer in Sprinklr |

---

### 3. Englisch/Tuerkisch (o2 Postpaid Privatkunden)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 33 | Inhouse Dunning - Englisch | E-Mail | CBC_XF_Collections | Transfer in Sprinklr |
| 34 | Vertragsthemen o2 Postpaid Care - Englisch | E-Mail | CBC_ENGLISCH | Transfer in Sprinklr |
| 35 | Vertragsthemen o2 Postpaid Care - Tuerkisch | Hotline | Tuerkisch o2 Care | Refer customer to Turkish hotline |

---

### 4. Hardware - Benutzen & Defekt

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 36 | Defekt - Beschwerde ueber Bearbeitung | E-Mail | CS_Hardware | Transfer in Sprinklr |
| 37 | Defekt - DSL Router | E-Mail | Kein Transfer | Handle per KB (router troubleshooting) |
| 38 | Defekt - mobile Hardware | E-Mail | CS_Hardware | Transfer in Sprinklr |
| 39 | DSL-Zugangsdaten, MAC-Adresse und Telefon-PIN | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 40 | Installation, Nutzung, Hilfe - DSL/Glasfaser/Kabel Router | E-Mail | Kein Transfer | Handle per KB (installation guides) |
| 41 | Installation, Nutzung, Hilfe - mobile Hardware/Homespot | E-Mail | CS_Hardware | Transfer in Sprinklr |
| 42 | WLAN-Hotspots | E-Mail | CS_Hardware | Transfer in Sprinklr |

---

### 5. Hardware - Logistik, Beratung & Vertrag

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 43 | Beratung zu Hardware und Routern | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 44 | Fundsachen/Fundbuero (kein Prepaid) | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 45 | Handyversicherung | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 46 | Logistik - Lieferung und Retouren | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 47 | o2 My Handy - Fragen zum Ratenplan | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 48 | o2 My Handy - Vorzeitige Vertragsaufloesung beantragen & Beschwerden | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 49 | o2 My Handy - Vorzeitige Vertragsaufloesung stornieren | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |

---

### 6. Hardware - SIM Karte & Sperren

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 50 | eSIM Installation, Einrichten, Synchronisieren, Beeintraechtigungen | E-Mail | CS_Hardware | Transfer in Sprinklr |
| 51 | eSIM/SIM/Multicard/Datacard - Bestellung, Tausch, Versand, Aktivierung, Deaktivierung | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 52 | PIN/PUK - Auskunft | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 53 | Sperren & Entsperren (SIM, DSL, Drittanbieter etc.) | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |

---

### 7. Rechnung

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 54 | Aendern/Einrichten Rechnungseinstellungen (Rechnungsart, Zustellungsart, EVN-Typ) | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 55 | Anfrage/Reklamation Rechnungsinhalt | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 56 | Drittanbieter - Reklamation/Anzweiflung | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 57 | Rechnungsduplikat | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 58 | Rechnungsduplikat Hardware | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |

---

### 8. Roaming

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 59 | Kaufmaennisch - Optionen und Kosten | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 60 | Technisch - Nutzung im Ausland nicht moeglich | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |

---

### 9. Rufnummernmitnahme Festnetz I@H (DSL, Kabel, FTTH)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 61 | Export - Beauftragung auflaufendem Vertrag, gekuendigt | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 62 | Export - Beauftragung auflaufendem Vertrag, ungekuendigt | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 63 | Import - Rufnummernmitnahme zu DSL, Kabel, Glasfaser - Auftrag, Terminverschiebung | E-Mail | Fremdcarrier-D019@telefonica.com | Forward to email |

---

### 10. Rufnummernmitnahme Festnetznummer (Homezone und Homespot)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 64 | Export - Portierungsstatus unklar | Alle Kanaele | Kein Transfer | Handle per KB (check porting status in system) |
| 65 | Import - Beauftragung per Formular | E-Mail | o2-portierung@telefonica.com | Forward to email |
| 66 | Import - Portierungsstatus unklar | Alle Kanaele | Kein Transfer | Handle per KB |

---

### 11. Rufnummernmitnahme MNP (Mobilfunknummer)

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 67 | Betrugsverdacht | E-Mail | Kein Transfer | Handle per KB (fraud procedures) |
| 68 | Export - Portierungserklaerung zur Freigabe aus dem Vertrag | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 69 | Import - automatische Aenderung Portierungstermin | Alle Kanaele | Kein Transfer | Handle per KB |
| 70 | Import - Beauftragung (ausser interne Portierung) | Alle Kanaele | Kein Transfer | Handle per KB |
| 71 | Import - Eingang wichtiger Dokumente (Portierungsauftraege, Kuendigungsbestaetigung, MNP Beschwerden) | E-Mail | o2-rufnummernmitnahme@telefonica.com | Forward to email |
| 72 | Import - Portierungsstatus unklar | Alle Kanaele | Kein Transfer | Handle per KB (check porting status) |
| 73 | Import - Sonstiges/spezieller Fehlerfall | E-Mail | Kein Transfer | Handle per KB |
| 74 | Import - Storno fuer Portierung zum Vertragsende | Alle Kanaele | Kein Transfer | Handle per KB |
| 75 | interne Portierung (innerhalb Telefonica Marken) | Alle Kanaele | Kein Transfer | Handle per KB; use internal porting form via Shorty SMS |

---

### 12. Self Service

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 76 | Newsletter | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 77 | o2 Apps (z. B. Mein o2, o2 Protect) | E-Mail | CS_Hardware | Transfer in Sprinklr |
| 78 | o2 E-Mail | E-Mail - Festnetz | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 79 | o2 E-Mail | E-Mail - Mobile | CS_Hardware | Transfer in Sprinklr |
| 80 | o2.de Portal | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |

---

### 13. Stoerung

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 81 | DSL | E-Mail | Kein Transfer | Handle per KB (DSL troubleshooting) |
| 82 | Forderung Entschaedigung/Minderung EECC TKG | E-Mail | Kein Transfer | Handle per KB (EECC compensation rules) |
| 83 | Homespot | E-Mail | CS_Hardware | Transfer in Sprinklr |
| 84 | Kabel | E-Mail | Kein Transfer | Handle per KB (cable troubleshooting) |
| 85 | Mailbox, Visual Voice Mail, o2 Voicemail | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 86 | MMS | E-Mail | CS_Hardware | Transfer in Sprinklr |
| 87 | Mobilfunk Daten (Ursache vermutlich Hardware/Konfiguration) | E-Mail | CS_Hardware | Transfer in Sprinklr |
| 88 | Mobilfunk Daten (Ursache vermutlich Netz) | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 89 | Mobilfunk Daten (Netz) - Anfragen Bundesnetzagentur | E-Mail | Verbraucherauskunft@telefonica.com | Forward to email |
| 90 | Mobilfunk Sprache | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 91 | Mobilfunk Sprache - Anfragen Bundesnetzagentur | E-Mail | Verbraucherauskunft@telefonica.com | Forward to email |
| 92 | o2 Mehrwertdienste (keine Drittanbieterdienste) | E-Mail | CS_Hardware | Transfer in Sprinklr |

---

### 14. Vertrag - Kuendigung

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 93 | Androhung, Fristen, Ablauf - fristgerecht & ausserordentlich | E-Mail - Festnetz | AS_DSL_SALCUS_KUENDIGUNG_ANFRAGEN_2ND_LEVEL | Transfer in Sprinklr |
| 94 | Androhung, Fristen, Ablauf - fristgerecht & ausserordentlich | E-Mail - Mobile | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 95 | Beschwerde ueber fehlende Kuendigungsbestaetigung / verzoegerte Deaktivierung | E-Mail - Festnetz | AS_DSL_SALCUS_KUENDIGUNG_ANFRAGEN_2ND_LEVEL | Transfer in Sprinklr |
| 96 | Beschwerde ueber fehlende Kuendigungsbestaetigung / verzoegerte Deaktivierung | E-Mail - Mobile/FMS | CBC_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr |
| 97 | eingehende Kuendigung - ausserordentlich (AOK) - DSL - sonstige Faelle | E-Mail | Kein Transfer | Handle per KB (AOK DSL procedures) |
| 98 | eingehende Kuendigung - ausserordentlich (AOK) - DSL - specific cases | E-Mail | AS_DSL_SALCUS_KUENDIGUNG_ANFRAGEN_2ND_LEVEL | Transfer in Sprinklr |
| 99 | eingehende Kuendigung - AOK - Mobile/FMS - Haft/Krankheit/Nutzertod | E-Mail | CBC_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr |
| 100 | eingehende Kuendigung - AOK - Mobile/FMS - Insolvenz | E-Mail | Kein Transfer | Handle per KB (insolvency procedures) |
| 101 | eingehende Kuendigung - AOK - Mobile/FMS - Handydefekt | E-Mail | CS_Hardware | Transfer in Sprinklr |
| 102 | eingehende Kuendigung - AOK - Mobile/FMS - Handyverlust | E-Mail | CBC_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr |
| 103 | eingehende Kuendigung - AOK - Mobile/FMS - Netzverfuegbarkeit | E-Mail | CS_XF_AKTION1 | Transfer in Sprinklr |
| 104 | eingehende Kuendigung - AOK - Mobile/FMS - Rechnungs-/Servicebeschwerde | E-Mail | KUENDIGUNG_RECHNUNG | Transfer in Sprinklr |
| 105 | eingehende Kuendigung - AOK - Mobile/FMS - Todesfall Vertragsinhaber | E-Mail | Kein Transfer | Handle per KB (death of account holder procedures) |
| 106 | eingehende Kuendigung - AOK - Mobile/FMS - Umzug ins Ausland | E-Mail | CS_XF_AKTION2 | Transfer in Sprinklr |
| 107 | eingehende Kuendigung - fristgerecht - DSL | E-Mail - DSL | AS_DSL_SALCUS_KUENDIGUNG_ANFRAGEN_2ND_LEVEL | Transfer in Sprinklr |
| 108 | eingehende Kuendigung - fristgerecht - Mobile Handydefekt | E-Mail | CS_Hardware | Transfer in Sprinklr |
| 109 | eingehende Kuendigung - fristgerecht - Mobile Rechnungs-/Servicebeschwerde | E-Mail | KUENDIGUNG_RECHNUNG | Transfer in Sprinklr |
| 110 | eingehende Kuendigung - fristgerecht - Mobile/FMS Netzverfuegbarkeit | E-Mail | CS_XF_AKTION1 | Transfer in Sprinklr |
| 118 | Kuendigungstermin falsch hinterlegt | E-Mail - Mobile/FMS | CBC_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr |
| 119 | Reaktivierungswunsch durch Kunde | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 120 | Reklamation Kuendigungsruecknahme | E-Mail - DSL | AS_DSL_SALCUS_KUENDIGUNG_ANFRAGEN_2ND_LEVEL | Transfer in Sprinklr |
| 121 | Reklamation Kuendigungsruecknahme | E-Mail - Mobile/FMS | CBC_KUENDIGUNGEN_SME_SOHO | Transfer in Sprinklr |

---

### 15. Vertrag - Stammdaten

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 122 | Accountzusammenfuehren/-trennung | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 123 | Bankverbindung / SEPA / Einzugsermaechtigung aendern / erteilen / widerrufen | E-Mail | CBC_Kundendaten | Transfer in Sprinklr |
| 124 | Beauskunftung gemaess DSGVO (Datenschutz) | E-Mail | DS_Beauskunftung@telefonica.com | Forward to email |
| 125 | Betreuung (Unterlagen zur gesetzlichen Betreuung von Kunden) | E-Mail | Kein Transfer | Handle per KB (guardianship documentation) |
| 126 | Datenschutzanfragen allgemein | E-Mail | Kein Transfer | Handle per KB |
| 127 | Festnetz - Umzug | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 128 | Kundendaten aendern (Name, Adresse, Geburtsdatum) | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 129 | Kundeneinwilligung/Permission Aenderung/Beschwerde | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 130 | Kundenkennzahl aendern | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 131 | Kundentyp aendern (Privat auf SOHO) | E-Mail | CS_E_XF_SELBSTSTAENDIGE | Transfer in Sprinklr |
| 132 | Kundentyp aendern (SOHO auf Privat) | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 133 | Vertragslaufzeit Anfrage | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 134 | Vertragsstilllegung | E-Mail | CBC_Vertragsstillegung | Transfer in Sprinklr |
| 135 | Vertragsuebernahme/Inhaberwechsel | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |

---

### 16. Vertrag - Tarife & Optionen

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 136 | Information zu Produkten, Optionen und Tarifen | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 137 | Mailbox (Infos, Menue, Kontaktwege etc.) | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 138 | Packs und Optionen aktivieren & deaktivieren | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 139 | Reklamation zu Tarif-, Pack- oder Optionswechsel (wenn nicht im Shop durchgefuehrt) | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 140 | Rufnummerntausch | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 141 | Super Select Tarife (Mediamarkt/Saturn) | Alle Kanaele | Kein Transfer | Refer customer to Mediamarkt/Saturn |

---

### 17. Vertrag - Vertragsabschluss

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 145 | Ablehnung Neuvertrag (z. B. Bonitaet) - Anfrage/Reklamation | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 146 | DSL-Auftrag im Aktivierungs-Status - Rueckfragen | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 147 | Neuvertrag - Interessentenanfrage | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 148 | Neuvertrag - Reklamation - Abschluss Hotline/Online | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 149 | Portierung - Export - aus laufendem Vertrag - gekuendigt | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 150 | Portierung - Export - aus laufendem Vertrag - ungekuendigt | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 151 | Portierung - Import - Beauftragung/Bearbeitungsstand/Fehler | E-Mail - Festnetz | Fremdcarrier-D019@telefonica.com | Forward to email |
| 152 | Portierung - Import - Beauftragung/Bearbeitungsstand/Fehler | E-Mail - Mobile | Ticket Themen-ID 653 an NP-Desk erstellen | Create SalCus ticket with Themen-ID 653, forward to NP-Desk |
| 153 | Terminverschiebung/Anfragen Technikertermin fuer Neuvertrag | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 154 | Vertragsanzweiflung/Betrugsverdacht | E-Mail | Kein Transfer | Handle per KB (fraud/contract dispute procedures) |
| 155 | Vertragskopie | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |

---

### 18. Vertrag - Vertragsverlaengerung

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 156 | Vertragsverlaengerung (VVL) Anfrage / Angebot | E-Mail | Kein Transfer | Refer customer to hotline (089 78 79 79 400) -- Backoffice does not handle VVL offers/sales |
| 157 | Laufzeit - Anfrage ohne VVL-Wunsch | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 158 | Reklamation/Rueckfrage nach Vertragsverlaengerung | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |

---

### 19. Vertrag - Widerruf

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 160 | Neuvertrag - DSL | E-Mail - DSL | Kein Transfer | Handle per KB (DSL revocation procedure) |
| 161 | Neuvertrag - eRetail | E-Mail | eretail-widerruf@telefonica.com | Forward to email |
| 162 | Neuvertrag - Hotline/Online - nur Storno - Abschluss < 14 Tage | E-Mail - Festnetz | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 163 | Neuvertrag - Hotline/Online - nur Storno - Abschluss < 14 Tage | E-Mail - Homespot | CBC_Widerruf | Transfer in Sprinklr |
| 164 | Neuvertrag - Hotline/Online - nur Storno - Abschluss < 14 Tage | E-Mail - Mobile | EKL_Onlineshop | Transfer in Sprinklr |
| 165 | Neuvertrag - Hotline/Online - nur Storno - Abschluss > 14 Tage | E-Mail | CBC_Widerruf | Transfer in Sprinklr |
| 166 | Neuvertrag - Reklamation - Abschluss Hotline/Online | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 167 | Neuvertrag - Reklamation - Abschluss Shop | E-Mail | DM_HAENDLERBESCHWERDEN | Transfer in Sprinklr |
| 168 | Neuvertrag - Shop - Storno | E-Mail | CBC_Widerruf | Transfer in Sprinklr |
| 169 | Neuvertrag - Shop - Storno - DSL | E-Mail - DSL | Kein Transfer | Handle per KB |
| 170 | Vertragsverlaengerung - Hotline/Online | E-Mail | CBC_Widerruf | Transfer in Sprinklr |
| 171 | Widerruf - Tarifwechsel, Pack- und Optionsbuchung | E-Mail | CBC_Widerruf | Transfer in Sprinklr |

---

### 20. Zahlung

| # | Fall | Kanal | Ziel-Kontakt | Action |
|---|---|---|---|---|
| 172 | Auszahlung | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 173 | Highspend - NUR aktuelle Ticketeintraege und "wichtigen Hinweis" im Kundendatensatz beachten | E-Mail | HUR@telefonica.com | Forward to email |
| 174 | Inkasso - Rueckfragen nach Abgabe | E-Mail | Kein Transfer | Handle per KB (post-collection inquiry procedures) |
| 175 | Mahnung - Rueckfragen | E-Mail | CBC_XF_Collections | Transfer in Sprinklr |
| 176 | Ratenzahlung | E-Mail | CBC_XF_Collections | Transfer in Sprinklr |
| 177 | Rechnungslauf aendern | E-Mail | **CBC_CARE_ALLGEMEIN** | **HANDLE DIRECTLY** |
| 178 | Ruecklastschrift - Ankuendigung | E-Mail | CBC_XF_Collections | Transfer in Sprinklr |
| 179 | Ruecklastschrift - Rueckfragen | E-Mail | CBC_XF_Collections | Transfer in Sprinklr |
| 180 | Sperrung - Rueckfragen | E-Mail | CBC_XF_Collections | Transfer in Sprinklr |
| 181 | Umbuchung (Einzahlung unter falscher Kundennummer) | E-Mail | CBC_XF_Collections | Transfer in Sprinklr |
| 182 | Verbleib einer Einzahlung / Ueberweisung | E-Mail | CBC_XF_Collections | Transfer in Sprinklr |
| 183 | Zahlung - Zahlungsaufschub - CACS-Status "rof" | E-Mail | CBC_XF_Collections | Transfer in Sprinklr |

---

## Transfer Goal Name Registry

> **BACKDOOR FOR UPDATES**: Transfer goal names may be updated. When instructed to rename a transfer goal,
> search this file for the old name and replace with the new name throughout.
> Use the `update-transfer-goals` skill or manually grep and replace.

Current transfer goal names and their last-known status:

| Transfer Goal | Status | Last Updated |
|---|---|---|
| AS_DSL_SALCUS_KUENDIGUNG_ANFRAGEN_2ND_LEVEL | Active | 2026-03-02 |
| ALDITALK_XF_SERVICE | Active | 2026-03-02 |
| AYYILDIZ_XF_POSTPAID | Active | 2026-03-02 |
| AYYILDIZ_XF_PREPAID | Active | 2026-03-02 |
| BLAU_XF_IMPRESSUM | Active | 2026-03-02 |
| BLAU_E_XF_PREPAID | Active | 2026-03-02 |
| BUSINESS-TEAM | Active | 2026-03-02 |
| CBC_CARE_ALLGEMEIN | Active (US) | 2026-03-02 |
| CBC_ENGLISCH | Active | 2026-03-02 |
| CBC_Kundendaten | Active | 2026-03-02 |
| CBC_KUENDIGUNGEN_SME_SOHO | Active | 2026-03-02 |
| CBC_Vertragsstillegung | Active | 2026-03-02 |
| CBC_Widerruf | Active | 2026-03-02 |
| CBC_XF_Collections | Active | 2026-03-02 |
| CS_E_XF_SELBSTSTAENDIGE | Active | 2026-03-02 |
| CS_Hardware | Active | 2026-03-02 |
| CS_Premium | Active | 2026-03-02 |
| CS_XF_AKTION1 | Active | 2026-03-02 |
| CS_XF_AKTION2 | Active | 2026-03-02 |
| CS_XF_LOOP_Allgemein | Active | 2026-03-02 |
| DM_HAENDLERBESCHWERDEN | Active | 2026-03-02 |
| EKL_Onlineshop | Active | 2026-03-02 |
| KUENDIGUNG_RECHNUNG | Active | 2026-03-02 |
| NETTOKOM_XF_SERVICE | Active | 2026-03-02 |
| WB_ANFRAGEN_PRESSESTELLE | Active | 2026-03-02 |
| WHATSAPPSIM_XF_SERVICE | Active | 2026-03-02 |
| WHITELABEL_XF_SERVICE | Active | 2026-03-02 |
