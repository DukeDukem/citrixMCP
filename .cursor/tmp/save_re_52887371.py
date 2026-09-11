# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Alex Schmidt,

vielen Dank, dass Sie uns die Position „Mehrwertdienste o2 unlimited Games Flatrates“ über 12,99 Euro auf Ihrer Juli-Rechnung vom 30.07. gemeldet haben.

Es ist verständlich, dass Ihnen diese Buchung vom 04.07. unklar ist, wenn Sie keinen App-Kauf oder kein Abo bewusst abgeschlossen haben, und dass Sie eine Erklärung bzw. – falls unberechtigt – eine Korrektur wünschen.

Bei o2 Unlimited Games handelt es sich um einen kostenpflichtigen o2-Mehrwertdienst (Spiele-Flatrate), der über die Mobilfunkrechnung abgerechnet wird. Anfragen dazu werden von der zuständigen Fachabteilung bearbeitet; Ihre Anfrage wurde dorthin weitergeleitet.

Parallel können Sie in Mein o2 unter o2.de bzw. in der Mein o2 App:
- unter Rechnung die Position zur Rechnung mit 593/08 am Ende nachvollziehen,
- gebuchte Mehrwert-/Entertainment-Dienste bzw. Abos prüfen und – sofern angezeigt – kündigen/deaktivieren,
- unter den Drittanbieter-Einstellungen eine Sperre setzen, damit künftig keine unerwünschten Buchungen über die Rechnung entstehen.

Für die Zuordnung nutzen wir Ihre Kundennummer mit 847 am Ende.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert "6098222847" not in text
assert "1626467593" not in text
assert "CS_Hardware" not in text
assert "CS_XF_E_HARDWARE" not in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52887371.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52887371", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
