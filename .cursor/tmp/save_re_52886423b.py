# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Dagmar Gehmacher,

vielen Dank, dass Sie uns die Einmalgebühr von 29,99 Euro für die Ersatz-SIM-Karte und die Umstände um Ihr Handy-Problem geschildert haben.

Es ist verständlich, dass Sie mit der Berechnung nicht einverstanden sind, nachdem die zugesandte SIM Ihr Problem nicht gelöst hat, die Mobilfunkfunktion zuvor deaktiviert war und im o2 Shop die Karte als nicht nötig eingestuft wurde – insbesondere nach dem zusätzlichen Aufwand für den Shop-Besuch.

Wir bestätigen Ihnen die Erstattung der Einmalgebühr von 29,99 Euro. Die Gutschrift wird mit Ihrem Kundenkonto verrechnet und erscheint in der Regel auf Ihrer nächsten Rechnung bzw. in Mein o2 unter Rechnung.

Sie können den Stand jederzeit unter o2.de bzw. in der Mein o2 App unter Rechnung einsehen (Ihre genannte Rechnung endet auf 554).

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert "16049970554" not in text
assert "Erstattung" in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52886423.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52886423", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
