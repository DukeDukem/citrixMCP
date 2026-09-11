# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Monika Christian Rehm,

vielen Dank, dass Sie uns die Roamingkosten von 59,49 Euro nach Ihrem Urlaub auf Kos und die unbeabsichtigte Einbuchung in ein türkisches Netz geschildert haben.

Es ist verständlich, dass Sie überrascht sind, obwohl Sie sich nicht in der Türkei aufgehalten haben – an der Küste von Kos kommt es durch die Nähe zur türkischen Grenze immer wieder zu solchen Netzwechseln.

Nach Prüfung der Sachlage müssen wir Ihnen mitteilen, dass wir die entstandenen Kosten von 59,49 Euro für Datennutzung außerhalb der EU leider nicht erstatten können. Die Abrechnung ist berechtigt: Bei Einbuchung in ein türkisches Netz gelten die Roamingtarife außerhalb der EU, auch wenn Sie sich physisch auf griechischem Gebiet aufgehalten haben.

Bitte prüfen Sie die Position bei Bedarf in Mein o2 unter o2.de bzw. in der Mein o2 App unter Rechnung und ggf. Einzelverbindungsnachweis nach.

Für künftige Aufenthalte in Grenzregionen empfehlen wir:
- in den Handy-Einstellungen die automatische Netzwahl zu deaktivieren und manuell ein griechisches Netz zu wählen,
- auf Roaming-Info-SMS und den Kostenschutz zu achten,
- unter o2.de die aktuellen Roaming-Hinweise für Nicht-EU-Länder nachzulesen.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert "nicht erstatten" in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52886659.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52886659", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
