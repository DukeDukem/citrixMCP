import json
import time
from pathlib import Path

reply = """Guten Tag,

vielen Dank für Ihre Nachricht zur Kündigung eines Mobilfunkvertrags und die Bitte um eine Kündigungsbestätigung.

Aus Datenschutzgründen bearbeiten wir Vertragsanliegen nicht über Dritte und geben keine Informationen zu Kundenkonten an Dritte weiter. Bitte bitten Sie den Vertragsinhaber bzw. die Vertragsinhaberin, uns das Anliegen direkt von der eigenen, bei o2 hinterlegten E-Mail-Adresse zu senden.

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

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz""".strip().replace("\r\n", "\n")

# Data-safety gates
assert reply.count("Guten Tag") == 1
assert "Christian Schramm" not in reply
assert "06.09" not in reply and "0176" not in reply
assert "Halle" not in reply and "Gustav" not in reply
assert "congstar" not in reply.lower()
assert "Fall #" not in reply
assert "letzten 4 Stellen Ihrer IBAN" in reply
assert "Kundennummer" in reply
assert "Dritte" in reply

payload = {
    "case_id": "#53006438",
    "response_text": reply,
    "saved_at": int(time.time()),
    "source": "user_directed",
}
base = Path(".cursor/skills/sprinklr-write-reply")
for name in ("latest_re_reply.json", "latest_user_directed_reply.json"):
    (base / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
Path("temp_reply.txt").write_bytes((reply + "\n").encode("utf-8"))
print("synced", len(reply))
