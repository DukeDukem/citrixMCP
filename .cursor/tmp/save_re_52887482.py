# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Anja Sendes-Domin,

vielen Dank, dass Sie uns die Bitte um sofortige Sperrung Ihres Internetanschlusses sowie die Situation rund um Ihre Kündigung und die weiterlaufenden Abbuchungen geschildert haben.

Es ist verständlich, dass Sie den Anschluss an der Hüttruper Str. in Greven nicht weiter nutzen und keine weiteren Beiträge dafür zahlen möchten.

Eine sofortige Außerkraftsetzung des Anschlusses (z. B. über eine Vertragsstillegung) sowie die Klärung dazu bearbeitet die zuständige Fachabteilung; Ihre Anfrage wurde dorthin weitergeleitet.

Parallel können Sie in Mein o2 unter o2.de bzw. in der Mein o2 App:
- unter Tarif & Vertrag den Kündigungsstatus und den frühestmöglichen Kündigungstermin prüfen bzw. eine Kündigung vormerken,
- sofern angeboten, eine Vertragsstillegung beantragen (dabei wird der Anschluss für den Stillegungszeitraum gesperrt; es gelten die dort genannten Voraussetzungen und Gebühren),
- offene Rechnungen unter Rechnung einsehen.

Für die Zuordnung nutzen wir Ihre Kundennummer mit 532 am Ende. Bitte senden Sie bei Rückfragen den bisherigen Verlauf mit und nennen Sie ggf. Ihre Festnetznummer.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert "6112758532" not in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text
assert "Anja Sendes-Domin" in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52887482.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52887482", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
