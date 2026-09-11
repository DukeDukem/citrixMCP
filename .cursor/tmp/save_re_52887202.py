# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Heike Spielmann,

vielen Dank, dass Sie uns das Login-Problem in Mein o2 geschildert haben – insbesondere, dass Sie Ihre Mobilfunkrechnung nicht einsehen können und nach Kennwort vergessen mit SMS-Code in einer Abfrage-Schleife hängen bleiben. Gut zu wissen ist zudem, dass Sie seit April zusätzlich einen o2 Home-Anschluss haben.

Es ist verständlich, dass Sie ohne funktionierenden Zugang keine Rechnungen abrufen können.

Bitte versuchen Sie nacheinander diese Schritte unter o2.de / Mein o2 bzw. in der Mein o2 App:
- Melden Sie sich mit Ihrer Mobilfunknummer als Benutzername an, um den Mobilfunkvertrag und die Rechnungen zu öffnen.
- Für den Home-/Festnetzvertrag ggf. separat mit der Festnetznummer anmelden (Mobilfunk und Festnetz können unterschiedliche Logins haben).
- Nutzen Sie „Kennwort vergessen“ und prüfen Sie, ob der Code alternativ per E-Mail wählbar ist; tippen Sie Rufnummer und Code manuell ein (nicht per Copy & Paste).
- Testen Sie einen anderen Browser bzw. den Inkognito-Modus und leeren Sie Cache/Cookies für o2.de.
- Nach erfolgreichem Login prüfen Sie oben den Vertragswechsel (Dropdown), falls beide Verträge sichtbar sind, und öffnen Sie unter Rechnung die gewünschte Mobilfunkrechnung.

Falls der Login weiterhin in der Schleife bleibt, antworten Sie bitte mit Ihrer Mobilfunknummer und – sofern vorhanden – Ihrer Festnetznummer bzw. Kundennummer. Dann können wir den Zugang gezielter zuordnen.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert text.count("Guten Tag") == 1
assert "Fall #" not in text
assert "Heike Spielmann" in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52887202.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52887202", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
