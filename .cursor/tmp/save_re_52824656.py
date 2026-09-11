# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Mario Kutscher,

vielen Dank, dass Sie uns auf den versehentlichen Tarifwechsel und Ihren Wunsch nach dem ursprünglich gewünschten 30-GB-Tarif mit Treuerabatt aufmerksam gemacht haben.

Es ist verständlich, dass Sie mit dem nun hinterlegten 150-GB-Tarif nicht einverstanden sind und die Konditionen korrigiert haben möchten – insbesondere nachdem Sie ausdrücklich 30 GB genannt hatten.

Aus Datenschutzgründen bearbeitet das E-Mail-Team keine individuellen Tarifangebote, Vertragsverlängerungen oder Treuerabatt-Aktionen. Für die Anpassung Ihres Tarifs (Mobilfunknummer mit 719 am Ende / Kundennummer mit 155 am Ende) wenden Sie sich bitte an die Kundenbetreuung unter 089 78 79 79 400. Dort können die Vertragsspezialisten passende Bestandskundenangebote und Rabatte mit Ihnen prüfen.

Parallel können Sie in Mein o2 unter o2.de bzw. in der Mein o2 App unter Tarif & Optionen Ihren aktuellen Tarif einsehen und – sofern verfügbar – online eine Vertragsverlängerung bzw. Tarifwechsel-Optionen prüfen.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert "6059667155" not in text
assert "15204041719" not in text and "4041719" not in text
assert "089 78 79 79 400" in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52824656.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52824656", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
