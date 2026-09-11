# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Cecile Zoé Dullin,

vielen Dank, dass Sie uns die erneuten Rechnungsprobleme und die Zahlungsaufforderung geschildert haben – insbesondere, dass zuletzt zu viel abgebucht wurde, die Verrechnung aussteht und Ihr o2 Shop den Vorgang noch prüft.

Es ist verständlich, dass Sie den offenen Betrag nicht begleichen möchten, bevor die strittigen Positionen und die ausstehende Verrechnung geklärt sind.

Bitte prüfen Sie parallel in Mein o2 unter o2.de bzw. in der Mein o2 App unter Rechnung:
- die aktuellen offenen Beträge und Einzelpositionen,
- ob eine Gutschrift oder Verrechnung bereits ausgewiesen ist,
- ältere Rechnungen, auf denen der zu hohe Abzug erkennbar ist.

Damit wir Ihren Vertrag und die Shop-Prüfung zuordnen können, senden Sie uns bitte Ihre Kundennummer und – sofern vorhanden – die Rechnungsnummer(n) der strittigen Beträge. Den Shop-Anhang können Sie im bisherigen E-Mail-Verlauf belassen.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert "Zoé" in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52887530.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52887530", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
