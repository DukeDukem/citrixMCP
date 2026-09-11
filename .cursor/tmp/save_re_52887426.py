# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Ibrahim Darwich,

vielen Dank, dass Sie uns Ihren Wunsch nach einer Ratenzahlung wegen der unerwarteten In-App-Käufe von etwa 550 Euro auf der Mobilfunkrechnung geschildert haben.

Es ist verständlich, dass Sie den offenen Betrag begleichen möchten, ihn aber derzeit nicht auf einmal zahlen können.

Anfragen zu Ratenzahlung und Zahlungsvereinbarungen werden von der zuständigen Fachabteilung für Zahlungsthemen bearbeitet; Ihre Anfrage wurde dorthin weitergeleitet.

Parallel können Sie Folgendes nutzen:
- In Mein o2 unter o2.de bzw. in der Mein o2 App unter Rechnung den offenen Betrag und die Positionen zur Rechnung mit 840/08 am Ende einsehen sowie Drittanbieter-/In-App-Buchungen nachvollziehen.
- Unter den Drittanbieter-Einstellungen eine Sperre setzen, damit künftig keine weiteren Käufe über die Rechnung laufen.
- Für eine individuelle Zahlungsvereinbarung den Mahnwesen-Chat unter o2.de/mahnwesen-chat (Mo–Fr 8–18 Uhr) oder telefonisch 089 78 79 79 456 (Mo–Fr 8–18 Uhr, gemäß Tarif*).

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert "1612594840" not in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text
assert "089 78 79 79 456" in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52887426.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52887426", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
