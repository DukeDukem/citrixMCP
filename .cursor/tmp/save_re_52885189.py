# -*- coding: utf-8 -*-
import json
import time
from pathlib import Path

text = """Guten Tag Rolf Pabst,

vielen Dank, dass Sie uns wegen der fehlenden Abbuchung von 3,96 EUR zu Ihrer Handy-Rechnung (Rechnungsnummer 1625236968/08) kontaktiert haben.

Es ist verständlich, dass Sie nachvollziehen möchten, warum der Betrag – auch über Vormonate hinweg – nicht von Ihrem Bankkonto eingezogen wurde.

Bitte prüfen Sie den Zahlungsstatus und die hinterlegten Daten direkt in Mein o2:

1. Melden Sie sich unter o2.de bzw. in der Mein o2 App an und öffnen Sie Ihre Rechnungen – dort sehen Sie offene Beträge und den Status zur Rechnungsnummer 1625236968/08.
2. Unter Meine Daten / Bankverbindung prüfen Sie, ob eine gültige IBAN und das Lastschriftmandat hinterlegt sind. Änderungen benötigen in der Regel einige Werktage Vorlauf vor dem nächsten Einzug.
3. Offene Beträge können Sie bei Bedarf selbst ausgleichen. Hinweise und Zahlungsmöglichkeiten finden Sie unter https://www.o2online.de/service/rechnung-zahlung/ – bei Überweisung bitte die Kundennummer mit 118 am Ende als Verwendungszweck angeben.

Bitte antworten Sie bei Rückfragen mit dem bisherigen E-Mail-Verlauf.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52885189.txt").write_text(
    text.strip() + "\n", encoding="utf-8"
)
rec = {"case_id": "#52885189", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
