# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag,

vielen Dank, dass Sie uns Ihre Kundennummer und die letzten vier Stellen Ihrer IBAN übermittelt haben und erneut um Rückmeldung zu Ihrem Anliegen mit Polizeianzeige sowie der Boku-Bestätigung zur Rückerstattung bitten.

Es ist verständlich, dass Sie nach der Wartezeit den Stand und das weitere Vorgehen wissen möchten – insbesondere weil Sie die Unterlagen bereits geschickt haben.

Bitte prüfen Sie parallel in Mein o2 unter o2.de bzw. in der Mein o2 App:
- unter Rechnung, ob die bestrittene Drittanbieter-/Boku-Position noch offen ist oder bereits ausgeglichen wirkt,
- unter den Drittanbieter-Einstellungen eine Sperre für künftige Drittanbieterdienste, damit keine neuen Buchungen entstehen.

Kontaktdaten des Drittanbieters stehen in der Regel auf der Mobilfunkrechnung; dort können Sie den Dienst auch direkt nachvollziehen. Für Ihr Vertragsverhältnis mit der Kundennummer mit 309 am Ende können Sie uns bei Bedarf das Rechnungsdatum der bestrittenen Position noch einmal nennen (ohne die vollständige Kundennummer zu wiederholen).

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert "6085032309" not in text
assert "7106" not in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52882167.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52882167", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
