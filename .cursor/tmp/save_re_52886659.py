# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Monika Christian Rehm,

vielen Dank, dass Sie uns die Roamingkosten von 59,49 Euro nach Ihrem Urlaub auf Kos und die unbeabsichtigte Einbuchung in ein türkisches Netz geschildert haben.

Es ist verständlich, dass Sie überrascht sind, obwohl Sie sich nicht in der Türkei aufgehalten haben – an der Küste von Kos kommt es durch die Nähe zur türkischen Grenze immer wieder zu solchen Netzwechseln.

Bitte prüfen Sie die Position zunächst in Mein o2 unter o2.de bzw. in der Mein o2 App unter Rechnung und ggf. Einzelverbindungsnachweis, damit die Datennutzung außerhalb der EU nachvollziehbar ist.

Für künftige Aufenthalte in Grenzregionen empfehlen wir:
- in den Handy-Einstellungen die automatische Netzwahl zu deaktivieren und manuell ein griechisches Netz zu wählen,
- auf Roaming-Info-SMS und den Kostenschutz zu achten,
- unter o2.de die aktuellen Roaming-Hinweise für Nicht-EU-Länder nachzulesen.

Damit wir Ihren Vertrag eindeutig zuordnen können, senden Sie uns bitte zusätzlich Ihre Kundennummer und Ihre Mobilfunknummer (oder zumindest die letzten Ziffern). Eine Kulanzentscheidung zu den 59,49 Euro hängt vom konkreten Rechnungs- und Nutzungsverlauf ab; ohne Zusicherung einer Erstattung prüfen Sie bitte parallel, ob auf der aktuellen Rechnung noch weitere Auslandspositionen ausgewiesen sind.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

# soften - "ohne Zusicherung" is good. Avoid sounding like we refuse - agent may grant later.
assert text.count("Guten Tag") == 1
assert "Fall #" not in text
assert "59,49" in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52886659.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52886659", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
