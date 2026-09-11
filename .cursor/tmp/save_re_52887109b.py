# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Raya Cherni,

vielen Dank, dass Sie die Bereinigung bzw. das Zurücksetzen Ihres Geräts sowie die weiterhin gesperrte SMS-Versandfunktion für die Mobilfunknummer mit 099 am Ende bestätigt haben.

Es ist verständlich, dass Sie den SMS-Versand wieder uneingeschränkt nutzen möchten.

Die systemseitige Freischaltung Ihres SMS-Versands wird beantragt. Nach der Freigabe dauert die Entsperrung in der Regel etwa zwei bis drei Tage. Bitte prüfen Sie den Versand danach erneut.

Zur Sicherheit behalten Sie die Drittanbieter- und Premium-Sperren in Mein o2 unter o2.de bzw. in der Mein o2 App bei, und installieren Sie weiterhin nur vertrauenswürdige Apps.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert "30873099" not in text
assert "894921" not in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52887109.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52887109", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
