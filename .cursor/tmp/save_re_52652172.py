# -*- coding: utf-8 -*-
import json
import time
from pathlib import Path

text = """Guten Tag Sabrina Beckers,

vielen Dank, dass Sie sich erneut wegen Ihres Internetanschlusses nach Erhalt des Routers und der in Rechnung gestellten Router-Grundgebühr gemeldet haben.

Es ist verständlich, dass Sie verärgert sind, nachdem Sie bereits länger auf eine Rückmeldung warten, den Anschluss seit Erhalt des Routers nicht nutzen können und nun entgegen der telefonischen Zusage die Grundgebühr abgerechnet sehen. Es tut uns leid, dass Sie in dieser Situation sind.

Um zu verhindern, dass unbefugte Dritte Ihre Kundendaten ändern oder Informationen aus Ihrem Vertrag erhalten, bearbeiten wir E-Mail-Anfragen zu Vertragsinhalten nur dann, wenn im Vorfeld bestimmte Angaben vom Anfragesteller gemacht werden.

Wir versichern Ihnen, dass es sich um eine Sicherheitsmaßnahme handelt, die ausschließlich dem Schutz Ihrer persönlichen Daten dient und bitten um Ihr Verständnis für diese Vorgehensweise.

Lassen Sie uns mit Ihrer Anfrage bitte noch folgende Informationen zukommen:

- die letzten 4 Stellen Ihrer IBAN
- und Ihre Kundennummer

Senden Sie bei Rückfragen den bisherigen E-Mail-Verlauf sowie mögliche Anhänge mit und fügen Sie Ihre Antwort ganz oben ein. Dann kümmern wir uns sofort um Ihr Anliegen.

Noch ein Tipp: Vieles können Sie rund um die Uhr auch direkt online unter o2.de erledigen. Ganz bequem und unabhängig von Öffnungszeiten. Registrieren Sie sich einfach für „Mein o2“.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52652172.txt").write_text(
    text.strip() + "\n", encoding="utf-8"
)
rec = {"case_id": "#52652172", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
