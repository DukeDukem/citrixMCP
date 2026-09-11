# -*- coding: utf-8 -*-
import json
import time
from pathlib import Path

text = """Guten Tag Harun Gücük,

vielen Dank, dass Sie uns auf den plötzlichen Ausfall Ihres Mobilfunkempfangs aufmerksam gemacht haben.

Es ist verständlich, dass Sie beunruhigt sind, wenn an Ihrem gewohnten Wohnort seit etwa 30 Minuten kein dauerhaftes Netz mehr verfügbar ist und die Signalanzeige auf null bleibt. Es tut uns leid, dass Sie davon betroffen sind.

Bitte prüfen und melden Sie die Situation wie folgt:

1. Nutzen Sie den o2 Live-Check unter https://www.o2online.de/netz/netzstoerung/ (auch in der Mein o2 App): Geben Sie Ihre Wohnadresse ein und prüfen Sie, ob vor Ort eine Störung oder Wartung angezeigt wird.
2. Falls keine Störung angezeigt wird oder das Problem weiterbesteht, melden Sie die Beeinträchtigung dort über „Geben Sie uns Feedback“ / „Jetzt melden“ und hinterlegen Sie Ihre Mobilfunknummer – Sie erhalten per SMS eine Bestätigung und Statusupdates.
3. Zusätzlich hilft oft ein Neustart des Geräts; die o2 my Service App bietet weitere Tests und Tipps zur Entstörung.

Bitte antworten Sie bei Rückfragen mit dem bisherigen E-Mail-Verlauf und möglichst Ihrer genauen Adresse bzw. Mobilfunknummer (nur mit den letzten Ziffern in der Antwort, falls Sie diese hier nennen möchten).

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

# Fix awkward last tip - don't ask for partial phone oddly. Simplify.
text = """Guten Tag Harun Gücük,

vielen Dank, dass Sie uns auf den plötzlichen Ausfall Ihres Mobilfunkempfangs aufmerksam gemacht haben.

Es ist verständlich, dass Sie beunruhigt sind, wenn an Ihrem gewohnten Wohnort seit etwa 30 Minuten kein dauerhaftes Netz mehr verfügbar ist und die Signalanzeige auf null bleibt. Es tut uns leid, dass Sie davon betroffen sind.

Bitte prüfen und melden Sie die Situation wie folgt:

1. Nutzen Sie den o2 Live-Check unter https://www.o2online.de/netz/netzstoerung/ (auch in der Mein o2 App): Geben Sie Ihre Wohnadresse ein und prüfen Sie, ob vor Ort eine Störung oder Wartung angezeigt wird.
2. Falls keine Störung angezeigt wird oder das Problem weiterbesteht, melden Sie die Beeinträchtigung dort über „Geben Sie uns Feedback“ bzw. „Jetzt melden“ und hinterlegen Sie Ihre Mobilfunknummer – Sie erhalten per SMS eine Bestätigung sowie Statusupdates.
3. Starten Sie Ihr Gerät neu; ergänzend bietet die o2 my Service App weitere Tests und Tipps zur Entstörung.

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
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52880640.txt").write_text(
    text.strip() + "\n", encoding="utf-8"
)
rec = {"case_id": "#52880640", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
