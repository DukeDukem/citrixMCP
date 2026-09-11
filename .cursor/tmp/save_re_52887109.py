# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Raya Cherni,

vielen Dank, dass Sie uns die gesperrte SMS-Versandfunktion und den Wechsel auf Ihre neue SIM-Karte nach der kompromittierten Karte geschildert haben.

Es ist verständlich, dass Sie den SMS-Versand wieder nutzen möchten, nachdem Spam-/Phishing-Versand über die alte Karte behoben wurde und Sie eine neue SIM erhalten haben.

Zur Sicherheit prüfen Sie bitte vor der Freischaltung noch Folgendes:
- Nutzen Sie dasselbe Handy wie zuvor: setzen Sie das Gerät auf Werkseinstellungen zurück (Backup kann Schadsoftware ggf. wieder einspielen – sensible Daten vorher sichern).
- Installieren Sie danach nur vertrauenswürdige Apps neu.
- In Mein o2 unter o2.de bzw. in der Mein o2 App können Sie Drittanbieterdienste und Premium-Rufnummern sperren, um Folgekosten zu vermeiden.

Antworten Sie kurz auf diese E-Mail, dass Ihr Gerät bereinigt bzw. zurückgesetzt ist und der SMS-Versand für die Mobilfunknummer mit 099 am Ende weiterhin blockiert ist. Dann kann die SMS-Sperre systemseitig für Ihren Anschluss beantragt werden.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert "894921007118370102" not in text
assert "30873099" not in text
assert "15730873099" not in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52887109.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52887109", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
