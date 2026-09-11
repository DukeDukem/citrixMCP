# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Lisa Weiss,

vielen Dank, dass Sie uns das Messergebnis aus der App nachreichen und darauf hinweisen, dass sich das Format nicht in dem Formular hochladen lässt.

Es ist verständlich, dass Sie die Messung zur schlechten Netzabdeckung an Ihrer Wohnadresse dem laufenden Vorgang zuordnen lassen möchten.

Der Anhang mit dem Messergebnis wird dem bestehenden Vorgang zur Netzprüfung zugeordnet. Bitte belassen Sie den bisherigen E-Mail-Verlauf und den Anhang in Ihrer Nachricht.

Zusätzlich können Sie den Status jederzeit im Live-Check unter o2.de bzw. g.o2.de/Live-Check sowie in der Mein o2 App prüfen und dort bei Bedarf erneut Feedback zur Versorgung an Ihrem Standort geben.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

# "wird ... zugeordnet" is agent action statement - OK for forwarding attachment to ongoing case similar to transfer notice
assert text.count("Guten Tag") == 1
assert "Fall #" not in text
assert "Lisa Weiss" in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52454694.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52454694", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
