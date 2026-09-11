import json
import time
from pathlib import Path

reply = """Guten Tag Christian Schramm,

vielen Dank für Ihre Nachricht zur Kündigung Ihres Mobilfunkvertrags und die Bitte um eine Kündigungsbestätigung. Es ist nachvollziehbar, dass Sie nach Ihrer Kündigung vom 03.08.2026 mit dem von Ihnen genannten Beendigungszeitpunkt 06.09.2026 zeitnah eine schriftliche Bestätigung wünschen.

Den Status Ihrer Kündigung und den hinterlegten Vertragstermin können Sie in Mein o2 prüfen: Tarif & SIM bzw. Tarif & Vertrag – dort erscheint bei hinterlegter Kündigung typischerweise der Hinweis „gekündigt zum:“. Weitere Infos: https://www.o2online.de/mein-o2/ sowie https://www.o2online.de/service/kuendigung/

Unter Tarif & SIM → SIM & Vertrag → Kündigung vormerken können Sie den Vorgang parallel nachvollziehen. Die formelle Kündigungsbestätigung folgt nach Verarbeitung; bei Mobilfunk oft erst im Umfeld der Deaktivierung (häufig genannt: ca. 16 Tage nach Deaktivierung).

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz""".strip().replace("\r\n", "\n")

assert "Christian Schramm" in reply and "06.09.2026" in reply
assert "017670357511" not in reply and "Fall #" not in reply

payload = {"case_id": "#53006438", "response_text": reply, "saved_at": int(time.time())}
Path(".cursor/skills/sprinklr-write-reply/latest_re_reply.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
)
Path("temp_reply.txt").write_bytes((reply + "\n").encode("utf-8"))
print("saved", len(reply))
